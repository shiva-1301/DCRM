# DCRM System — Enterprise Model Retraining & Management

A professional web application for **Dynamic Contact Resistance Measurement (DCRM)** analysis, predictive diagnostics, model retraining, field operations, and system management.

The system combines a Flask-based backend, MongoDB data storage, machine-learning-based diagnostics, an administrative dashboard, real-time employee interactions, and a React/Vite-based graph visualization component.

---

## 🚀 Overview

The DCRM System is designed to support the analysis and management of Dynamic Contact Resistance Measurement data.

The platform provides:

* Predictive diagnostics for DCRM measurements
* Fault classification
* Human-in-the-loop model retraining
* Emergency/SOS reporting
* Personnel and system monitoring
* Real-time employee messaging
* Interactive graph visualization
* Centralized data management through MongoDB

The goal is to provide a unified platform for analyzing DCRM measurements and supporting field and administrative workflows.

---

## ✨ Key Features

### 🔬 Predictive Diagnostics

The system analyzes DCRM measurement data and provides predictive classification for supported fault categories:

* **Healthy**
* **Main**
* **Arc**

The diagnostic workflow is designed to assist personnel in identifying potential issues from measurement data.

### 🤖 Model Retraining

The application supports a human-in-the-loop retraining workflow.

Validated measurement results can be incorporated into the model improvement process, allowing the diagnostic system to be updated as additional data becomes available.

### 🚨 SOS Management

Provides an emergency reporting workflow for field personnel.

Personnel can raise SOS reports so that relevant emergency information can be communicated to the appropriate users or administrators.

### 👨‍💼 Admin Dashboard

The administrative interface provides centralized monitoring and management capabilities, including:

* Personnel monitoring
* System information
* User management
* Operational information
* Diagnostic-related workflows

### 💬 Employee Interactions

The system provides real-time messaging functionality for communication between employees.

### 📊 Graph Visualization

The project includes a dedicated graph visualization component built using **Vite/React** for advanced visualization of measurement-related data.

---

# 🏗️ System Architecture

At a high level, the system follows this workflow:

```text
                    ┌─────────────────────┐
                    │      User / Admin   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Flask Web Server  │
                    │       app.py        │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
       ┌─────────────┐  ┌─────────────┐  ┌──────────────┐
       │ ML /        │  │ MongoDB     │  │ Application  │
       │ Diagnostics │  │ Database    │  │ Workflows    │
       └──────┬──────┘  └─────────────┘  └──────────────┘
              │
              ▼
       ┌─────────────────┐
       │ Prediction /    │
       │ Model Retraining│
       └─────────────────┘

                    ┌─────────────────────┐
                    │ Graph Plotter       │
                    │ React + Vite        │
                    └─────────────────────┘
```

---

# 🔄 Application Workflow

A typical diagnostic workflow can be represented as:

```text
DCRM Measurement Data
          │
          ▼
     Data Processing
          │
          ▼
   ML Diagnostic Model
          │
          ▼
   Fault Classification
          │
     ┌────┴─────┐
     │          │
     ▼          ▼
 Healthy    Fault Detected
               │
               ▼
       Human Validation
               │
               ▼
       Model Retraining
```

The retraining workflow is designed around human validation so that newly reviewed results can contribute to future model improvement.

---

# 🛠️ Technology Stack

## Backend

* Python
* Flask
* REST-based application workflows

## Database

* MongoDB

## Machine Learning

* Python-based machine-learning pipeline
* Predictive diagnostics
* Model retraining workflow

## Frontend

* HTML
* CSS
* JavaScript
* Jinja2 Templates
* Lightning-style modular dashboard components

## Graph Visualization

* React
* Vite
* Node.js
* npm

## Development

* Git
* GitHub
* Python Virtual Environment

---

# 📁 Project Structure

```text
DCRM/
│
├── app.py
│   └── Main Flask application
│
├── database.py
│   └── MongoDB models and database helpers
│
├── ml/
│   └── Machine learning logic and models
│
├── static/
│   ├── style.css
│   ├── dashboard.css
│   └── JavaScript/static assets
│
├── templates/
│   ├── Application templates
│   └── components/
│       └── Reusable UI components such as sidebar.html
│
├── graph_plotter/
│   └── React/Vite graph visualization component
│
├── requirements.txt
│   └── Python dependencies
│
└── README.md
```

---

# 🚀 Quick Start for New Devices

Follow these steps to clone and run the project on a new machine.

## 1. Prerequisites

Make sure the following are installed:

* **Python 3.10+**
* **MongoDB**

  * Running locally, or
  * A valid MongoDB connection URI
