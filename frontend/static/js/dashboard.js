// Get prediction data from URL parameters
const urlParams = new URLSearchParams(window.location.search);
const predictionData = JSON.parse(decodeURIComponent(urlParams.get('data') || '{}'));

// Global variables
let currentFilePath = null;
let currentPrediction = null;
let probabilityChart = null;
let confidenceGauge = null;

// DOM Elements
const loadingOverlay = document.getElementById('loadingOverlay');
const loadingText = document.getElementById('loadingText');
const toast = document.getElementById('toast');
const correctionModal = document.getElementById('correctionModal');

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    if (!predictionData || !predictionData.prediction) {
        showToast('No prediction data available', 'error');
        setTimeout(() => {
            window.location.href = '/';
        }, 2000);
        return;
    }

    currentFilePath = predictionData.filepath;
    currentPrediction = predictionData.prediction;

    // Record start time for analysis duration
    const startTime = performance.now();

    // Populate dashboard
    populateStats(predictionData);
    createCharts(predictionData);
    populateResultsTable(predictionData);
    generateInsights(predictionData);

    // Calculate and display analysis time
    const endTime = performance.now();
    const duration = ((endTime - startTime) / 1000).toFixed(2);
    document.getElementById('analysisTime').textContent = duration + 's';

    // Setup event listeners
    setupEventListeners();
});

function populateStats(data) {
    // Fault Type
    const faultType = document.getElementById('faultType');
    faultType.textContent = data.prediction;
    faultType.className = 'stat-value ' + data.prediction;

    // Confidence Level
    const maxProb = Math.max(...Object.values(data.probabilities));
    const confidencePercent = (maxProb * 100).toFixed(1);
    document.getElementById('confidenceLevel').textContent = confidencePercent + '%';

    // File Info
    document.getElementById('fileName').textContent = data.filename;
    document.getElementById('vectorSize').textContent = `${data.vector_size.toLocaleString()} features analyzed`;
}

function createCharts(data) {
    createProbabilityChart(data.probabilities);
    createConfidenceGauge(data.probabilities, data.prediction);
}

function createProbabilityChart(probabilities) {
    const ctx = document.getElementById('probabilityChart').getContext('2d');

    const labels = Object.keys(probabilities).map(label =>
        label.charAt(0).toUpperCase() + label.slice(1)
    );
    const values = Object.values(probabilities).map(val => (val * 100).toFixed(1));

    const colors = {
        'Healthy': {
            bg: 'rgba(16, 185, 129, 0.8)',
            border: 'rgba(16, 185, 129, 1)'
        },
        'Main': {
            bg: 'rgba(245, 158, 11, 0.8)',
            border: 'rgba(245, 158, 11, 1)'
        },
        'Arc': {
            bg: 'rgba(239, 68, 68, 0.8)',
            border: 'rgba(239, 68, 68, 1)'
        }
    };

    probabilityChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Probability (%)',
                data: values,
                backgroundColor: labels.map(label => colors[label].bg),
                borderColor: labels.map(label => colors[label].border),
                borderWidth: 2,
                borderRadius: 8,
                barThickness: 60
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return context.parsed.y + '% probability';
                        }
                    },
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: {
                        size: 14,
                        weight: 'bold'
                    },
                    bodyFont: {
                        size: 13
                    },
                    cornerRadius: 8
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function (value) {
                            return value + '%';
                        },
                        font: {
                            size: 12
                        }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    ticks: {
                        font: {
                            size: 13,
                            weight: '600'
                        }
                    },
                    grid: {
                        display: false
                    }
                }
            },
            animation: {
                duration: 1500,
                easing: 'easeOutQuart'
            }
        }
    });
}

function createConfidenceGauge(probabilities, prediction) {
    const ctx = document.getElementById('confidenceGauge').getContext('2d');

    const predictionProb = probabilities[prediction] * 100;
    const remaining = 100 - predictionProb;

    const gaugeColor = prediction === 'healthy' ?
        ['rgba(16, 185, 129, 0.9)', 'rgba(16, 185, 129, 0.6)'] :
        prediction === 'main' ?
            ['rgba(245, 158, 11, 0.9)', 'rgba(245, 158, 11, 0.6)'] :
            ['rgba(239, 68, 68, 0.9)', 'rgba(239, 68, 68, 0.6)'];

    confidenceGauge = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: [prediction.charAt(0).toUpperCase() + prediction.slice(1), 'Other'],
            datasets: [{
                data: [predictionProb, remaining],
                backgroundColor: [
                    gaugeColor[0],
                    'rgba(229, 231, 235, 0.5)'
                ],
                borderWidth: 0,
                circumference: 180,
                rotation: 270
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '75%',
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return context.parsed.toFixed(1) + '%';
                        }
                    },
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    cornerRadius: 8
                }
            },
            animation: {
                animateRotate: true,
                animateScale: true,
                duration: 2000,
                easing: 'easeOutQuart'
            }
        },
        plugins: [{
            id: 'centerText',
            beforeDraw: function (chart) {
                const width = chart.width;
                const height = chart.height;
                const ctx = chart.ctx;

                ctx.restore();
                const fontSize = (height / 150).toFixed(2);
                ctx.font = fontSize + "em sans-serif";
                ctx.textBaseline = "middle";

                const text = predictionProb.toFixed(1) + "%";
                const textX = Math.round((width - ctx.measureText(text).width) / 2);
                const textY = height / 1.7;

                ctx.fillStyle = '#111827';
                ctx.fillText(text, textX, textY);

                ctx.font = (fontSize * 0.4) + "em sans-serif";
                const subText = "Confidence";
                const subTextX = Math.round((width - ctx.measureText(subText).width) / 2);
                const subTextY = textY + 30;

                ctx.fillStyle = '#6b7280';
                ctx.fillText(subText, subTextX, subTextY);

                ctx.save();
            }
        }]
    });
}

