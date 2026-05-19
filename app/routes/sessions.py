from flask import Blueprint, request, jsonify

from db.schema import get_db

sessions_bp = Blueprint("sessions", __name__)


@sessions_bp.route("/sessions", methods=["POST"])
def create_session():
    conn = get_db()
    cur = conn.cursor()
    row = cur.execute("SELECT value FROM settings WHERE key='active_target_id'").fetchone()
    active_target_id = int(row[0]) if row else 1
    cur.execute(
        "INSERT INTO sessions (target_id, total_messages, attacks_fired, breaches) VALUES (?, 0, 0, 0)",
        (active_target_id,),
    )
    conn.commit()
    session_id = cur.lastrowid
    conn.close()
    return jsonify({"session_id": session_id})


@sessions_bp.route("/sessions/<int:session_id>/messages", methods=["POST"])
def add_message(session_id):
    data = request.get_json()
    role            = data.get("role", "user")
    content         = data.get("content", "")
    is_attack       = int(data.get("is_attack", 0))
    attack_category = data.get("attack_category")
    success         = data.get("success")
    severity        = data.get("severity")
    leaked_markers  = data.get("leaked_markers")
    reason          = data.get("reason")
    mitigation      = data.get("mitigation")

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO messages
               (session_id, role, content, is_attack, attack_category,
                success, severity, leaked_markers, reason, mitigation)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (session_id, role, content, is_attack, attack_category,
         success, severity, leaked_markers, reason, mitigation),
    )
    message_id = cur.lastrowid

    cur.execute(
        "UPDATE sessions SET total_messages = total_messages + 1 WHERE id = ?",
        (session_id,),
    )
    if is_attack:
        cur.execute(
            "UPDATE sessions SET attacks_fired = attacks_fired + 1 WHERE id = ?",
            (session_id,),
        )
        if success:
            cur.execute(
                "UPDATE sessions SET breaches = breaches + 1 WHERE id = ?",
                (session_id,),
            )

    conn.commit()
    conn.close()
    return jsonify({"message_id": message_id})


@sessions_bp.route("/sessions", methods=["GET"])
def list_sessions():
    conn = get_db()
    cur = conn.cursor()
    rows = cur.execute("""
        SELECT s.id, s.started_at, s.ended_at,
               s.total_messages, s.attacks_fired, s.breaches,
               t.name AS target_name
        FROM sessions s
        JOIN targets t ON s.target_id = t.id
        ORDER BY s.started_at DESC
        LIMIT 50
    """).fetchall()
    conn.close()
    return jsonify([{
        "id":             row[0],
        "started_at":     row[1],
        "ended_at":       row[2],
        "total_messages": row[3],
        "attacks_fired":  row[4],
        "breaches":       row[5],
        "target_name":    row[6],
    } for row in rows])


@sessions_bp.route("/sessions/<int:session_id>/messages", methods=["GET"])
def get_messages(session_id):
    conn = get_db()
    cur = conn.cursor()
    rows = cur.execute("""
        SELECT id, role, content, is_attack,
               attack_category, success, severity,
               leaked_markers, reason, mitigation, timestamp
        FROM messages
        WHERE session_id = ?
        ORDER BY timestamp ASC
    """, (session_id,)).fetchall()
    conn.close()
    return jsonify([{
        "id":             row[0],
        "role":           row[1],
        "content":        row[2],
        "is_attack":      row[3],
        "attack_category": row[4],
        "success":        row[5],
        "severity":       row[6],
        "leaked_markers": row[7],
        "reason":         row[8],
        "mitigation":     row[9],
        "timestamp":      row[10],
    } for row in rows])
