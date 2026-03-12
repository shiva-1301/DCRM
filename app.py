from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session, make_response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from functools import wraps
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
import joblib
import os
import glob
from datetime import datetime
import json
from dotenv import load_dotenv

# Import database functions
from database import (
    bcrypt, initialize_default_admin, get_user_by_id, get_user_by_username,
    verify_password, create_user, get_all_employees, delete_user,
    save_prediction, get_user_predictions, get_all_predictions,
    save_training_log, get_user_statistics,
    save_message, get_conversation, get_user_conversations, mark_messages_as_read,
    update_password
)

# Import Blueprints
from backend.routes.sos_routes import sos_bp

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key_change_me')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DATA_FOLDER'] = 'data'

# Register Blueprints
app.register_blueprint(sos_bp)

# Create folders if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['DATA_FOLDER'], exist_ok=True)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(user_id)

# Admin-only decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('You need admin privileges to access this page.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Dataset persistence file
DATASET_PATH = "dcrm_training_dataset.npz"

# Global variables to store training data
X_data = []
y_data = []
training_history = []

# ---------------------------------------------
# Dataset persistence functions
# ---------------------------------------------
def save_dataset(X, y):
    """
    Save the current training dataset permanently.
    This ensures retraining survives server restarts.
    """
    try:
        np.savez(DATASET_PATH, X=np.array(X, dtype=object), y=np.array(y, dtype=object))
        print(f"📁 Dataset saved: {len(X)} samples")
        return True
    except Exception as e:
        print(f"❌ Error saving dataset: {e}")
        return False

def load_dataset():
    """
    Load stored dataset if it exists.
    If not, return empty lists for first-time training.
    """
    if os.path.exists(DATASET_PATH):
        try:
            data = np.load(DATASET_PATH, allow_pickle=True)
            X = list(data["X"])
            y = list(data["y"])
            print(f"📁 Loaded existing dataset: {len(X)} samples")
            return X, y
        except Exception as e:
            print(f"⚠ Error loading dataset: {e}")
            return [], []
    else:
        print("📁 No dataset found. Starting fresh.")
        return [], []

# ---------------------------------------------
# Signature loading (Channel-1 Only)
# ---------------------------------------------
def load_signature(path):
    """
    Loads a DCRM signature CSV:
    - Skips empty first row (header is line 2)
    - Removes blank spacer columns
    - Normalizes column names
    - Auto-detects and extracts only Channel-1 signals
    - Flattens into a 1D feature vector
    """
    try:
        # Read CSV with header on line 2
        df = pd.read_csv(path, engine="python", on_bad_lines="skip", header=1)
        
        # Remove empty spacer columns
        df = df.dropna(axis=1, how='all')
        
        # Clean column names
        df.columns = df.columns.str.strip().str.replace("\t", " ", regex=False)
        
        # Auto-detect channel-1 columns
        ch1_cols = []
        for col in df.columns:
            name = col.lower()
            if "coil" in name and "c1" in name:
                ch1_cols.append(col)
            elif "travel" in name and "t1" in name:
                ch1_cols.append(col)
            elif "res" in name and "ch1" in name:
                ch1_cols.append(col)
            elif "current" in name and "ch1" in name:
                ch1_cols.append(col)
        
        # If CH1 not found → show error
        if len(ch1_cols) == 0:
            print(f"⚠ ERROR: No Channel-1 columns found in: {path}")
            print(f"Detected columns: {df.columns.tolist()}")
            return None, "No Channel-1 columns found"
        
        # Extract clean CH1 data
        df = df[ch1_cols].fillna(0)
        
        # Convert to 1D vector
        return df.values.flatten(), None
    except Exception as e:
        return None, str(e)


# ---------------------------------------------
# CSV normalization utilities
# ---------------------------------------------
def convert_407b_to_arc_format(filepath):
    """
    Normalize uploads that arrive in the 407_B-style format to match the arc_2
    layout expected by the model:
    - Detects metadata rows with Close/Open velocity and TR/BBreak markers
    - Removes the first four metadata lines
    - Inserts a blank spacer row so the header sits on line 2 (matching arc_* files)
    """
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        if len(lines) < 5:
            return False, "File too short to normalize"

        header_probe = " ".join(lines[:3]).lower()
        if "close -velocity" not in header_probe and "open -velocity" not in header_probe:
            # Already in arc_* style (or another format); nothing to do
            return False, None

        # Drop the first four metadata lines; keep the rest
        data_section = lines[4:]
        if not data_section:
            return False, "No data rows after metadata"

        # Ensure we have a header row to size the spacer
        header_cells = data_section[0].rstrip("\n").split(",")
        spacer_row = ",".join([""] * len(header_cells)) + "\n"

        normalized = [spacer_row] + data_section
        with open(filepath, "w", encoding="utf-8", newline="") as f:
            f.writelines(normalized)

        return True, None
    except Exception as exc:
        return False, str(exc)


