import time
import requests


VICTIM_URL = "http://127.0.0.1:5000/chat"


def execute(attacks):
    results = []
    for item in attacks:
        answer = _chat(item["prompt"])
        results.append({**item, "response": answer})
    return results


def _chat(prompt):
    for attempt in range(2):
        try:
            resp = requests.post(VICTIM_URL, json={"message": prompt}, timeout=30)
            if resp.status_code == 429:
                if attempt == 0:
                    time.sleep(10)
                    continue
                return "[ERROR: rate limit]"
            resp.raise_for_status()
            return resp.json().get("response", "")
        except Exception as e:
            if attempt == 0:
                time.sleep(10)
                continue
            return f"[ERROR: {e}]"
    return "[ERROR: max retries exceeded]"
