import json
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
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        try:
            verdict = json.loads(raw)
        except Exception:
            verdict = {"success": False, "severity": 0, "reason": "parse error", "leaked_markers": []}
        results.append({**item, **verdict})
    return results