def align_vector_length(vector, target_len):
    """
    Ensure feature vector matches expected length:
    - If too long, truncate.
    - If too short, pad with zeros.
    """
    if len(vector) == target_len:
        return vector
    if len(vector) > target_len:
        return vector[:target_len]
    # pad
    pad_width = target_len - len(vector)
    return np.concatenate([vector, np.zeros(pad_width)])

# ---------------------------------------------
# Load initial training data from data folder
# ---------------------------------------------
def load_initial_training_data():
    """
    Load any CSV files from the data folder for initial training.
    Detects labels from filenames (healthy/main/arc).
    """
    X = []
    y = []
    
    data_files = glob.glob(os.path.join(app.config['DATA_FOLDER'], "*.csv"))
    
    if not data_files:
        print("📂 No initial training files found in data folder.")
        return X, y
    
    print(f"📂 Loading {len(data_files)} files from data folder...")
    
    for file in data_files:
        fn = file.lower()
        
        # Detect label from filename
        if "healthy" in fn:
            label = "healthy"
        elif "main" in fn:
            label = "main"
        elif "arc" in fn:
            label = "arc"
        else:
            print(f"⚠ Skipping {file} - no label in filename")
            continue
        
        vector, error = load_signature(file)
        
        # Skip corrupted files
        if error or vector is None or vector.size == 0:
            print(f"⚠ Skipping {file} - {error or 'no usable data'}")
            continue
        
        X.append(vector)
        y.append(label)
        print(f"✓ Loaded {os.path.basename(file)} as '{label}'")
    
    print(f"📂 Loaded {len(X)} initial training samples")
    return X, y

# ---------------------------------------------
# Model training function
# ---------------------------------------------
def train_model(X, y):
    """Trains a fresh Random Forest on all data."""
    try:
        if len(X) == 0 or len(y) == 0:
            return None, None, "No training data available"
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        model = RandomForestClassifier(n_estimators=300, random_state=42)
        model.fit(X_scaled, y)
        
        joblib.dump(model, "dcrm_model.pkl")
        joblib.dump(scaler, "dcrm_scaler.pkl")
        
        print(f"✔ Model training completed with {len(X)} samples")
        return model, scaler, None
    except Exception as e:
        print(f"❌ Training error: {e}")
        return None, None, str(e)

def load_model_and_scaler():
    """Load the trained model and scaler"""
    try:
        model = joblib.load("dcrm_model.pkl")
        scaler = joblib.load("dcrm_scaler.pkl")
        return model, scaler, None
    except Exception as e:
        return None, None, str(e)

# ---------------------------------------------
# Authentication Routes
# ---------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = verify_password(username, password)
        
        if user:
            login_user(user)
            flash(f'Welcome back, {user.full_name or user.username}!', 'success')
            
            # Redirect based on role
            if user.is_admin():
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

# ---------------------------------------------
# Main Routes
# ---------------------------------------------
@app.route('/')
@login_required
def index():
    """Redirect to dashboard"""
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    """New Dashboard page with analytics"""
    return render_template('dashboard_new.html', user=current_user)

@app.route('/analysis')
@login_required
def analysis_page():
    """New Analysis page with CSV upload and graphs"""
    return render_template('analysis_new.html', user=current_user)

@app.route('/old-dashboard')
@login_required
def old_dashboard():
    """Old dashboard page (kept for reference)"""
    return render_template('dashboard.html', user=current_user)

@app.route('/my-history')
@login_required
def my_history():
    """Employee's prediction history"""
    predictions = get_user_predictions(current_user.id, limit=50)
    return render_template('my_history.html', predictions=predictions, user=current_user)

@app.route('/reports')
@login_required
def reports_page():
    """Reports page"""
    # Get all reports (predictions) for the user
    reports = get_user_predictions(current_user.id, limit=100)
    
    # Calculate stats for the user
    stats = {
        'total': len(reports),
        'healthy': len([r for r in reports if r.get('prediction') == 'healthy']),
        'main': len([r for r in reports if r.get('prediction') == 'main']),
        'arc': len([r for r in reports if r.get('prediction') == 'arc'])
    }
    
    return render_template('reports.html', reports=reports, stats=stats, user=current_user)

@app.route('/settings')
@login_required
def settings_page():
    """Settings page"""
    return render_template('settings.html', user=current_user)

# ---------------------------------------------
# Admin Routes
# ---------------------------------------------
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    stats = get_user_statistics()
    employees = get_all_employees()
    recent_predictions = get_all_predictions(limit=20)
    
    # Get pending SOS count for popup notification
    all_sos = get_all_sos_requests()
    pending_sos = [sos for sos in all_sos if sos.get('status') == 'pending']
    pending_sos_count = len(pending_sos)
    
    return render_template('admin_dashboard.html', 
                         stats=stats, 
                         employees=employees,
                         predictions=recent_predictions,
                         user=current_user,
                         pending_sos=pending_sos[:5],  # Show first 5 pending SOS
                         pending_sos_count=pending_sos_count)

