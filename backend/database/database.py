"""
MongoDB database layer — collections + all CRUD helpers.
"""
from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime
from flask_bcrypt import Bcrypt
from flask_login import UserMixin
from bson.objectid import ObjectId
import os
from dotenv import load_dotenv

load_dotenv()

bcrypt = Bcrypt()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "dcrm_system")

client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
db = client[MONGODB_DB_NAME]

users_col = db["users"]
predictions_col = db["predictions"]
training_logs_col = db["training_logs"]
sos_col = db["sos_requests"]
interactions_col = db["employee_interactions"]

# ── Indexes ────────────────────────────────────────────────────────────────────
def ensure_indexes():
    users_col.create_index([("username", ASCENDING)], unique=True)
    users_col.create_index([("email", ASCENDING)], unique=True)
    predictions_col.create_index([("user_id", ASCENDING), ("timestamp", DESCENDING)])
    sos_col.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
    interactions_col.create_index([("sender_id", ASCENDING), ("receiver_id", ASCENDING)])
    interactions_col.create_index([("created_at", DESCENDING)])


# ── User Model ─────────────────────────────────────────────────────────────────
class User(UserMixin):
    def __init__(self, data: dict):
        self.id = str(data["_id"])
        self.username = data["username"]
        self.email = data["email"]
        self.role = data["role"]
        self.full_name = data.get("full_name", "")
        self.created_at = data.get("created_at")
        self._active = data.get("is_active", True)

    @property
    def is_active(self):
        return self._active

    def is_admin(self):
        return self.role == "admin"

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "full_name": self.full_name,
            "created_at": self.created_at,
            "is_active": self._active,
        }


# ── User CRUD ──────────────────────────────────────────────────────────────────
def create_user(username, email, password, role="employee", full_name=""):
    if users_col.find_one({"$or": [{"username": username}, {"email": email}]}):
        return None, "User with this username or email already exists"
    doc = {
        "username": username,
        "email": email,
        "password": bcrypt.generate_password_hash(password).decode("utf-8"),
        "role": role,
        "full_name": full_name,
        "created_at": datetime.utcnow(),
        "is_active": True,
    }
    result = users_col.insert_one(doc)
    doc["_id"] = result.inserted_id
    return User(doc), None


def get_user_by_id(user_id: str):
    try:
        data = users_col.find_one({"_id": ObjectId(user_id)})
        return User(data) if data else None
    except Exception:
        return None


def get_user_by_username(username: str):
    data = users_col.find_one({"username": username})
    return User(data) if data else None


def verify_password(username: str, password: str):
    data = users_col.find_one({"username": username})
    if data and data.get("is_active", True):
        if bcrypt.check_password_hash(data["password"], password):
            return User(data)
    return None


def get_all_employees():
    return [User(u) for u in users_col.find({"role": "employee"})]


def delete_user(user_id: str) -> bool:
    try:
        return users_col.delete_one({"_id": ObjectId(user_id)}).deleted_count > 0
    except Exception:
        return False


def update_password(user_id: str, new_password: str) -> bool:
    try:
        hashed = bcrypt.generate_password_hash(new_password).decode("utf-8")
        return (
            users_col.update_one(
                {"_id": ObjectId(user_id)}, {"$set": {"password": hashed}}
            ).modified_count
            > 0
        )
    except Exception:
        return False


def initialize_default_admin():
    admin_user = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    admin_pass = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
    admin_email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@dcrm.com")
    if not users_col.find_one({"username": admin_user}):
        user, error = create_user(admin_user, admin_email, admin_pass, role="admin", full_name="System Administrator")
        if user:
            print(f"Default admin created: {admin_user}")
            print(f"Password: {admin_pass}")
            print("Please change the password after first login!")
        else:
            print(f"Failed to create admin: {error}")
    else:
        print(f"Admin user '{admin_user}' already exists")


# ── Predictions ────────────────────────────────────────────────────────────────
def save_prediction(user_id, filename, prediction, probabilities, vector_size):
    doc = {
        "user_id": user_id,
        "filename": filename,
        "prediction": prediction,
        "probabilities": probabilities,
        "vector_size": vector_size,
        "timestamp": datetime.utcnow(),
    }
    result = predictions_col.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def get_user_predictions(user_id, limit=50):
    return list(predictions_col.find({"user_id": user_id}).sort("timestamp", DESCENDING).limit(limit))


def get_all_predictions(limit=100):
    rows = list(predictions_col.find().sort("timestamp", DESCENDING).limit(limit))
    result = []
    for p in rows:
        user = get_user_by_id(p["user_id"])
        result.append({
            "_id": str(p["_id"]),
            "user_id": p["user_id"],
            "username": user.username if user else "Unknown",
            "full_name": user.full_name if user else "Unknown",
            "filename": p["filename"],
            "prediction": p["prediction"],
            "probabilities": p["probabilities"],
            "vector_size": p["vector_size"],
            "timestamp": p["timestamp"],
        })
    return result


