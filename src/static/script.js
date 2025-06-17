// Activity Logger JavaScript with Auto-Save
document.addEventListener('DOMContentLoaded', function() {
    generateActivitySections();
    setupEventListeners();
    loadSavedData(); // Load any previously saved data
    setupAutoSave(); // Setup automatic saving
});

function generateActivitySections() {
    const activitiesContainer = document.getElementById('activities');
    
    for (let hour = 1; hour <= 8; hour++) {
        const section = createActivitySection(hour);
        activitiesContainer.appendChild(section);
    }
}

function createActivitySection(hour) {
    const section = document.createElement('div');
    section.className = 'activity-section';
    section.innerHTML = `
        <div class="activity-header">
            <div class="activity-title">Hour ${hour}</div>
            <div class="rating-display" id="rating-${hour}">⭐⭐⭐⭐⭐</div>
        </div>
        
        <div class="activity-grid">
            <div class="metric-group">
                <label>Quote Calls:</label>
                <input type="number" id="quote_calls_${hour}" min="0" value="0" data-hour="${hour}" data-field="quote_calls">
            </div>
            <div class="metric-group">
                <label>Appointments Generated:</label>
                <input type="number" id="appointments_generated_${hour}" min="0" value="0" data-hour="${hour}" data-field="appointments_generated">
            </div>
            <div class="metric-group">
                <label>In Person Appointments:</label>
                <input type="number" id="in_person_appointments_${hour}" min="0" value="0" data-hour="${hour}" data-field="in_person_appointments">
            </div>
            <div class="metric-group">
                <label>Phone Appointments:</label>
                <input type="number" id="phone_appointments_${hour}" min="0" value="0" data-hour="${hour}" data-field="phone_appointments">
            </div>
            <div class="metric-group">
                <label>Cars Sold:</label>
                <input type="number" id="cars_sold_${hour}" min="0" value="0" data-hour="${hour}" data-field="cars_sold">
            </div>
            <div class="metric-group">
                <label>Cars Delivered:</label>
                <input type="number" id="cars_delivered_${hour}" min="0" value="0" data-hour="${hour}" data-field="cars_delivered">
            </div>
            <div class="metric-group">
                <label>Advertisements Posted:</label>
                <input type="number" id="advertisements_posted_${hour}" min="0" value="0" data-hour="${hour}" data-field="advertisements_posted">
            </div>
        </div>
        
        <div class="description-group">
            <label>Activity Description:</label>
            <textarea id="description_${hour}" data-hour="${hour}" data-field="description" placeholder="Describe your activities for this hour..."></textarea>
        </div>
    `;
    
    return section;
}

function setupEventListeners() {
    // Add event listeners for all metric inputs
    document.addEventListener('input', function(e) {
        if (e.target.type === 'number' && e.target.dataset.hour) {
            updateRating(e.target.dataset.hour);
        }
        
        // Auto-save on any input change
        if (e.target.dataset.hour || e.target.id === 'name') {
            saveDataToLocalStorage();
        }
    });
    
    // Auto-save on textarea changes
    document.addEventListener('change', function(e) {
        if (e.target.tagName === 'TEXTAREA' || e.target.id === 'name') {
            saveDataToLocalStorage();
        }
    });
    
    // Button event listeners
    document.getElementById('downloadBtn').addEventListener('click', handleDownloadAndSlack);
    document.getElementById('slackOnlyBtn').addEventListener('click', handleSlackOnly);
    
    // Add clear data button
    addClearDataButton();
}

function setupAutoSave() {
    // Save data every 30 seconds as backup
    setInterval(saveDataToLocalStorage, 30000);
    
    // Save data before page unload
    window.addEventListener('beforeunload', function(e) {
        saveDataToLocalStorage();
        
        // Check if there's unsaved data
        const hasData = checkForUnsavedData();
        if (hasData) {
            e.preventDefault();
            e.returnValue = 'You have unsaved activity data. Are you sure you want to leave?';
            return e.returnValue;
        }
    });
    
    // Show recovery message if data exists
    showRecoveryMessageIfNeeded();
}

