// Dealership data and geolocation functionality
let dealerships = [];
let userLocation = null;
let selectedDealership = null;

// DOM Elements
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

function handleDealershipSelection() {
    const selectedId = dealershipSelect.value;
    if (selectedId) {
        selectedDealership = dealerships.find(d => d.id === selectedId);
        showLocationSection();
        updateStep(2);
        
        // For Test Site, show a special message but still require location verification
        if (selectedId === 'test_site') {
            locationMessage.textContent = 'Test Site: Location verification will be bypassed if geolocation fails';
        }
    } else {
        hideLocationSection();
        updateStep(1);
    }
}

function handleTestSiteBypass() {
    // Set mock location for Test Site - ensure global access
    userLocation = {
        latitude: 43.6532,
        longitude: -79.3832,
        accuracy: 10
    };
    
    // Ensure selectedDealership is properly set
    if (!selectedDealership) {
        selectedDealership = dealerships.find(d => d.id === 'test_site');
    }
    
    // Show location section with bypass message
    showLocationSection();
    
    // Immediately show success state
    locationIcon.textContent = '✅';
    locationTitle.textContent = 'Location Verified!';
    locationMessage.textContent = 'Test Site - Location verification bypassed';
    
    // Hide verify button and show check-in button
    verifyLocationBtn.style.display = 'none';
    checkinBtn.style.display = 'inline-flex';
    
    // Update to step 3
    updateStep(3);
    
    showNotification('Test Site selected - Location verification bypassed!', 'success');
    
    // Debug log to verify data is set
    console.log('Test Site bypass completed:', {
        userLocation: userLocation,
        selectedDealership: selectedDealership
    });
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
    // Special handling for Test Site - bypass location requirement
    if (selectedDealership && selectedDealership.id === 'test_site') {
        handleTestSiteBypass();
        return;
    }
    
    locationIcon.textContent = '⚠️';
    locationTitle.textContent = 'Location Error';
    locationMessage.textContent = error.message;
    
    verifyLocationBtn.style.display = 'none';
    retryBtn.style.display = 'inline-flex';
    
    showNotification(error.message, 'error');
}

function showLocationDetails(result) {
    document.getElementById('userLocation').textContent = `${userLocation.latitude.toFixed(6)}, ${userLocation.longitude.toFixed(6)}`;
    document.getElementById('dealershipLocation').textContent = selectedDealership.address;
    document.getElementById('distance').textContent = result.distance ? `${result.distance.toFixed(0)} meters` : 'Unknown';
    locationDetails.style.display = 'block';
}

async function handleCheckin() {
    if (!selectedDealership || !userLocation) {
        console.error('Missing data for check-in:', {
            selectedDealership: selectedDealership,
            userLocation: userLocation
        });
        showNotification('Please complete location verification first', 'error');
        return;
    }

    checkinBtn.disabled = true;
    checkinBtn.innerHTML = '<span class="btn-icon">⏳</span>Checking In...';

    try {
        const requestData = {
            dealership_id: selectedDealership.id,
            dealership_name: selectedDealership.name,
            user_latitude: userLocation.latitude,
            user_longitude: userLocation.longitude
        };
        
        console.log('Sending check-in request:', requestData);

        const response = await fetch('/api/checkin', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });

        const result = await response.json();
        
        console.log('Check-in response:', result);
        
        if (result.success) {
            showNotification('Check-in successful! Redirecting to activity logging...', 'success');
            setTimeout(() => {
                window.location.href = '/index.html';
            }, 2000);
        } else {
            showNotification(result.message || 'Check-in failed', 'error');
            checkinBtn.disabled = false;
            checkinBtn.innerHTML = '<span class="btn-icon">✅</span>Check In';
        }
    } catch (error) {
        console.error('Check-in error:', error);
        showNotification('Check-in failed. Please try again.', 'error');
        checkinBtn.disabled = false;
        checkinBtn.innerHTML = '<span class="btn-icon">✅</span>Check In';
    }
}

function updateStep(activeStep) {
    // Reset all steps
    step1.classList.remove('active', 'completed');
    step2.classList.remove('active', 'completed');
    step3.classList.remove('active', 'completed');
    
    // Set completed steps
    if (activeStep >= 2) step1.classList.add('completed');
    if (activeStep >= 3) step2.classList.add('completed');
    
    // Set active step
    if (activeStep === 1) step1.classList.add('active');
    if (activeStep === 2) step2.classList.add('active');
    if (activeStep === 3) step3.classList.add('active');
}

function showNotification(message, type = 'info') {
    notificationText.textContent = message;
    notification.className = `notification ${type}`;
    notification.style.display = 'block';
    
    // Auto-hide success notifications
    if (type === 'success') {
        setTimeout(hideNotification, 5000);
    }
}

function hideNotification() {
    notification.style.display = 'none';
}

