// Dealership data and geolocation functionality
let dealerships = [];
let userLocation = null;
let selectedDealership = null;

// DOM Elements
let userNameInput;
let dealershipSelect;
let verifyLocationBtn;
let checkinBtn;
let retryBtn;
let notification;
let notificationText;
let closeNotificationBtn;

// Step elements
let step1, step2, step3;
let locationSection;
let locationIcon;
let locationTitle;
let locationMessage;
let locationDetails;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    console.log('Check-in page loaded');
    initializeElements();
    loadDealerships();
    attachEventListeners();
});

function initializeElements() {
    userNameInput = document.getElementById('userName');
    dealershipSelect = document.getElementById('dealership');
    verifyLocationBtn = document.getElementById('verifyLocationBtn');
    checkinBtn = document.getElementById('checkinBtn');
    retryBtn = document.getElementById('retryBtn');
    notification = document.getElementById('notification');
    notificationText = document.getElementById('notificationText');
    closeNotificationBtn = document.getElementById('closeNotification');
    
    step1 = document.getElementById('step1');
    step2 = document.getElementById('step2');
    step3 = document.getElementById('step3');
    locationSection = document.getElementById('locationSection');
    locationIcon = document.getElementById('locationIcon');
    locationTitle = document.getElementById('locationTitle');
    locationMessage = document.getElementById('locationMessage');
    locationDetails = document.getElementById('locationDetails');
}

async function loadDealerships() {
    try {
        const response = await fetch('/api/dealerships');
        if (response.ok) {
            dealerships = await response.json();
            populateDealershipSelect();
        } else {
            showNotification('Failed to load dealerships', 'error');
        }
    } catch (error) {
        console.error('Error loading dealerships:', error);
        showNotification('Error loading dealerships', 'error');
    }
}

function populateDealershipSelect() {
    dealerships.forEach(dealership => {
        const option = document.createElement('option');
        option.value = dealership.id;
        option.textContent = dealership.name;
        dealershipSelect.appendChild(option);
    });
}

function attachEventListeners() {
    userNameInput.addEventListener('input', checkFormCompletion);
    dealershipSelect.addEventListener('change', handleDealershipSelection);
    verifyLocationBtn.addEventListener('click', verifyLocation);
    checkinBtn.addEventListener('click', handleCheckin);
    retryBtn.addEventListener('click', resetLocationVerification);
    closeNotificationBtn.addEventListener('click', hideNotification);
    
    document.getElementById('checkinForm').addEventListener('submit', function(e) {
        e.preventDefault();
        handleCheckin();
    });
}

function checkFormCompletion() {
    const userName = userNameInput.value.trim();
    const selectedId = dealershipSelect.value;
    
    if (userName && selectedId) {
        selectedDealership = dealerships.find(d => d.id === selectedId);
        showLocationSection();
        updateStep(2);
    } else {
        hideLocationSection();
        updateStep(1);
    }
}

function handleDealershipSelection() {
    checkFormCompletion();
}

function showLocationSection() {
    locationSection.style.display = 'block';
    verifyLocationBtn.style.display = 'inline-flex';
    resetLocationStatus();
}

function hideLocationSection() {
    locationSection.style.display = 'none';
    verifyLocationBtn.style.display = 'none';
    checkinBtn.style.display = 'none';
    retryBtn.style.display = 'none';
}

function resetLocationStatus() {
    locationIcon.textContent = '📍';
    locationTitle.textContent = 'Ready to Verify Location';
    locationMessage.textContent = 'Click "Verify Location" to check your proximity to the dealership';
    locationDetails.style.display = 'none';
    checkinBtn.style.display = 'none';
    retryBtn.style.display = 'none';
    verifyLocationBtn.style.display = 'inline-flex';
}

function resetLocationVerification() {
    userLocation = null;
    resetLocationStatus();
    updateStep(2);
}

async function verifyLocation() {
    const userName = userNameInput.value.trim();
    if (!userName) {
        showNotification('Please enter your name first', 'error');
        return;
    }
    
    if (!selectedDealership) {
        showNotification('Please select a dealership first', 'error');
        return;
    }

    verifyLocationBtn.disabled = true;
    locationIcon.textContent = '🔄';
    locationTitle.textContent = 'Getting Your Location...';
    locationMessage.textContent = 'Please allow location access when prompted';

    try {
        userLocation = await getCurrentPosition();
        await checkProximity();
    } catch (error) {
        console.error('Location error:', error);
        handleLocationError(error);
    } finally {
        verifyLocationBtn.disabled = false;
    }
}