function populateResultsTable(data) {
    const tbody = document.getElementById('resultsTableBody');
    tbody.innerHTML = '';

    const probabilities = data.probabilities;
    const prediction = data.prediction;

    // Sort by probability (highest first)
    const sorted = Object.entries(probabilities).sort((a, b) => b[1] - a[1]);

    sorted.forEach(([faultType, probability]) => {
        const row = document.createElement('tr');
        const percent = (probability * 100).toFixed(1);
        const isPredicted = faultType === prediction;

        row.innerHTML = `
            <td class="fault-type-cell">${faultType.charAt(0).toUpperCase() + faultType.slice(1)}</td>
            <td class="probability-cell">${percent}%</td>
            <td>
                <div class="progress-bar-container">
                    <div class="progress-bar ${faultType}" style="width: ${percent}%"></div>
                </div>
            </td>
            <td>
                <span class="status-badge ${isPredicted ? 'predicted' : 'alternative'}">
                    ${isPredicted ? 'PREDICTED' : 'Alternative'}
                </span>
            </td>
        `;

        tbody.appendChild(row);
    });
}

function generateInsights(data) {
    const container = document.getElementById('insightsContent');
    const probabilities = data.probabilities;
    const prediction = data.prediction;
    const maxProb = probabilities[prediction];

    const insights = [];

    // Confidence level insight
    if (maxProb >= 0.9) {
        insights.push({
            type: 'positive',
            icon: '✓',
            title: 'High Confidence Prediction',
            description: `The model is highly confident (${(maxProb * 100).toFixed(1)}%) about this classification. This indicates a clear fault pattern.`
        });
    } else if (maxProb >= 0.7) {
        insights.push({
            type: 'info',
            icon: 'i',
            title: 'Moderate Confidence',
            description: `The prediction has ${(maxProb * 100).toFixed(1)}% confidence. Consider cross-validating with additional data if available.`
        });
    } else {
        insights.push({
            type: 'warning',
            icon: '⚠',
            title: 'Low Confidence Alert',
            description: `Confidence is only ${(maxProb * 100).toFixed(1)}%. The model may need retraining with similar samples. Please verify manually.`
        });
    }

    // Fault-specific insights
    if (prediction === 'healthy') {
        insights.push({
            type: 'positive',
            icon: '✓',
            title: 'No Fault Detected',
            description: 'The system appears to be operating normally. All monitored parameters are within acceptable ranges.'
        });
    } else if (prediction === 'arc') {
        insights.push({
            type: 'warning',
            icon: '⚠',
            title: 'Arc Fault Detected',
            description: 'Arcing has been identified in the contact system. Immediate inspection recommended to prevent equipment damage.'
        });
    } else if (prediction === 'main') {
        insights.push({
            type: 'warning',
            icon: '⚠',
            title: 'Main Contact Fault',
            description: 'A fault in the main contact has been detected. Schedule maintenance to prevent system failure.'
        });
    }

    // Close alternatives insight
    const sortedProbs = Object.entries(probabilities).sort((a, b) => b[1] - a[1]);
    if (sortedProbs.length > 1 && sortedProbs[1][1] > 0.2) {
        insights.push({
            type: 'info',
            icon: 'i',
            title: 'Alternative Classification Possible',
            description: `There's a ${(sortedProbs[1][1] * 100).toFixed(1)}% probability of '${sortedProbs[1][0]}' fault. Consider this if the primary prediction seems incorrect.`
        });
    }

    // Render insights
    container.innerHTML = insights.map(insight => `
        <div class="insight-item ${insight.type}">
            <div class="insight-icon">
                <span style="font-size: 24px;">${insight.icon}</span>
            </div>
            <div class="insight-content">
                <h4>${insight.title}</h4>
                <p>${insight.description}</p>
            </div>
        </div>
    `).join('');
}

function setupEventListeners() {
    // Validate correct
    document.getElementById('validateCorrect').addEventListener('click', handleCorrectPrediction);

    // Validate incorrect
    document.getElementById('validateIncorrect').addEventListener('click', () => {
        correctionModal.style.display = 'flex';
    });

    // Label options in modal
    document.querySelectorAll('.label-option').forEach(option => {
        option.addEventListener('click', () => {
            // Highlight selected
            document.querySelectorAll('.label-option').forEach(opt => {
                opt.classList.remove('selected');
            });
            option.classList.add('selected');

            const label = option.dataset.label;
            setTimeout(() => {
                retrainModel(label);
            }, 500);
        });
    });
}

function handleCorrectPrediction() {
    showToast('Prediction confirmed as correct!', 'success');
    setTimeout(() => {
        window.location.href = '/';
    }, 1500);
}

async function retrainModel(correctLabel) {
    correctionModal.style.display = 'none';
    showLoading('Retraining model with corrected label...');

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
        showToast(`Model retrained successfully! Total samples: ${data.total_samples}`, 'success');

        setTimeout(() => {
            window.location.href = '/';
        }, 2000);
    } catch (error) {
        hideLoading();
        showToast(error.message, 'error');
    }
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

// Close modal when clicking outside
window.addEventListener('click', (e) => {
    if (e.target === correctionModal) {
        correctionModal.style.display = 'none';
    }
});
