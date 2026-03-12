# DCRM Retraining Interface — Comprehensive Project Report

> **Generated:** March 10, 2026  
> **Purpose:** AI-readable architectural and implementation summary of the full codebase.

---

## 1. Project Overview

### Project Name
**DCRM Retraining Interface** (Dynamic Contact Resistance Measurement System)

### Purpose
A web-based platform for field engineers (employees) and administrators to upload DCRM CSV measurement files, get ML-based fault predictions, validate/correct those predictions, and continuously retrain the underlying model — all through an authenticated browser interface.

### Problem It Solves
Electrical contacts in circuit breakers and switchgear degrade over time. DCRM (Dynamic Contact Resistance Measurement) tests produce CSV data that is traditionally analyzed manually. This system:
- Automates fault classification into three categories: **Healthy**, **Main Contact Fault**, and **Arc Fault**
- Enables field engineers to validate AI predictions and submit corrections, which immediately improve the model via online retraining
- Provides management dashboards, SOS request handling, and employee-to-employee messaging

### Key Features Implemented
- **CSV Upload & Prediction** — Upload a DCRM CSV, receive an instant ML classification
- **Model Feedback**: Ensured the validation and retraining UI is fully connected and functional.

### 🤖 Model Bootstrapping
Resolved the "No such file or directory: 'dcrm_model.pkl'" error by generating an initial model.

- **Sample Data Preparation**: Identifed sample CSV files from the `graph_plotter` directory and converted them into a bootstrap training dataset in the `data/` folder.
- **Auto-Training**: Executed the `ml/training/train_model.py` script to generate the initial `dcrm_model.pkl` and `dcrm_scaler.pkl`.
- **System Restoration**: Deployed the generated model files to the project root, enabling the predictive analysis feature.
- **Model Retraining** — Validate / correct predictions; the model retrains live with the new sample
- **Persistent Dataset** — Training data is saved to `dcrm_training_dataset.npz` and survives server restarts
- **Role-Based Access** — Admin vs Employee roles with separate views
- **Admin Dashboard** — Statistics, employee management, SOS notifications
- **Employee Dashboard** — Personal analytics, health trends, recent tests
- **Analysis Page** — Detailed time-series graphs per channel after prediction
- **SOS Requests** — Employees raise alarms; admins resolve them
- **Employee Interactions** — In-app messaging between employees
- **Field Advisor Chatbot** — Rule-based chatbot answering DCRM domain questions
- **Graph Plotter Tool** — Standalone React/Vite SPA embedded in the Flask app for side-by-side CSV comparison with interactive Plotly charts
- **Report Download** — Text-based DCRM test report download per prediction
- **User Guide Page** — In-app documentation

---

## 2. Tech Stack

### Backend
| Technology | Version | Purpose |
|---|---|---|
| Python | 3.12 | Primary language |
| Flask | 3.1.x | Web framework |
| Flask-Login | 0.6.3 | Session-based authentication |
| Flask-Bcrypt | 1.0.1 | Password hashing |
| scikit-learn | 1.3.x | RandomForestClassifier, StandardScaler |
| pandas | 2.1.x | CSV parsing |
| numpy | bundled | Feature vector operations |
| joblib | 1.3.x | Model serialization (.pkl files) |
| pymongo | 4.16 | MongoDB driver |
| python-dotenv | 1.0.0 | `.env` configuration |

### Database
| Technology | Details |
|---|---|
| MongoDB | Local instance on `localhost:27017` (configurable via `.env`) |
| Database Name | `dcrm_system` |
| Collections | `users`, `predictions`, `training_logs`, `sos_requests`, `employee_interactions` |

### Frontend (Flask Templates — Jinja2)
| Technology | Purpose |
|---|---|
| Jinja2 HTML templates | Server-rendered pages |
| Chart.js | Probability bar chart, confidence gauge on dashboard |
| Vanilla JS (dashboard.js, script.js, sidebar-toggle.js) | Client-side interactions |
| CSS (dashboard.css, style.css) | Custom styling, dark theme |

