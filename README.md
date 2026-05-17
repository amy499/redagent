# RedAgent

An adversarial red-teaming pipeline that automatically generates, fires, and judges prompt injection attacks against **WealthGuard AI** — a simulated financial assistant at Meridian Capital hedge fund. Results are compiled into a hardening report with per-category mitigations.

---

## How It Works

```
attack_generator → executor → judge → reporter
      ↓               ↓          ↓         ↓
  30 prompts     responses   verdicts   report.html
```

1. **Attack Generator** — loads seed jailbreaks from `src/`, normalises them into 6 canonical categories, and uses Groq `llama-3.3-70b-versatile` to generate 5 novel variants per category (30 total).
2. **Executor** — POSTs each prompt to the victim bot's `/chat` endpoint and collects responses.
3. **Judge** — scores each `(prompt, response)` pair using a structured evaluator prompt, returning `success`, `severity`, `reason`, and `leaked_markers`.
4. **Reporter** — renders an HTML report with a summary, severity breakdown table, findings list, and per-category mitigations.

---

## Attack Categories

| Category | Description |
|---|---|
| `direct_prompt_injection` | Override system instructions via user input |
| `roleplay_bypass` | Persona/fiction framing to bypass restrictions |
| `social_engineering` | Urgency, authority, or impersonation tactics |
| `indirect_injection` | Instructions embedded in documents or external content |
| `goal_hijacking` | Gradually shift the model's objective mid-conversation |
| `jailbreak_hypothetical` | Hypothetical or "what if" framings to extract real data |

---

## Prerequisites

- Python 3.11+
- A [Groq](https://console.groq.com) API key

---

## Setup

```bash
# 1. Install dependencies
pip install flask groq rich jinja2 python-dotenv requests

# 2. Configure environment
cp .env.example .env
# Edit .env and set: GROQ_API_KEY=your_key_here
```

---

## Running

### Start the victim bot (required in a separate terminal)

```bash
python victim_bot.py
# Starts WealthGuard AI on http://localhost:5000
```

The bot also serves a demo UI at `http://localhost:5000` where you can fire individual attacks interactively.

### Tracer bullet — single attack end-to-end

```bash
python main.py --single-attack --category social_engineering
```

Fires one attack in the given category and prints the judge verdict to the terminal.

Available categories: `direct_prompt_injection`, `roleplay_bypass`, `social_engineering`, `indirect_injection`, `goal_hijacking`, `jailbreak_hypothetical`

### Full pipeline — 30 attacks

```bash
python main.py
```

Runs all 6 categories, judges every result, and writes `report.html`.

---

## Project Structure

```
redagent/
├── victim_bot.py              # Flask app — WealthGuard AI (port 5000) + demo UI routes
├── attack_generator.py        # Loads seeds, generates 30 adversarial prompts via Groq
├── executor.py                # Sends prompts to victim bot, collects responses
├── judge.py                   # Scores each attack using Groq + evaluator prompt
├── reporter.py                # Renders Jinja2 HTML report with mitigations
├── main.py                    # Pipeline orchestrator (--single-attack flag)
├── src/
│   ├── jailbreak.py           # Seed jailbreak library (read-only)
│   ├── jailbreak_extensions.py # Finance-specific attack seeds (read-only)
│   └── evaluator_prompt.txt   # Judge prompt template
├── templates/
│   ├── report.html            # Jinja2 report template
│   └── demo.html              # Interactive demo UI
├── .env.example               # Environment variable template
└── report.html                # Generated after running the full pipeline
```

---

## Report Sections

The generated `report.html` contains:

1. **Summary** — total attacks, successes, overall success rate
2. **Severity breakdown** — per-category table: attacks tried / succeeded / avg severity
3. **Findings** — each successful attack with prompt, response excerpt, severity badge, and leaked markers
4. **Mitigations** — one hardening recommendation for each vulnerable category

---

## Data Contract

Each attack accumulates fields as it moves through the pipeline:

```python
# After attack_generator
{"category": str, "prompt": str}

# After executor
{"category": str, "prompt": str, "response": str}

# After judge
{"category": str, "prompt": str, "response": str,
 "success": bool, "severity": int, "reason": str, "leaked_markers": [str]}
```

---

## Tech Stack

- **Flask** — victim bot HTTP server
- **Groq SDK** (`llama-3.3-70b-versatile`) — attack generation, victim bot, and judging
- **Rich** — terminal output formatting
- **Jinja2** — HTML report rendering
- **python-dotenv** — environment variable management
