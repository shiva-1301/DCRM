"""
MongoDB Database Configuration and Models
"""
from pymongo import MongoClient
from datetime import datetime
from flask_bcrypt import Bcrypt
from flask_login import UserMixin
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize bcrypt
bcrypt = Bcrypt()

# MongoDB Configuration
MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'dcrm_system')

# Connect to MongoDB (serverSelectionTimeoutMS avoids hanging at import time)
client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
db = client[MONGODB_DB_NAME]

# Collections
users_collection = db['users']
predictions_collection = db['predictions']
training_logs_collection = db['training_logs']
sos_collection = db['sos_requests']
interactions_collection = db['employee_interactions']

# User Model Class
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.email = user_data['email']
        self.role = user_data['role']  # 'admin' or 'employee'
        self.full_name = user_data.get('full_name', '')
        self.created_at = user_data.get('created_at')
        self.active = user_data.get('is_active', True)
    
    @property
    def is_active(self):
        return self.active
    
    def is_admin(self):
        return self.role == 'admin'
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'full_name': self.full_name,
            'created_at': self.created_at,
            'is_active': self.active
        }

# Database Helper Functions
def create_user(username, email, password, role='employee', full_name=''):
    """Create a new user"""
    # Check if user exists
    if users_collection.find_one({'$or': [{'username': username}, {'email': email}]}):
        return None, "User with this username or email already exists"
    
    # Hash password
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    
    # Create user document
    user_doc = {
        'username': username,
        'email': email,
        'password': hashed_password,
        'role': role,
        'full_name': full_name,
        'created_at': datetime.utcnow(),
        'is_active': True
    }
    
    result = users_collection.insert_one(user_doc)
    user_doc['_id'] = result.inserted_id
    
    return User(user_doc), None

def get_user_by_username(username):
    """Get user by username"""
    user_data = users_collection.find_one({'username': username})
    if user_data:
        return User(user_data)
    return None

def get_user_by_id(user_id):
    """Get user by ID"""
    from bson.objectid import ObjectId
    try:
        user_data = users_collection.find_one({'_id': ObjectId(user_id)})
        if user_data:
            return User(user_data)
    except:
        pass
    return None

def verify_password(username, password):
    """Verify user password"""
    user_data = users_collection.find_one({'username': username})
    if user_data and user_data.get('is_active', True):
        if bcrypt.check_password_hash(user_data['password'], password):
            return User(user_data)
    return None

def get_all_employees():
    """Get all employee users"""
    employees = users_collection.find({'role': 'employee'})
    return [User(emp) for emp in employees]

def delete_user(user_id):
    """Delete a user"""
    from bson.objectid import ObjectId
    try:
        result = users_collection.delete_one({'_id': ObjectId(user_id)})
        return result.deleted_count > 0
    except:
        return False

def update_password(user_id, new_password):
    """Update user password"""
    from bson.objectid import ObjectId
    try:
        # Hash new password
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        
        result = users_collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'password': hashed_password}}
        )
        return result.modified_count > 0
    except:
        return False

def save_prediction(user_id, filename, prediction, probabilities, vector_size):
    """Save a prediction to database"""
    prediction_doc = {
        'user_id': user_id,
        'filename': filename,
        'prediction': prediction,
        'probabilities': probabilities,
        'vector_size': vector_size,
        'timestamp': datetime.utcnow()
    }
    
    result = predictions_collection.insert_one(prediction_doc)
    prediction_doc['_id'] = result.inserted_id
    return prediction_doc

def get_user_predictions(user_id, limit=50):
    """Get predictions for a specific user"""
    predictions = predictions_collection.find(
        {'user_id': user_id}
    ).sort('timestamp', -1).limit(limit)
    
    return list(predictions)

