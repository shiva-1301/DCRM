import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change_me_in_production")
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    DATA_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "dcrm_system")
    DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
    DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@dcrm.com")
    ML_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ml")
    MODEL_PATH = os.path.join(ML_DIR, "model", "dcrm_model.pkl")
    SCALER_PATH = os.path.join(ML_DIR, "model", "dcrm_scaler.pkl")
    DATASET_PATH = os.path.join(ML_DIR, "dataset", "dcrm_training_dataset.npz")
    TRAINING_HISTORY_PATH = os.path.join(ML_DIR, "training_history.json")
    TEMPLATES_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "templates")
    STATIC_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "static")
