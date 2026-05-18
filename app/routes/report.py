import glob
import os
from flask import Blueprint, jsonify, send_from_directory

from db.schema import get_db

report_bp = Blueprint("report", __name__)

_REPORTS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "reports"))


@report_bp.route("/report")
def report():
    files = sorted(glob.glob(os.path.join(_REPORTS_DIR, "*.html")), reverse=True)
    if not files:
        return "No reports generated yet. Run the pipeline first.", 404
    with open(files[0], encoding="utf-8") as f:
        return f.read()


@report_bp.route("/reports")
def list_reports():
    conn = get_db()
    cur = conn.cursor()
    rows = cur.execute("""
        SELECT r.id, r.filename, r.total_attacks, r.successes,
               r.breach_rate, r.created_at, t.name AS target_name
        FROM reports r
        JOIN targets t ON r.target_id = t.id
        ORDER BY r.created_at DESC
    """).fetchall()
    conn.close()
    return jsonify([{
        "id":           row[0],
        "filename":     row[1],
        "total_attacks": row[2],
        "successes":    row[3],
        "breach_rate":  row[4],
        "created_at":   row[5],
        "target_name":  row[6],
    } for row in rows])


@report_bp.route("/reports/<path:filename>")
def serve_report(filename):
    return send_from_directory(_REPORTS_DIR, filename)
