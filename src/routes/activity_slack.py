from flask import Blueprint, jsonify, request, send_file, session
from datetime import datetime
import io
import json
import urllib.request
import urllib.parse
import urllib.error
import os

activity_bp = Blueprint('activity', __name__, url_prefix='/api')

def send_to_slack(name, activities, total_metrics, dealership_info=None, checkin_time=None, webhook_url=None):
    """Send activity log to Slack channel."""
    # Get webhook URL from environment variable
    slack_webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    
    if not slack_webhook_url:
        return False, "Slack webhook URL not configured. Please set SLACK_WEBHOOK_URL environment variable."
    
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
        from datetime import datetime
        import pytz
        
        # Use Eastern Time for date display
        eastern = pytz.timezone('America/Toronto')
        utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
        local_time = utc_now.astimezone(eastern)
        
        context_parts = [f"*Date:* {local_time.strftime('%Y-%m-%d')}", f"*Total Score:* {total_score} points"]
        
        if dealership_info:
            context_parts.append(f"*📍 Location:* {dealership_info}")
        
        if checkin_time:
            context_parts.append(f"*🕐 Check-in Time:* {checkin_time}")
        
        context_text = " | ".join(context_parts)
        
        # Create Slack message
        message = {
            "text": f"📊 Daily Activity Report - {name}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"📊 Daily Activity Report - {name}"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": context_text
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*📈 Daily Summary:*"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*🚗 Cars Sold:* {total_metrics['cars_sold']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*🚚 Cars Delivered:* {total_metrics['cars_delivered']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*📞 Quote Calls:* {total_metrics['quote_calls']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*📅 Appointments Generated:* {total_metrics['appointments_generated']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*🤝 In-Person Appointments:* {total_metrics['in_person_appointments']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*☎️ Phone Appointments:* {total_metrics['phone_appointments']}"
                        }
                    ]
                }
            ]
        }
        
        # Add hourly breakdown if there are activities with descriptions
        hourly_details = []
        for i, activity in enumerate(activities):
            if activity.get('description', '').strip():
                hour_num = i + 1
                score = (
                    int(activity.get('quote_calls', 0)) * 2 +
                    int(activity.get('appointments_generated', 0)) * 4 +
                    int(activity.get('in_person_appointments', 0)) * 6 +
                    int(activity.get('phone_appointments', 0)) * 3 +
                    int(activity.get('cars_sold', 0)) * 10 +
                    int(activity.get('cars_delivered', 0)) * 8 +
                    int(activity.get('advertisements_posted', 0)) * 1
                )
                
                # Calculate rating (1-5 stars)
                if score >= 20:
                    rating = 5
                elif score >= 15:
                    rating = 4
                elif score >= 10:
                    rating = 3
                elif score >= 5:
                    rating = 2
                else:
                    rating = 1
                
                stars = "⭐" * rating
                hourly_details.append(f"*Hour {hour_num}:* {activity.get('description', '')} {stars}")
        
        if hourly_details:
            message["blocks"].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*🕐 Hourly Activities:*\n" + "\n".join(hourly_details[:5])  # Limit to first 5 to avoid message length issues
                }
            })
        
        # Send to Slack
        data = json.dumps(message).encode('utf-8')
        req = urllib.request.Request(
            slack_webhook_url,
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        response = urllib.request.urlopen(req, timeout=10)
        
        if response.getcode() == 200:
            return True, "Successfully sent to Slack"
        else:
            return False, f"Slack API error: {response.getcode()}"
            
    except Exception as e:
        return False, f"Error sending to Slack: {str(e)}"

@activity_bp.route("/activities/calculate-rating", methods=["POST"])
def calculate_rating():
    """Calculate productivity rating based on activity metrics."""
    data = request.json
    
    # Extract metrics
    quote_calls = int(data.get('quote_calls', 0))
    appointments_generated = int(data.get('appointments_generated', 0))
    in_person_appointments = int(data.get('in_person_appointments', 0))
    phone_appointments = int(data.get('phone_appointments', 0))
    cars_sold = int(data.get('cars_sold', 0))
    cars_delivered = int(data.get('cars_delivered', 0))
    advertisements_posted = int(data.get('advertisements_posted', 0))
    
    # Calculate weighted score
    # Weights: Cars Sold (10), Cars Delivered (8), In-Person Appointments (4),
    # Appointments Generated (2), Phone Appointments (3), Quote Calls (1), Advertisements Posted (1)
    score = (
        quote_calls * 1 +
        appointments_generated * 2 +
        in_person_appointments * 4 +
        phone_appointments * 3 +
        cars_sold * 10 +
        cars_delivered * 8 +
        advertisements_posted * 1
    )
    
    # Calculate rating (1-5 stars)
    if score >= 20:
        rating = 5
    elif score >= 15:
        rating = 4
    elif score >= 10:
        rating = 3
    elif score >= 5:
        rating = 2
    else:
        rating = 1
    
    return jsonify({"rating": rating})

@activity_bp.route("/activities/pdf", methods=["POST"])
def generate_pdf():
    """Generate a PDF file from activity data and optionally send to Slack."""
    data = request.json
    name = data.get('name', 'User')
    activities = data.get('activities', [])
    send_slack = data.get('send_slack', False)
    
    # Get check-in information from session (with fallback)
    try:
        dealership_name = session.get('dealership_name', 'Unknown Location')
        checkin_time = session.get('checkin_time', None)
    except:
        dealership_name = 'Unknown Location'
        checkin_time = None
    
    # Create a simple text representation instead of PDF
    content = []
    content.append(f"Daily Activity Log - {name}")
    content.append(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    content.append(f"Location: {dealership_name}")
    if checkin_time:
        content.append(f"Check-in Time: {checkin_time}")
    content.append("-" * 50)
    
    total_metrics = {
        'quote_calls': 0,
        'appointments_generated': 0,
        'in_person_appointments': 0,
        'phone_appointments': 0,
        'cars_sold': 0,
        'cars_delivered': 0,
        'advertisements_posted': 0
    }
    
    for i, activity in enumerate(activities):
        hour_num = i + 1
        content.append(f"\nHour {hour_num}:")
        content.append(f"Activity Description: {activity.get('description', '')}")
        content.append(f"Quote Calls: {activity.get('quote_calls', 0)}")
        content.append(f"Appointments Generated: {activity.get('appointments_generated', 0)}")
        content.append(f"In Person Appointments: {activity.get('in_person_appointments', 0)}")
        content.append(f"Phone Appointments: {activity.get('phone_appointments', 0)}")
        content.append(f"Cars Sold: {activity.get('cars_sold', 0)}")
        content.append(f"Cars Delivered: {activity.get('cars_delivered', 0)}")
        content.append(f"Advertisements Posted: {activity.get('advertisements_posted', 0)}")
        
        # Calculate productivity rating
        score = (
            int(activity.get('quote_calls', 0)) * 1 +
            int(activity.get('appointments_generated', 0)) * 2 +
            int(activity.get('in_person_appointments', 0)) * 4 +
            int(activity.get('phone_appointments', 0)) * 3 +
            int(activity.get('cars_sold', 0)) * 10 +
            int(activity.get('cars_delivered', 0)) * 8 +
            int(activity.get('advertisements_posted', 0)) * 1
        )
        
        # Calculate rating (1-5 stars)
        if score >= 20:
            rating = 5
        elif score >= 15:
            rating = 4
        elif score >= 10:
            rating = 3
        elif score >= 5:
            rating = 2
        else:
            rating = 1
            
        content.append(f"Productivity Rating: {rating} stars")
        
        # Update totals
        for key in total_metrics:
            total_metrics[key] += int(activity.get(key, 0))
    
    # Add summary section
    content.append("\n" + "=" * 50)
    content.append("DAILY SUMMARY")
    content.append("=" * 50)
    for key, value in total_metrics.items():
        content.append(f"Total {key.replace('_', ' ').title()}: {value}")
    
    # Send to Slack automatically (always enabled)
    slack_success = False
    slack_message = ""
    slack_success, slack_message = send_to_slack(name, activities, total_metrics, dealership_name, checkin_time)
    
    # Automatic checkout after successful Slack submission
    if slack_success:
        try:
            # Clear check-in information from session
            session.pop('checked_in', None)
            session.pop('dealership_id', None)
            session.pop('dealership_name', None)
            session.pop('checkin_latitude', None)
            session.pop('checkin_longitude', None)
            session.pop('checkin_time', None)
            print(f"Auto-checkout completed for {name} after successful Slack submission")
        except Exception as e:
            print(f"Auto-checkout error: {e}")
    
    # Create a text file in memory
    text_content = "\n".join(content)
    buffer = io.BytesIO(text_content.encode('utf-8'))
    buffer.seek(0)
    
    # Prepare response with Slack status
    response = send_file(
        buffer,
        mimetype='text/plain',
        as_attachment=True,
        download_name=f"Daily_Activity_Log_{name}_{datetime.now().strftime('%Y-%m-%d')}.txt"
    )
    
    # Add Slack status to response headers (always sent now)
    response.headers['X-Slack-Status'] = 'success' if slack_success else 'error'
    response.headers['X-Slack-Message'] = slack_message
    
    return response

@activity_bp.route("/send-to-slack", methods=["POST"])
def send_to_slack_endpoint():
    """Send activity data to Slack - alternative endpoint for frontend compatibility."""
    return send_slack_only()

@activity_bp.route("/activities/slack", methods=["POST"])
def send_slack_only():
    """Send activity data to Slack without generating a file."""
    data = request.json
    name = data.get('name', 'User')
    activities = data.get('activities', [])
    
    # Get check-in information from session (with fallback)
    try:
        dealership_name = session.get('dealership_name', 'Unknown Location')
        checkin_time = session.get('checkin_time', None)
    except:
        dealership_name = 'Unknown Location'
        checkin_time = None
    
    # Calculate totals
    total_metrics = {
        'quote_calls': 0,
        'appointments_generated': 0,
        'in_person_appointments': 0,
        'phone_appointments': 0,
        'cars_sold': 0,
        'cars_delivered': 0,
        'advertisements_posted': 0
    }
    
    for activity in activities:
        for key in total_metrics:
            total_metrics[key] += int(activity.get(key, 0))
    
    # Send to Slack (uses environment variable for webhook URL)
    success, message = send_to_slack(name, activities, total_metrics, dealership_name, checkin_time)
    
    # Automatic checkout after successful Slack submission
    if success:
        try:
            # Clear check-in information from session
            session.pop('checked_in', None)
            session.pop('dealership_id', None)
            session.pop('dealership_name', None)
            session.pop('checkin_latitude', None)
            session.pop('checkin_longitude', None)
            session.pop('checkin_time', None)
            print(f"Auto-checkout completed for {name} after successful Slack-only submission")
        except Exception as e:
            print(f"Auto-checkout error: {e}")
    
    return jsonify({
        'success': success,
        'message': message
    })