def get_all_predictions(limit=100):
    """Get all predictions (admin only)"""
    from bson.objectid import ObjectId
    
    predictions = predictions_collection.find().sort('timestamp', -1).limit(limit)
    predictions_list = []
    
    for pred in predictions:
        # Get user info
        user = get_user_by_id(pred['user_id'])
        pred_dict = {
            '_id': str(pred['_id']),
            'user_id': pred['user_id'],
            'username': user.username if user else 'Unknown',
            'full_name': user.full_name if user else 'Unknown',
            'filename': pred['filename'],
            'prediction': pred['prediction'],
            'probabilities': pred['probabilities'],
            'vector_size': pred['vector_size'],
            'timestamp': pred['timestamp']
        }
        predictions_list.append(pred_dict)
    
    return predictions_list

def get_predictions_by_employee(user_id):
    """Get predictions grouped by employee (admin view)"""
    from bson.objectid import ObjectId
    
    predictions = predictions_collection.find(
        {'user_id': user_id}
    ).sort('timestamp', -1)
    
    return list(predictions)

def save_training_log(user_id, filename, correct_label, total_samples):
    """Save retraining log"""
    log_doc = {
        'user_id': user_id,
        'filename': filename,
        'correct_label': correct_label,
        'total_samples': total_samples,
        'timestamp': datetime.utcnow()
    }
    
    result = training_logs_collection.insert_one(log_doc)
    return result.inserted_id

def initialize_default_admin():
    """Create default admin user if not exists"""
    admin_username = os.getenv('DEFAULT_ADMIN_USERNAME', 'admin')
    admin_password = os.getenv('DEFAULT_ADMIN_PASSWORD', 'admin123')
    admin_email = os.getenv('DEFAULT_ADMIN_EMAIL', 'admin@dcrm.com')
    
    # Check if admin exists
    existing_admin = users_collection.find_one({'username': admin_username})
    
    if not existing_admin:
        user, error = create_user(
            username=admin_username,
            email=admin_email,
            password=admin_password,
            role='admin',
            full_name='System Administrator'
        )
        if user:
            print(f"✅ Default admin created: {admin_username}")
            print(f"   Password: {admin_password}")
            print(f"   ⚠️  Please change the password after first login!")
            return True
        else:
            print(f"❌ Failed to create admin: {error}")
            return False
    else:
        print(f"✅ Admin user '{admin_username}' already exists")
        return True

def get_user_statistics():
    """Get user statistics for admin dashboard"""
    total_users = users_collection.count_documents({'role': 'employee'})
    total_predictions = predictions_collection.count_documents({})
    total_admins = users_collection.count_documents({'role': 'admin'})
    
    # Calculate average health across all users
    all_predictions = list(predictions_collection.find({}, {'prediction': 1}))
    if all_predictions:
        healthy_count = sum(1 for p in all_predictions if p.get('prediction') == 'healthy')
        average_health = (healthy_count / len(all_predictions)) * 100
    else:
        average_health = 0
    
    return {
        'total_employees': total_users,
        'total_predictions': total_predictions,
        'total_admins': total_admins,
        'average_health': round(average_health, 1)
    }

# SOS Functions
def create_sos_request(user_id, problem_type, description, severity="standard", category="other"):
    """Create a new SOS request"""
    sos_doc = {
        'user_id': user_id,
        'problem_type': problem_type,
        'description': description,
        'severity': severity,
        'category': category,
        'status': 'pending',  # pending, resolved
        'created_at': datetime.utcnow(),
        'resolved_at': None,
        'resolved_by': None
    }
    
    result = sos_collection.insert_one(sos_doc)
    sos_doc['_id'] = result.inserted_id
    return sos_doc

def get_user_sos_requests(user_id):
    """Get SOS requests for a specific user"""
    requests = sos_collection.find({'user_id': user_id}).sort('created_at', -1)
    return list(requests)

