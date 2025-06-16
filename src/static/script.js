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

async function calculateAndUpdateRating(hourIndex) {
    const metrics = {};
    
    METRICS.forEach(metric => {
        const input = document.getElementById(`${metric.id}_${hourIndex}`);
        metrics[metric.id] = parseInt(input.value) || 0;
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
        
        const response = await fetch("/api/activities/slack", {
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