function saveDataToLocalStorage() {
    try {
        const data = {
            name: document.getElementById('name').value,
            activities: {},
            timestamp: new Date().toISOString(),
            dealership: sessionStorage.getItem('dealership_name') || 'Unknown'
        };
        
        // Save all activity data
        for (let hour = 1; hour <= 8; hour++) {
            data.activities[hour] = {
                quote_calls: document.getElementById(`quote_calls_${hour}`).value,
                appointments_generated: document.getElementById(`appointments_generated_${hour}`).value,
                in_person_appointments: document.getElementById(`in_person_appointments_${hour}`).value,
                phone_appointments: document.getElementById(`phone_appointments_${hour}`).value,
                cars_sold: document.getElementById(`cars_sold_${hour}`).value,
                cars_delivered: document.getElementById(`cars_delivered_${hour}`).value,
                advertisements_posted: document.getElementById(`advertisements_posted_${hour}`).value,
                description: document.getElementById(`description_${hour}`).value
            };
        }
        
        localStorage.setItem('activityLoggerData', JSON.stringify(data));
        
        // Show auto-save indicator briefly
        showAutoSaveIndicator();
        
    } catch (error) {
        console.error('Error saving data to localStorage:', error);
    }
}

function loadSavedData() {
    try {
        const savedData = localStorage.getItem('activityLoggerData');
        if (!savedData) return;
        
        const data = JSON.parse(savedData);
        
        // Load name
        if (data.name) {
            document.getElementById('name').value = data.name;
        }
        
        // Load activity data
        for (let hour = 1; hour <= 8; hour++) {
            if (data.activities[hour]) {
                const activity = data.activities[hour];
                
                // Load numeric fields
                const fields = ['quote_calls', 'appointments_generated', 'in_person_appointments', 
                               'phone_appointments', 'cars_sold', 'cars_delivered', 'advertisements_posted'];
                
                fields.forEach(field => {
                    const element = document.getElementById(`${field}_${hour}`);
                    if (element && activity[field]) {
                        element.value = activity[field];
                    }
                });
                
                // Load description
                const descElement = document.getElementById(`description_${hour}`);
                if (descElement && activity.description) {
                    descElement.value = activity.description;
                }
                
                // Update rating
                updateRating(hour);
            }
        }
        
    } catch (error) {
        console.error('Error loading saved data:', error);
    }
}

function checkForUnsavedData() {
    // Check if name is filled
    const name = document.getElementById('name').value.trim();
    if (name) return true;
    
    // Check if any activities are filled
    for (let hour = 1; hour <= 8; hour++) {
        const fields = ['quote_calls', 'appointments_generated', 'in_person_appointments', 
                       'phone_appointments', 'cars_sold', 'cars_delivered', 'advertisements_posted'];
        
        for (const field of fields) {
            const value = document.getElementById(`${field}_${hour}`).value;
            if (value && parseInt(value) > 0) return true;
        }
        
        const description = document.getElementById(`description_${hour}`).value.trim();
        if (description) return true;
    }
    
    return false;
}

function showRecoveryMessageIfNeeded() {
    const savedData = localStorage.getItem('activityLoggerData');
    if (savedData) {
        try {
            const data = JSON.parse(savedData);
            const savedTime = new Date(data.timestamp);
            const now = new Date();
            const hoursDiff = (now - savedTime) / (1000 * 60 * 60);
            
            // Show recovery message if data is less than 24 hours old
            if (hoursDiff < 24) {
                showRecoveryBanner(savedTime, data.dealership);
            }
        } catch (error) {
            console.error('Error checking saved data:', error);
        }
    }
}

function showRecoveryBanner(savedTime, dealership) {
    const banner = document.createElement('div');
    banner.className = 'recovery-banner';
    banner.innerHTML = `
        <div class="recovery-content">
            <span class="recovery-icon">💾</span>
            <div class="recovery-text">
                <strong>Unsaved data found!</strong><br>
                Saved: ${savedTime.toLocaleString()} at ${dealership}
            </div>
            <div class="recovery-buttons">
                <button onclick="clearSavedData()" class="btn-clear">Clear</button>
                <button onclick="hideRecoveryBanner()" class="btn-keep">Keep Data</button>
            </div>
        </div>
    `;
    
    document.body.insertBefore(banner, document.body.firstChild);
}

function hideRecoveryBanner() {
    const banner = document.querySelector('.recovery-banner');
    if (banner) {
        banner.remove();
    }
}

function clearSavedData() {
    localStorage.removeItem('activityLoggerData');
    hideRecoveryBanner();
    
    // Clear all form fields
    document.getElementById('name').value = '';
    for (let hour = 1; hour <= 8; hour++) {
        const fields = ['quote_calls', 'appointments_generated', 'in_person_appointments', 
                       'phone_appointments', 'cars_sold', 'cars_delivered', 'advertisements_posted'];
        
        fields.forEach(field => {
            document.getElementById(`${field}_${hour}`).value = '0';
        });
        
        document.getElementById(`description_${hour}`).value = '';
        updateRating(hour);
    }
    
    showStatus('Saved data cleared', 'info');
}

