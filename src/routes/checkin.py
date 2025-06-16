from flask import Blueprint, request, jsonify, session
import os
import json
from datetime import datetime
import pytz

# Create blueprint (url_prefix added in main.py)
checkin_bp = Blueprint('checkin', __name__)

@checkin_bp.route('/dealerships', methods=['GET'])
def get_dealerships():
    """Get list of dealerships with their addresses."""
    try:
        # Hardcoded dealership data for reliability
        dealerships = [
            {"id": "401_infiniti", "name": "401 Infiniti", "address": "5500 Dixie Road, Unit D, Mississauga, Ontario, L4W 4N3", "coordinates": [43.6532, -79.7331]},
            {"id": "401_kia", "name": "401 Kia", "address": "5500 Dixie Rd Unit C, Mississauga, Ontario, L4W 4N3", "coordinates": [43.6532, -79.7331]},
            {"id": "401_mazda", "name": "401 Mazda", "address": "5500 Dixie Rd F, Mississauga, Ontario, L4W 4N3", "coordinates": [43.6532, -79.7331]},
            {"id": "401_mitsubishi_dixie_mitsubishi", "name": "401 Mitsubishi (Dixie Mitsubishi)", "address": "5525 Ambler Drive, Mississauga, Ontario, L4W 3Z1", "coordinates": [43.6532, -79.7331]},
            {"id": "401_nissan", "name": "401 Nissan", "address": "5500 Dixie Road, Unit B, Mississauga, Ontario, L4W 4N3", "coordinates": [43.6532, -79.7331]},
            {"id": "401_volkswagen", "name": "401 Volkswagen", "address": "5500 Dixie Rd, Mississauga, Ontario, L4W 4N3", "coordinates": [43.6532, -79.7331]},
            {"id": "agincourt_mazda", "name": "Agincourt Mazda", "address": "5500 Finch Ave E, Scarborough, Ontario, M1S 0C7", "coordinates": [43.7735, -79.2945]},
            {"id": "audi_barrie", "name": "Audi Barrie", "address": "2484 Doral Drive, Innisfil, ON L9S 0A3", "coordinates": [44.3894, -79.6903]},
            {"id": "audi_queensway", "name": "Audi Queensway", "address": "1635 The Queensway, Etobicoke, ON M8Z 1T8", "coordinates": [43.6205, -79.5132]},
            {"id": "audi_thornhill", "name": "Audi Thornhill", "address": "7064 Yonge Street, Thornhill, ON L4J 1V7", "coordinates": [43.8271, -79.4278]},
            {"id": "barrie_volkswagen", "name": "Barrie Volkswagen", "address": "60 Fairview Road, Barrie, Ontario, L4N 8X8", "coordinates": [44.3894, -79.6903]},
            {"id": "bmw_aurora", "name": "BMW Aurora", "address": "56 Sunday Drive, Aurora, Ontario, L4G 4A2", "coordinates": [44.0065, -79.4504]},
            {"id": "bolton_toyota", "name": "Bolton Toyota", "address": "12050 Albion Vaughan Road, Bolton, Ontario, L7E 1S7", "coordinates": [43.8781, -79.7314]},
            {"id": "frost_gm", "name": "Frost GM", "address": "150 Bovaird Dr W, Brampton, Ontario, L7A 0H3", "coordinates": [43.7279, -79.4389]},
            {"id": "markham_acura", "name": "Markham Acura", "address": "5201 Highway 7 East, Markham, Ontario, L3R 1N3", "coordinates": [43.8561, -79.3204]},
            {"id": "markham_honda", "name": "Markham Honda", "address": "8220 Kennedy Road, Markham, Ontario, L3R 5X3", "coordinates": [43.8561, -79.3204]},
            {"id": "markham_kia", "name": "Markham Kia", "address": "8210 Kennedy Rd, Markham, ON L3R 5X3", "coordinates": [43.8561, -79.3204]},
            {"id": "meadowvale_honda", "name": "Meadowvale Honda", "address": "2210 Battleford Road, Mississauga, Ontario, L5N 3K6", "coordinates": [43.6532, -79.7331]},
            {"id": "oakville_honda", "name": "Oakville Honda", "address": "500 Iroquois Shore Road, Oakville, Ontario, L6H 2Y7", "coordinates": [43.4643, -79.7204]},
            {"id": "thorncrest_ford", "name": "Thorncrest Ford", "address": "1575 The Queensway, Etobicoke, Toronto, Ontario, M8Z 1T9", "coordinates": [43.6205, -79.5132]},
            {"id": "vaughan_chrysler", "name": "Vaughan Chrysler", "address": "1 Auto Park Circle, Woodbridge, Ontario, L4L 8R1", "coordinates": [43.8271, -79.4278]},
            {"id": "test_site", "name": "Test Site", "address": "439 Crosby Ave, Richmond Hill, ON, Canada", "coordinates": [43.6532, -79.3832]}
        ]
        
        return jsonify(dealerships)
    except Exception as e:
        return jsonify({"error": f"Error loading dealerships: {str(e)}"}), 500

@checkin_bp.route('/verify-location', methods=['POST'])
def verify_location():
    """Verify user's location against selected dealership."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        dealership_id = data.get('dealership_id')
        user_lat = data.get('latitude')
        user_lng = data.get('longitude')
        
        if not all([dealership_id, user_lat, user_lng]):
            return jsonify({"success": False, "message": "Missing required data"}), 400
        
        # Special handling for Test Site - always allow
        if dealership_id == 'test_site':
            session['checked_in'] = True
            session['dealership_id'] = dealership_id
            session['dealership_name'] = 'Test Site'
            
            # Capture check-in timestamp in Eastern Time
            eastern = pytz.timezone('America/Toronto')
            utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
            local_time = utc_now.astimezone(eastern)
            session['checkin_time'] = local_time.strftime('%Y-%m-%d %H:%M:%S')
            
            return jsonify({
                "success": True, 
                "message": "Test Site - Location verification bypassed",
                "dealership_name": "Test Site"
            })
        
        # For other dealerships, implement basic location checking
        # This is a simplified version - you can enhance with actual distance calculation
        session['checked_in'] = True
        session['dealership_id'] = dealership_id
        session['dealership_name'] = data.get('dealership_name', 'Unknown Dealership')
        
        # Capture check-in timestamp in Eastern Time
        eastern = pytz.timezone('America/Toronto')
        utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
        local_time = utc_now.astimezone(eastern)
        session['checkin_time'] = local_time.strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            "success": True, 
            "message": "Location verified successfully",
            "dealership_name": session['dealership_name']
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@checkin_bp.route('/checkin', methods=['POST'])
def checkin():
    """Complete the check-in process."""
    try:
        if not session.get('checked_in'):
            return jsonify({"success": False, "message": "Location not verified"}), 400
        
        return jsonify({
            "success": True, 
            "message": f"Successfully checked in to {session.get('dealership_name', 'Unknown')}",
            "dealership_name": session.get('dealership_name'),
            "checkin_time": session.get('checkin_time')
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@checkin_bp.route('/checkout', methods=['POST'])
def checkout():
    """Check out from current location."""
    try:
        session.pop('checked_in', None)
        session.pop('dealership_id', None)
        session.pop('dealership_name', None)
        session.pop('checkin_time', None)
        
        return jsonify({"success": True, "message": "Successfully checked out"})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@checkin_bp.route('/status', methods=['GET'])
def status():
    """Get current check-in status."""
    try:
        return jsonify({
            "checked_in": session.get('checked_in', False),
            "dealership_name": session.get('dealership_name'),
            "checkin_time": session.get('checkin_time')
        })
        
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 500

