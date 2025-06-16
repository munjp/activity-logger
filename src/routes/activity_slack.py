from flask import Blueprint, request, jsonify, session, send_file
from datetime import datetime
import io
import json
import urllib.request
import urllib.parse
import urllib.error
import os
import pytz

# Create blueprint (url_prefix added in main.py)
activity_bp = Blueprint('activity', __name__)

def send_to_slack(name, activities, total_metrics, dealership_info=None, checkin_time=None):
    """Send activity log to Slack channel."""
    # Use environment variable for webhook URL
    slack_webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    
    if not slack_webhook_url:
        return False, "Slack webhook URL not configured in environment variables"
    
    try:
        # Calculate total productivity score
        total_score = 0
        for activity in activities:
            score = (
                int(activity.get('quote_calls', 0)) * 1 +
                int(activity.get('appointments_generated', 0)) * 2 +
                int(activity.get('in_person_appointments', 0)) * 4 +
                int(activity.get('phone_appointments', 0)) * 3 +
                int(activity.get('cars_sold', 0)) * 10 +
                int(activity.get('cars_delivered', 0)) * 8 +
                int(activity.get('advertisements_posted', 0)) * 1
            )
            total_score += score
        
        # Create location and check-in context
        eastern = pytz.timezone('America/Toronto')
        utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
        local_time = utc_now.astimezone(eastern)
        
        context_parts = [f"*Date:* {local_time.strftime('%Y-%m-%d')}", f"*Total Score:* {total_score} points"]
        
        if dealership_info:
            context_parts.append(f"*📍 Location:* {dealership_info}")
        
        if checkin_time:
            context_parts.append(f"*🕐 Check-in Time:* {checkin_time}")
        
        context_text = " | ".join(context_parts)
        
        # Create activity summary
        activity_lines = []
        for i, activity in enumerate(activities, 1):
            # Calculate weighted score for this hour
            score = (
                int(activity.get('quote_calls', 0)) * 1 +
                int(activity.get('appointments_generated', 0)) * 2 +
                int(activity.get('in_person_appointments', 0)) * 4 +
                int(activity.get('phone_appointments', 0)) * 3 +
                int(activity.get('cars_sold', 0)) * 10 +
                int(activity.get('cars_delivered', 0)) * 8 +
                int(activity.get('advertisements_posted', 0)) * 1
            )
            
            # Determine star rating
            if score >= 20:
                stars = "⭐⭐⭐⭐⭐"
            elif score >= 15:
                stars = "⭐⭐⭐⭐"
            elif score >= 10:
                stars = "⭐⭐⭐"
            elif score >= 5:
                stars = "⭐⭐"
            else:
                stars = "⭐"
            
            activity_lines.append(f"Hour {i}: {stars} ({score} points)")
            
            # Add activity details if any
            details = []
            if int(activity.get('cars_sold', 0)) > 0:
                details.append(f"🚗 {activity.get('cars_sold')} cars sold")
            if int(activity.get('cars_delivered', 0)) > 0:
                details.append(f"🚚 {activity.get('cars_delivered')} cars delivered")
            if int(activity.get('in_person_appointments', 0)) > 0:
                details.append(f"🤝 {activity.get('in_person_appointments')} in-person appointments")
            if int(activity.get('appointments_generated', 0)) > 0:
                details.append(f"📅 {activity.get('appointments_generated')} appointments generated")
            if int(activity.get('phone_appointments', 0)) > 0:
                details.append(f"☎️ {activity.get('phone_appointments')} phone appointments")
            if int(activity.get('quote_calls', 0)) > 0:
                details.append(f"📞 {activity.get('quote_calls')} quote calls")
            if int(activity.get('advertisements_posted', 0)) > 0:
                details.append(f"📢 {activity.get('advertisements_posted')} ads posted")
            
            if details:
                activity_lines.append(f"  {', '.join(details)}")
        
        # Create Slack message
        message = {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Daily Activity Log - {name}*\n{context_text}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "\n".join(activity_lines)
                    }
                }
            ]
        }
        
        # Send to Slack
        data = json.dumps(message).encode('utf-8')
        req = urllib.request.Request(slack_webhook_url, data=data, headers={'Content-Type': 'application/json'})
        
        with urllib.request.urlopen(req) as response:
            if response.getcode() == 200:
                return True, "Successfully sent to Slack"
            else:
                return False, f"Slack API error: {response.getcode()}"
                
    except urllib.error.HTTPError as e:
        return False, f"HTTP Error {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return False, f"URL Error: {e.reason}"
    except Exception as e:
        return False, f"Error sending to Slack: {str(e)}"