function showAutoSaveIndicator() {
    // Remove existing indicator
    const existing = document.querySelector('.auto-save-indicator');
    if (existing) existing.remove();
    
    // Create new indicator
    const indicator = document.createElement('div');
    indicator.className = 'auto-save-indicator';
    indicator.textContent = '💾 Auto-saved';
    document.body.appendChild(indicator);
    
    // Remove after 2 seconds
    setTimeout(() => {
        if (indicator.parentNode) {
            indicator.remove();
        }
    }, 2000);
}

function addClearDataButton() {
    const buttonGroup = document.querySelector('.button-group');
    const clearBtn = document.createElement('button');
    clearBtn.textContent = '🗑️ Clear All Data';
    clearBtn.className = 'btn btn-warning';
    clearBtn.onclick = function() {
        if (confirm('Are you sure you want to clear all entered data? This cannot be undone.')) {
            clearSavedData();
        }
    };
    buttonGroup.appendChild(clearBtn);
}

function updateRating(hour) {
    const metrics = [
        'quote_calls', 'appointments_generated', 'in_person_appointments',
        'phone_appointments', 'cars_sold', 'cars_delivered', 'advertisements_posted'
    ];
    
    const data = {};
    metrics.forEach(metric => {
        const input = document.getElementById(`${metric}_${hour}`);
        data[metric] = parseInt(input.value) || 0;
    });
    
    // Calculate rating using the same logic as backend
    fetch('/api/activities/calculate-rating', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        const ratingDisplay = document.getElementById(`rating-${hour}`);
        const stars = '⭐'.repeat(result.rating);
        ratingDisplay.textContent = stars;
    })
    .catch(error => {
        console.error('Error calculating rating:', error);
    });
}

function collectActivityData() {
    const name = document.getElementById('name').value.trim();
    if (!name) {
        showStatus('Please enter your name', 'error');
        return null;
    }
    
    const activities = [];
    
    for (let hour = 1; hour <= 8; hour++) {
        const activity = {
            hour: hour,
            quote_calls: parseInt(document.getElementById(`quote_calls_${hour}`).value) || 0,
            appointments_generated: parseInt(document.getElementById(`appointments_generated_${hour}`).value) || 0,
            in_person_appointments: parseInt(document.getElementById(`in_person_appointments_${hour}`).value) || 0,
            phone_appointments: parseInt(document.getElementById(`phone_appointments_${hour}`).value) || 0,
            cars_sold: parseInt(document.getElementById(`cars_sold_${hour}`).value) || 0,
            cars_delivered: parseInt(document.getElementById(`cars_delivered_${hour}`).value) || 0,
            advertisements_posted: parseInt(document.getElementById(`advertisements_posted_${hour}`).value) || 0,
            description: document.getElementById(`description_${hour}`).value.trim()
        };
        activities.push(activity);
    }
    
    return { name, activities };
}

async function handleDownloadAndSlack() {
    const data = collectActivityData();
    if (!data) return;
    
    showStatus('Generating report and sending to Slack...', 'info');
    
    try {
        const response = await fetch('/api/activities/pdf', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            // Get Slack status from headers
            const slackStatus = response.headers.get('X-Slack-Status');
            const slackMessage = response.headers.get('X-Slack-Message');
            
            // Download the file
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Daily_Activity_Log_${data.name}_${new Date().toISOString().split('T')[0]}.txt`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            if (slackStatus === 'success') {
                showStatus('Report downloaded and sent to Slack successfully!', 'success');
                // Clear saved data after successful submission
                clearSavedDataAfterSubmission();
            } else {
                showStatus(`Report downloaded. Slack error: ${slackMessage}`, 'error');
            }
        } else {
            showStatus('Error generating report', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showStatus('Error generating report', 'error');
    }
}

async function handleSlackOnly() {
    const data = collectActivityData();
    if (!data) return;
    
    showStatus('Sending to Slack...', 'info');
    
    try {
        const response = await fetch('/api/send-to-slack', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showStatus('Successfully sent to Slack!', 'success');
            // Clear saved data after successful submission
            clearSavedDataAfterSubmission();
        } else {
            showStatus(`Slack error: ${result.message}`, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showStatus('Error sending to Slack', 'error');
    }
}

function clearSavedDataAfterSubmission() {
    // Clear localStorage after successful submission
    localStorage.removeItem('activityLoggerData');
    
    // Remove any recovery banners
    hideRecoveryBanner();
}

function showStatus(message, type) {
    const statusDiv = document.getElementById('status');
    statusDiv.textContent = message;
    statusDiv.className = `status-message ${type}`;
    statusDiv.style.display = 'block';
    
    // Auto-hide success messages after 5 seconds
    if (type === 'success') {
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 5000);
    }
}

