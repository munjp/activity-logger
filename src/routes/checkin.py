from flask import Blueprint, jsonify, request, session
from datetime import datetime
import os

checkin_bp = Blueprint('checkin', __name__, url_prefix='/api')

# Global variable to store dealerships data
dealerships_data = []

def load_dealerships():
    """Load dealerships from the text file."""
    global dealerships_data
    dealerships_data = []
    
    try:
        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level to src, then to static
        file_path = os.path.join(current_dir, '..', 'static', 'dealership_addresses.txt')
        
        print(f"Loading dealerships from: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Parse the content
        lines = content.strip().split('\n')
        current_dealership = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this is a numbered dealership line
            if line and line[0].isdigit() and '.' in line:
                # Extract name and address
                parts = line.split(':', 1)
                if len(parts) == 2:
                    name_part = parts[0].strip()
                    address = parts[1].strip()
                    
                    # Remove the number prefix
                    if '.' in name_part:
                        name = name_part.split('.', 1)[1].strip()
                        
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
                            coordinates = {'lat': 43.6532, 'lng': -79.3832}
                        
                        dealership = {
                            'id': dealership_id,
                            'name': name,
                            'address': address,
                            'coordinates': coordinates
                        }
                        dealerships_data.append(dealership)
                        print(f"Added dealership: {name} ({dealership_id}) at {coordinates}")
        
        print(f"Successfully loaded {len(dealerships_data)} dealerships")
        return True
        
    except Exception as e:
        print(f"Error loading dealerships: {e}")
        return False

@checkin_bp.route('/dealerships', methods=['GET'])
def get_dealerships():
    """Get list of all dealerships."""
    # Ensure dealerships are loaded
    if not dealerships_data:
        load_dealerships()
    
    print(f"API: Returning {len(dealerships_data)} dealerships")
    return jsonify(dealerships_data)

@checkin_bp.route('/verify-location', methods=['POST'])
def verify_location():
    """Verify user's location against selected dealership."""
    # Ensure dealerships are loaded
    if not dealerships_data:
        load_dealerships()
    
    print(f"Verify location called. Dealerships loaded: {len(dealerships_data)}")
    
    data = request.json
    print(f"Received data: {data}")
    
    if not data:
        return jsonify({'success': False, 'message': 'No data received'}), 400
    
    dealership_id = data.get('dealership_id')
    user_lat = data.get('user_latitude')
    user_lng = data.get('user_longitude')
    
    print(f"Verifying location for dealership: {dealership_id}")
    print(f"User coordinates: {user_lat}, {user_lng}")
    
    if not all([dealership_id, user_lat is not None, user_lng is not None]):
        missing = []
        if not dealership_id:
            missing.append('dealership_id')
        if user_lat is None:
            missing.append('user_latitude')
        if user_lng is None:
            missing.append('user_longitude')
        return jsonify({'success': False, 'message': f'Missing required data: {", ".join(missing)}'}), 400
    
    # Find the dealership
    dealership = None
    for d in dealerships_data:
        if d['id'] == dealership_id:
            dealership = d
            break
    
    if not dealership:
        return jsonify({'success': False, 'message': 'Dealership not found'}), 404
    
    # Check if dealership has coordinates
    if not dealership.get('coordinates'):
        return jsonify({'success': False, 'message': 'Dealership location not available'}), 400
    
    dealership_lat = dealership['coordinates']['lat']
    dealership_lng = dealership['coordinates']['lng']
    
    print(f"Dealership coordinates: {dealership_lat}, {dealership_lng}")
    
    # Calculate distance using Haversine formula
    import math
    
    def haversine_distance(lat1, lon1, lat2, lon2):
        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        return c * r * 1000  # Convert to meters
    
    distance = haversine_distance(user_lat, user_lng, dealership_lat, dealership_lng)
    print(f"Distance calculated: {distance:.2f} meters")
    
    # For Test Site, always allow (bypass distance check)
    if dealership_id == 'test_site':
        print("Test Site detected - bypassing distance check")
        return jsonify({
            'success': True,
            'message': 'Location verified (Test Site)',
            'distance': distance,
            'dealership_name': dealership['name']
        })
    
    # Smart device detection - different radius for mobile vs PC
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(device in user_agent for device in [
        'mobile', 'android', 'iphone', 'ipad', 'ipod', 'blackberry', 
        'windows phone', 'opera mini', 'iemobile'
    ])
    
    # Set different radius based on device type
    if is_mobile:
        max_distance = 500  # 500m for mobile devices (accurate GPS)
        device_type = "Mobile"
    else:
        max_distance = 2000  # 2km for PC users (inaccurate WiFi location)
        device_type = "PC"
    
    print(f"Device detected: {device_type}, Max distance: {max_distance}m")
    
    if distance <= max_distance:
        success_message = f'Location verified ({device_type})'
        if not is_mobile and distance > 500:
            success_message += f' - PC location accuracy: {distance:.0f}m'
        
        return jsonify({
            'success': True,
            'message': success_message,
            'distance': distance,
            'dealership_name': dealership['name'],
            'device_type': device_type
        })
    else:
        # Different error messages for mobile vs PC
        if is_mobile:
            error_message = f'You are {distance:.0f}m away from {dealership["name"]}. Please get closer to check in.'
        else:
            error_message = f'PC location shows {distance:.0f}m from {dealership["name"]}. This may be due to WiFi location inaccuracy. Try using your phone or contact your manager.'
        
        return jsonify({
            'success': False,
            'message': error_message,
            'distance': distance,
            'dealership_name': dealership['name']
        })

@checkin_bp.route('/checkin', methods=['POST'])
def checkin():
    """Check in to a dealership."""
    # Ensure dealerships are loaded
    if not dealerships_data:
        load_dealerships()
    
    print(f"Check-in called. Dealerships loaded: {len(dealerships_data)}")
    
    data = request.json
    print(f"Received check-in data: {data}")
    
    if not data:
        return jsonify({'success': False, 'message': 'No data received'}), 400
    
    dealership_id = data.get('dealership_id')
    dealership_name = data.get('dealership_name')
    user_lat = data.get('user_latitude')
    user_lng = data.get('user_longitude')
    
    print(f"Check-in for dealership: {dealership_id} ({dealership_name})")
    print(f"User coordinates: {user_lat}, {user_lng}")
    
    if not all([dealership_id, dealership_name, user_lat is not None, user_lng is not None]):
        missing = []
        if not dealership_id:
            missing.append('dealership_id')
        if not dealership_name:
            missing.append('dealership_name')
        if user_lat is None:
            missing.append('user_latitude')
        if user_lng is None:
            missing.append('user_longitude')
        return jsonify({'success': False, 'message': f'Missing required data: {", ".join(missing)}'}), 400
    
    # Store check-in information in session
    try:
        session['checked_in'] = True
        session['dealership_id'] = dealership_id
        session['dealership_name'] = dealership_name
        session['checkin_latitude'] = user_lat
        session['checkin_longitude'] = user_lng
        session['checkin_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"Check-in successful for {dealership_name}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully checked in to {dealership_name}',
            'dealership_name': dealership_name,
            'checkin_time': session['checkin_time']
        })
        
    except Exception as e:
        print(f"Check-in error: {e}")
        return jsonify({'success': False, 'message': f'Check-in failed: {str(e)}'}), 500

