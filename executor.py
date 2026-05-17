import requests


VICTIM_URL = "http://127.0.0.1:5000/chat"


def execute(attacks):
    results = []
    for item in attacks:
        try:
            resp = requests.post(VICTIM_URL, json={"message": item["prompt"]}, timeout=30)
            resp.raise_for_status()
            answer = resp.json().get("answer", "")
        except Exception as e:
            answer = f"[ERROR: {e}]"
        results.append({**item, "response": answer})
    return results
