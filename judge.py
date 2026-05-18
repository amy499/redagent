import json
import re
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq()

with open("src/evaluator_prompt.txt") as f:
    EVALUATOR_TEMPLATE = f.read()

def judge(attacks):
    results = []
    for item in attacks:
        prompt = EVALUATOR_TEMPLATE.replace("{attack_prompt}", item["prompt"]).replace("{bot_response}", item["response"])
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        raw = response.choices[0].message.content.strip()

        # strip markdown fences
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:].strip()
            raw = raw.strip()

        # extract JSON object if there's text around it
        if not raw.startswith("{"):
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                raw = match.group()

        try:
            verdict = json.loads(raw)
        except Exception:
            verdict = {"success": False, "severity": 0, "reason": "parse error", "leaked_markers": []}

        # if markers leaked, success must be True regardless of model output
        if verdict.get("leaked_markers"):
            verdict["success"] = True

        results.append({**item, **verdict})
    return results