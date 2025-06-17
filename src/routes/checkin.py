from flask import Blueprint, jsonify, request, session, redirect, url_for
import json
import math
import urllib.request
import urllib.parse
import urllib.error
import os

checkin_bp = Blueprint('checkin', __name__)

# Dealership data loaded from file
dealerships_data = []

def load_dealerships():
    """Load dealership data from the text file with simplified processing"""
    global dealerships_data
    try:
        with open('src/static/dealership_addresses.txt', 'r') as file:
            content = file.read()
            
        dealerships_data = []
        lines = content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line and ':' in line and not line.startswith('Dealership Addresses'):
                try:
                    # Parse format: "1. 401 Infiniti: 5500 Dixie Road, Unit D, Mississauga, Ontario, L4W 4N3"
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        name_part = parts[0].strip()
                        address = parts[1].strip()
                        
                        # Extract name (remove number prefix)
                        if '. ' in name_part:
                            name = name_part.split('. ', 1)[1]
                        else:
                            name = name_part
                        
                        # Generate ID from name
                        dealership_id = name.lower().replace(' ', '_').replace('(', '').replace(')', '')
                        
                        # Add coordinates for all dealerships (using real geocoded addresses)
                        dealership_coordinates = {
                            '401_infiniti': {'lat': 43.646769, 'lng': -79.6359934},
                            '401_kia': {'lat': 43.646769, 'lng': -79.6359934},
                            '401_mazda': {'lat': 43.646769, 'lng': -79.6359934},
                            '401_mitsubishi_dixie_mitsubishi': {'lat': 43.6444388, 'lng': -79.6442699},
                            '401_nissan': {'lat': 43.646769, 'lng': -79.6359934},
                            '401_volkswagen': {'lat': 43.646769, 'lng': -79.6359934},
                            'agincourt_mazda': {'lat': 43.8128735, 'lng': -79.2444342},
                            'audi_barrie': {'lat': 44.3017312, 'lng': -79.6823509},
                            'audi_queensway': {'lat': 43.6154775, 'lng': -79.5466424},
                            'audi_thornhill': {'lat': 43.7994946, 'lng': -79.4212594},
                            'barrie_volkswagen': {'lat': 44.3592463, 'lng': -79.692863},
                            'bmw_aurora': {'lat': 44.0065, 'lng': -79.4504},
                            'bolton_toyota': {'lat': 43.8497373, 'lng': -79.6957908},
                            'frost_gm': {'lat': 43.7038815, 'lng': -79.7892515},
                            'markham_acura': {'lat': 43.8658623, 'lng': -79.2867289},
                            'markham_honda': {'lat': 43.8557957, 'lng': -79.3061335},
                            'markham_kia': {'lat': 43.8556092, 'lng': -79.3074614},
                            'meadowvale_honda': {'lat': 43.5802831, 'lng': -79.757078},
                            'oakville_honda': {'lat': 43.4692995, 'lng': -79.6800906},
                            'thorncrest_ford': {'lat': 43.61664, 'lng': -79.5403798},
                            'vaughan_chrysler': {'lat': 43.8361, 'lng': -79.5083},
                            'test_site': {'lat': 43.8850691, 'lng': -79.4190847}
                        }
                        
                        coordinates = dealership_coordinates.get(dealership_id)
                        if not coordinates:
                            # Default coordinates for any missing dealerships
                            coordinates = {'lat': 43.6532, 'lng': -79.3832}  # Toronto area
                        
                        dealership = {
                            'id': dealership_id,
                            'name': name,
                            'address': address,
                            'latitude': coordinates['lat'] if coordinates else None,
                            'longitude': coordinates['lng'] if coordinates else None
                        }
                        dealerships_data.append(dealership)
                        print(f"Loaded dealership: {name} ({'with coordinates' if coordinates else 'no coordinates'})")
                        
                except Exception as e:
                    print(f"Error processing dealership line '{line}': {e}")
                    continue
                    
        print(f"Successfully loaded {len(dealerships_data)} dealerships")
        return True
    except Exception as e:
        print(f"Error loading dealerships: {e}")
        dealerships_data = []
        return False