* **Node.js & npm**

  * Required only for the graph plotter component
* **Git**

---

## 2. Clone the Repository

```bash
git clone https://github.com/shiva-1301/DCRM.git
cd DCRM
```

---

## 3. Create a Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux/macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

## 5. Environment Configuration

Create a `.env` file in the root directory.

Example:

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

### ⚠️ Security Notice

The credentials above are intended for **local development/testing**.

Do not use:

```text
admin / admin123
```

in a production deployment.

Use strong, unique credentials and keep secrets in environment variables rather than committing them to Git.

Never commit the `.env` file to the repository.

---

# 🗄️ MongoDB Configuration

The application requires MongoDB for data persistence.

The default local configuration is:

```text
mongodb://localhost:27017/
```

with the database:

```text
dcrm_system
```

If MongoDB is hosted remotely, update:

```env
MONGODB_URI=<your-mongodb-connection-string>
```

and configure the appropriate database name.

---

# ▶️ Run the Application

Start the Flask application:

```bash
python app.py
```

The application should then be available at:

```text
http://localhost:5000
```

Open the URL in a browser.

---

# 📊 Graph Plotter

The project contains a separate graph visualization component under:

```text
graph_plotter/
```

This component uses:

* React
* Vite
* Node.js
* npm

To work with the graph plotter:

```bash
cd graph_plotter
npm install
```

Then use the appropriate development command defined by the project's `package.json`.

For example:

```bash
npm run dev
```

> The exact command should follow the scripts configured in `graph_plotter/package.json`.

---

# 🔐 Default Access

### Admin Panel

```text
/admin-panel
```

Default development credentials:

```text
Username: admin
Password: admin123
Email: admin@dcrm.com
```

**Change the default password immediately after the first login.**

For production deployments, configure secure credentials through environment variables or the application's supported authentication mechanism.

---

# 👥 User Roles

The application supports workflows for different types of users, including:

### Administrator

Administrators can access management and monitoring functionality such as:

* Personnel management
* System monitoring
* Administrative dashboards
* Operational workflows

### Field / Employee Users

Employees or field personnel can use application functionality such as:

* DCRM diagnostic workflows
* Measurement-related operations
* SOS reporting
* Employee interactions/messaging

> Exact permissions depend on the authentication and authorization logic implemented in the application.

---

# 🔬 Predictive Diagnostics

The diagnostic module provides classification of supported DCRM conditions.

Current classification categories include:

```text
Healthy
Main
Arc
```

The general workflow is:

```text
Measurement
     ↓
Data Processing
     ↓
ML Model
     ↓
Prediction
     ↓
Fault Classification
     ↓
Result Display
```

The diagnostic output is intended to assist personnel in identifying potential equipment/contact-related conditions.

---

# 🤖 Model Retraining

The system includes a model retraining workflow designed around **human validation**.

### General workflow

```text
Existing Model
      ↓
Prediction
      ↓
Human Review
      ↓
Validation / Correction
      ↓
Training Data Update
      ↓
Model Retraining
      ↓
Updated Model
```

This approach allows reviewed results to become part of the model improvement process.

---

# 🚨 SOS Management

The SOS module provides emergency reporting functionality for field personnel.

A typical workflow is:

```text
Field Personnel
       ↓
    Raise SOS
       ↓
 Emergency Information
       ↓
 Administrator / Relevant User
       ↓
     Response
```

This provides a dedicated channel for reporting urgent field situations.

---

# 💬 Real-Time Interactions

The system includes messaging functionality that enables employees to communicate with each other within the application.

This can support:

* Employee-to-employee communication
* Operational coordination
* Field communication
* Issue reporting

---

# 📈 Data Visualization

The graph plotter provides a dedicated visualization component for displaying measurement-related information.

The visualization layer is separated into:

```text
graph_plotter/
```

and uses a React/Vite-based frontend.

This separation allows visualization functionality to evolve independently from the primary Flask application.

---

# 🧩 Core Application Modules

The project can broadly be divided into the following modules:

| Module           | Purpose                                  |
| ---------------- | ---------------------------------------- |
| Authentication   | User authentication and access control   |
| Admin Dashboard  | Administrative monitoring and management |
| Diagnostics      | DCRM predictive analysis                 |
| Machine Learning | Prediction and model-related processing  |
| Model Retraining | Human-validated model improvement        |
| SOS Management   | Emergency reporting                      |
| Messaging        | Employee communication                   |
| Database         | MongoDB persistence and helpers          |
| Graph Plotter    | Interactive measurement visualization    |

---

# ⚙️ Configuration

