import time
import requests

from db.schema import get_db

_FALLBACK_URL = "http://127.0.0.1:5000/chat"


def execute(attacks):
    # Read active target config from DB on every call so settings changes take effect immediately
    conn = get_db()
    cur = conn.cursor()
    row = cur.execute("SELECT value FROM settings WHERE key='active_target_id'").fetchone()
    active_target_id = int(row[0]) if row else 1
    target = cur.execute(
        "SELECT endpoint_url, request_field, response_field, auth_header FROM targets WHERE id = ?",
        (active_target_id,),
    ).fetchone()
    conn.close()

    if target:
        endpoint_url   = target[0] or _FALLBACK_URL
        request_field  = target[1] or "message"
        response_field = target[2] or "response"
        auth_header    = target[3]
    else:
        endpoint_url   = _FALLBACK_URL
        request_field  = "message"
        response_field = "response"
        auth_header    = None

    results = []
    for item in attacks:
        answer = _chat(item["prompt"], endpoint_url, request_field, response_field, auth_header)
        results.append({**item, "response": answer})
    return results


def _chat(prompt, endpoint_url, request_field, response_field, auth_header):
    headers = {"Content-Type": "application/json"}
    if auth_header:
        headers["Authorization"] = auth_header
    body = {request_field: prompt}

    for attempt in range(2):
        try:
            resp = requests.post(endpoint_url, json=body, headers=headers, timeout=15)
            if resp.status_code == 429:
                if attempt == 0:
                    time.sleep(10)
                    continue
                return "[ERROR: rate limit]"
            resp.raise_for_status()
            resp_json = resp.json()
            if response_field in resp_json:
                return resp_json[response_field]
            return f"[ERROR: field '{response_field}' not in response: {resp.text[:200]}]"
        except requests.exceptions.Timeout:
            if attempt == 0:
                time.sleep(5)
                continue
            return "Connection timed out"
        except requests.exceptions.ConnectionError:
            if attempt == 0:
                time.sleep(5)
                continue
            return "Could not connect to target endpoint"
        except Exception as e:
            if attempt == 0:
                time.sleep(10)
                continue
            return f"[ERROR: {e}]"
    return "[ERROR: max retries exceeded]"