def send_checkin_slack_notification(dealership_name, checkin_time, user_lat, user_lng, distance, device_type):
    """Send a Slack notification when user checks in"""
    try:
        webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
        if not webhook_url:
            print("SLACK_WEBHOOK_URL not configured - skipping Slack notification")
            return False
        
        # Determine device type for display
        device_display = "📱 Mobile Device" if device_type == "mobile" else "🖥️ PC"
        
        # Format distance for display
        if distance is not None:
            distance_text = f"{distance:.0f}m from dealership"
        else:
            distance_text = "Location verified"
        
        # Create rich Slack message using blocks
        slack_message = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🏢 Dealership Check-In"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Location:*\n{dealership_name}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Time:*\n{checkin_time} Eastern"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Device:*\n{device_display}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Accuracy:*\n{distance_text}"
                        }
                    ]
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"📍 Location verified • ✅ Check-in successful • 🕐 {checkin_time}"
                        }
                    ]
                }
            ]
        }
        
        # Send to Slack
        data = json.dumps(slack_message).encode('utf-8')
        req = urllib.request.Request(webhook_url, data=data)
        req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req) as response:
            if response.getcode() == 200:
                print(f"Check-in Slack notification sent successfully for {dealership_name}")
                return True
            else:
                print(f"Slack notification failed with status: {response.getcode()}")
                return False
                
    except Exception as e:
        print(f"Error sending check-in Slack notification: {e}")
        return False

