// Global variables
let currentFilePath = null;
let currentPrediction = null;

// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const browseBtn = document.getElementById('browseBtn');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileSize');
const changeFileBtn = document.getElementById('changeFileBtn');
const predictBtnGroup = document.getElementById('predictBtnGroup');
const predictBtn = document.getElementById('predictBtn');
const resultsSection = document.getElementById('resultsSection');
const predictedClass = document.getElementById('predictedClass');
const correctBtn = document.getElementById('correctBtn');
const incorrectBtn = document.getElementById('incorrectBtn');
const correctionSection = document.getElementById('correctionSection');
const loadingOverlay = document.getElementById('loadingOverlay');
const loadingText = document.getElementById('loadingText');
const toast = document.getElementById('toast');
const historyContainer = document.getElementById('historyContainer');
const totalSamples = document.getElementById('totalSamples');

// Event Listeners
uploadArea.addEventListener('click', () => fileInput.click());
browseBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    fileInput.click();
});
fileInput.addEventListener('change', handleFileSelect);
changeFileBtn.addEventListener('click', resetUpload);
predictBtn.addEventListener('click', predictFile);
correctBtn.addEventListener('click', handleCorrectPrediction);
incorrectBtn.addEventListener('click', () => {
    correctionSection.style.display = 'block';
});

// Drag and drop
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
});

// Label options
document.querySelectorAll('.label-option').forEach(option => {
    option.addEventListener('click', () => {
        const label = option.dataset.label;
        retrainModel(label);
    });
});

// Functions
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
}

function handleFile(file) {
    if (!file.name.endsWith('.csv')) {
        showToast('Please select a CSV file', 'error');
        return;
    }

    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);

    uploadArea.style.display = 'none';
    fileInfo.style.display = 'flex';
    predictBtnGroup.style.display = 'block';
    resultsSection.style.display = 'none';
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

function resetUpload() {
    fileInput.value = '';
    uploadArea.style.display = 'block';
    fileInfo.style.display = 'none';
    predictBtnGroup.style.display = 'none';
    resultsSection.style.display = 'none';
    currentFilePath = null;
    currentPrediction = null;
}

async function predictFile() {
    const file = fileInput.files[0];
    if (!file) return;

    showLoading('Analyzing file...');

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/predict', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Prediction failed');
        }

        currentFilePath = data.filepath;
        currentPrediction = data.prediction;

        hideLoading();
        showToast('Prediction completed! Redirecting to dashboard...', 'success');

        // Redirect to dashboard with prediction data
        setTimeout(() => {
            const encodedData = encodeURIComponent(JSON.stringify(data));
            window.location.href = `/dashboard?data=${encodedData}`;
        }, 1000);
    } catch (error) {
        hideLoading();
        showToast(error.message, 'error');
    }
}

function displayResults(data) {
    resultsSection.style.display = 'block';

    // Set predicted class
    predictedClass.textContent = data.prediction;
    predictedClass.className = 'label-value ' + data.prediction;

    // Set confidence bars
    const probabilities = data.probabilities;
    updateConfidenceBar('healthyBar', probabilities.healthy || 0);
    updateConfidenceBar('mainBar', probabilities.main || 0);
    updateConfidenceBar('arcBar', probabilities.arc || 0);

    // Reset correction section
    correctionSection.style.display = 'none';
    document.querySelectorAll('.label-option').forEach(opt => {
        opt.classList.remove('selected');
    });

    // Smooth scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function updateConfidenceBar(barId, probability) {
    const bar = document.getElementById(barId);
    const percent = (probability * 100).toFixed(1);
    const fill = bar.querySelector('.confidence-fill');
    const percentText = bar.querySelector('.confidence-percent');

    percentText.textContent = percent + '%';

    // Animate width
    setTimeout(() => {
        fill.style.width = percent + '%';
    }, 100);
}

function handleCorrectPrediction() {
    showToast('Prediction confirmed as correct!', 'success');
    setTimeout(() => {
        resultsSection.style.display = 'none';
        resetUpload();
    }, 1500);
}

async function retrainModel(correctLabel) {
    // Highlight selected option
    document.querySelectorAll('.label-option').forEach(opt => {
        opt.classList.remove('selected');
        if (opt.dataset.label === correctLabel) {
            opt.classList.add('selected');
        }
    });

    showLoading('Retraining model...');

    try {
        const response = await fetch('/api/retrain', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                filepath: currentFilePath,
                correct_label: correctLabel
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Retraining failed');
        }

        hideLoading();
        showToast('Model retrained successfully!', 'success');

        // Update stats
        await loadStats();
        await loadHistory();

        // Reset UI
        setTimeout(() => {
            resultsSection.style.display = 'none';
            resetUpload();
        }, 1500);
    } catch (error) {
        hideLoading();
        showToast(error.message, 'error');
    }
}

async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();

        if (data.total_samples !== undefined) {
            totalSamples.textContent = data.total_samples;
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

async function loadHistory() {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();

        if (data.history && data.history.length > 0) {
            renderHistory(data.history);
        }
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

function renderHistory(history) {
    historyContainer.innerHTML = '';

    // Show last 10 items, most recent first
    const recentHistory = history.slice(-10).reverse();

    recentHistory.forEach(item => {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';

        const timestamp = new Date(item.timestamp).toLocaleString();

        historyItem.innerHTML = `
            <div class="history-info">
                <div class="history-filename">${item.filename}</div>
                <div class="history-meta">${timestamp}</div>
            </div>
            <div class="history-label ${item.label}">
                ${item.label.toUpperCase()}
            </div>
        `;

        historyContainer.appendChild(historyItem);
    });
}

function showLoading(text = 'Processing...') {
    loadingText.textContent = text;
    loadingOverlay.style.display = 'flex';
}

function hideLoading() {
    loadingOverlay.style.display = 'none';
}

function showToast(message, type = 'info') {
    toast.textContent = message;
    toast.className = 'toast ' + type;
    toast.classList.add('show');

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadHistory();
});