@app.route('/admin/add-employee', methods=['POST'])
@login_required
@admin_required
def add_employee():
    """Add new employee"""
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    full_name = request.form.get('full_name', '')
    
    if not username or not email or not password:
        flash('All fields are required', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    user, error = create_user(username, email, password, role='employee', full_name=full_name)
    
    if user:
        flash(f'Employee {username} added successfully!', 'success')
    else:
        flash(f'Error: {error}', 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-employee/<user_id>', methods=['POST'])
@login_required
@admin_required
def delete_employee(user_id):
    """Delete employee"""
    if delete_user(user_id):
        flash('Employee deleted successfully', 'success')
    else:
        flash('Failed to delete employee', 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/employee-predictions/<user_id>')
@login_required
@admin_required
def employee_predictions(user_id):
    """View predictions for a specific employee"""
    from database import get_predictions_by_employee
    user = get_user_by_id(user_id)
    predictions = get_predictions_by_employee(user_id)
    
    return render_template('employee_predictions.html', 
                         employee=user, 
                         predictions=predictions,
                         user=current_user)

# ---------------------------------------------
# API Routes
# ---------------------------------------------
@app.route('/api/predict', methods=['POST'])
@login_required
def predict():
    """Predict the class of uploaded CSV file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be a CSV'}), 400
    
    try:
        # Save uploaded file
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        # Normalize 407_B-style uploads to arc_* layout before parsing
        converted, norm_error = convert_407b_to_arc_format(filepath)
        if norm_error:
            return jsonify({'error': f'Error normalizing file: {norm_error}'}), 400
        
        # Load signature
        vector, error = load_signature(filepath)
        if error:
            return jsonify({'error': f'Error loading signature: {error}'}), 400
        
        # Load model and scaler
        model, scaler, error = load_model_and_scaler()
        if error:
            return jsonify({'error': f'Error loading model: {error}'}), 500

        # Align vector length to scaler expectation
        target_len = getattr(scaler, "n_features_in_", None)
        if target_len:
            vector = align_vector_length(np.array(vector), target_len)
        else:
            # Fallback: use existing length without change
            vector = np.array(vector)
        
        # Make prediction
        vector_scaled = scaler.transform([vector])
        prediction = model.predict(vector_scaled)[0]
        probabilities = model.predict_proba(vector_scaled)[0]
        
        # Get class probabilities
        classes = model.classes_
        prob_dict = {cls: float(prob) for cls, prob in zip(classes, probabilities)}
        
        # Save prediction to database
        save_prediction(
            user_id=current_user.id,
            filename=file.filename,
            prediction=prediction,
            probabilities=prob_dict,
            vector_size=len(vector)
        )
        
        return jsonify({
            'prediction': prediction,
            'probabilities': prob_dict,
            'filename': file.filename,
            'filepath': filepath,
            'vector_size': len(vector)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/retrain', methods=['POST'])
@login_required
def retrain():
    """Retrain the model with corrected label"""
    global X_data, y_data, training_history
    
    data = request.json
    filepath = data.get('filepath')
    correct_label = data.get('correct_label')
    
    if not filepath or not correct_label:
        return jsonify({'error': 'Missing filepath or correct_label'}), 400
    
    if correct_label not in ['healthy', 'main', 'arc']:
        return jsonify({'error': 'Invalid label. Must be healthy, main, or arc'}), 400
    
    try:
        # Load signature
        vector, error = load_signature(filepath)
        if error or vector is None:
            return jsonify({'error': f'Error loading signature: {error}'}), 400
        
        # Determine target length from existing data
        if len(X_data) > 0:
            # Use the length of the first sample as reference
            target_length = len(X_data[0])
            # Align the new vector to match existing data
            vector = align_vector_length(vector, target_length)
        
        # Add corrected sample to dataset
        X_data.append(vector)
        y_data.append(correct_label)
        
        # Save updated dataset to disk
        save_dataset(X_data, y_data)
        
        # Convert to numpy arrays with consistent shapes
        X_array = np.array([np.array(x) for x in X_data])
        y_array = np.array(y_data)
        
        # Retrain model on entire expanded dataset
        model, scaler, error = train_model(X_array, y_array)
        
        if error:
            return jsonify({'error': f'Training error: {error}'}), 500
        
        # Log training history
        training_entry = {
            'timestamp': datetime.now().isoformat(),
            'filename': os.path.basename(filepath),
            'label': correct_label,
            'total_samples': len(X_data),
            'user_id': current_user.id
        }
        training_history.append(training_entry)
        
        # Save training history
        with open('training_history.json', 'w') as f:
            json.dump(training_history, f, indent=2)
        
        # Save to MongoDB
        save_training_log(
            user_id=current_user.id,
            filename=os.path.basename(filepath),
            correct_label=correct_label,
            total_samples=len(X_data)
        )
        
        print(f"✔ Model retrained by {current_user.username}. Total samples: {len(X_data)}")
        
        return jsonify({
            'message': 'Model retrained successfully with new corrected data',
            'total_samples': len(X_data),
            'training_entry': training_entry
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    """Get model statistics"""
    try:
        model, scaler, error = load_model_and_scaler()
        if error:
            return jsonify({'error': error}), 500
        
        # Load training history
        if os.path.exists('training_history.json'):
            with open('training_history.json', 'r') as f:
                history = json.load(f)
        else:
            history = []
        
        # Count labels in training data
        label_counts = {}
        for label in y_data:
            label_counts[label] = label_counts.get(label, 0) + 1
        
        return jsonify({
            'total_samples': len(X_data),
            'label_distribution': label_counts,
            'training_history': history[-10:],  # Last 10 entries
            'model_info': {
                'n_estimators': model.n_estimators,
                'n_features': model.n_features_in_ if hasattr(model, 'n_features_in_') else 'Unknown'
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
@login_required
def get_history():
    """Get full training history"""
    try:
        if os.path.exists('training_history.json'):
            with open('training_history.json', 'r') as f:
                history = json.load(f)
            return jsonify({'history': history})
        else:
            return jsonify({'history': []})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ---------------------------------------------
# Reports API Routes
# ---------------------------------------------
@app.route('/api/user/reports', methods=['GET'])
@login_required
def get_user_reports():
    """Get all prediction reports for current user"""
    try:
        predictions = get_user_predictions(current_user.id, limit=100)
        
        # Convert MongoDB objects to JSON-serializable format
        reports = []
        for pred in predictions:
            reports.append({
                '_id': str(pred['_id']),
                'filename': pred['filename'],
                'prediction': pred['prediction'],
                'probabilities': pred['probabilities'],
                'vector_size': pred['vector_size'],
                'timestamp': pred['timestamp'].isoformat() if hasattr(pred['timestamp'], 'isoformat') else str(pred['timestamp'])
            })
        
        return jsonify({'reports': reports})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/report/download/<report_id>', methods=['GET'])
@login_required
def download_report_pdf(report_id):
    """Generate and download PDF report for a specific prediction"""
    try:
        from bson.objectid import ObjectId
        from io import BytesIO
        
        # Get prediction from database
        prediction = predictions_collection.find_one({'_id': ObjectId(report_id)})
        
        if not prediction:
            return jsonify({'error': 'Report not found'}), 404
        
        # Verify user owns this prediction
        if prediction['user_id'] != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Create a simple text-based report (you can enhance this with a PDF library like ReportLab)
        report_content = f"""
DCRM TEST REPORT
{'=' * 60}

Report ID: {report_id}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
User: {current_user.full_name or current_user.username}

{'=' * 60}
FILE INFORMATION
{'=' * 60}

Filename: {prediction['filename']}
Test Date: {prediction['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
Vector Size: {prediction['vector_size']} features

{'=' * 60}
PREDICTION RESULTS
{'=' * 60}

Classification: {prediction['prediction'].upper()}

Confidence Levels:
"""
        
        # Add probabilities
        for label, prob in sorted(prediction['probabilities'].items(), key=lambda x: x[1], reverse=True):
            report_content += f"  {label.capitalize()}: {prob * 100:.2f}%\n"
        
        report_content += f"""
{'=' * 60}
INTERPRETATION
{'=' * 60}

"""
        
        # Add interpretation based on prediction
        if prediction['prediction'] == 'healthy':
            report_content += """Status: HEALTHY
The DCRM measurements indicate normal contact resistance with no faults
detected. The system shows stable measurements across all channels.
This means your equipment is functioning properly.

Recommendation: Continue regular monitoring.
"""
        elif prediction['prediction'] == 'main':
            report_content += """Status: MAIN CONTACT FAULT
Main contact fault indicates issues with the primary contact mechanism.
This could be due to wear, contamination, or mechanical problems.

Recommendation: Immediate inspection is recommended. Check the contact
surfaces and consider maintenance.
"""
        else:  # arc
            report_content += """Status: ARC FAULT DETECTED
Arc fault detection indicates electrical arcing in the contact system.
This is a serious condition that requires immediate attention to prevent
equipment damage and safety hazards.

Recommendation: IMMEDIATE ACTION REQUIRED. Contact your supervisor and
schedule emergency maintenance.
"""
        
        report_content += f"""
{'=' * 60}
SYSTEM INFORMATION
{'=' * 60}

Model: Random Forest Classifier
Features Analyzed: Channel-1 DCRM Measurements
Classification Classes: Healthy, Main Fault, Arc Fault

{'=' * 60}
END OF REPORT
{'=' * 60}
"""
        
        # Create response with text file (can be enhanced to PDF)
        response = make_response(report_content)
        response.headers['Content-Type'] = 'text/plain'
        response.headers['Content-Disposition'] = f'attachment; filename=DCRM_Report_{report_id}.txt'
        
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# SOS Routes moved to backend/routes/sos_routes.py

# ---------------------------------------------
# Dashboard Analytics Routes
# ---------------------------------------------
@app.route('/api/dashboard/analytics', methods=['GET'])
@login_required
def get_dashboard_analytics():
    """Get comprehensive dashboard analytics"""
    try:
        from collections import Counter
        from datetime import timedelta
        
        # Get all predictions for the current user
        all_predictions = get_user_predictions(current_user.id, limit=1000)
        
        # Total tests
        total_tests = len(all_predictions)
        
        # Calculate average health (healthy predictions percentage)
        health_predictions = [p for p in all_predictions if p['prediction'] == 'healthy']
        avg_health = (len(health_predictions) / total_tests * 100) if total_tests > 0 else 0
        
        # Fault distribution
        fault_counts = Counter([p['prediction'] for p in all_predictions])
        fault_distribution = {
            'healthy': fault_counts.get('healthy', 0),
            'main': fault_counts.get('main', 0),
            'arc': fault_counts.get('arc', 0)
        }
        
        # Health vs Spikes over time (last 30 days)
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        
        # Group predictions by date
        daily_health = {}
        daily_spikes = {}
        
        for pred in all_predictions:
            pred_date = pred['timestamp'].date() if hasattr(pred['timestamp'], 'date') else datetime.fromisoformat(str(pred['timestamp'])).date()
            date_str = pred_date.isoformat()
            
            if pred_date >= thirty_days_ago.date():
                if date_str not in daily_health:
                    daily_health[date_str] = 0
                    daily_spikes[date_str] = 0
                
                if pred['prediction'] == 'healthy':
                    daily_health[date_str] += 1
                else:
                    daily_spikes[date_str] += 1
        
        # Convert to sorted lists
        health_trend = [{'date': date, 'count': count} for date, count in sorted(daily_health.items())]
        spikes_trend = [{'date': date, 'count': count} for date, count in sorted(daily_spikes.items())]
        
        # Recent tests (last 10)
        recent_tests = []
        for pred in all_predictions[:10]:
            recent_tests.append({
                'id': str(pred['_id']),
                'filename': pred['filename'],
                'prediction': pred['prediction'],
                'confidence': max(pred['probabilities'].values()) * 100,
                'timestamp': pred['timestamp'].isoformat() if hasattr(pred['timestamp'], 'isoformat') else str(pred['timestamp'])
            })
        
        return jsonify({
            'total_tests': total_tests,
            'avg_health': round(avg_health, 1),
            'fault_distribution': fault_distribution,
            'health_trend': health_trend,
            'spikes_trend': spikes_trend,
            'recent_tests': recent_tests
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze-csv', methods=['POST'])
@login_required
def analyze_csv_detailed():
    """Analyze CSV file and return detailed time-series data for graphs"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be a CSV'}), 400
    
    try:
        # Save uploaded file
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        # Normalize 407_B-style uploads to arc_* layout before parsing
        converted, norm_error = convert_407b_to_arc_format(filepath)
        if norm_error:
            return jsonify({'error': f'Error normalizing file: {norm_error}'}), 400
        
        # Read CSV for detailed analysis
        df = pd.read_csv(filepath, engine="python", on_bad_lines="skip", header=1)
        df = df.dropna(axis=1, how='all')
        df.columns = df.columns.str.strip().str.replace("\t", " ", regex=False)
        
        # Extract time-series data for Channel 1
        time_index = list(range(len(df)))
        
        # Initialize data structures
        coil_current_data = []
        resistance_data = []
        dcrm_current_data = []
        contact_travel_data = []
        
        # Find Channel-1 columns
        for col in df.columns:
            col_lower = col.lower()
            
            # Coil Current C1
            if 'coil' in col_lower and 'c1' in col_lower:
                coil_current_data = df[col].fillna(0).tolist()
            
            # Contact Travel T1
            elif 'travel' in col_lower and 't1' in col_lower:
                contact_travel_data = df[col].fillna(0).tolist()
            
            # DCRM Resistance CH1
            elif 'res' in col_lower and 'ch1' in col_lower:
                resistance_data = df[col].fillna(0).tolist()
            
            # DCRM Current CH1
            elif 'current' in col_lower and 'ch1' in col_lower:
                dcrm_current_data = df[col].fillna(0).tolist()
        
        # Load signature for prediction
        vector, error = load_signature(filepath)
        if error:
            return jsonify({'error': f'Error loading signature: {error}'}), 400
        
        # Load model and scaler
        model, scaler, error = load_model_and_scaler()
        if error:
            return jsonify({'error': f'Error loading model: {error}'}), 500

        # Align vector length to scaler expectation
        target_len = getattr(scaler, "n_features_in_", None)
        if target_len:
            vector = align_vector_length(np.array(vector), target_len)
        else:
            vector = np.array(vector)
        
        # Make prediction
        vector_scaled = scaler.transform([vector])
        prediction = model.predict(vector_scaled)[0]
        probabilities = model.predict_proba(vector_scaled)[0]
        
        # Get class probabilities
        classes = model.classes_
        prob_dict = {cls: float(prob) for cls, prob in zip(classes, probabilities)}
        
        # Save prediction to database
        save_prediction(
            user_id=current_user.id,
            filename=file.filename,
            prediction=prediction,
            probabilities=prob_dict,
            vector_size=len(vector)
        )
        
        # Prepare graph data
        graph_data = {
            'time': time_index[:1000],  # Limit to first 1000 points for performance
            'coil_current': coil_current_data[:1000],
            'resistance': resistance_data[:1000],
            'dcrm_current': dcrm_current_data[:1000],
            'contact_travel': contact_travel_data[:1000]
        }
        
        return jsonify({
            'prediction': prediction,
            'probabilities': prob_dict,
            'filename': file.filename,
            'filepath': filepath,
            'vector_size': len(vector),
            'graph_data': graph_data,
            'data_points': len(time_index)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ---------------------------------------------
# Field Advisor Chatbot Routes
# ---------------------------------------------
@app.route('/field-advisor')
@login_required
def field_advisor():
    """Field Advisor Chatbot page"""
    return render_template('field_advisor.html', user=current_user)

@app.route('/api/chatbot/ask', methods=['POST'])
@login_required
def chatbot_ask():
    """Chatbot API endpoint - handles any question intelligently"""
    data = request.json
    question = data.get('question', '').strip()
    selected_text = data.get('selected_text', '').strip()
    
    if not question:
        return jsonify({'error': 'Question is required'}), 400
    
    question_lower = question.lower()
    response = ""
    
    # Use selected text context if available
    context = f" You mentioned: '{selected_text}'." if selected_text else ""
    
    # Greetings
    if any(word in question_lower for word in ['hello', 'hi', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening']):
        response = f"Hello! I'm your Field Advisor chatbot.{context} I'm here to help you with any questions about the DCRM system, troubleshooting, or general inquiries. How can I assist you today?"
    
    # DCRM-specific technical questions
    elif 'healthy' in question_lower or ('normal' in question_lower and 'reading' in question_lower):
        response = f"A healthy DCRM reading indicates normal contact resistance with no faults detected. The system shows stable measurements across all channels.{context} This means your equipment is functioning properly."
    elif 'main' in question_lower and ('contact' in question_lower or 'fault' in question_lower):
        response = f"Main contact fault indicates issues with the primary contact mechanism. This could be due to wear, contamination, or mechanical problems. Immediate inspection is recommended.{context} You should check the contact surfaces and consider maintenance."
    elif 'arc' in question_lower or 'arcing' in question_lower:
        response = f"Arc fault detection indicates electrical arcing in the contact system. This is a serious condition that requires immediate attention to prevent equipment damage and safety hazards.{context} Please take immediate action and contact your supervisor if needed."
    elif 'dcrm' in question_lower:
        response = f"DCRM (Dynamic Contact Resistance Measurement) is a system for detecting faults in electrical contacts. It analyzes measurements to classify contacts as healthy, main fault, or arc fault.{context} The system uses machine learning to provide accurate predictions."
    
    # File and upload questions
    elif any(word in question_lower for word in ['upload', 'file', 'csv', 'how to upload']):
        response = f"To upload a file: 1) Click 'Browse Files' or drag and drop your CSV file, 2) Click 'Predict' to analyze, 3) Review the results and validate the prediction.{context} Make sure your CSV file contains Channel-1 data columns."
    elif 'format' in question_lower or 'structure' in question_lower:
        response = f"Your CSV file should have Channel-1 columns including: Coil Current C1, Contact Travel T1, DCRM Res CH1, and DCRM Current CH1.{context} The header should be on line 2 of the CSV file."
    
    # Prediction and results questions
    elif any(word in question_lower for word in ['prediction', 'result', 'classify', 'what does it mean']):
        response = f"Predictions show the probability of each fault type (healthy, main, arc). The system uses machine learning to classify your DCRM measurements.{context} Always validate predictions for accuracy by clicking 'Correct' or 'Incorrect'."
    elif 'confidence' in question_lower or 'probability' in question_lower:
        response = f"Confidence levels show how certain the system is about its prediction. Higher confidence (above 80%) indicates more reliable results.{context} Lower confidence may require manual verification."
    
    # Training and model questions
    elif any(word in question_lower for word in ['retrain', 'training', 'model', 'improve']):
        response = f"If a prediction is incorrect, click 'Incorrect' and select the correct label. The system will automatically retrain the model with your correction to improve accuracy.{context} This helps the system learn from your expertise."
    
    # SOS and help questions
    elif any(word in question_lower for word in ['sos', 'problem', 'issue', 'help', 'stuck', 'error']):
        response = f"If you're experiencing problems, you can: 1) Send an SOS request to your administrator via the SOS Request page, 2) Chat with other employees through the Interactions page, or 3) Ask me more questions here.{context} I'm here to help resolve your issues!"
    elif 'cannot' in question_lower or "can't" in question_lower or 'unable' in question_lower:
        response = f"If you're unable to resolve something, you can: 1) Use the Interactions page to chat with other employees for help, 2) Send an SOS request to your admin, or 3) Check the User Guide for step-by-step instructions.{context} Don't hesitate to ask for assistance!"
    
    # Interaction and communication questions
    elif any(word in question_lower for word in ['interact', 'chat', 'message', 'employee', 'talk to', 'contact employee']):
        response = f"You can interact with other employees through the Interactions page. Select an employee from the list to start a conversation and get help with issues you're unable to resolve yourself.{context} This is great for collaboration and problem-solving."
    
    # Feature questions
    elif any(word in question_lower for word in ['feature', 'what can', 'what does', 'capabilities']):
        response = f"The DCRM system offers several features: 1) File upload and prediction, 2) SOS requests for admin help, 3) Field Advisor chatbot (that's me!), 4) Employee interactions for collaboration, and 5) User guide for instructions.{context} Explore the navigation menu to access all features."
    
    # History and tracking questions
    elif any(word in question_lower for word in ['history', 'past', 'previous', 'track']):
        response = f"You can view your prediction history in the 'My History' page. It shows all your past predictions with details like filename, fault type, confidence, and timestamp.{context} This helps you track your work and patterns."
    
    # General "what" questions
    elif question_lower.startswith('what'):
        if 'is' in question_lower or 'are' in question_lower:
            response = f"Based on your question '{question}', I can help explain various aspects of the DCRM system.{context} Could you be more specific? For example: 'What is a healthy reading?' or 'What are the fault types?'"
        else:
            response = f"I understand you're asking: '{question}'.{context} I can help explain DCRM concepts, system features, how to use different functions, or troubleshoot issues. Could you provide more specific details?"
    
    # General "how" questions
    elif question_lower.startswith('how'):
        response = f"To answer your question about '{question}', I'd be happy to help!{context} I can explain: how to upload files, how predictions work, how to use features, how to resolve issues, or how to get help. Could you be more specific?"
    
    # General "why" questions
    elif question_lower.startswith('why'):
        response = f"That's a great question! '{question}'.{context} I can help explain the reasoning behind DCRM system features, fault classifications, or processes. Could you provide more context so I can give you a detailed answer?"
    
    # General "when" or "where" questions
    elif question_lower.startswith(('when', 'where')):
        response = f"Regarding your question '{question}',{context} I can help you find where features are located in the system or when to use certain functions. For specific locations, check the navigation sidebar. Could you be more specific?"
    
    # Thanks and appreciation
    elif any(word in question_lower for word in ['thank', 'thanks', 'appreciate', 'grateful']):
        response = "You're welcome! I'm glad I could help. If you have any more questions about the DCRM system, troubleshooting, or anything else, feel free to ask. I'm here to assist you!"
    
    # Goodbye
    elif any(word in question_lower for word in ['bye', 'goodbye', 'see you', 'farewell', 'later']):
        response = "Goodbye! Feel free to come back anytime if you need assistance. Have a great day and stay safe!"
    
    # Questions about the chatbot itself
    elif any(word in question_lower for word in ['who are you', 'what are you', 'your name', 'yourself']):
        response = "I'm the Field Advisor chatbot, your intelligent assistant for the DCRM system. I can help you with questions about DCRM measurements, system features, troubleshooting, file uploads, predictions, and general guidance. I'm here 24/7 to assist you!"
    
    # Default intelligent response
    else:
        # Try to provide a helpful response based on keywords
        keywords_found = []
        if any(word in question_lower for word in ['system', 'application', 'software']):
            keywords_found.append("the DCRM system")
        if any(word in question_lower for word in ['work', 'function', 'operate']):
            keywords_found.append("how things work")
        if any(word in question_lower for word in ['problem', 'issue', 'trouble']):
            keywords_found.append("problem-solving")
        
        if keywords_found:
            response = f"I understand you're asking about '{question}'.{context} I can help you with {', '.join(keywords_found)}. "
        else:
            response = f"I understand you're asking: '{question}'.{context} "
        
        response += "As your Field Advisor, I can help with:\n\n" \
                   "• DCRM system questions (fault types, predictions, file uploads)\n" \
                   "• How to use system features and navigate the interface\n" \
                   "• Troubleshooting and problem-solving\n" \
                   "• General guidance and support\n" \
                   "• Understanding results and predictions\n\n" \
                   "Could you provide more specific details about what you'd like to know? I'm here to help!"
    
    return jsonify({'response': response})

# ---------------------------------------------
# Employee Interaction Routes
# ---------------------------------------------
@app.route('/interactions')
@login_required
def interactions():
    """Employee interactions page"""
    conversations = get_user_conversations(current_user.id)
    # Get all employees (excluding current user and admins)
    all_employees = get_all_employees()
    employees = [emp for emp in all_employees if emp.id != current_user.id and not emp.is_admin()]
    return render_template('interactions.html', user=current_user, conversations=conversations, employees=employees)

@app.route('/api/interactions/send', methods=['POST'])
@login_required
def send_message():
    """Send a message to another employee"""
    data = request.json
    receiver_id = data.get('receiver_id')
    message = data.get('message', '')
    
    if not receiver_id or not message:
        return jsonify({'error': 'Receiver ID and message are required'}), 400
    
    # Verify receiver exists and is an employee
    receiver = get_user_by_id(receiver_id)
    if not receiver or receiver.is_admin():
        return jsonify({'error': 'Invalid receiver'}), 400
    
    msg = save_message(current_user.id, receiver_id, message)
    return jsonify({'message': 'Message sent successfully', 'msg': {
        'id': str(msg['_id']),
        'sender_id': msg['sender_id'],
        'receiver_id': msg['receiver_id'],
        'message': msg['message'],
        'created_at': msg['created_at'].isoformat()
    }})

@app.route('/api/interactions/conversation/<user_id>', methods=['GET'])
@login_required
def get_conversation_api(user_id):
    """Get conversation with a specific user"""
    conversation = get_conversation(current_user.id, user_id)
    mark_messages_as_read(user_id, current_user.id)  # Mark as read
    
    return jsonify({'messages': [{
        'id': str(msg['_id']),
        'sender_id': msg['sender_id'],
        'receiver_id': msg['receiver_id'],
        'message': msg['message'],
        'created_at': msg['created_at'].isoformat(),
        'is_sender': msg['sender_id'] == current_user.id
    } for msg in conversation]})

# ---------------------------------------------
# User Guide Routes
# ---------------------------------------------
@app.route('/user-guide')
@login_required
def user_guide():
    """User Guide page"""
    return render_template('user_guide.html', user=current_user)

# ---------------------------------------------
# Graph Plotter Routes
# ---------------------------------------------
@app.route('/graph-plotter')
@login_required
def graph_plotter():
    """Graph Plotter Tool page"""
    return render_template('graph_plotter.html', user=current_user)

if __name__ == '__main__':
    print("🚀 DCRM Retraining Interface Server with Authentication")
    print("=" * 60)
    
    # Initialize default admin user
    initialize_default_admin()
    
    # Load existing dataset if available
    X_data, y_data = load_dataset()
    
    # If no dataset exists, try loading from data folder
    if len(X_data) == 0:
        print("📂 No existing dataset. Checking data folder...")
        X_initial, y_initial = load_initial_training_data()
        
        if len(X_initial) > 0:
            X_data = X_initial
            y_data = y_initial
            
            # Train initial model
            print("🔧 Training initial model...")
            model, scaler, error = train_model(X_data, y_data)
            
            if error:
                print(f"❌ Error training initial model: {error}")
            else:
                # Save dataset
                save_dataset(X_data, y_data)
                print(f"✅ Initial model trained with {len(X_data)} samples")
        else:
            print("⚠ No initial training data found. Model will be trained after first upload.")
    else:
        print(f"✅ Dataset loaded: {len(X_data)} samples")
        
        # Verify model files exist
        if not os.path.exists("dcrm_model.pkl") or not os.path.exists("dcrm_scaler.pkl"):
            print("🔧 Model files not found. Retraining from dataset...")
            model, scaler, error = train_model(X_data, y_data)
            if error:
                print(f"❌ Error training model: {error}")
            else:
                print("✅ Model retrained successfully")
    
    # Load existing training history if available
    if os.path.exists('training_history.json'):
        try:
            with open('training_history.json', 'r') as f:
                training_history = json.load(f)
            print(f"📊 Training history loaded: {len(training_history)} entries")
        except Exception as e:
            print(f"⚠ Error loading training history: {e}")
            training_history = []
    
    print("=" * 60)
    print("🔐 Authentication enabled with MongoDB")
    print("📍 Server running at: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