### Graph Plotter (Standalone SPA — `graph_plotter/`)
| Technology | Version | Purpose |
|---|---|---|
| React | 19.x | SPA framework |
| TypeScript | 5.9.x | Type safety |
| Vite | 5.4.x | Build tool |
| Plotly.js / react-plotly.js | 3.3.x | Interactive time-series graphs |
| PapaParse | 5.5.x | Client-side CSV parsing |
| Tailwind CSS | 4.x | Utility-first styling |
| React Router DOM | 7.x | Client-side routing |
| lucide-react | 0.555 | Icon library |

### Authentication
- Session-based login with **Flask-Login**
- Passwords hashed with **bcrypt**
- Role-based access: `admin` / `employee`
- `admin_required` custom decorator protecting admin routes

### Deployment / Hosting
- Development only: Flask built-in dev server (`debug=True`, port 5000)
- No production WSGI config (Gunicorn/uWSGI) present
- MongoDB Atlas URI is configurable in `.env` (currently set to local MongoDB)

---

## 3. Project Architecture

### Overview
```
User Browser
    │
    ├── Jinja2 HTML Templates (server-rendered pages)
    │       served by Flask routes in app.py
    │
    ├── REST API calls (fetch/XHR from JS)
    │       /api/* endpoints in app.py
    │
    └── Graph Plotter (embedded iframe or standalone)
            React SPA (graph_plotter/src/)
            Communicates only via client-side CSV file reads (no API)
```

### Backend Layer Structure (`app.py`)
Flask does not enforce a strict MVC layering, but the code is logically separated:

| Layer | Location | Responsibility |
|---|---|---|
| **Routes / Controllers** | `app.py` — `@app.route(...)` functions | Handle HTTP requests, call helpers, return JSON/HTML |
| **Service / Business Logic** | `app.py` — helper functions (`load_signature`, `train_model`, `convert_407b_to_arc_format`, `align_vector_length`, `load_dataset`, `save_dataset`) | ML inference, CSV normalization, feature extraction |
| **Data Access / Repository** | `database.py` | All MongoDB CRUD operations |
| **Models** | `database.py` — `User(UserMixin)` class | User entity used by Flask-Login |

### Frontend Structure

**Jinja2 Templates (`templates/`)**
```
login.html              — Login form
dashboard_new.html      — Employee analytics dashboard (primary)
dashboard.html          — Old dashboard (kept for reference)
analysis_new.html       — CSV upload + time-series analysis
my_history.html         — Employee prediction history
reports.html            — Downloadable reports list
settings.html           — User settings / password change
sos.html                — Employee SOS request form
field_advisor.html      — Chatbot UI
interactions.html       — Employee-to-employee messaging
user_guide.html         — In-app user documentation
graph_plotter.html      — Embeds the React graph plotter tool
admin_dashboard.html    — Admin overview (stats, employees, predictions, SOS)
admin_sos.html          — Admin SOS management
employee_predictions.html — Admin: view predictions for a specific employee
index.html              — Redirects to dashboard
```

**React SPA (`graph_plotter/src/`)**
```
main.tsx                — React entry point
App.tsx                 — Router: / → Layout, /edit → EditModeDraggable
context/
  DataContext.tsx        — Global state for loaded files, axis selections, range, units
components/
  Layout.tsx             — Main shell: sidebar ControlPanel + GraphViewer + DataGrid
  FileUpload.tsx         — Drag-and-drop upload for up to 2 DCRM CSV files
  ControlPanel.tsx       — Axis selector, range slider, unit prefs, export CSV
  GraphViewer.tsx        — Plotly.js scatter plot (dual-file comparison)
  DataGrid.tsx           — Scrollable raw data table
  StatsPanel.tsx         — Summary statistics (min, max, mean per channel)
  MetadataPanel.tsx      — Parsed metadata from CSV header block
  EditMode.tsx           — Static edit mode (possibly legacy)
  EditModeDraggable.tsx  — Draggable/resizable panel edit mode
utils/
  dataParser.ts          — PapaParse CSV → DCRMData typed struct (metadata + typed series)
  unitConversion.ts      — Unit conversions: A/mA, mm/cm, µΩ/mΩ, ms/s
```

