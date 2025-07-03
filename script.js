// script.js

// The base URL of your running FastAPI backend
const API_BASE_URL = "http://127.0.0.1:8000";

// --- DOM Element References ---
// We get references to all the interactive elements on the page
const vehicleInfoDiv = document.getElementById('vehicle-info-display');
const identifyTextBtn = document.getElementById('identify-text-btn');
const identifyImageBtn = document.getElementById('identify-image-btn');
const vehicleTextInput = document.getElementById('vehicle-text-input');
const vinFileInput = document.getElementById('vin-file-input');
const getDiagnosisTextBtn = document.getElementById('get-diagnosis-text-btn');
const problemDescriptionInput = document.getElementById('problem-description-input');
const resultsContainer = document.getElementById('results-container');
const loader = document.getElementById('loader');
const getDiagnosisImageBtn = document.getElementById('get-diagnosis-image-btn');
const problemFileInput = document.getElementById('problem-file-input');

// --- State Management ---
// A simple object to hold the currently identified vehicle's info
let identifiedVehicle = null;

// --- Helper Functions ---
function showLoader() {
    loader.classList.remove('hidden');
    resultsContainer.innerHTML = ''; // Clear previous results
}

function hideLoader() {
    loader.classList.add('hidden');
}

function updateVehicleDisplay(vehicle) {
    if (vehicle) {
        identifiedVehicle = vehicle;
        vehicleInfoDiv.innerHTML = `
            <p><strong>Make:</strong> ${vehicle.make}</p>
            <p><strong>Model:</strong> ${vehicle.model}</p>
            <p><strong>Year:</strong> ${vehicle.year}</p>
        `;
        getDiagnosisTextBtn.disabled = false; // Enable the text diagnosis button
        getDiagnosisImageBtn.disabled = false; // Enable the image diagnosis button
    } else {
        vehicleInfoDiv.innerHTML = '<p>Could not identify vehicle.</p>';
        getDiagnosisTextBtn.disabled = true;
        getDiagnosisImageBtn.disabled = true;
    }
}

function displayResults(data) {
    if (data.error) {
        resultsContainer.innerHTML = `<p style="color: red;"><strong>Error:</strong> ${data.error}</p>`;
        return;
    }

    let problemsHtml = data.potential_problems.map(p => `<li><strong>${p.name}:</strong> ${p.description}</li>`).join('');
    let stepsHtml = data.next_steps.map(s => `<li>${s}</li>`).join('');
    
    resultsContainer.innerHTML = `
        <div class="result-section">
            <h3>Severity: <span style="color: ${data.severity.level === 'CRITICAL' ? 'red' : 'orange'};">${data.severity.level}</span></h3>
            <p>${data.severity.message}</p>
        </div>
        <div class="result-section">
            <h3>Potential Problems</h3>
            <ul>${problemsHtml}</ul>
        </div>
        <div class="result-section">
            <h3>Recommended Next Steps</h3>
            <ul>${stepsHtml}</ul>
        </div>
        <div class="result-section">
            <h3>Estimated Cost</h3>
            <p>${data.estimated_cost.range}</p>
            <p><small>${data.estimated_cost.disclaimer}</small></p>
        </div>
    `;
}

// --- Event Listeners ---

identifyTextBtn.addEventListener('click', async () => {
    const query = vehicleTextInput.value;
    if (!query) {
        alert("Please enter a vehicle description.");
        return;
    }
    
    showLoader();
    try {
        const response = await fetch(`${API_BASE_URL}/vehicle/identify-from-text`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail);
        updateVehicleDisplay(data);
    } catch (error) {
        alert("Error identifying vehicle: " + error.message);
        updateVehicleDisplay(null);
    } finally {
        hideLoader();
    }
});

identifyImageBtn.addEventListener('click', async () => {
    const file = vinFileInput.files[0];
    if (!file) {
        alert("Please select an image file.");
        return;
    }

    const formData = new FormData();
    formData.append('file', file);
    
    showLoader();
    try {
        const response = await fetch(`${API_BASE_URL}/vehicle/identify-from-image`, {
            method: 'POST',
            body: formData // No Content-Type header needed; browser sets it for FormData
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail);
        updateVehicleDisplay(data);
    } catch (error) {
        alert("Error identifying vehicle: " + error.message);
        updateVehicleDisplay(null);
    } finally {
        hideLoader();
    }
});

getDiagnosisTextBtn.addEventListener('click', async () => {
    const description = problemDescriptionInput.value;
    if (!description) {
        alert("Please describe the problem.");
        return;
    }
    if (!identifiedVehicle) {
        alert("Please identify a vehicle first.");
        return;
    }

    const payload = {
        vehicle: identifiedVehicle,
        history: [{ role: "user", content: description }]
    };

    showLoader();
    try {
        const response = await fetch(`${API_BASE_URL}/diagnose/conversation`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail);
        displayResults(data);
    } catch (error) {
        displayResults({ error: error.message });
    } finally {
        hideLoader();
    }
});

getDiagnosisImageBtn.addEventListener('click', async () => {
    const description = problemDescriptionInput.value;
    const file = problemFileInput.files[0];

    if (!description) {
        alert("Please describe the problem in the text box.");
        return;
    }
    if (!file) {
        alert("Please select an image file for diagnosis.");
        return;
    }
    if (!identifiedVehicle) {
        alert("Please identify a vehicle first.");
        return;
    }

    // Use FormData for multipart file uploads
    const formData = new FormData();
    formData.append('make', identifiedVehicle.make);
    formData.append('model', identifiedVehicle.model);
    formData.append('year', identifiedVehicle.year);
    formData.append('prompt', description);
    formData.append('file', file);

    showLoader();
    try {
        const response = await fetch(`${API_BASE_URL}/diagnose/image`, {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail);
        displayResults(data);
    } catch (error) {
        displayResults({ error: error.message });
    } finally {
        hideLoader();
    }
});