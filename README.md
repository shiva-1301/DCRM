# DCRM System — Enterprise Model Retraining & Management

A professional, enterprise-grade web application for Dynamic Contact Resistance Measurement (DCRM) analysis, predictive diagnostics, and model retraining.

## 🚀 Quick Start for New Devices

Follow these steps to clone and run the project on a new machine:

### 1. Prerequisites
- **Python 3.10+**
- **MongoDB** (running locally or a connection URI)
- **Node.js & npm** (only for the graph plotter component)

### 2. Clone the Repository
```bash
git clone https://github.com/shiva-1301/DCRM.git
cd DCRM
```

### 3. Setup Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Environment Configuration
Create a `.env` file in the root directory and add the following:
```env
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB_NAME=dcrm_system

# Flask Configuration
SECRET_KEY=your_super_secret_random_string
FLASK_ENV=development

# Default Admin Credentials
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=admin123
DEFAULT_ADMIN_EMAIL=admin@dcrm.com
```

### 6. Run the Application
```bash
python app.py
```
The application will be available at `http://localhost:5000`.

---

## 🏗️ Project Structure
```
DCRM/
├── app.py              # Main Flask Application
├── database.py         # MongoDB Models & Helpers
├── ml/                 # Machine Learning Logic & Models
├── static/             # CSS (style.css, dashboard.css) & JS
├── templates/          # Modular Jinja2 Templates
│   └── components/     # Reusable UI (sidebar.html, etc.)
└── graph_plotter/      # Advanced Visualization (Vite/React)
```

## 🔐 Default Access
- **Admin Panel**: `/admin-panel`
- **Username**: `admin`
- **Password**: `admin123`
*(Please change the password immediately after first login)*

## 🛠️ Main Features
- **Predictive Diagnostics**: Real-time classification of fault types (Healthy, Main, Arc).
- **Model Retraining**: Human-in-the-loop validation to improve model accuracy over time.
- **SOS Management**: Emergency reporting system for field personnel.
- **Admin Dashboard**: Comprehensive personnel and system monitoring.
- **Interactions**: Real-time messaging between employees.

---
*Maintained by the DCRM Team.*
