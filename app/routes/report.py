import glob
import os
from flask import Blueprint

report_bp = Blueprint("report", __name__)

_REPORTS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "reports"))


@report_bp.route("/report")
def report():
    files = sorted(glob.glob(os.path.join(_REPORTS_DIR, "*.html")), reverse=True)
    if not files:
        return "No reports generated yet. Run the pipeline first.", 404
    with open(files[0], encoding="utf-8") as f:
        return f.read()