The primary environment variables are:

| Variable                 | Purpose                  |
| ------------------------ | ------------------------ |
| `MONGODB_URI`            | MongoDB connection URI   |
| `MONGODB_DB_NAME`        | MongoDB database name    |
| `SECRET_KEY`             | Flask application secret |
| `FLASK_ENV`              | Flask environment        |
| `DEFAULT_ADMIN_USERNAME` | Initial admin username   |
| `DEFAULT_ADMIN_PASSWORD` | Initial admin password   |
| `DEFAULT_ADMIN_EMAIL`    | Initial admin email      |

---

# 🧪 Development

For development, create and activate a Python virtual environment before installing dependencies.

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
python app.py
```

---

# 🔒 Security Best Practices

Before deploying the application outside a local development environment:

* Change all default credentials.
* Use a strong Flask `SECRET_KEY`.
* Keep `.env` out of version control.
* Use environment-specific configuration.
* Use secure MongoDB credentials.
* Restrict database access where possible.
* Do not expose development credentials publicly.
* Use HTTPS for production deployments.
* Apply appropriate authentication and authorization controls.
* Validate and sanitize user-provided input.
* Review uploaded DCRM data before processing.

---

# 🐛 Troubleshooting

## MongoDB Connection Error

Verify that MongoDB is running and that:

```env
MONGODB_URI
```

contains the correct connection string.

---

## Python Dependency Error

Make sure the virtual environment is activated:

### Windows

```bash
venv\Scripts\activate
```

Then reinstall dependencies:

```bash
pip install -r requirements.txt
```

---

## Port 5000 Already in Use

Check whether another application is already using port `5000`.

Stop the conflicting process or configure the Flask application to use another available port.

---

## Graph Plotter Issues

Make sure Node.js and npm are installed:

```bash
node --version
npm --version
```

Then:

```bash
cd graph_plotter
npm install
```

Use the scripts defined in:

```text
graph_plotter/package.json
```

---

# 🤝 Contributing

Contributions are welcome.

## Development Workflow

1. Clone the repository.

```bash
git clone https://github.com/shiva-1301/DCRM.git
```

2. Create a feature branch.

```bash
git checkout -b feature/your-feature-name
```

3. Make your changes.

4. Test the changes locally.

5. Commit your work.

```bash
git add .
git commit -m "Add: description of change"
```

6. Push your branch.

```bash
git push origin feature/your-feature-name
```

7. Open a Pull Request.

8. Describe:

   * What changed
   * Why it changed
   * How it was tested
   * Any known limitations

---

# 📌 Contribution Guidelines

When contributing:

* Keep changes focused.
* Avoid unnecessary modifications to unrelated files.
* Follow the existing project structure.
* Use clear commit messages.
* Test changes before creating a Pull Request.
* Do not commit secrets or `.env` files.
* Update documentation when introducing new functionality.
* Clearly describe breaking changes.

---

# 🗺️ Roadmap

Potential areas for future development include:

* Improved diagnostic model performance
* Expanded fault classification
* Enhanced model monitoring
* Automated model evaluation
* Advanced DCRM visualization
* More detailed analytics dashboards
* Improved role-based access control
* Production deployment support
* Automated testing and CI/CD
* Enhanced audit logging
* Improved notification workflows

These items represent potential development directions and may not currently be implemented.

---

# 📜 Project Status

The DCRM System is under active development.

Features and implementation details may evolve as new diagnostic, visualization, retraining, and management capabilities are introduced.

---

# 👨‍💻 Maintainers & Contributors

The project is maintained by the **DCRM Team**.

Contributions from project collaborators and contributors are welcome.

---

# 📄 License

Add the project's applicable license information here.

If the repository does not currently have a license, choose an appropriate license before publishing the project for external reuse.

---

# 📞 Support

For project-related issues:

1. Check the troubleshooting section.
2. Review existing GitHub Issues.
3. Create a new GitHub Issue with:

   * A clear description
   * Steps to reproduce
   * Expected behavior
   * Actual behavior
   * Relevant logs/errors
   * Environment information

---

## ⭐ Project Summary

**DCRM System** provides an integrated platform for:

```text
DCRM Measurements
       │
       ▼
Data Analysis
       │
       ▼
Predictive Diagnostics
       │
       ├──────────────► Fault Classification
       │
       ▼
Human Validation
       │
       ▼
Model Retraining
       │
       ▼
Improved Diagnostics

Alongside:

Admin Management
SOS Reporting
Employee Messaging
Graph Visualization
MongoDB Data Management
```

---

*Maintained by the DCRM Team.*