def get_all_sos_requests(limit=100):
    """Get all SOS requests (admin only)"""
    requests = sos_collection.find().sort('created_at', -1).limit(limit)
    requests_list = []
    
    for req in requests:
        user = get_user_by_id(req['user_id'])
        req_dict = {
            '_id': str(req['_id']),
            'user_id': req['user_id'],
            'username': user.username if user else 'Unknown',
            'full_name': user.full_name if user else 'Unknown',
            'problem_type': req['problem_type'],
            'description': req['description'],
            'status': req['status'],
            'created_at': req['created_at'],
            'resolved_at': req.get('resolved_at'),
            'resolved_by': req.get('resolved_by')
        }
        requests_list.append(req_dict)
    
    return requests_list

def resolve_sos_request(sos_id, resolved_by):
    """Resolve an SOS request"""
    from bson.objectid import ObjectId
    try:
        result = sos_collection.update_one(
            {'_id': ObjectId(sos_id)},
            {
                '$set': {
                    'status': 'resolved',
                    'resolved_at': datetime.utcnow(),
                    'resolved_by': resolved_by
                }
            }
        )
        return result.modified_count > 0
    except:
        return False

# Employee Interaction Functions
def save_message(sender_id, receiver_id, message):
    """Save a message between employees"""
    message_doc = {
        'sender_id': sender_id,
        'receiver_id': receiver_id,
        'message': message,
        'created_at': datetime.utcnow(),
        'read': False
    }
    
    result = interactions_collection.insert_one(message_doc)
    message_doc['_id'] = result.inserted_id
    return message_doc

def get_conversation(user1_id, user2_id, limit=50):
    """Get conversation between two users"""
    from bson.objectid import ObjectId
    
    # Get messages where user1 sent to user2 or user2 sent to user1
    messages = interactions_collection.find({
        '$or': [
            {'sender_id': user1_id, 'receiver_id': user2_id},
            {'sender_id': user2_id, 'receiver_id': user1_id}
        ]
    }).sort('created_at', 1).limit(limit)
    
    return list(messages)

def get_user_conversations(user_id):
    """Get all conversations for a user"""
    from bson.objectid import ObjectId
    
    # Get all unique users this user has conversed with
    sent_messages = interactions_collection.find({'sender_id': user_id}).distinct('receiver_id')
    received_messages = interactions_collection.find({'receiver_id': user_id}).distinct('sender_id')
    
    all_user_ids = list(set(sent_messages + received_messages))
    
    conversations = []
    for other_user_id in all_user_ids:
        other_user = get_user_by_id(other_user_id)
        if other_user:
            # Get last message
            last_message = interactions_collection.find_one({
                '$or': [
                    {'sender_id': user_id, 'receiver_id': other_user_id},
                    {'sender_id': other_user_id, 'receiver_id': user_id}
                ]
            }, sort=[('created_at', -1)])
            
            conversations.append({
                'user_id': other_user_id,
                'username': other_user.username,
                'full_name': other_user.full_name,
                'last_message': last_message['message'] if last_message else '',
                'last_message_time': last_message['created_at'] if last_message else None
            })
    
    # Sort by last message time
    conversations.sort(key=lambda x: x['last_message_time'] or datetime.min, reverse=True)
    return conversations

def mark_messages_as_read(sender_id, receiver_id):
    """Mark messages as read"""
    interactions_collection.update_many(
        {'sender_id': sender_id, 'receiver_id': receiver_id, 'read': False},
        {'$set': {'read': True}}
    )

def get_user_statistics():
    """Get user statistics for admin dashboard"""
    total_users = users_collection.count_documents({'role': 'employee'})
    total_predictions = predictions_collection.count_documents({})
    total_admins = users_collection.count_documents({'role': 'admin'})
    
    # Calculate average health across all users
    all_predictions = list(predictions_collection.find({}, {'prediction': 1}))
    if all_predictions:
        healthy_count = sum(1 for p in all_predictions if p.get('prediction') == 'healthy')
        average_health = (healthy_count / len(all_predictions)) * 100
    else:
        average_health = 0
    
    return {
        'total_employees': total_users,
        'total_predictions': total_predictions,
        'total_admins': total_admins,
        'average_health': round(average_health, 1)
    }
