import os
import datetime
import json
import threading
from flask import Flask, request, Response, redirect
from waitress import serve
import time
import random
import requests
from flask_cors import CORS
from setup_logging import get_logger

# for local dev, load env vars from a .env file
from dotenv import load_dotenv
load_dotenv()

service_url = os.environ["Quix__Deployment__Network__PublicUrl"]
data_api_endpoint = os.getenv("data_api_endpoint", "")

logger = get_logger()

app = Flask(__name__)

# Enable CORS for all routes and origins by default
CORS(app)

# Dictionary to track active test threads
active_tests = {}

def build_api_url(endpoint, test_id):
    """Build the API URL by appending test_id to the endpoint, handling trailing slashes."""
    if not endpoint:
        return None
    
    # Remove trailing slash from endpoint if present
    endpoint = endpoint.rstrip('/')
    return f"{endpoint}/{test_id}"

def run_ecu_test(test_id, ramp_delay, set_speed, start_time):
    """Run the ECU test in a background thread."""
    try:
        active_tests[test_id] = {"status": "running", "start_time": time.time()}
        def generate_data():
            # Calculate values based on set_speed
            base_voltage = 14.9 - (set_speed * 1.6)
            base_current = 8000 + (set_speed * 6000)
            base_load_cell = -140000 + (set_speed * 10000)

            # Generate fluctuating values
            voltage_v = base_voltage + random.uniform(-0.1, 0.1)
            current_ma = base_current + random.uniform(-500, 500)
            load_cell_raw_value = base_load_cell + random.uniform(-5000, 5000)

            # Current timestamp in milliseconds
            timestamp = int(time.time() * 1000 - start_time)

            return {
                "timestamp": timestamp,
                "ina260": {
                    "voltage_v": voltage_v,
                    "current_ma": current_ma
                },
                "load_cell": {
                    "raw_value": load_cell_raw_value,
                    "is_ready": True
                },
                "set_speed": set_speed
            }

        # Generate data every 50ms and send chunks every 200ms
        data_interval = 50  # Generate data every 50ms
        send_interval = 200  # Send data every 200ms
        end_time = start_time + ramp_delay

        data_chunk = []
        last_send_time = time.time() * 1000

        while time.time() * 1000 < end_time:
            current_time = time.time() * 1000

            # Generate and accumulate data
            data_to_chunk = generate_data()
            data_chunk.append(data_to_chunk)

            # Send chunk if send_interval has elapsed
            if current_time - last_send_time >= send_interval:
                if data_api_endpoint != "":
                    api_url = build_api_url(data_api_endpoint, test_id)
                    response = requests.post(api_url, json={"data": data_chunk})
                    logger.debug(f"Sent chunk with {len(data_chunk)} items, Response: {response.status_code}")
                else:
                    logger.debug(f"Sent chunk: {test_id} :: {len(data_chunk)} items, Response: Not sent (no endpoint configured)")
                
                data_chunk = []
                last_send_time = current_time

            time.sleep(data_interval / 1000)  # Convert milliseconds to seconds

        # Send any remaining data in the final chunk
        if data_chunk:
            if data_api_endpoint != "":
                api_url = build_api_url(data_api_endpoint, test_id)
                response = requests.post(api_url, json={"data": data_chunk})
                logger.debug(f"Sent final chunk with {len(data_chunk)} items, Response: {response.status_code}")
            else:
                logger.debug(f"Sent final chunk: {test_id} :: {len(data_chunk)} items, Response: Not sent (no endpoint configured)")
        
        logger.info(f"ECU test {test_id} completed successfully")
    
    except Exception as e:
        logger.error(f"Error running ECU test {test_id}: {str(e)}")
    
    finally:
        # Mark the test as completed
        if test_id in active_tests:
            active_tests[test_id]["status"] = "completed"

@app.route("/", methods=['GET'])
def redirect_to_swagger():
    html = "POST data to `/ecu/start`"
    return Response(html, mimetype='text/html', status=200)

@app.route("/ecu/start", methods=['POST'])
def post_data_without_key():
    data = request.json
    logger.debug(f"{data}")

    # Extract test_id and ramp_delay from the request
    test_id = data.get("test_id")
    
    # Check if a test with this ID is already running
    if test_id in active_tests and active_tests[test_id]["status"] == "running":
        logger.warning(f"Test {test_id} is already running")
        return Response(
            json.dumps({
                "status": "error",
                "message": f"Test {test_id} is already running"
            }),
            mimetype='application/json',
            status=409
        )
    
    ramp_delay = int(data.get("ramp_delay", 6000))  # Default to 6000ms if not provided
    set_speed = float(data.get("set_speed", 0.5))  # Default to 0.5 if not provided
    start_time = time.time() * 1000  # Start time in milliseconds

    # Start the test in a background thread
    thread = threading.Thread(target=run_ecu_test, args=(test_id, ramp_delay, set_speed, start_time), daemon=True)
    thread.start()

    # Return immediately to the caller
    return Response(json.dumps({"status": "started", "test_id": test_id}), mimetype='application/json', status=202)

if __name__ == '__main__':
    serve(app, host="0.0.0.0", port=80)