@activity_bp.route('/submit-activity', methods=['POST'])
def submit_activity():
    """Submit activity log and send to Slack."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        name = data.get('name', 'Unknown')
        activities = data.get('activities', [])
        
        if not activities:
            return jsonify({"success": False, "message": "No activities provided"}), 400
        
        # Get check-in information
        dealership_name = session.get('dealership_name', 'Unknown Location')
        checkin_time = session.get('checkin_time')
        
        # Calculate total metrics
        total_metrics = {
            'total_score': 0,
            'total_activities': len(activities)
        }
        
        # Send to Slack automatically
        slack_success, slack_message = send_to_slack(name, activities, total_metrics, dealership_name, checkin_time)
        
        # Auto-checkout after successful Slack submission
        if slack_success:
            session.pop('checked_in', None)
            session.pop('dealership_id', None)
            session.pop('dealership_name', None)
            session.pop('checkin_time', None)
        
        # Create text file content
        eastern = pytz.timezone('America/Toronto')
        utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
        local_time = utc_now.astimezone(eastern)
        
        file_content = f"Daily Activity Log - {name}\n"
        file_content += f"Date: {local_time.strftime('%Y-%m-%d')}\n"
        file_content += f"Location: {dealership_name}\n"
        if checkin_time:
            file_content += f"Check-in Time: {checkin_time}\n"
        file_content += f"Generated: {local_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        for i, activity in enumerate(activities, 1):
            file_content += f"Hour {i}:\n"
            file_content += f"  Cars Sold: {activity.get('cars_sold', 0)}\n"
            file_content += f"  Cars Delivered: {activity.get('cars_delivered', 0)}\n"
            file_content += f"  In-Person Appointments: {activity.get('in_person_appointments', 0)}\n"
            file_content += f"  Appointments Generated: {activity.get('appointments_generated', 0)}\n"
            file_content += f"  Phone Appointments: {activity.get('phone_appointments', 0)}\n"
            file_content += f"  Quote Calls: {activity.get('quote_calls', 0)}\n"
            file_content += f"  Advertisements Posted: {activity.get('advertisements_posted', 0)}\n\n"
        
        # Create file for download
        file_buffer = io.BytesIO()
        file_buffer.write(file_content.encode('utf-8'))
        file_buffer.seek(0)
        
        response_data = {
            "success": True,
            "message": "Activity log processed successfully",
            "slack_success": slack_success,
            "slack_message": slack_message,
            "auto_checkout": slack_success
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@activity_bp.route('/submit-slack-only', methods=['POST'])
def submit_slack_only():
    """Submit activity log to Slack only (no file download)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        name = data.get('name', 'Unknown')
        activities = data.get('activities', [])
        
        if not activities:
            return jsonify({"success": False, "message": "No activities provided"}), 400
        
        # Get check-in information
        dealership_name = session.get('dealership_name', 'Unknown Location')
        checkin_time = session.get('checkin_time')
        
        # Calculate total metrics
        total_metrics = {
            'total_score': 0,
            'total_activities': len(activities)
        }
        
        # Send to Slack
        slack_success, slack_message = send_to_slack(name, activities, total_metrics, dealership_name, checkin_time)
        
        # Auto-checkout after successful Slack submission
        if slack_success:
            session.pop('checked_in', None)
            session.pop('dealership_id', None)
            session.pop('dealership_name', None)
            session.pop('checkin_time', None)
        
        return jsonify({
            "success": slack_success,
            "message": slack_message,
            "auto_checkout": slack_success
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

