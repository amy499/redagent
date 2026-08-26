# RedAgent — What Happens After Judgment (Feedback Loop Analysis)

## 1. The pipeline as it actually runs

```
attack_generator.generate_all()   →   executor.execute()   →   judge.judge()   →   reporter.generate_report()
   (Groq generates prompts)          (POST to target)         (marker match          (Jinja2 HTML +
                                                                 + LLM verdict,          SQLite `reports` row)
                                                                 writes SQLite
                                                                 `results` rows)
```

Entry points that drive this: `main.py:run_full()`, `app/routes/attack.py:run_pipeline()`, `app/routes/attack.py:stream()`. All three call the same four functions in the same order, once, and then stop.

## 2. Exactly what happens after judgment

`judge.judge()` (`app/core/judge.py:39-140`) does two things per attack:

1. Inserts a row into the `results` table (`prompt_sent`, `bot_response`, `success`, `severity`, `leaked_markers`, `reason`, `category`) — `judge.py:116-134`.
2. Returns the annotated list back up the call stack.

That list is handed straight to `reporter.generate_report()` (`app/core/reporter.py:21-80`), which:

- Groups results by `category`, computes `success_rate` and per-category `avg_severity` (`reporter.py:22-40`).
- Looks up a **static, hardcoded** mitigation string per category that had ≥1 success, from the module-level `MITIGATIONS` dict (`reporter.py:11-18`). This dict is fixed at import time — it is never generated from the judge's actual `reason` text, never varies with severity, and is identical no matter what the attack content was.
- Renders `report.html`, writes it to `reports/report_<timestamp>.html`.
- Inserts one summary row into the `reports` table (`filename`, `total_attacks`, `successes`, `breach_rate`) — `reporter.py:63-77`.

**And that's it.** The function returns the file path. Nothing downstream consumes the `reports` or `results` tables to change future behavior.

## 3. Where a flywheel would have to plug in — and doesn't

| Component | Reads from `results`/`reports` tables? | Adapts based on past judgments? |
|---|---|---|
| `attack_generator.generate_all()` | No — always pulls the same static seeds from `seed/jailbreak.py` / `jailbreak_extensions.py` (explicitly read-only, per `CLAUDE.md`) | No — few-shot examples are always "first 3 seeds in DB for this category," never "3 highest-severity past successes" |
| `chat.py` (`WealthGuard` system prompt) | No | No — `SYSTEM_PROMPT` is built once at **module import time** from `app/data/wealthguard_data.json` (`chat.py:70`) and never touched again while the process runs |
| `reporter.MITIGATIONS` | No | No — 6 fixed strings, one per category, chosen by category key alone |
| Judge's `severity`/`reason` | Stored, displayed | Never referenced anywhere else in the codebase (`grep` for `severity` outside `judge.py`/`reporter.py`/templates turns up nothing that consumes it programmatically) |

Every "run full pipeline" is therefore an **independent, memoryless trial**. Run it ten times in a row and the tenth run generates attacks with the same seed pool, same few-shot examples, and hits a target whose defenses haven't moved, unless a person intervenes by hand between runs.

## 4. Defining a feedback loop / flywheel explicitly

For a system to be a genuine (even rudimentary) flywheel, it needs a **closed loop**: output of stage N must become an input that changes stage 1 on the *next* cycle, without a human re-authoring code or prompts in between. Concretely, that requires at least one of:

1. **Generator feedback** — `attack_generator` reads prior `results` and re-weights which seeds/categories/temperature to use next (e.g., "roleplay_bypass had 0% success in the last 3 reports, spend fewer tokens there; try mutated variants of the 2 prompts that scored severity ≥4").
2. **Defender feedback** — the judge's findings (or `MITIGATIONS`) get programmatically folded into the target's system prompt / guardrails before the next run (e.g., appending "never discuss ASML order timing" after a leak on that marker), so the target actually hardens between iterations.
3. **Judge feedback** — the judge's own scoring criteria adjust based on false-positive/negative corrections (there's no correction mechanism here at all — no human-in-the-loop labeling that updates the evaluator prompt).

**None of these three loops exist in RedAgent today.** What exists is stage 1→2→3→4 exactly once per invocation, with the only "memory" being human-readable artifacts (the HTML report, the `results`/`reports` tables) that a person can look at and *then choose* to go edit `wealthguard_data.json`, `MITIGATIONS`, or the seed files by hand — which is a human closing the loop, not the system.

## 5. Verdict on "rudimentary flywheel"

Calling the current structure a flywheel would be generous. What RedAgent has is:

- A **scorecard generator** (judge + reporter) — solid, structured, persisted.
- A **static mitigation lookup**, not a mitigation *generator* — it's a dictionary keyed by category, unrelated to the specific judge output.
- **Zero code paths** that read `results`/`reports` back into `attack_generator`, `chat.py`'s system prompt, or the judge itself.

So: it produces the *raw material* a flywheel would consume (categorized, severity-scored breach data), but nothing in the repo turns that material back into a changed input for the next cycle. The `Roadmap` section of `README.md` even lists "Real third-party target testing" and "CI/CD integration" as still `[ ]` — consistent with there being no iterative-hardening loop yet.

## 6. What minimal change would make it a real (if rudimentary) flywheel

Smallest viable version, in order of effort:
1. After `generate_report()`, have `reporter` also emit a short "top failing categories + example leaked prompts" summary and write it to a file `last_run_feedback.json`.
2. Have `attack_generator._generate()` check for that file and, if present, inject the **highest-severity prompts from the previous run** as additional few-shot examples for categories that succeeded — turning "yesterday's win" into "today's more refined attack."
3. Optionally, auto-append a defensive clause to `wealthguard_data.json`'s system-prompt builder for any marker that leaked, so the target measurably hardens run-over-run and you can chart breach-rate trending down.

None of this exists yet — this section is a proposal, not a description of current behavior.
