document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('csv-file-input');
    const fileInfo = document.getElementById('fileInfo');
    const fileNameDisplay = document.getElementById('file-name-display');
    const uploadBtn = document.getElementById('upload-btn');
    const loadingSpinner = document.getElementById('loading-spinner');
    const errorMessage = document.getElementById('error-message');
    const chartsSection = document.getElementById('charts-section');

    let selectedFile = null;
    const chartInstances = {};

    // Drag & drop handlers
    if (dropZone) {
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.style.borderColor = '#667eea';
            dropZone.style.background = '#f3f4f6';
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.style.borderColor = '#d1d5db';
            dropZone.style.background = '';
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.style.borderColor = '#d1d5db';
            dropZone.style.background = '';
            handleFile(e.dataTransfer.files[0]);
        });
    }

    // File input change handler
    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            handleFile(e.target.files[0]);
        });
    }

    function handleFile(file) {
        if (file && (file.name.endsWith('.csv') || file.name.endsWith('.txt') || file.name.endsWith('.dat'))) {
            selectedFile = file;
            if (fileNameDisplay) fileNameDisplay.textContent = '📄 ' + file.name;
            if (dropZone) dropZone.style.display = 'none';
            if (fileInfo) fileInfo.style.display = 'block';
            if (errorMessage) errorMessage.style.display = 'none';
        } else if (file) {
            showError('Please select a valid CSV file.');
            selectedFile = null;
        }
    }

    // Upload & Plot button
    if (uploadBtn) {
        uploadBtn.addEventListener('click', async () => {
            if (!selectedFile) {
                showError('Please select a file first.');
                return;
            }

            if (errorMessage) errorMessage.style.display = 'none';
            if (loadingSpinner) loadingSpinner.style.display = 'flex';
            if (chartsSection) chartsSection.style.display = 'none';

            const formData = new FormData();
            formData.append('file', selectedFile);

            try {
                const response = await fetch('/api/plot', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (response.ok) {
                    displayResults(data);
                } else {
                    showError('Error: ' + (data.error || 'Unknown error occurred.'));
                }
            } catch (error) {
                showError('Connection Error: ' + error.message);
            } finally {
                if (loadingSpinner) loadingSpinner.style.display = 'none';
            }
        });
    }

    function showError(msg) {
        if (errorMessage) {
            errorMessage.textContent = msg;
            errorMessage.style.display = 'block';
        } else {
            alert(msg);
        }
    }

    function displayResults(graphData) {
        if (chartsSection) chartsSection.style.display = 'block';

        const timeLabels = graphData.time;

        createCombinedChart(timeLabels, graphData);
        createChart('coilCurrChart', 'Coil Current (A)', timeLabels, graphData.coil_current, '#3b82f6');
        createChart('resChart', 'Resistance (µΩ)', timeLabels, graphData.resistance, '#8b5cf6');
        createChart('dcrmCurrChart', 'DCRM Current (A)', timeLabels, graphData.dcrm_current, '#10b981');
        createChart('travelChart', 'Contact Travel (mm)', timeLabels, graphData.contact_travel, '#f59e0b');
    }

    function createCombinedChart(labels, graphData) {
        const can = document.getElementById('combinedChart');
        if (!can) return;
        const ctx = can.getContext('2d');
        if (chartInstances['combinedChart']) chartInstances['combinedChart'].destroy();
        
        chartInstances['combinedChart'] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    { label: 'Coil Current (A)', data: graphData.coil_current, borderColor: '#3b82f6', backgroundColor: 'transparent', borderWidth: 1.5, pointRadius: 0, tension: 0.1, yAxisID: 'y' },
                    { label: 'Resistance (µΩ)', data: graphData.resistance, borderColor: '#8b5cf6', backgroundColor: 'transparent', borderWidth: 1.5, pointRadius: 0, tension: 0.1, yAxisID: 'y1' },
                    { label: 'DCRM Current (A)', data: graphData.dcrm_current, borderColor: '#10b981', backgroundColor: 'transparent', borderWidth: 1.5, pointRadius: 0, tension: 0.1, yAxisID: 'y' },
                    { label: 'Contact Travel (mm)', data: graphData.contact_travel, borderColor: '#f59e0b', backgroundColor: 'transparent', borderWidth: 1.5, pointRadius: 0, tension: 0.1, yAxisID: 'y2' }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: { position: 'bottom', labels: { usePointStyle: true, padding: 20 } },
                    zoom: {
                        zoom: { wheel: { enabled: true }, drag: { enabled: true, backgroundColor: 'rgba(102, 126, 234, 0.1)' }, mode: 'x' },
                        pan: { enabled: true, mode: 'x' }
                    }
                },
                scales: {
                    x: { grid: { display: false } },
                    y: { position: 'left', title: { display: true, text: 'Current (A)' } },
                    y1: { position: 'right', title: { display: true, text: 'Resistance' }, grid: { display: false } },
                    y2: { position: 'right', display: false }
                }
            }
        });
    }

    function createChart(canvasId, title, labels, data, color) {
        const can = document.getElementById(canvasId);
        if (!can) return;
        const ctx = can.getContext('2d');
        if (chartInstances[canvasId]) chartInstances[canvasId].destroy();

        chartInstances[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{ label: title, data: data, borderColor: color, backgroundColor: color + '20', borderWidth: 2, pointRadius: 0, tension: 0.1, fill: true }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    zoom: {
                        zoom: { wheel: { enabled: true }, drag: { enabled: true, backgroundColor: 'rgba(0,0,0,0.05)' }, mode: 'x' },
                        pan: { enabled: true, mode: 'x' }
                    }
                },
                scales: { 
                    x: { grid: { display: false } }, 
                    y: { beginAtZero: false, title: { display: true, text: title } } 
                }
            }
        });
    }
});