function getCurrentPosition() {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject(new Error('Geolocation is not supported by this browser'));
            return;
        }

        navigator.geolocation.getCurrentPosition(
            position => {
                resolve({
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                    accuracy: position.coords.accuracy
                });
            },
            error => {
                let message = 'Unable to get your location';
                switch(error.code) {
                    case error.PERMISSION_DENIED:
                        message = 'Location access denied. Please enable location services.';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        message = 'Location information unavailable.';
                        break;
                    case error.TIMEOUT:
                        message = 'Location request timed out.';
                        break;
                }
                reject(new Error(message));
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 60000
            }
        );
    });
}

async function checkProximity() {
    locationIcon.textContent = '📏';
    locationTitle.textContent = 'Calculating Distance...';
    locationMessage.textContent = 'Checking your proximity to the dealership';

    try {
        const response = await fetch('/api/verify-location', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                dealership_id: selectedDealership.id,
                user_latitude: userLocation.latitude,
                user_longitude: userLocation.longitude
            })
        });

        const result = await response.json();
        
        if (result.success) {
            handleLocationSuccess(result);
        } else {
            handleLocationFailure(result);
        }
    } catch (error) {
        console.error('Proximity check error:', error);
        handleLocationError(error);
    }
}

function handleLocationSuccess(result) {
    locationIcon.textContent = '✅';
    locationTitle.textContent = 'Location Verified!';
    locationMessage.textContent = `You are within range of ${selectedDealership.name}`;
    
    showLocationDetails(result);
    
    verifyLocationBtn.style.display = 'none';
    checkinBtn.style.display = 'inline-flex';
    
    updateStep(3);
    showNotification('Location verified successfully!', 'success');
}

function handleLocationFailure(result) {
    locationIcon.textContent = '❌';
    locationTitle.textContent = 'Location Verification Failed';
    locationMessage.textContent = result.message || 'You are too far from the selected dealership';
    
    showLocationDetails(result);
    
    verifyLocationBtn.style.display = 'none';
    retryBtn.style.display = 'inline-flex';
    
    showNotification(result.message || 'Location verification failed', 'error');
}

function handleLocationError(error) {
    locationIcon.textContent = '⚠️';
    locationTitle.textContent = 'Location Error';
    locationMessage.textContent = error.message;
    
    verifyLocationBtn.style.display = 'none';
    retryBtn.style.display = 'inline-flex';
    
    showNotification(error.message, 'error');
}

function showLocationDetails(result) {
    document.getElementById('userLocation').textContent = 
        `${userLocation.latitude.toFixed(6)}, ${userLocation.longitude.toFixed(6)}`;
    document.getElementById('dealershipLocation').textContent = selectedDealership.address;
    document.getElementById('distance').textContent = 
        result.distance ? `${result.distance.toFixed(0)} meters` : 'Unknown';
    
    locationDetails.style.display = 'block';
}

async function handleCheckin() {
    const userName = userNameInput.value.trim();
    
    if (!userName) {
        showNotification('Please enter your name', 'error');
        return;
    }
    
    if (!selectedDealership || !userLocation) {
        showNotification('Please complete location verification first', 'error');
        return;
    }

    checkinBtn.disabled = true;
    checkinBtn.innerHTML = '<span class="btn-icon">⏳</span>Checking In...';

    try {
        const response = await fetch('/api/checkin', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_name: userName,
                dealership_id: selectedDealership.id,
                dealership_name: selectedDealership.name,
                user_latitude: userLocation.latitude,
                user_longitude: userLocation.longitude
            })
        });

        const result = await response.json();
        
        if (result.success) {
            showNotification(`Check-in successful for ${userName}! Redirecting to activity logging...`, 'success');
            setTimeout(() => {
                window.location.href = '/static/index.html';
            }, 2000);
        } else {
            throw new Error(result.message || 'Check-in failed');
        }
    } catch (error) {
        console.error('Check-in error:', error);
        showNotification(error.message, 'error');
        checkinBtn.disabled = false;
        checkinBtn.innerHTML = '<span class="btn-icon">✅</span>Check In';
    }
}

function updateStep(stepNumber) {
    // Reset all steps
    [step1, step2, step3].forEach(step => {
        step.classList.remove('active', 'completed');
    });
    
    // Mark completed steps
    for (let i = 1; i < stepNumber; i++) {
        document.getElementById(`step${i}`).classList.add('completed');
    }
    
    // Mark current step as active
    if (stepNumber <= 3) {
        document.getElementById(`step${stepNumber}`).classList.add('active');
    }
}

function showNotification(message, type = 'info') {
    notificationText.textContent = message;
    notification.className = `notification ${type}`;
    notification.classList.remove('hidden');
    
    // Auto-hide after 5 seconds for success/info messages
    if (type === 'success' || type === 'info') {
        setTimeout(hideNotification, 5000);
    }
}

function hideNotification() {
    notification.classList.add('hidden');
}

