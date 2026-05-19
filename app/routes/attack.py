import json
import time
from flask import Blueprint, request, jsonify, Response, stream_with_context

from app.core.attack_generator import generate_all, _normalise, _generate, CANONICAL_CATEGORIES
from app.core.executor import execute
from app.core.judge import judge as run_judge
from app.core.reporter import generate_report
from db.schema import get_db
from seed.jailbreak import jailbreak
from seed.jailbreak_extensions import ALL_EXTENSIONS

attack_bp = Blueprint("attack", __name__)


def _sse(data):
    return f"data: {json.dumps(data)}\n\n"


@attack_bp.route("/attack", methods=["POST"])
def attack():
    data = request.get_json()
    category = data.get("category", "social_engineering")

    seeds = _normalise(jailbreak + ALL_EXTENSIONS)
    category_seeds = [s for s in seeds if s["category"] == category]
    examples = category_seeds[:3] if len(category_seeds) >= 3 else []
    attacks = _generate(category, examples)[:1]
    if not attacks:
        return jsonify({
            "error": "Could not generate attack",
            "attack": "",
            "response": "",
            "success": False,
            "severity": 0,
            "reason": "Attack generation failed — try again",
            "leaked_markers": [],
        }), 200

    executed = execute(attacks)
    judged = run_judge(executed)
    result = judged[0]

    return jsonify({
        "attack": attacks[0]["prompt"],
        "response": executed[0]["response"],
        "success": result.get("success"),
        "severity": result.get("severity"),
        "reason": result.get("reason"),
        "leaked_markers": result.get("leaked_markers", []),
    })


@attack_bp.route("/run-pipeline", methods=["POST"])
def run_pipeline():
    attacks = generate_all()
    judged = []
    for i, attack in enumerate(attacks):
        if i > 0:
            time.sleep(1)
        executed = execute([attack])
        judged.extend(run_judge(executed))
    generate_report(judged)
    successes = len([r for r in judged if r.get("success")])
    return jsonify({"successes": successes, "total": len(judged)})


@attack_bp.route("/stream")
def stream():
    def generate():
        all_results = []
        seeds = _normalise(jailbreak + ALL_EXTENSIONS)
        attack_n = 0
        total = len(CANONICAL_CATEGORIES) * 5

        for category in CANONICAL_CATEGORIES:
            yield _sse({"type": "phase", "category": category})

            category_seeds = [s for s in seeds if s["category"] == category]
            examples = category_seeds[:3] if len(category_seeds) >= 3 else []

            try:
                attacks = _generate(category, examples)
            except Exception as e:
                yield _sse({"type": "error", "msg": f"Generate failed for {category}: {e}"})
                continue

            for attack in attacks:
                attack_n += 1
                yield _sse({"type": "attack", "n": attack_n, "total": total,
                            "category": category, "prompt": attack["prompt"][:140]})
                try:
                    executed = execute([attack])
                    yield _sse({"type": "response", "preview": executed[0]["response"][:140]})
                    judged = run_judge(executed)
                    result = judged[0]
                    all_results.append(result)
                    yield _sse({"type": "verdict",
                                "success": result.get("success", False),
                                "severity": result.get("severity", 0),
                                "reason": result.get("reason", ""),
                                "markers": result.get("leaked_markers", [])})
                except Exception as e:
                    yield _sse({"type": "error", "msg": f"Attack {attack_n} failed: {e}"})

        try:
            generate_report(all_results)
            successes = sum(1 for r in all_results if r.get("success"))
            yield _sse({"type": "done", "total": len(all_results),
                        "successes": successes, "report_ready": True})
        except Exception as e:
            yield _sse({"type": "error", "msg": f"Report generation failed: {e}"})

    return Response(
        stream_with_context(generate()),
        content_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )


@attack_bp.route("/settings", methods=["GET"])
def get_settings():
    conn = get_db()
    cur = conn.cursor()
    rows = cur.execute("SELECT key, value FROM settings").fetchall()
    settings = {row[0]: row[1] for row in rows}
    targets = cur.execute("SELECT id, name FROM targets").fetchall()
    conn.close()
    settings["targets"] = [{"id": t[0], "name": t[1]} for t in targets]
    return jsonify(settings)


@attack_bp.route("/settings", methods=["POST"])
def save_settings():
    data = request.get_json()
    allowed = {"aggression_level", "judge_model", "active_target_id"}
    conn = get_db()
    updated = []
    for key, value in data.items():
        if key in allowed:
            conn.execute("UPDATE settings SET value=? WHERE key=?", (str(value), key))
            updated.append(key)
    conn.commit()
    conn.close()
    return jsonify({"status": "ok", "updated": updated})