### Folder Structure
```
retrain-x/
├── app.py                      — Flask application, all routes and ML logic
├── database.py                 — MongoDB models and CRUD helpers
├── .env                        — Environment variables (DB URI, secrets)
├── requirements.txt            — Python dependencies
├── dcrm_model.pkl              — Trained RandomForest model (joblib)
├── dcrm_scaler.pkl             — Fitted StandardScaler (joblib)
├── dcrm_training_dataset.npz   — Persisted training dataset (numpy)
├── training_history.json       — JSON log of all retraining events
├── templates/                  — Jinja2 HTML templates
├── static/
│   ├── css/                    — dashboard.css, style.css
│   └── js/                     — dashboard.js, script.js,- [x] Verify Analysis Page functionality <!-- id: 17 -->
- [x] Resolve Model Loading Error <!-- id: 18 -->
    - [x] Identify bootstrap data from project files <!-- id: 19 -->
    - [x] Create initial training dataset in `data/` folder <!-- id: 20 -->
    - [x] Run model training script to generate `.pkl` files <!-- id: 21 -->
    - [x] Verify backend can load the model correctly <!-- id: 22 -->
│   ├── src/                    — React source code
│   ├── public/                 — Static assets
│   └── package.json            — Node.js dependencies
└── venv/                       — Python virtual environment (Linux-style paths)
```

---

## 4. System Flow

### Employee Prediction Flow
```
1. Employee logs in → Flask-Login session created
2. Employee navigates to Analysis page
3. Employee uploads a DCRM CSV file
4. POST /api/analyze-csv or /api/predict
   a. File saved to uploads/
   b. convert_407b_to_arc_format() normalizes CSV layout if needed
   c. load_signature() extracts Channel-1 feature vector
   d. align_vector_length() pads/truncates vector to match scaler expectation
   e. model.predict() + model.predict_proba() run inference
   f. Prediction saved to MongoDB predictions collection
   g. JSON response: {prediction, probabilities, graph_data, filepath}
5. Client renders prediction result + time-series graphs
6. Employee validates: if incorrect, selects correct label
7. POST /api/retrain
   a. Loads feature vector from file on disk
   b. align_vector_length() to match existing data
   c. Appends {vector, label} to global X_data / y_data
   d. save_dataset() persists to .npz
   e. train_model() retrains RandomForest on full dataset
   f. Saves updated model .pkl files
   g. Logs event to training_history.json + MongoDB training_logs
```

### Admin Flow
```
1. Admin logs in → redirected to /admin dashboard
2. Admin sees: employee list, stats (total tests, avg health), recent predictions, SOS alerts
3. Admin can: add employees, delete employees, view per-employee predictions
4. Admin manages SOS requests: views pending ones, marks resolved
```

### API Communication
- All data exchange between frontend JS and backend uses **JSON over AJAX (fetch API)**
- File uploads use **multipart/form-data**
- No WebSocket; the chatbot and interactions use polling/page reload patterns

### Database Interaction
- All DB operations are synchronous via pymongo
- `database.py` functions are imported directly into `app.py`
- No ORM — raw PyMongo document dictionaries with manual conversion to `User` objects

---

## 5. Database Design

### Database Type
MongoDB (NoSQL, document-oriented)

### Collections

#### `users`
| Field | Type | Description |
|---|---|---|
| `_id` | ObjectId | Primary key |
| `username` | string | Unique login name |
| `email` | string | Unique email |
| `password` | string | bcrypt hash |
| `role` | string | `"admin"` or `"employee"` |
| `full_name` | string | Display name |
| `created_at` | datetime | Account creation timestamp |
| `is_active` | bool | Account enabled flag |

