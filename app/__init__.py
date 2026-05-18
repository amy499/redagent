import os
from flask import Flask


def create_app():
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    app = Flask(__name__, template_folder=template_dir)

    from app.routes.chat import chat_bp
    from app.routes.attack import attack_bp
    from app.routes.report import report_bp

    app.register_blueprint(chat_bp)
    app.register_blueprint(attack_bp)
    app.register_blueprint(report_bp)

    return app
