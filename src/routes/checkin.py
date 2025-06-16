from flask import Blueprint, jsonify, request, session, redirect, url_for
import json
import math
import urllib.request
import urllib.parse
import urllib.error

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
                        
                        # For Test Site, provide coordinates; for others, use placeholder
                        if dealership_id == 'test_site':
                            coordinates = {'lat': 43.8828, 'lng': -79.4403}  # Richmond Hill area
                        else:
                            coordinates = None  # Skip geocoding for faster loading
                        
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

def geocode_address(address):
    """Geocode an address using a free geocoding service"""
    try:
        # Use Nominatim (OpenStreetMap) for free geocoding
        base_url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': address,
            'format': 'json',
            'limit': 1,
            'countrycodes': 'ca'  # Limit to Canada
        }
        
        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        
        # Add user agent header as required by Nominatim
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'DealershipCheckin/1.0')
        
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            
        if data and len(data) > 0:
            return {
                'lat': float(data[0]['lat']),
                'lng': float(data[0]['lon'])
            }
        else:
            print(f"No coordinates found for address: {address}")
            return None
            
    except Exception as e:
        print(f"Geocoding error for {address}: {e}")
        return None

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
        
        # Special handling for Test Site - always allow check-in
        if dealership_id == 'test_site':
            max_distance = 500  # Define max_distance for Test Site
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
        
        # Check if within acceptable range (500 meters)
        max_distance = 500  # meters
        within_range = distance <= max_distance
        
        return jsonify({
            'success': within_range,
            'distance': distance,
            'max_distance': max_distance,
            'message': f'You are {distance:.0f}m from {dealership["name"]}' + 
                      ('' if within_range else f' (max allowed: {max_distance}m)')
        })
        
    except Exception as e:
        print(f"Location verification error: {e}")
        return jsonify({
            'success': False,
            'message': 'Location verification failed'
        }), 500

@checkin_bp.route('/checkin', methods=['POST'])
def checkin():
    """Check in user to dealership"""
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
        
        # Store check-in information in session
        session['checked_in'] = True
        session['dealership_id'] = dealership_id
        session['dealership_name'] = dealership_name
        session['checkin_latitude'] = user_lat
        session['checkin_longitude'] = user_lng
        session['checkin_time'] = checkin_time_str
        
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

