import os
import sys
# Required for Vercel
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, redirect, send_from_directory, jsonify
from flask_cors import CORS

# Import blueprints
from routes.checkin import checkin_bp
from routes.activity_slack import activity_bp

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

# Configure Flask
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key-change-in-production')

# Register blueprints with /api prefix
app.register_blueprint(checkin_bp, url_prefix='/api')
app.register_blueprint(activity_bp, url_prefix='/api')

# Root route - redirect to check-in
@app.route('/')
def index():
    return redirect('/checkin.html')

# Serve check-in page
@app.route('/checkin.html')
def checkin():
    return send_from_directory('static', 'checkin.html')

# Serve activity logging page
@app.route('/index.html')
def activity_page():
    return send_from_directory('static', 'index.html')

# Health check endpoint
@app.route('/health')
def health():
    return jsonify({"status": "healthy", "message": "Activity Logger is running"})

# For local development
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)

