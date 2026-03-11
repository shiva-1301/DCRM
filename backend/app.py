"""
DCRM Fault Detection Platform — Application Factory
"""
import os
from flask import Flask
from flask_login import LoginManager

from backend.config import Config
from backend.database.database import bcrypt, ensure_indexes, initialize_default_admin, get_user_by_id
from backend.services.ml_service import (
    load_dataset, load_training_history, load_initial_training_data,
    train_model, save_dataset,
)

# ── Blueprints ─────────────────────────────────────────────────────────────────
from backend.routes.auth_routes import auth_bp
from backend.routes.dashboard_routes import dashboard_bp
from backend.routes.admin_routes import admin_bp
from backend.routes.prediction_routes import prediction_bp
from backend.routes.sos_routes import sos_bp
from backend.routes.interaction_routes import interaction_bp
from backend.routes.chatbot_routes import chatbot_bp


def create_app(config: object = Config) -> Flask:
    app = Flask(
        __name__,
        template_folder=config.TEMPLATES_FOLDER,
        static_folder=config.STATIC_FOLDER,
    )
    app.config.from_object(config)

    # Ensure upload & data directories exist
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["DATA_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join(app.config["ML_DIR"], "model"), exist_ok=True)
    os.makedirs(os.path.join(app.config["ML_DIR"], "dataset"), exist_ok=True)

    # Extensions
    bcrypt.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."

    @login_manager.user_loader
    def load_user(user_id):
        return get_user_by_id(user_id)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(prediction_bp)
    app.register_blueprint(sos_bp)
    app.register_blueprint(interaction_bp)
    app.register_blueprint(chatbot_bp)

    return app


def _bootstrap_ml(app: Flask):
    """Populate in-memory dataset and ensure model files exist (run once at startup)."""
    import backend.services.ml_service as ml_svc

    with app.app_context():
        load_dataset()
        load_training_history()

        if not ml_svc.X_data:
            print("No saved dataset. Checking data folder...")
            X, y = load_initial_training_data(app.config["DATA_FOLDER"])
            if X:
                ml_svc.X_data, ml_svc.y_data = X, y
                print("Training initial model...")
                model, _, err = train_model(X, y)
                if err:
                    print(f"Initial training error: {err}")
                else:
                    save_dataset(X, y)
                    print(f"Initial model trained: {len(X)} samples")
            else:
                print("No training data found. Upload a CSV to train the model.")
        else:
            print(f"Dataset ready: {len(ml_svc.X_data)} samples")
            # Rebuild model files if missing
            if not os.path.exists(app.config["MODEL_PATH"]):
                import numpy as np
                print("Model files missing -- retraining from saved dataset...")
                train_model([np.array(x) for x in ml_svc.X_data], ml_svc.y_data)


if __name__ == "__main__":
    print("DCRM Retraining Interface -- starting up")
    print("=" * 60)

    flask_app = create_app()

    with flask_app.app_context():
        ensure_indexes()
        initialize_default_admin()

    _bootstrap_ml(flask_app)

    debug = os.getenv("FLASK_ENV", "production") == "development"
    print(f"Auth: MongoDB | Debug: {debug}")
    print("Location: http://localhost:5000")
    print("=" * 60)

    flask_app.run(debug=debug, host="127.0.0.1", port=5000)