@checkin_bp.route('/checkout', methods=['POST'])
def checkout():
    """Check out from current dealership."""
    try:
        if not session.get('checked_in'):
            return jsonify({'success': False, 'message': 'Not currently checked in'}), 400
        
        dealership_name = session.get('dealership_name', 'Unknown')
        
        # Clear check-in information
        session.pop('checked_in', None)
        session.pop('dealership_id', None)
        session.pop('dealership_name', None)
        session.pop('checkin_latitude', None)
        session.pop('checkin_longitude', None)
        session.pop('checkin_time', None)
        
        print(f"Check-out successful from {dealership_name}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully checked out from {dealership_name}'
        })
        
    except Exception as e:
        print(f"Check-out error: {e}")
        return jsonify({'success': False, 'message': f'Check-out failed: {str(e)}'}), 500

@checkin_bp.route('/status', methods=['GET'])
def get_status():
    """Get current check-in status."""
    try:
        if session.get('checked_in'):
            return jsonify({
                'checked_in': True,
                'dealership_id': session.get('dealership_id'),
                'dealership_name': session.get('dealership_name'),
                'checkin_time': session.get('checkin_time')
            })
        else:
            return jsonify({'checked_in': False})
            
    except Exception as e:
        print(f"Status check error: {e}")
        return jsonify({'checked_in': False})

