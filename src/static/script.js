// Configuration
const HOUR_INTERVALS = [
    'Hour 1',
    'Hour 2', 
    'Hour 3',
    'Hour 4',
    'Hour 5',
    'Hour 6',
    'Hour 7',
    'Hour 8'
];

const METRICS = [
    { id: 'quote_calls', label: '# of Quote Calls' },
    { id: 'appointments_generated', label: '# of Appointments Generated' },
    { id: 'in_person_appointments', label: '# of In Person Appointments' },
    { id: 'phone_appointments', label: '# of Phone Appointments' },
    { id: 'cars_sold', label: '# of Cars Sold' },
    { id: 'cars_delivered', label: '# of Cars Delivered' },
    { id: 'advertisements_posted', label: '# of Advertisements Posted' }
];

// DOM Elements
let activityForm;
let notification;
let notificationText;
let closeNotificationBtn;
let slackOnlyBtn;
let dealershipInfo;
let dealershipName;
let checkoutBtn;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded');
    initializeElements();
    loadCheckinStatus();
    attachEventListeners();
    loadSavedData(); // Load any previously saved data
    setupAutoSave(); // Setup automatic saving
});

function initializeElements() {
    console.log('Initializing elements');
    activityForm = document.getElementById('activityForm');
    notification = document.getElementById('notification');
    notificationText = document.getElementById('notificationText');
    closeNotificationBtn = document.getElementById('closeNotification');
    slackOnlyBtn = document.getElementById('slackOnlyBtn');
    dealershipInfo = document.getElementById('dealershipInfo');
    dealershipName = document.getElementById('dealershipName');
    checkoutBtn = document.getElementById('checkoutBtn');
    console.log('Elements initialized:', {
        activityForm,
        notification,
        notificationText,
        closeNotificationBtn,
        slackOnlyBtn,
        dealershipInfo,
        dealershipName,
        checkoutBtn
    });
}

function attachEventListeners() {
    // Add event listeners for metric inputs to calculate productivity rating
    document.addEventListener('input', function(e) {
        if (e.target.matches('input[type="number"]')) {
            const hourIndex = e.target.dataset.hour;
            if (hourIndex !== undefined) {
                calculateAndUpdateRating(hourIndex);
            }
        }
        
        // Auto-save on any input change
        if (e.target.matches('input[type="number"]') || e.target.id === 'userName') {
            saveDataToLocalStorage();
        }
    });
    
    // Auto-save on textarea changes
    document.addEventListener('change', function(e) {
        if (e.target.tagName === 'TEXTAREA' || e.target.id === 'userName') {
            saveDataToLocalStorage();
        }
    });
    
    // Form submission - now exports to PDF and automatically sends to Slack
    if (activityForm) {
        activityForm.addEventListener('submit', handlePDFExport);
    }
    
    // Notification close
    if (closeNotificationBtn) {
        closeNotificationBtn.addEventListener('click', hideNotification);
    }
    
    // Slack only button
    if (slackOnlyBtn) {
        slackOnlyBtn.addEventListener('click', handleSlackOnly);
    }
    
    // Checkout button
    if (checkoutBtn) {
        checkoutBtn.addEventListener('click', handleCheckout);
    }
}

// AUTO-SAVE FUNCTIONALITY
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
            name: document.getElementById('userName')?.value || '',
            activities: {},
            timestamp: new Date().toISOString(),
            dealership: sessionStorage.getItem('dealership_name') || 'Unknown'
        };
        
        // Save all activity data
        for (let i = 0; i < HOUR_INTERVALS.length; i++) {
            data.activities[i] = {
                description: document.getElementById(`description_${i}`)?.value || ''
            };
            
            METRICS.forEach(metric => {
                const input = document.getElementById(`${metric.id}_${i}`);
                data.activities[i][metric.id] = input?.value || '0';
            });
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
        if (data.name && document.getElementById('userName')) {
            document.getElementById('userName').value = data.name;
        }
        
        // Load activity data
        for (let i = 0; i < HOUR_INTERVALS.length; i++) {
            if (data.activities[i]) {
                const activity = data.activities[i];
                
                // Load description
                const descElement = document.getElementById(`description_${i}`);
                if (descElement && activity.description) {
                    descElement.value = activity.description;
                }
                
                // Load metric fields
                METRICS.forEach(metric => {
                    const element = document.getElementById(`${metric.id}_${i}`);
                    if (element && activity[metric.id]) {
                        element.value = activity[metric.id];
                    }
                });
                
                // Update rating
                calculateAndUpdateRating(i);
            }
        }
        
    } catch (error) {
        console.error('Error loading saved data:', error);
    }
}

