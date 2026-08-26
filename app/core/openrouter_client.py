import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# OpenRouter free-tier models are capped at 20 requests/minute and 50/day.
# Space calls at least this far apart so a 48-attack run doesn't burst past the RPM cap.
_MIN_CALL_INTERVAL = 3
_last_call_at = 0.0


def chat_completion(model, messages, temperature=0.7, max_retries=5):
    """POST to OpenRouter's OpenAI-compatible endpoint, paced for the free tier.

    Paces calls at least _MIN_CALL_INTERVAL apart and retries 429s with exponential
    backoff. Returns the assistant message content (stripped) or raises RuntimeError
    if the request can't be completed.
    """
    global _last_call_at

    headers = {
        "Authorization": f"Bearer {_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {"model": model, "messages": messages, "temperature": temperature}

    delay = 3
    for attempt in range(max_retries):
        elapsed = time.monotonic() - _last_call_at
        if elapsed < _MIN_CALL_INTERVAL:
            time.sleep(_MIN_CALL_INTERVAL - elapsed)

        try:
            resp = requests.post(_OPENROUTER_URL, headers=headers, json=body, timeout=30)
        except requests.exceptions.RequestException as e:
            _last_call_at = time.monotonic()
            if attempt == max_retries - 1:
                raise RuntimeError(f"OpenRouter request failed: {e}")
            time.sleep(delay)
            delay *= 2
            continue

        _last_call_at = time.monotonic()

        if resp.status_code == 429:
            if attempt == max_retries - 1:
                raise RuntimeError(f"OpenRouter rate limit exceeded after {max_retries} attempts: {resp.text[:300]}")
            time.sleep(delay)
            delay *= 2
            continue

        if resp.status_code != 200:
            raise RuntimeError(f"OpenRouter error {resp.status_code}: {resp.text[:300]}")

        data = resp.json()
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError(f"OpenRouter returned no choices: {data}")
        return choices[0]["message"]["content"].strip()

    raise RuntimeError("OpenRouter request failed after retries")