#### `predictions`
| Field | Type | Description |
|---|---|---|
| `_id` | ObjectId | Primary key |
| `user_id` | string | Reference to users._id (as string) |
| `filename` | string | Uploaded CSV filename |
| `prediction` | string | `"healthy"`, `"main"`, or `"arc"` |
| `probabilities` | dict | `{healthy: float, main: float, arc: float}` |
| `vector_size` | int | Number of features extracted |
| `timestamp` | datetime | Prediction timestamp |

#### `training_logs`
| Field | Type | Description |
|---|---|---|
| `_id` | ObjectId | Primary key |
| `user_id` | string | Who submitted the correction |
| `filename` | string | Source CSV filename |
| `correct_label` | string | Validated correct label |
| `total_samples` | int | Dataset size after this retraining |
| `timestamp` | datetime | Retraining timestamp |

#### `sos_requests`
| Field | Type | Description |
|---|---|---|
| `_id` | ObjectId | Primary key |
| `user_id` | string | Requesting employee |
| `problem_type` | string | Category of issue |
| `description` | string | Detailed description |
| `status` | string | `"pending"` or `"resolved"` |
| `created_at` | datetime | Request creation time |
| `resolved_at` | datetime | Resolution timestamp (nullable) |
| `resolved_by` | string | Admin user_id who resolved (nullable) |

#### `employee_interactions`
| Field | Type | Description |
|---|---|---|
| `_id` | ObjectId | Primary key |
| `sender_id` | string | Sending employee user_id |
| `receiver_id` | string | Receiving employee user_id |
| `message` | string | Message content |
| `created_at` | datetime | Sent timestamp |
| `read` | bool | Whether receiver has read it |

### Relationships
- `predictions.user_id` → `users._id` (manual lookup, no FK constraint)
- `training_logs.user_id` → `users._id`
- `sos_requests.user_id` → `users._id`; `resolved_by` → `users._id`
- `employee_interactions.sender_id`, `receiver_id` → `users._id`

---

## 6. API Endpoints

### Authentication
| Endpoint | Method | Purpose | Notes |
|---|---|---|---|
| `/login` | GET | Render login page | |
| `/login` | POST | Authenticate user | Form: `username`, `password`. Redirects admin→`/admin`, employee→`/dashboard` |
| `/logout` | GET | Log out current user | Requires login |

### Page Routes
| Endpoint | Method | Auth | Purpose |
|---|---|---|---|
| `/` | GET | Employee | Redirects to `/dashboard` |
| `/dashboard` | GET | Employee | Analytics dashboard |
| `/analysis` | GET | Employee | CSV upload + analysis page |
| `/my-history` | GET | Employee | Past predictions |
| `/reports` | GET | Employee | Downloadable reports list |
| `/settings` | GET | Employee | Settings page |
| `/sos` | GET | Employee | SOS request form |
| `/field-advisor` | GET | Employee | Chatbot page |
| `/interactions` | GET | Employee | Employee messaging |
| `/user-guide` | GET | Employee | User guide |
| `/graph-plotter` | GET | Employee | Embedded React graph plotter |
| `/admin` | GET | Admin only | Admin dashboard |
| `/admin/sos` | GET | Admin only | SOS management page |
| `/admin/employee-predictions/<user_id>` | GET | Admin only | Per-employee predictions |