function checkForUnsavedData() {
    // Check if name is filled
    const name = document.getElementById('userName')?.value?.trim();
    if (name) return true;
    
    // Check if any activities are filled
    for (let i = 0; i < HOUR_INTERVALS.length; i++) {
        // Check descriptions
        const description = document.getElementById(`description_${i}`)?.value?.trim();
        if (description) return true;
        
        // Check metrics
        for (const metric of METRICS) {
            const value = document.getElementById(`${metric.id}_${i}`)?.value;
            if (value && parseInt(value) > 0) return true;
        }
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
    if (document.getElementById('userName')) {
        document.getElementById('userName').value = '';
    }
    
    for (let i = 0; i < HOUR_INTERVALS.length; i++) {
        // Clear descriptions
        const descElement = document.getElementById(`description_${i}`);
        if (descElement) descElement.value = '';
        
        // Clear metrics
        METRICS.forEach(metric => {
            const element = document.getElementById(`${metric.id}_${i}`);
            if (element) element.value = '0';
        });
        
        // Update rating
        calculateAndUpdateRating(i);
    }
    
    showNotification('Saved data cleared', 'info');
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

function clearSavedDataAfterSubmission() {
    // Clear localStorage after successful submission
    localStorage.removeItem('activityLoggerData');
    
    // Remove any recovery banners
    hideRecoveryBanner();
}

// ORIGINAL FUNCTIONALITY (PRESERVED)
async function calculateAndUpdateRating(hourIndex) {
    const metrics = {};
    
    METRICS.forEach(metric => {
        const input = document.getElementById(`${metric.id}_${hourIndex}`);
        metrics[metric.id] = parseInt(input?.value) || 0;
    });
    
    try {
        const response = await fetch('/api/activities/calculate-rating', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(metrics)
        });
        
        if (response.ok) {
            const data = await response.json();
            updateStarsDisplay(hourIndex, data.rating);
        }
    } catch (error) {
        console.error('Error calculating rating:', error);
    }
}

function updateStarsDisplay(hourIndex, rating) {
    const starsContainer = document.querySelector(`.stars[data-hour="${hourIndex}"]`);
    if (!starsContainer) return;
    
    const stars = starsContainer.querySelectorAll('.star');
    
    stars.forEach((star, index) => {
        if (index < Math.floor(rating)) {
            star.classList.add('filled');
        } else {
            star.classList.remove('filled');
        }
    });
}

async function handlePDFExport(e) {
    e.preventDefault();
    
    const userName = document.getElementById('userName').value.trim();
    if (!userName) {
        showNotification('Please enter your name', 'error');
        return;
    }
    
    const activities = [];
    
    for (let i = 0; i < HOUR_INTERVALS.length; i++) {
        const activityData = {
            description: document.getElementById(`description_${i}`).value || ''
        };
        
        METRICS.forEach(metric => {
            const input = document.getElementById(`${metric.id}_${i}`);
            activityData[metric.id] = parseInt(input.value) || 0;
        });
        
        activities.push(activityData);
    }
    
    try {
        // Show loading message
        showNotification('Generating activity log and sending to Slack...', 'info');
        
        const requestData = {
            name: userName,
            activities: activities
        };
        
        const response = await fetch("/api/activities/pdf", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        if (response.ok) {
            // Get the filename from the response headers
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'Daily_Activity_Log.txt';
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="(.+)"/);
                if (filenameMatch) {
                    filename = filenameMatch[1];
                }
            }
            
            // Create blob and download
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            // Check for Slack status (always sent now)
            const slackStatus = response.headers.get('X-Slack-Status');
            const slackMessage = response.headers.get('X-Slack-Message');
            
            let message = "Activity log downloaded successfully!";
            if (slackStatus === 'success') {
                message += " Also sent to team Slack channel.";
            } else if (slackStatus === 'error') {
                message += ` Slack error: ${slackMessage}`;
            }
            
            showNotification(message, "success");
            
            // Clear saved data after successful submission
            clearSavedDataAfterSubmission();
            
            // Redirect to check-in page after successful submission and auto-checkout
            setTimeout(() => {
                window.location.href = '/checkin.html';
            }, 2000); // Wait 2 seconds to show the success message
        } else {
            const errorData = await response.json();
            showNotification(`Error: ${errorData.error}`, 'error');
        }
    } catch (error) {
        console.error('Error generating activity log:', error);
        showNotification('Error generating activity log. Please try again.', 'error');
    }
}