def get_predictions_by_employee(user_id):
    return list(predictions_col.find({"user_id": user_id}).sort("timestamp", DESCENDING))


def get_prediction_by_id(report_id: str):
    try:
        return predictions_col.find_one({"_id": ObjectId(report_id)})
    except Exception:
        return None


# ── Training Logs ──────────────────────────────────────────────────────────────
def save_training_log(user_id, filename, correct_label, total_samples):
    doc = {
        "user_id": user_id,
        "filename": filename,
        "correct_label": correct_label,
        "total_samples": total_samples,
        "timestamp": datetime.utcnow(),
    }
    result = training_logs_col.insert_one(doc)
    return result.inserted_id


# ── Statistics ─────────────────────────────────────────────────────────────────
def get_user_statistics():
    total_employees = users_col.count_documents({"role": "employee"})
    total_predictions = predictions_col.count_documents({})
    total_admins = users_col.count_documents({"role": "admin"})
    all_preds = list(predictions_col.find({}, {"prediction": 1}))
    if all_preds:
        healthy = sum(1 for p in all_preds if p.get("prediction") == "healthy")
        avg_health = round((healthy / len(all_preds)) * 100, 1)
    else:
        avg_health = 0.0
    return {
        "total_employees": total_employees,
        "total_predictions": total_predictions,
        "total_admins": total_admins,
        "average_health": avg_health,
    }


# ── SOS ────────────────────────────────────────────────────────────────────────
def create_sos_request(user_id, problem_type, description):
    doc = {
        "user_id": user_id,
        "problem_type": problem_type,
        "description": description,
        "status": "pending",
        "created_at": datetime.utcnow(),
        "resolved_at": None,
        "resolved_by": None,
    }
    result = sos_col.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def get_user_sos_requests(user_id):
    return list(sos_col.find({"user_id": user_id}).sort("created_at", DESCENDING))


def get_all_sos_requests(limit=100):
    rows = list(sos_col.find().sort("created_at", DESCENDING).limit(limit))
    result = []
    for r in rows:
        user = get_user_by_id(r["user_id"])
        result.append({
            "_id": str(r["_id"]),
            "user_id": r["user_id"],
            "username": user.username if user else "Unknown",
            "full_name": user.full_name if user else "Unknown",
            "problem_type": r["problem_type"],
            "description": r["description"],
            "status": r["status"],
            "created_at": r["created_at"],
            "resolved_at": r.get("resolved_at"),
            "resolved_by": r.get("resolved_by"),
        })
    return result


def resolve_sos_request(sos_id: str, resolved_by: str) -> bool:
    try:
        return (
            sos_col.update_one(
                {"_id": ObjectId(sos_id)},
                {"$set": {"status": "resolved", "resolved_at": datetime.utcnow(), "resolved_by": resolved_by}},
            ).modified_count
            > 0
        )
    except Exception:
        return False


# ── Interactions ───────────────────────────────────────────────────────────────
def save_message(sender_id, receiver_id, message):
    doc = {
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "message": message,
        "created_at": datetime.utcnow(),
        "read": False,
    }
    result = interactions_col.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def get_conversation(user1_id, user2_id, limit=50):
    return list(
        interactions_col.find({
            "$or": [
                {"sender_id": user1_id, "receiver_id": user2_id},
                {"sender_id": user2_id, "receiver_id": user1_id},
            ]
        }).sort("created_at", ASCENDING).limit(limit)
    )


def get_user_conversations(user_id):
    sent = interactions_col.find({"sender_id": user_id}).distinct("receiver_id")
    received = interactions_col.find({"receiver_id": user_id}).distinct("sender_id")
    all_ids = list(set(sent + received))
    conversations = []
    for other_id in all_ids:
        other = get_user_by_id(other_id)
        if not other:
            continue
        last = interactions_col.find_one(
            {"$or": [
                {"sender_id": user_id, "receiver_id": other_id},
                {"sender_id": other_id, "receiver_id": user_id},
            ]},
            sort=[("created_at", DESCENDING)],
        )
        conversations.append({
            "user_id": other_id,
            "username": other.username,
            "full_name": other.full_name,
            "last_message": last["message"] if last else "",
            "last_message_time": last["created_at"] if last else None,
        })
    conversations.sort(key=lambda x: x["last_message_time"] or datetime.min, reverse=True)
    return conversations


def mark_messages_as_read(sender_id, receiver_id):
    interactions_col.update_many(
        {"sender_id": sender_id, "receiver_id": receiver_id, "read": False},
        {"$set": {"read": True}},
    )