### JSON APIs
| Endpoint | Method | Auth | Purpose | Request | Response |
|---|---|---|---|---|---|
| `/api/predict` | POST | Employee | Predict from uploaded CSV | `multipart: file` | `{prediction, probabilities, filename, filepath, vector_size}` |
| `/api/analyze-csv` | POST | Employee | Predict + return time-series graph data | `multipart: file` | `{prediction, probabilities, graph_data: {time, coil_current, resistance, dcrm_current, contact_travel}, data_points}` |
| `/api/retrain` | POST | Employee | Retrain model with correction | `JSON: {filepath, correct_label}` | `{message, total_samples, training_entry}` |
| `/api/stats` | GET | Employee | Model statistics + label distribution | — | `{total_samples, label_distribution, training_history, model_info}` |
| `/api/history` | GET | Employee | Full training history | — | `{history: [...]}` |
| `/api/dashboard/analytics` | GET | Employee | Dashboard charts data | — | `{total_tests, avg_health, fault_distribution, health_trend, spikes_trend, recent_tests}` |
| `/api/user/reports` | GET | Employee | All predictions for current user | — | `{reports: [...]}` |
| `/api/report/download/<report_id>` | GET | Employee | Download text report for a prediction | — | `text/plain` attachment |
| `/api/sos/create` | POST | Employee | Submit SOS request | `JSON: {problem_type, description}` | `{message, sos: {...}}` |
| `/api/sos/resolve/<sos_id>` | POST | Admin only | Resolve an SOS request | — | `{message}` |
| `/api/chatbot/ask` | POST | Employee | Ask chatbot a question | `JSON: {question, selected_text?}` | `{response: string}` |
| `/api/interactions/send` | POST | Employee | Send message to employee | `JSON: {receiver_id, message}` | `{message, msg: {...}}` |
| `/api/interactions/conversation/<user_id>` | GET | Employee | Get conversation with a user | — | `{messages: [...]}` |
| `/admin/add-employee` | POST | Admin only | Create new employee | Form: `username, email, password, full_name` | Redirect + flash |
| `/admin/delete-employee/<user_id>` | POST | Admin only | Delete employee | — | Redirect + flash |

---

## 7. Important Modules / Components

### `app.py`
The monolithic application file (~1,280 lines). Contains:
- Flask app initialization and config
- `load_signature(path)` — CSV parser that auto-detects Channel-1 columns (`coil c1`, `travel t1`, `res ch1`, `current ch1`) and flattens to a 1D numpy vector
- `convert_407b_to_arc_format(filepath)` — Normalizes 407_B-style CSVs (with velocity metadata header) to the arc_* layout expected by `load_signature`
- `align_vector_length(vector, target_len)` — Pads (zeros) or truncates feature vectors for consistency across retraining
- `load_dataset()` / `save_dataset()` — Numpy `.npz` persistence for the full training set
- `train_model(X, y)` — Trains a `RandomForestClassifier(n_estimators=300)` with a `StandardScaler`, saves `.pkl` files
- All Flask route handlers (authentication, pages, APIs)
- Startup logic: loads dataset, retrains if `.pkl` missing, initializes admin

### `database.py`
MongoDB data access layer (~420 lines):
- `User(UserMixin)` — Flask-Login compatible user model
- `create_user`, `get_user_by_username`, `get_user_by_id`, `verify_password`, `delete_user`, `update_password`
- `save_prediction`, `get_user_predictions`, `get_all_predictions`
- `save_training_log`
- `initialize_default_admin` — Creates default admin on first launch
- `create_sos_request`, `get_user_sos_requests`, `get_all_sos_requests`, `resolve_sos_request`
- `save_message`, `get_conversation`, `get_user_conversations`, `mark_messages_as_read`
- `get_user_statistics`

### `graph_plotter/src/utils/dataParser.ts`
Client-side DCRM CSV parser:
- `findDataHeaderRow()` — Scans first 100 rows to locate the data column header row (looks for "Coil Current", "Contact Travel", "DCRM")
- `extractMetadata()` — Parses key-value metadata from header rows above the data
- `getSamplingInterval()` — Extracts sampling speed (kHz) to compute a real time axis
- `parseDCRMFile(file)` — Returns a `DCRMData` object with `metadata`, `time[]`, `series{}`, and `groups{coilCurrents, contactTravel, dcrmResistance, dcrmCurrent, others}`