function showNotification(message, type = 'success') {
    if (!notificationText || !notification) return;
    
    notificationText.textContent = message;
    notification.className = `notification ${type === 'error' ? 'error' : type === 'info' ? 'info' : ''}`;
    notification.classList.remove('hidden');
    
    // Auto-hide after 5 seconds for success/info, 8 seconds for errors
    const timeout = type === 'error' ? 8000 : 5000;
    setTimeout(hideNotification, timeout);
}

function hideNotification() {
    if (notification) {
        notification.classList.add('hidden');
    }
}

async function handleSlackOnly(e) {
    e.preventDefault();
    
    const userName = document.getElementById('userName').value.trim();
    if (!userName) {
        showNotification('Please enter your name first.', 'error');
        return;
    }
    
    // Collect activity data
    const activities = [];
    
    for (let i = 0; i < HOUR_INTERVALS.length; i++) {
        const activityData = {
            description: document.getElementById(`description_${i}`).value || ''
        };
        
        METRICS.forEach(metric => {
            const input = document.getElementById(`${metric.id}_${i}`);
            activityData[metric.id] = parseInt(input.value) || 0;
        });
        
        activities.push(activityData);
    }
    
    try {
        // Show loading message
        showNotification('Sending to team Slack channel...', 'info');
        
        const response = await fetch("/api/send-to-slack", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: userName,
                activities: activities
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification("Successfully sent to team Slack channel!", "success");
            
            // Clear saved data after successful submission
            clearSavedDataAfterSubmission();
            
            // Redirect to check-in page after successful submission and auto-checkout
            setTimeout(() => {
                window.location.href = '/checkin.html';
            }, 2000); // Wait 2 seconds to show the success message
        } else {
            showNotification(`Slack error: ${result.message}`, 'error');
        }
    } catch (error) {
        console.error('Error sending to Slack:', error);
        showNotification('Error sending to Slack. Please try again.', 'error');
    }
}

async function loadCheckinStatus() {
    try {
        const response = await fetch('/api/checkin-status');
        if (response.ok) {
            const status = await response.json();
            if (status.checked_in && status.dealership_name) {
                showDealershipInfo(status.dealership_name);
            }
        }
    } catch (error) {
        console.error('Error loading check-in status:', error);
    }
}

function showDealershipInfo(name) {
    if (dealershipInfo && dealershipName) {
        dealershipName.textContent = name;
        dealershipInfo.style.display = 'block';
    }
}

function hideDealershipInfo() {
    if (dealershipInfo) {
        dealershipInfo.style.display = 'none';
    }
}

async function handleCheckout() {
    if (!confirm('Are you sure you want to check out? You will need to check in again to log activities.')) {
        return;
    }
    
    try {
        checkoutBtn.disabled = true;
        checkoutBtn.innerHTML = '<span class="checkout-icon">⏳</span>Checking Out...';
        
        const response = await fetch('/api/checkout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Checked out successfully! Redirecting...', 'success');
            setTimeout(() => {
                window.location.href = '/checkin.html';
            }, 2000);
        } else {
            throw new Error(result.message || 'Checkout failed');
        }
    } catch (error) {
        console.error('Checkout error:', error);
        showNotification(error.message, 'error');
        checkoutBtn.disabled = false;
        checkoutBtn.innerHTML = '<span class="checkout-icon">🚪</span>Check Out';
    }
}

