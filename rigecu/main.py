import os
import datetime
import json
from flask import Flask, request, Response, redirect
from flasgger import Swagger
from waitress import serve
import time

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

app.config['SWAGGER'] = {
    'title': 'Test Rig ECU Simulator',
    'description': 'This API is intended to simulate a test rig.',
    'uiversion': 3
}

swagger = Swagger(app)

@app.route("/", methods=['GET'])
def redirect_to_swagger():
    return redirect("/apidocs/")

@app.route("/ecu/start", methods=['POST'])
def post_data_without_key():
    data = request.json
    logger.debug(f"{data}")

    import requests

    # Extract test_id and ramp_delay from the request
    test_id = data.get("test_id")
    ramp_delay = data.get("ramp_delay", 6000)  # Default to 6000ms if not provided

    set_speed = data.get("set_speed", 0.5)  # Default to 0.5 if not provided
    start_time = time.time() * 1000  # Start time in milliseconds

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

    # Send data every 50ms for the duration of ramp_delay
    interval = 50  # in milliseconds
    end_time = start_time + ramp_delay

    while time.time() * 1000 < end_time:
        data_to_send = generate_data()
        if(data_api_endpoint != ""):
            response = requests.post(data_api_endpoint, json={"test_id": test_id, "data": [data_to_send]})
        logger.debug(f"Sent data: {data_to_send}, Response: {response.status_code}")
        time.sleep(interval / 1000)  # Convert milliseconds to seconds

    return Response(status=200)

if __name__ == '__main__':
    serve(app, host="0.0.0.0", port=80)