### `graph_plotter/src/context/DataContext.tsx`
React global state (Context API):
- Holds state for two loaded files (`data`, `data2`), axis selections, row range, grid/legend visibility, and unit preferences
- Default units: current → Amperes, travel → mm, resistance → µΩ, time → ms

### `graph_plotter/src/components/GraphViewer.tsx`
- Renders a `react-plotly.js` scatter plot
- File 1 series shown in **blue** palette (solid lines), File 2 in **green** palette (dotted lines)
- X-axis can be Time, Index, or any series column
- Applies unit conversion from `unitConversion.ts`
- Slices data by the user-defined row range

### `graph_plotter/src/components/ControlPanel.tsx`
Left sidebar with collapsible sections:
- File management (upload 1 or 2 files)
- X-axis source and column selector
- Y-axis multi-selector for both files
- Row range slider
- Unit preferences (per signal type)
- Grid / legend toggles
- Export visible data as CSV

### `static/js/dashboard.js`
Client-side JS for the old-style prediction result dashboard page:
- Reads prediction data from URL query params
- Creates Chart.js probability bar chart and confidence gauge
- Handles "Correct / Incorrect" validation UI and calls `/api/retrain`

---

## 8. Current Implementation Status

### Completed
- Full authentication system (login/logout, role-based access, password hashing)
- CSV upload, Channel-1 feature extraction, and ML prediction pipeline
- Online retraining with persistent dataset storage
- Admin dashboard with employee management, statistics, recent predictions, SOS alerts
- Employee dashboard with fault distribution charts and health trend
- Analysis page with time-series graph rendering after prediction
- SOS request creation and admin resolution workflow
- Employee-to-employee messaging (interactions)
- Field advisor chatbot (rule-based, domain-specific)
- Graph Plotter standalone SPA (dual-file DCRM CSV comparison with Plotly)
  - File upload (up to 2 files), metadata display, stats, data grid
  - Unit conversion, row range selection, export CSV
  - Edit mode with draggable panels
- Report download per prediction (plain text)
- Training history tracking (JSON file + MongoDB)
- 407_B CSV format auto-normalization

### Partially Implemented
- **Chatbot** — Rule-based keyword matching only; no LLM integration. Falls back to a generic catch-all message. Does not handle multi-turn conversation context.
- **Report Download** — Generates a `.txt` file, not a proper PDF. The code comment explicitly notes "you can enhance this with a PDF library like ReportLab".
- **Graph Plotter integration** — The React SPA is a separate Vite project that must be built and served separately. `graph_plotter.html` renders it as an embedded page, but there is no build step wired into the Flask startup.
- **User Settings** — The settings page route exists and renders `settings.html`, but no password-change API endpoint is wired up in the current routes (though `update_password()` exists in `database.py`).
- **`/old-dashboard` route** — `dashboard.html` is kept "for reference" but is still accessible.

### Missing / Placeholder
- **No input sanitization** on file uploads beyond extension check (`.csv` only)
- **No rate limiting** on any API endpoint
- **No pagination** for history/reports — uses hard-coded `limit=50/100`
- **No WebSocket / real-time** for interactions; users must manually refresh to see new messages
- **No email notifications** for SOS requests or critical faults
- **No production WSGI server config** (Gunicorn, uWSGI not present)
- **No automated tests** (no `tests/` folder, no `pytest`, no `unittest`)
- **No CSRF protection** on POST form routes (Flask-WTF not used)
- **No `.gitignore`** observed — `.pkl`, `.npz`, `.env`, and `venv/` may be committed to version control

---

## 9. Dependencies

### Python (`requirements.txt`)
```
Flask==3.0.0
pandas==2.1.4
scikit-learn==1.3.2
joblib==1.3.2
pymongo==4.6.1
flask-login==0.6.3
flask-bcrypt==1.0.1
python-dotenv==1.0.0
```
> **Note:** Actual installed versions may differ (e.g., pymongo 4.16 was installed during setup).

