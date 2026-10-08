# DCRM Fault Diagnostics Platform

A Flask web app for analysing **Dynamic Contact Resistance Measurement (DCRM)** tests on high-voltage circuit breakers. Field engineers upload a DCRM CSV, the app classifies the breaker condition with a machine-learning model (Healthy / Main-contact wear / Arcing-contact wear), plots the test curves, and lets experts correct predictions to retrain the model over time.

**Live demo:** _coming soon — see [Deployment](#deployment)_

![Screenshot placeholder](docs/screenshot-dashboard.png)
<!-- Add screenshots to docs/ and update the paths above -->

## Features

- **Fault prediction:** upload a DCRM CSV and get a classification with per-class confidence.
- **Analysis view:** resistance, current and travel curves with interactive charts.
- **Graph Plotter:** zoomable, multi-channel plots of any DCRM test file.
- **Human-in-the-loop retraining:** correct a wrong prediction and the model retrains instantly.
- **Reports and history:** every prediction is saved per user and can be downloaded as a report.
- **SOS:** field staff can raise urgent issues, and admins track and resolve them.
- **Interactions:** direct messaging between employees.
- **Field Advisor:** a rule-based assistant for common DCRM troubleshooting questions.
- **Admin panel:** manage employees and view their prediction activity.
- **Responsive UI:** works on desktop, tablet and mobile (off-canvas navigation on small screens).

## Tech stack

| Layer    | Tech |
|----------|------|
| Backend  | Python 3.10+, Flask 3 (blueprints), Flask-Login, Flask-Bcrypt |
| Database | MongoDB (PyMongo) |
| ML       | scikit-learn, NumPy, pandas, joblib |
| Frontend | Jinja2 templates, vanilla JS, Chart.js, CSS custom properties |
| Hosting  | Gunicorn on Render (config included) |

## Project structure

```
DCRM/
├── backend/
│   ├── app.py            # App factory + dev server entry
│   ├── config.py         # All settings, read from environment
│   ├── database/         # MongoDB models & helpers
│   ├── routes/           # Blueprints: auth, dashboard, admin, prediction, sos, ...
│   ├── services/         # ML, CSV parsing, prediction, reports, retraining
│   └── utils/            # Upload + security helpers
├── frontend/
│   ├── templates/        # Jinja2 pages
│   └── static/{css,js}/  # Stylesheets and scripts
├── ml/                   # Training script + feature engineering (model files are generated)
├── data/                 # Seed CSVs used to train the first model
├── datasets/             # Real DCRM test files (402, 407, 410 breakers)
├── wsgi.py               # Production entrypoint (gunicorn wsgi:app)
└── render.yaml           # One-click Render deployment
```

## Local setup

**Prerequisites:** Python 3.10+, and MongoDB running locally (or a MongoDB Atlas URI).

```bash
git clone https://github.com/shiva-1301/DCRM.git
cd DCRM

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt

cp .env.example .env           # then edit the values
python -m backend.app
```

Open http://localhost:5000. On first start the app creates the admin account from `DEFAULT_ADMIN_*` and trains an initial model from `data/`.

### Environment variables

| Variable | Purpose |
|----------|---------|
| `MONGODB_URI` | MongoDB connection string |
| `MONGODB_DB_NAME` | Database name (default `dcrm_system`) |
| `SECRET_KEY` | Flask session signing key. **Required in production.** |
| `DEFAULT_ADMIN_USERNAME` / `DEFAULT_ADMIN_PASSWORD` / `DEFAULT_ADMIN_EMAIL` | First admin account |
| `SESSION_COOKIE_SECURE` | `true` when served over HTTPS |
| `FLASK_ENV` | `development` enables debug mode |
| `HOST`, `PORT` | Dev server bind address |

> Locally the admin password falls back to `admin123` if unset. Always set `DEFAULT_ADMIN_PASSWORD` before deploying, and change it after first login.

## Deployment

The repo ships with a [render.yaml](render.yaml) blueprint for Render's free tier.

1. Create a free MongoDB Atlas cluster. Add a database user, allow access from `0.0.0.0/0`, and copy the connection string.
2. Push this branch to GitHub.
3. On [render.com](https://render.com), choose **New → Blueprint** and select the repo. Render reads `render.yaml`.
4. When prompted, set `MONGODB_URI` (the Atlas string) and `DEFAULT_ADMIN_PASSWORD`. `SECRET_KEY` is generated automatically.
5. Deploy, then put the `.onrender.com` URL in the "Live demo" line above.

> Render's free disk is ephemeral. Uploaded files and the retrained model reset on each redeploy, and the app automatically retrains from `data/` at startup. User accounts, predictions and SOS records live in MongoDB and persist.

## How the model works

Each CSV is reduced to a fixed vector of statistical features (resistance, current and travel characteristics, see [ml/utils/features.py](ml/utils/features.py)). These are scaled and fed to a scikit-learn classifier. Corrections submitted from the Analysis page are appended to the training set, and the model is retrained on the spot.
