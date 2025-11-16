"""
Flask Backend Server for Dobot IoT Control App

This server provides a RESTful API to control the Dobot robotic arm.
It acts as a bridge between a front-end application and the Dobot's TCP/IP interface.
"""
import sys
import os
from flask import Flask, jsonify, request, render_template

# --- Dobot API Integration ---
# To import the dobot_api module from the parent directory, we need to add its path.
# The 'Dobot/TCP-IP-4Axis-Python-main' directory contains the dobot_api.py file.
# This assumes the server is run from the root of the 'dobot-iot-control-app' project.
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
dobot_api_path = os.path.join(parent_dir, "Dobot", "TCP-IP-4Axis-Python-main")
sys.path.append(dobot_api_path)

try:
    from dobot_api import DobotApiDashboard, DobotApiMove, DobotApi
except ImportError as e:
    print(f"Error: Failed to import dobot_api. Please ensure the path is correct: {dobot_api_path}")
    print(f"Original error: {e}")
    sys.exit(1)

# --- Configuration ---
# !! IMPORTANT !!
# Change this to your Dobot's actual IP address.
ROBOT_IP = "192.168.1.6"

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Dobot API Instances ---
# It's better to initialize these once when the server starts.
try:
    dashboard = DobotApiDashboard(ROBOT_IP, 29999)
    move = DobotApiMove(ROBOT_IP, 30003)
    feed = DobotApi(ROBOT_IP, 30004) # Feedback port can be used in a separate thread
    print("Successfully connected to Dobot API.")
except Exception as e:
    print(f"Failed to initialize Dobot API. Please check the connection and IP address. Error: {e}")
    # We don't exit here, to allow API to show the error.
    dashboard = None
    move = None
    feed = None

# --- Helper Function ---
def check_dobot_connection():
    """Checks if the Dobot API instances are available."""
    if not dashboard or not move or not feed:
        return False, jsonify({
            "status": "error",
            "message": "Dobot is not connected. Check the server logs for details."
        }), 503 # Service Unavailable
    return True, None, None

# --- Web Interface Route ---
@app.route('/')
def index():
    """Serves the main control panel page."""
    return render_template('index.html')

# --- API Endpoints ---

@app.route('/api/connection/check', methods=['GET'])
def connection_check():
    """
    Checks and returns the status of each Dobot port connection.
    This performs a live "heartbeat" check on the dashboard port.
    """
    status = {
        "dashboard": False,
        "move": False,
        "feed": False
    }

    # For dashboard, perform a live check by sending a command
    if dashboard:
        try:
            # GetErrorID is a lightweight command perfect for a heartbeat
            dashboard.GetErrorID()
            status["dashboard"] = True
        except Exception as e:
            # Any exception during communication means the connection is likely dead
            print(f"Dashboard connection check failed: {e}")
            status["dashboard"] = False

    # For move and feed, a live check is harder without a simple query command.
    # Their status is often tied to the dashboard. We'll rely on the initial
    # object creation and the live dashboard status as a strong indicator.
    if move and status["dashboard"]:
        status["move"] = True
    
    if feed and status["dashboard"]:
        status["feed"] = True

    return jsonify(status)

@app.route('/api/robot/enable', methods=['POST'])
def enable_robot():
    """Enables the robot."""
    is_connected, error_response, status_code = check_dobot_connection()
    if not is_connected:
        return error_response, status_code

    try:
        result = dashboard.EnableRobot()
        return jsonify({"status": "success", "message": "Robot enabled.", "robot_response": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/robot/disable', methods=['POST'])
def disable_robot():
    """Disables the robot."""
    is_connected, error_response, status_code = check_dobot_connection()
    if not is_connected:
        return error_response, status_code

    try:
        result = dashboard.DisableRobot()
        return jsonify({"status": "success", "message": "Robot disabled.", "robot_response": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/robot/stop', methods=['POST'])
def stop_robot():
    """Stops the robot and clears the command queue."""
    is_connected, error_response, status_code = check_dobot_connection()
    if not is_connected:
        return error_response, status_code

    try:
        result = dashboard.ResetRobot()
        return jsonify({"status": "success", "message": "Robot stopped and queue cleared.", "robot_response": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/robot/position', methods=['GET'])
def get_position():
    """Gets the current robot position (Pose)."""
    is_connected, error_response, status_code = check_dobot_connection()
    if not is_connected:
        return error_response, status_code

    try:
        pose_str = dashboard.GetPose()
        # The response is a string like "0,{},GetPose(x,y,z,r)". We parse it.
        parts = pose_str.replace(')', '').split('(')
        coords_str = parts[1]
        coords = [float(c) for c in coords_str.split(',')]
        
        return jsonify({
            "status": "success",
            "position": {
                "x": coords[0],
                "y": coords[1],
                "z": coords[2],
                "r": coords[3]
            },
            "robot_response": pose_str
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to parse position: {str(e)}"}), 500

@app.route('/api/robot/move/j', methods=['POST'])
@app.route('/api/robot/move/l', methods=['POST'])
def move_robot():
    """
    Moves the robot using MovJ (joint) or MovL (linear) motion.
    Expects a JSON payload with coordinates.
    e.g., {"x": 200, "y": 100, "z": 50, "r": 0}
    """
    is_connected, error_response, status_code = check_dobot_connection()
    if not is_connected:
        return error_response, status_code

    data = request.get_json()
    if not data or not all(k in data for k in ["x", "y", "z", "r"]):
        return jsonify({"status": "error", "message": "Invalid payload. Required keys: x, y, z, r"}), 400

    x, y, z, r = data['x'], data['y'], data['z'], data['r']
    
    # Determine which move type from the URL rule
    move_type = 'MovJ' if 'move/j' in request.path else 'MovL'
    
    try:
        if move_type == 'MovJ':
            result = move.MovJ(x, y, z, r)
        else:
            result = move.MovL(x, y, z, r)
        
        # Optional: Wait for the move to complete.
        # For a real application, you might want to make this asynchronous.
        move.Sync()

        return jsonify({
            "status": "success",
            "message": f"Executing {move_type} to ({x}, {y}, {z}, {r}) and waiting for completion.",
            "robot_response": result
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/robot/speed', methods=['POST'])
def set_speed():
    """
    Sets the global speed factor.
    Expects a JSON payload with a speed ratio.
    e.g., {"ratio": 80}
    """
    is_connected, error_response, status_code = check_dobot_connection()
    if not is_connected:
        return error_response, status_code

    data = request.get_json()
    if not data or 'ratio' not in data:
        return jsonify({"status": "error", "message": "Invalid payload. Required key: ratio"}), 400

    ratio = data['ratio']
    if not 1 <= ratio <= 100:
        return jsonify({"status": "error", "message": "Speed ratio must be between 1 and 100."}), 400

    try:
        result = dashboard.SpeedFactor(ratio)
        return jsonify({"status": "success", "message": f"Global speed set to {ratio}%.", "robot_response": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- Main Execution ---
if __name__ == '__main__':
    # Run the Flask server
    # host='0.0.0.0' makes the server accessible from any device on the network.
    app.run(host='0.0.0.0', port=5000, debug=True)
