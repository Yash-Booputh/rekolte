from flask import Flask, jsonify
from flask_cors import CORS

from routes.auth import auth_bp
from routes.predict import predict_bp
from routes.harvest import harvest_bp
from routes.bulletins import bulletins_bp
from routes.model_mgmt import model_mgmt_bp
from routes.reports import reports_bp
from routes.notifications import notifications_bp

def create_app():
    app = Flask(__name__)
    CORS(app, origins="*", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], allow_headers=["Content-Type", "Authorization"])

    prefix = "/api"
    app.register_blueprint(auth_bp, url_prefix=prefix)
    app.register_blueprint(predict_bp, url_prefix=prefix)
    app.register_blueprint(harvest_bp, url_prefix=prefix)
    app.register_blueprint(bulletins_bp, url_prefix=prefix)
    app.register_blueprint(model_mgmt_bp, url_prefix=prefix)
    app.register_blueprint(reports_bp, url_prefix=prefix)
    app.register_blueprint(notifications_bp, url_prefix=prefix)

    @app.route("/api/ping")
    def ping():
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
    app.run(debug=True, port=5000)