### Node.js — Graph Plotter (`graph_plotter/package.json`)
**Runtime dependencies:**
```
react ^19.2.0
react-dom ^19.2.0
react-router-dom ^7.10.1
plotly.js ^3.3.0
react-plotly.js ^2.6.0
papaparse ^5.5.3
tailwindcss ^4.1.17
lucide-react ^0.555.0
clsx ^2.1.1
tailwind-merge ^3.4.0
```
**Dev dependencies:**
```
vite ^5.4.11
typescript ~5.9.3
@vitejs/plugin-react ^4.3.4
eslint ^9.39.1
```

---

## 10. Potential Issues and Improvements

### Security Concerns
1. **No CSRF protection** — All POST form routes (add employee, delete employee, login) lack CSRF tokens. An attacker could perform cross-site request forgery. **Fix:** Add Flask-WTF with `CSRFProtect`.
2. **File upload path traversal risk** — `file.filename` is used directly in `os.path.join(upload_folder, file.filename)` without sanitization. A crafted filename like `../../etc/passwd` could be dangerous. **Fix:** Use `werkzeug.utils.secure_filename()`.
3. **`.env` may be committed to version control** — Contains MongoDB URI and `SECRET_KEY`. **Fix:** Add `.env` to `.gitignore`.
4. **`SECRET_KEY` has a weak fallback** — `os.getenv('SECRET_KEY', 'default_secret_key_change_me')`. If `.env` is missing, the fallback is used. **Fix:** Raise an error if `SECRET_KEY` is not set in production.
5. **No rate limiting** — `/api/predict` and `/login` are open to brute-force. **Fix:** Add Flask-Limiter.
6. **Report ownership check is string comparison** — `prediction['user_id'] != current_user.id` — both are strings, so this is correct, but it relies on consistency in how user IDs are stored.
7. **Bare `except:` clauses in `database.py`** — Several functions silently swallow all exceptions with bare `except: return False/None`. This hides bugs. **Fix:** Catch specific exceptions and log errors.

### Code Quality Issues
1. **Monolithic `app.py`** (~1,280 lines) — All routes, ML logic, and startup code in one file. Should be split into Flask Blueprints (e.g., `auth`, `api`, `admin`, `ml`).
2. **Global mutable state** — `X_data`, `y_data`, `training_history` are module-level lists. This is not thread-safe and will cause race conditions under concurrent requests. **Fix:** Use a database-backed queue or file lock for training operations.
3. **Chatbot is pure `if/elif` keyword matching** — ~250 lines of nested conditionals. Will not understand paraphrased or complex questions.
4. **`training_history.json` + MongoDB duplication** — Training history is stored in both a local JSON file and MongoDB `training_logs`. These can diverge.
5. **`predictions_collection` imported in `app.py`** — The `download_report_pdf` route directly imports `predictions_collection` from `database`, bypassing the data access layer.

### Performance Improvements
1. **Graph data truncated to 1000 points** in `/api/analyze-csv` — Hardcoded limit; should be configurable.
2. **`get_all_predictions(limit=100)`** loads all predictions with user info in a loop (N+1 query pattern). **Fix:** Use MongoDB `$lookup` aggregation.
3. **Model retraining blocks the HTTP response** — `train_model()` is called synchronously inside a request. On large datasets this will time out. **Fix:** Offload to a background Celery/RQ worker.
4. **Feature vectors stored as Python objects in `.npz`** (`dtype=object`) — This prevents optimized numpy operations. **Fix:** Pad all vectors to a fixed length at collection time and store as float32.

### Missing Error Handling
- No handling for when `dcrm_model.pkl` or `dcrm_scaler.pkl` is missing at prediction time (returns 500 with raw exception string).
- No validation that the uploaded CSV actually contains DCRM data before processing.
- The `load_initial_training_data()` silently skips files without a label in the filename; there's no user feedback.

---

