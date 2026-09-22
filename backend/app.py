"""
Backend entry point.

    python init_db.py   # once, to create tables + seed data from schema.sql
    python app.py        # start the API server
"""
from datetime import timedelta

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import Config
from routes import api


def create_app():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = Config.JWT_SECRET_KEY
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=Config.JWT_ACCESS_TOKEN_EXPIRES_MIN)

    CORS(app)  # allow the frontend (served separately) to call this API
    JWTManager(app)

    app.register_blueprint(api, url_prefix="/api")

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
