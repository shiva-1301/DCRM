# DCRM Model Retraining Interface

A modern, interactive web interface for DCRM (Dynamic Contact Resistance Measurement) model prediction and retraining with persistent dataset storage.

## Features

✨ **Prediction**: Upload CSV files and get instant classification results  
📊 **Confidence Display**: Visual confidence bars for all three classes (healthy, main, arc)  
🔄 **Model Retraining**: Validate predictions and retrain the model with correct labels  
💾 **Dataset Persistence**: All training data is saved and survives server restarts  
📂 **Auto Training**: Automatically loads and trains from initial CSV files in data folder  
📈 **Training History**: Track all retraining sessions  
🎨 **Modern UI**: Beautiful dark theme with smooth animations  
📱 **Responsive**: Works on all devices  

## Installation

1. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

Or use the virtual environment (recommended):
```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

## Initial Setup (Optional)

If you have initial training CSV files, you can set them up before first run:

1. **Place training files** in the `data/` folder with labels in filenames:
   - Files with "healthy" in name → healthy class
   - Files with "main" in name → main fault class
   - Files with "arc" in name → arc fault class

   Examples:
   ```
   data/healthy_sample_1.csv
   data/main_fault_01.csv
   data/arc_fault_test.csv
   ```

2. On first startup, the server will:
   - Load all CSV files from `data/` folder
   - Extract Channel-1 features
   - Train the initial model
   - Save the dataset for future use

## Usage

1. **Start the server**:
```bash
python app.py
```

Or use the quick start script:
```bash
./start.sh
```

2. **Open your browser** and navigate to:
```
http://localhost:5000
```

3. **Upload a CSV file** by dragging and dropping or clicking Browse

4. **Click Predict** to get classification results

5. **Validate the prediction**:
   - Click "Correct" if the prediction is accurate
   - Click "Incorrect" and select the correct label to retrain the model

## Dataset Persistence

The system automatically saves and loads training data:

- **Dataset File**: `dcrm_training_dataset.npz`
- **Model Files**: `dcrm_model.pkl`, `dcrm_scaler.pkl`
- **Training Log**: `training_history.json`

These files ensure:
- Training data persists across server restarts
- No data loss when retraining
- Incremental learning from corrections

## File Structure

```
retrain/
├── app.py                       # Flask backend server
├── dcrm_model.pkl              # Trained RandomForest model
├── dcrm_scaler.pkl             # StandardScaler for preprocessing
├── dcrm_training_dataset.npz   # Persistent training dataset
├── training_history.json       # Training log
├── arc_2.csv                   # Sample test dataset
├── requirements.txt            # Python dependencies
├── setup.sh                    # Setup helper script
├── start.sh                    # Quick start script
├── data/                       # Initial training files (optional)
├── templates/
│   └── index.html              # Main HTML template
├── static/
│   ├── css/
│   │   └── style.css           # Styles and animations
│   └── js/
│       └── script.js           # Frontend logic
└── uploads/                    # Uploaded files directory
```

## API Endpoints

### POST /api/predict
Upload a CSV file and get predictions
- **Request**: multipart/form-data with 'file' field
- **Response**: JSON with prediction, probabilities, and metadata

### POST /api/retrain
Retrain the model with a corrected label
- **Request**: JSON with filepath and correct_label
- **Response**: JSON with success message and updated statistics

### GET /api/stats
Get current model statistics
- **Response**: JSON with total samples, label distribution, and recent history

### GET /api/history
Get full training history
- **Response**: JSON with complete training history

## CSV File Format

The CSV files should have:
- Header on line 2
- Channel-1 columns containing:
  - Coil Current C1
  - Contact Travel T1
  - DCRM Res CH1
  - DCRM Current CH1

Example: See `arc_2.csv` for reference

## Technologies Used

- **Backend**: Flask (Python)
- **Machine Learning**: scikit-learn, RandomForestClassifier
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Styling**: Custom CSS with gradients and animations
- **Fonts**: Inter (Google Fonts)

## Model Details

- **Algorithm**: Random Forest Classifier
- **Features**: All Channel-1 measurements from CSV
- **Classes**: healthy, main, arc
- **Preprocessing**: StandardScaler normalization

## Contributing

Feel free to submit issues or pull requests to improve the interface!

## License

MIT License