## 11. Setup Instructions

### Prerequisites
- Python 3.12+
- MongoDB running locally on port 27017
- Node.js 18+ (only needed for the Graph Plotter SPA development)

### Steps

#### 1. Clone / Navigate to the project
```bash
cd retrain-x
```

#### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```
> Or activate the existing venv: `source venv/bin/activate` (Linux/Mac) or `.\venv\bin\Activate.ps1` (Windows PowerShell).

#### 3. Configure environment
The `.env` file is already present:
```env
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB_NAME=dcrm_system
SECRET_KEY=dcrm_super_secret_key_change_in_production_2024
FLASK_ENV=development
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=admin123
DEFAULT_ADMIN_EMAIL=admin@dcrm.com
```
Change `MONGODB_URI` to your MongoDB Atlas URI if using cloud MongoDB.

#### 4. Ensure MongoDB is running
```bash
# Windows: MongoDB should be running as a service
# Verify with:
mongosh --eval "db.runCommand({ connectionStatus: 1 })"
```

#### 5. (Optional) Add initial training data
Place DCRM CSV files in the `data/` folder with labels in filenames:
- `data/healthy_sample.csv`
- `data/main_fault_01.csv`  
- `data/arc_fault_test.csv`

#### 6. Run the Flask server
```bash
python app.py
```
On startup the server will:
- Create default admin user (`admin` / `admin123`) if not present
- Load existing dataset from `dcrm_training_dataset.npz`
- Retrain model if `.pkl` files are missing
- Start on `http://localhost:5000`

#### 7. Access the application
- Open `http://localhost:5000` in your browser
- Login with `admin` / `admin123`
- **Change the admin password after first login**

#### 8. (Optional) Run the Graph Plotter SPA in development
```bash
cd graph_plotter
npm install
npm run dev
# Opens on http://localhost:5173
```
To build for production embedding in Flask:
```bash
npm run build
# Copy dist/ contents to Flask static folder
```

---

## 12. Future Scope

### High Priority
1. **LLM-powered Chatbot** — Replace keyword matching with an LLM (e.g., OpenAI GPT, local Ollama) for intelligent multi-turn conversations about DCRM data
2. **PDF Report Generation** — Use ReportLab or WeasyPrint to generate structured PDF reports with charts
3. **Background Job Queue** — Move model retraining to Celery + Redis so it doesn't block HTTP requests
4. **CSRF Protection** — Add Flask-WTF for all forms
5. **File Upload Security** — Add `secure_filename`, MIME-type validation, and file size limits

### Medium Priority
6. **Flask Blueprints** — Split `app.py` into `auth/`, `api/`, `admin/`, `ml/`, `interactions/` blueprints
7. **Real-time Notifications** — Use Flask-SocketIO for live SOS alerts, new messages, and retraining progress
8. **Automated Testing** — Add `pytest` suite for ML pipeline, API endpoints, and database functions
9. **Multi-channel Analysis** — Currently only Channel-1 is used. Support Channel-2 and Channel-3 for richer feature sets
10. **Model Versioning** — Track model versions (e.g., MLflow or simple file versioning) so admins can roll back to a previous model
11. **Graph Plotter Integration** — Build the React SPA as part of Flask startup (or host as a sub-app) rather than requiring a separate build step

### Long-term / Advanced
12. **Batch Upload** — Allow uploading multiple CSV files at once for bulk prediction
13. **Trend Alerts** — Automatically flag when a device shows degrading health trend over time
14. **Mobile App** — Progressive Web App (PWA) or React Native app for field engineers
15. **Data Export** — Export full prediction history to Excel/CSV for external analysis
16. **Multi-tenant / Multi-site** — Support multiple electrical substations/sites under one deployment
17. **CI/CD Pipeline** — GitHub Actions for automated testing and deployment to cloud (e.g., AWS EC2, Azure App Service)
18. **Docker Compose** — Containerize Flask + MongoDB for reproducible deployments