def detect_device_type(user_agent):
    """Detect if the user is on a mobile device or PC"""
    if not user_agent:
        return "unknown"
    
    user_agent = user_agent.lower()
    mobile_indicators = [
        'mobile', 'android', 'iphone', 'ipad', 'ipod', 
        'blackberry', 'windows phone', 'opera mini'
    ]
    
    for indicator in mobile_indicators:
        if indicator in user_agent:
            return "mobile"
    
    return "pc"

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using Haversine formula"""
    if None in [lat1, lon1, lat2, lon2]:
        return None
        
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in meters
    r = 6371000
    
    return c * r

@checkin_bp.route('/dealerships')
def get_dealerships():
    """Get list of all dealerships"""
    if not dealerships_data:
        load_dealerships()
    
    # Return simplified data for frontend
    simplified_data = []
    for d in dealerships_data:
        simplified_data.append({
            'id': d['id'],
            'name': d['name'],
            'address': d['address']
        })
    
    return jsonify(simplified_data)

@checkin_bp.route('/verify-location', methods=['POST'])
def verify_location():
    """Verify user location against selected dealership"""
    try:
        # Ensure dealerships are loaded
        if not dealerships_data:
            load_dealerships()
            
        data = request.get_json()
        dealership_id = data.get('dealership_id')
        user_lat = data.get('user_latitude')
        user_lng = data.get('user_longitude')
        
        print(f"Verify-location request: dealership_id={dealership_id}, user_lat={user_lat}, user_lng={user_lng}")
        print(f"Dealerships loaded: {len(dealerships_data)}")
        
        if not all([dealership_id, user_lat, user_lng]):
            return jsonify({
                'success': False,
                'message': 'Missing required location data'
            }), 400
        
        # Find dealership
        dealership = next((d for d in dealerships_data if d['id'] == dealership_id), None)
        if not dealership:
            return jsonify({
                'success': False,
                'message': 'Dealership not found'
            }), 404
        
        if dealership['latitude'] is None or dealership['longitude'] is None:
            return jsonify({
                'success': False,
                'message': 'Dealership location not available'
            }), 400
        
        # Detect device type for different radius limits
        user_agent = request.headers.get('User-Agent', '')
        device_type = detect_device_type(user_agent)
        
        # Set radius based on device type
        if device_type == "mobile":
            max_distance = 500  # Strict for mobile (accurate GPS)
        else:
            max_distance = 3500  # Generous for PC (WiFi location inaccuracy)
        
        # Special handling for Test Site - always allow check-in
        if dealership_id == 'test_site':
            max_distance = 5000  # Very generous for test site
            return jsonify({
                'success': True,
                'distance': 0,
                'max_distance': max_distance,
                'message': f'Test Site - Location verification bypassed'
            })
        
        # Calculate distance
        distance = calculate_distance(
            user_lat, user_lng,
            dealership['latitude'], dealership['longitude']
        )
        
        if distance is None:
            return jsonify({
                'success': False,
                'message': 'Unable to calculate distance'
            }), 400
        
        # Check if within acceptable range
        within_range = distance <= max_distance
        
        device_display = "Mobile" if device_type == "mobile" else "PC"
        message = f'Location verified ({device_display})' if within_range else f'You are {distance:.0f}m from {dealership["name"]} (max allowed: {max_distance}m for {device_display})'
        
        return jsonify({
            'success': within_range,
            'distance': distance,
            'max_distance': max_distance,
            'device_type': device_type,
            'message': message
        })
        
    except Exception as e:
        print(f"Location verification error: {e}")
        return jsonify({
            'success': False,
            'message': 'Location verification failed'
        }), 500

@checkin_bp.route('/checkin', methods=['POST'])
def checkin():
    """Check in user to dealership with Slack notification"""
    try:
        # Ensure dealerships are loaded
        if not dealerships_data:
            load_dealerships()
            
        from datetime import datetime
        import pytz
        
        data = request.get_json()
        dealership_id = data.get('dealership_id')
        dealership_name = data.get('dealership_name')
        user_lat = data.get('user_latitude')
        user_lng = data.get('user_longitude')
        
        print(f"Check-in request: dealership_id={dealership_id}, dealership_name={dealership_name}, user_lat={user_lat}, user_lng={user_lng}")
        print(f"Dealerships loaded: {len(dealerships_data)}")
        
        if not all([dealership_id, dealership_name]):
            return jsonify({
                'success': False,
                'message': 'Missing required check-in data'
            }), 400
        
        # Capture check-in timestamp in Eastern Time
        eastern = pytz.timezone('America/Toronto')
        utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
        checkin_time = utc_now.astimezone(eastern)
        checkin_time_str = checkin_time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Detect device type
        user_agent = request.headers.get('User-Agent', '')
        device_type = detect_device_type(user_agent)
        
        # Calculate distance for Slack notification
        distance = None
        if user_lat and user_lng:
            # Find dealership for coordinates
            dealership = next((d for d in dealerships_data if d['id'] == dealership_id), None)
            if dealership and dealership['latitude'] and dealership['longitude']:
                distance = calculate_distance(
                    user_lat, user_lng,
                    dealership['latitude'], dealership['longitude']
                )
        
        # Store check-in information in session
        session['checked_in'] = True
        session['dealership_id'] = dealership_id
        session['dealership_name'] = dealership_name
        session['checkin_latitude'] = user_lat
        session['checkin_longitude'] = user_lng
        session['checkin_time'] = checkin_time_str
        
        # Send Slack notification (non-blocking - check-in succeeds even if Slack fails)
        try:
            send_checkin_slack_notification(
                dealership_name, 
                checkin_time_str, 
                user_lat, 
                user_lng, 
                distance,
                device_type
            )
        except Exception as slack_error:
            print(f"Slack notification failed but check-in continues: {slack_error}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully checked in to {dealership_name} at {checkin_time_str}'
        })
        
    except Exception as e:
        print(f"Check-in error: {e}")
        return jsonify({
            'success': False,
            'message': 'Check-in failed'
        }), 500

@checkin_bp.route('/checkout', methods=['POST'])
def checkout():
    """Check out user from dealership"""
    try:
        # Clear check-in information from session
        session.pop('checked_in', None)
        session.pop('dealership_id', None)
        session.pop('dealership_name', None)
        session.pop('checkin_latitude', None)
        session.pop('checkin_longitude', None)
        session.pop('checkin_time', None)
        
        return jsonify({
            'success': True,
            'message': 'Successfully checked out'
        })
        
    except Exception as e:
        print(f"Check-out error: {e}")
        return jsonify({
            'success': False,
            'message': 'Check-out failed'
        }), 500

@checkin_bp.route('/checkin-status')
def checkin_status():
    """Get current check-in status"""
    return jsonify({
        'checked_in': session.get('checked_in', False),
        'dealership_id': session.get('dealership_id'),
        'dealership_name': session.get('dealership_name'),
        'checkin_time': session.get('checkin_time')
    })

# Initialize dealerships when module loads
load_dealerships()

