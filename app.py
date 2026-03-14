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
import requests

# Import database functions
from database import (
    bcrypt, initialize_default_admin, get_user_by_id, get_user_by_username,
    verify_password, create_user, get_all_employees, delete_user,
    save_prediction, get_user_predictions, get_all_predictions,
    save_training_log, get_user_statistics,
    save_message, get_conversation, get_user_conversations, mark_messages_as_read,
    update_password, predictions_collection, get_all_sos_requests
)

# Import Blueprints
from backend.routes.sos_routes import sos_bp
from backend.routes.prediction_routes import prediction_bp

# Import ML utilities
from ml.utils.features import extract_features

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key_change_me')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DATA_FOLDER'] = 'data'

# ML paths — point to where the model files actually live
app.config['MODEL_PATH'] = os.path.join(os.path.dirname(__file__), 'dcrm_model.pkl')
app.config['SCALER_PATH'] = os.path.join(os.path.dirname(__file__), 'dcrm_scaler.pkl')
app.config['DATASET_PATH'] = os.path.join(os.path.dirname(__file__), 'dcrm_training_dataset.npz')
app.config['TRAINING_HISTORY_PATH'] = os.path.join(os.path.dirname(__file__), 'ml', 'training_history.json')

# Register Blueprints
app.register_blueprint(sos_bp)
app.register_blueprint(prediction_bp)

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
    Loads a DCRM signature CSV and extracts statistical features.
    """
    try:
        # Read CSV with header on line 2
        df = pd.read_csv(path, engine="python", on_bad_lines="skip", header=1)
        
        # Remove empty spacer columns
        df = df.dropna(axis=1, how='all')
        
        # Clean column names
        df.columns = df.columns.str.strip().str.replace("\t", " ", regex=False)
        
        # Use centralized feature extraction
        return extract_features(df), None
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

@app.route('/report-details/<report_id>')
@login_required
def report_details(report_id):
    """Detailed view for a single report"""
    from bson.objectid import ObjectId
    try:
        # Get prediction from database
        report = predictions_collection.find_one({'_id': ObjectId(report_id)})
        
        if not report:
            flash('Report not found', 'danger')
            return redirect(url_for('reports_page'))
        
        # Verify user owns this prediction
        if report['user_id'] != current_user.id:
            flash('Unauthorized access', 'danger')
            return redirect(url_for('reports_page'))
        
        # Calculate confidence if not present
        if 'confidence' not in report:
            probs = report.get('probabilities', {})
            pred_class = report.get('prediction')
            report['confidence'] = float(probs.get(pred_class, 0.0)) * 100
            
        return render_template('report_details_page.html', report=report, user=current_user)
        
    except Exception as e:
        flash(f'Error retrieving report: {str(e)}', 'danger')
        return redirect(url_for('reports_page'))

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

@app.route('/admin/sos')
@login_required
@admin_required
def admin_sos():
    """Admin SOS management page"""
    all_sos = get_all_sos_requests()
    return render_template('admin_sos.html', user=current_user, sos_requests=all_sos)

# ---------------------------------------------
# API Routes
# ---------------------------------------------
@app.route('/api/predict', methods=['POST'])
@login_required
def predict():
    """Predict the class of uploaded CSV file using statistical features"""
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
        
        # Parse CSV and extract statistical features (24 features)
        df = pd.read_csv(filepath, engine='python', on_bad_lines='skip', header=1)
        df = df.dropna(axis=1, how='all')
        df.columns = df.columns.str.strip().str.replace('\t', ' ', regex=False)
        
        features = extract_features(df)
        if features is None or len(features) == 0:
            return jsonify({'error': 'Could not extract features from CSV'}), 400
        
        # Load model and scaler
        model, scaler, error = load_model_and_scaler()
        if error:
            return jsonify({'error': f'Error loading model: {error}'}), 500
        
        # Make prediction
        vector_scaled = scaler.transform([features])
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
            vector_size=len(features)
        )
        
        return jsonify({
            'prediction': prediction,
            'probabilities': prob_dict,
            'filename': file.filename,
            'filepath': filepath,
            'vector_size': len(features)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/retrain', methods=['POST'])
@login_required
def retrain():
    """Retrain the model with corrected label using statistical features"""
    global X_data, y_data, training_history
    
    data = request.json
    filepath = data.get('filepath')
    correct_label = data.get('correct_label')
    
    if not filepath or not correct_label:
        return jsonify({'error': 'Missing filepath or correct_label'}), 400
    
    if correct_label not in ['healthy', 'main', 'arc']:
        return jsonify({'error': 'Invalid label. Must be healthy, main, or arc'}), 400
    
    try:
        # Parse CSV and extract statistical features (same as prediction)
        df = pd.read_csv(filepath, engine='python', on_bad_lines='skip', header=1)
        df = df.dropna(axis=1, how='all')
        df.columns = df.columns.str.strip().str.replace('\t', ' ', regex=False)
        
        features = extract_features(df)
        if features is None or len(features) == 0:
            return jsonify({'error': 'Could not extract features from CSV'}), 400
        
        # Add corrected sample to dataset
        X_data.append(features)
        y_data.append(correct_label)
        
        # Save updated dataset to disk
        save_dataset(X_data, y_data)
        
        # Convert to numpy arrays
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
    """Generate and download a professional PDF report for a specific prediction"""
    from bson.objectid import ObjectId
    from fpdf import FPDF
    from io import BytesIO
    from flask import send_file
    
    try:
        # Get prediction from database
        prediction = predictions_collection.find_one({'_id': ObjectId(report_id)})
        
        if not prediction:
            return jsonify({'error': 'Report not found'}), 404
        
        # Verify user owns this prediction
        if prediction['user_id'] != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Create PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Header
        pdf.set_font("Helvetica", 'B', 24)
        pdf.set_text_color(31, 41, 55)
        pdf.cell(0, 20, "DCRM Diagnostic Report", ln=True, align='C')
        
        pdf.set_font("Helvetica", 'I', 10)
        pdf.cell(0, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='C')
        pdf.ln(10)
        
        # Section Header Style
        def section_header(title):
            pdf.set_font("Helvetica", 'B', 14)
            pdf.set_fill_color(243, 244, 246)
            pdf.set_text_color(55, 65, 81)
            pdf.cell(0, 10, f"  {title}", ln=True, fill=True)
            pdf.ln(5)

        # File Info
        section_header("Test Information")
        pdf.set_font("Helvetica", '', 11)
        pdf.set_text_color(31, 41, 55)
        pdf.cell(50, 8, "Filename:", 0)
        pdf.cell(0, 8, str(prediction['filename']), 0, ln=True)
        pdf.cell(50, 8, "Timestamp:", 0)
        pdf.cell(0, 8, prediction['timestamp'].strftime('%Y-%m-%d %H:%M:%S'), 0, ln=True)
        pdf.cell(50, 8, "Features Analyzed:", 0)
        pdf.cell(0, 8, f"{prediction['vector_size']} parameters", 0, ln=True)
        pdf.ln(10)
        
        # Prediction Results
        section_header("Analysis Results")
        
        # Big status box
        status = prediction['prediction'].upper()
        if status == 'HEALTHY':
            pdf.set_fill_color(209, 250, 229)
            pdf.set_text_color(6, 95, 70)
        elif status == 'MAIN':
            pdf.set_fill_color(254, 243, 199)
            pdf.set_text_color(146, 64, 14)
        else:
            pdf.set_fill_color(254, 226, 226)
            pdf.set_text_color(153, 27, 27)
            
        pdf.set_font("Helvetica", 'B', 16)
        pdf.cell(0, 15, f"DIAGNOSIS: {status}", ln=True, fill=True, align='C')
        pdf.ln(10)
        
        # Probabilities Table
        pdf.set_font("Helvetica", 'B', 12)
        pdf.set_text_color(55, 65, 81)
        pdf.cell(95, 10, "Classification Category")
        pdf.cell(95, 10, "Confidence Level")
        pdf.ln()
        
        pdf.set_font("Helvetica", '', 11)
        for label, prob in sorted(prediction['probabilities'].items(), key=lambda x: x[1], reverse=True):
            pdf.cell(95, 8, label.capitalize(), border='B')
            pdf.cell(95, 8, f"{prob * 100:.1f}%", border='B')
            pdf.ln()
        pdf.ln(10)
        
        # Recommendations
        section_header("Field Recommendations")
        pdf.set_font("Helvetica", '', 11)
        pdf.set_text_color(31, 41, 55)
        
        if status == 'HEALTHY':
            rec = "The system is performing within normal operational parameters. No immediate action is required. Continue following your standard periodic maintenance schedule."
        elif status == 'MAIN':
            rec = "Detected anomalies in main contact resistance. This baseline deviation suggests early-stage contact degradation or misalignment. IMMEDIATE INSPECTION of primary contact surfaces is recommended during the next maintenance window."
        else:
            rec = "CRITICAL: Signature indicates high-frequency resistance fluctuations characteristic of arc faults. HIGH RISK OF FAILURE. Immediate interrupter inspection required. DO NOT return to service until verified."
            
        pdf.multi_cell(0, 6, rec)
        
        # Footer
        pdf.set_y(-25)
        pdf.set_font("Helvetica", 'I', 8)
        pdf.set_text_color(156, 163, 175)
        pdf.cell(0, 10, "Auto-generated by DCRM AI Diagnostic Engine. Use as supporting tool for field decisions.", align='C')
        
        # Output PDF to BytesIO buffer
        pdf_buffer = BytesIO(bytes(pdf.output()))
        pdf_buffer.seek(0)
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'DCRM_Report_{report_id}.pdf'
        )
        
    except Exception as e:
        print(f"PDF Error: {e}")
        import traceback
        traceback.print_exc()
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
    """Analyze CSV file using statistical features and return time-series for graphs"""
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
        
        # Read CSV for both feature extraction and graph rendering
        df = pd.read_csv(filepath, engine='python', on_bad_lines='skip', header=1)
        df = df.dropna(axis=1, how='all')
        df.columns = df.columns.str.strip().str.replace('\t', ' ', regex=False)
        
        # Extract statistical features (24 features) for prediction
        features = extract_features(df)
        if features is None or len(features) == 0:
            return jsonify({'error': 'Could not extract features from CSV'}), 400
        
        # Load model and scaler
        model, scaler, error = load_model_and_scaler()
        if error:
            return jsonify({'error': f'Error loading model: {error}'}), 500
        
        # Make prediction using statistical features
        vector_scaled = scaler.transform([features])
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
            vector_size=len(features)
        )
        
        # Extract time-series data for graphs
        time_index = list(range(len(df)))
        coil_current_data = []
        resistance_data = []
        dcrm_current_data = []
        contact_travel_data = []
        
        for col in df.columns:
            name = col.lower()
            if 'coil' in name and 'c1' in name:
                coil_current_data = df[col].fillna(0).tolist()
            elif 'travel' in name and 't1' in name:
                contact_travel_data = df[col].fillna(0).tolist()
            elif 'res' in name and 'ch1' in name:
                resistance_data = df[col].fillna(0).tolist()
            elif 'current' in name and 'ch1' in name:
                dcrm_current_data = df[col].fillna(0).tolist()
        
        # Downsample for performance
        step = max(1, len(time_index) // 2000)
        graph_data = {
            'time': time_index[::step],
            'coil_current': coil_current_data[::step] if coil_current_data else [],
            'resistance': resistance_data[::step] if resistance_data else [],
            'dcrm_current': dcrm_current_data[::step] if dcrm_current_data else [],
            'contact_travel': contact_travel_data[::step] if contact_travel_data else []
        }
        
        return jsonify({
            'prediction': prediction,
            'probabilities': prob_dict,
            'filename': file.filename,
            'filepath': filepath,
            'vector_size': len(features),
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

# Load DCRM technical info for chatbot grounding
DCRM_INFO_CONTENT = ""
try:
    info_path = os.path.join('data', 'dcrm_info.md')
    if os.path.exists(info_path):
        # Explicitly loading as UTF-8 with replacement for any stray bytes
        with open(info_path, 'r', encoding='utf-8', errors='replace') as f:
            DCRM_INFO_CONTENT = f.read()
            print("📖 DCRM Technical Info loaded for Field Advisor")
except Exception as e:
    print(f"⚠ Could not load dcrm_info.md: {e}")

@app.route('/api/chatbot/ask', methods=['POST'])
@login_required
def chatbot_ask():
    """Chatbot API endpoint - uses Groq LLM grounded in DCRM knowledge"""
    data = request.json
    question = data.get('question', '').strip()
    
    if not question:
        return jsonify({'error': 'Question is required'}), 400
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return jsonify({'response': "I'm having trouble connecting to my brain (API key missing). Please contact the administrator."})

    try:
        # System prompt to focus the LLM as a Field Advisor
        system_prompt = (
            "You are the 'Field Advisor', an expert assistant for the DCRM (Dynamic Contact Resistance Measurement) system. "
            "Your goal is to help field engineers troubleshoot issues, understand measurements, and use the DCRM platform effectively. "
            "Use the provided technical reference documentation to answer questions accurately. "
            "If the information is not in the documentation, use your general knowledge but prioritize the documentation. "
            "Be professional, concise, and technically precise.\n\n"
            f"TECHNICAL DOCUMENTATION:\n{DCRM_INFO_CONTENT}"
        )

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                "temperature": 0.2,
                "max_tokens": 1024
            },
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result['choices'][0]['message']['content']
            return jsonify({'response': answer})
        else:
            print(f"Groq API Error: {response.status_code} - {response.text}")
            return jsonify({'response': "I'm sorry, I'm experiencing some technical difficulties. Please try again in a moment."})
            
    except Exception as e:
        print(f"Chatbot Error: {e}")
        return jsonify({'response': "I encountered an error while processing your request. Please check your connection and try again."})
    
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
