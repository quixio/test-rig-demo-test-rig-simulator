import os
import datetime
import json
import requests
from flask import Flask, request, Response, redirect
from waitress import serve
import time

from flask_cors import CORS

from setup_logging import get_logger

# for local dev, load env vars from a .env file
from dotenv import load_dotenv
load_dotenv()

service_url = os.getenv("Quix__Deployment__Network__PublicUrl")
data_api_endpoint = os.getenv("data_api_endpoint", "")
test_api_url = os.getenv("TEST_API_URL", "http://localhost:3000/api/tests")
ecu_api_url = os.getenv("ECU_API_URL", "http://localhost:3001/api/ecu")

logger = get_logger()

app = Flask(__name__)

# Enable CORS for all routes and origins by default
CORS(app)

app.static_folder = '.'
app.static_url_path = ''

# Store the current test ID
current_test_id = "TEST-001"

def increment_test_id(test_id):
    """Extract number from test ID, increment it, and return new ID"""
    parts = test_id.split('-')
    if len(parts) == 2 and parts[1].isdigit():
        number = int(parts[1]) + 1
        return f"{parts[0]}-{number:03d}"
    return test_id

@app.route("/image_1.png")
def serve_image():
    return app.send_static_file('image_1.png')

@app.route("/", methods=['GET'])
def home_page():
    global current_test_id
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Data Entry Form</title>
        <style>
            body {{
                font-family: 'MS Sans Serif', Arial, sans-serif;
                background-color: #c0c0c0;
                margin: 0;
                padding: 20px;
            }}
            
            .form-container {{
                background-color: #c0c0c0;
                border: 2px outset #dfdfdf;
                border-right-color: #808080;
                border-bottom-color: #808080;
                padding: 8px;
                width: 450px;
                box-shadow: 1px 1px 0 #ffffff inset, -1px -1px 0 #808080 inset;
            }}
            
            .title-bar {{
                background: linear-gradient(to right, #000080, #1084d7);
                color: white;
                padding: 2px 2px;
                margin: -8px -8px 8px -8px;
                font-weight: bold;
                font-size: 11px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            
            .form-group {{
                margin-bottom: 10px;
                display: flex;
                align-items: center;
            }}
            
            label {{
                width: 140px;
                font-size: 11px;
                color: #000000;
                font-weight: normal;
            }}
            
            input[type="text"],
            input[type="number"] {{
                width: 250px;
                padding: 3px 2px;
                font-family: 'MS Sans Serif', Arial, sans-serif;
                font-size: 11px;
                border: 2px inset #dfdfdf;
                border-right-color: #808080;
                border-bottom-color: #808080;
                background-color: #ffffff;
            }}
            
            input[type="text"]:focus,
            input[type="number"]:focus {{
                outline: none;
            }}
            
            button {{
                width: 90px;
                height: 28px;
                font-family: 'MS Sans Serif', Arial, sans-serif;
                font-size: 11px;
                background-color: #c0c0c0;
                border: 2px outset #dfdfdf;
                border-right-color: #808080;
                border-bottom-color: #808080;
                color: #000000;
                cursor: pointer;
                font-weight: bold;
                margin-top: 15px;
                margin-right: 5px;
            }}
            
            button:active {{
                border-style: inset;
                border-top-color: #808080;
                border-left-color: #808080;
                border-right-color: #dfdfdf;
                border-bottom-color: #dfdfdf;
            }}
            
            .button-group {{
                text-align: center;
                margin-top: 20px;
            }}
            
            .main-container {{
                display: flex;
                gap: 20px;
            }}
            
            .image-container {{
                flex-shrink: 0;
            }}
            
            .image-container img {{
                border: 2px outset #dfdfdf;
                border-right-color: #808080;
                border-bottom-color: #808080;
                background-color: #c0c0c0;
                max-width: 500px;
                height: auto;
            }}
        </style>
    </head>
    <body>
        <h1>LabVIEW Simulation</h1>
        <div class="main-container">
            <div class="form-container">
            <div class="title-bar">
                <span>Test Data Entry</span>
                <span>_</span>
            </div>
            <form method="POST" action="/submit-test">
                <div class="form-group">
                    <label for="testid">Test ID:</label>
                    <input type="text" id="testid" name="testid" value="{current_test_id}" required>
                </div>
                
                <div class="form-group">
                    <label for="campaignid">Campaign ID:</label>
                    <input type="text" id="campaignid" name="campaignid" value="CAMP-2024-001" required>
                </div>
                
                <div class="form-group">
                    <label for="sampleid">Sample ID:</label>
                    <input type="text" id="sampleid" name="sampleid" value="SAMPLE-001" required>
                </div>
                
                <div class="form-group">
                    <label for="environmentid">Environment ID:</label>
                    <input type="text" id="environmentid" name="environmentid" value="ENV-LAB-01" required>
                </div>
                
                <div class="form-group">
                    <label for="batteryid">Battery ID:</label>
                    <input type="text" id="batteryid" name="batteryid" value="BATT-12345" required>
                </div>
                
                <div class="form-group">
                    <label for="fanid">Fan ID:</label>
                    <input type="text" id="fanid" name="fanid" value="FAN-001" required>
                </div>
                
                <div class="form-group">
                    <label for="motorid">Motor ID:</label>
                    <input type="text" id="motorid" name="motorid" value="MOT-001" required>
                </div>
                
                <div class="form-group">
                    <label for="shroudid">Shroud ID:</label>
                    <input type="text" id="shroudid" name="shroudid" value="SHROUD-001" required>
                </div>
                
                <div class="form-group">
                    <label for="throttle">Throttle %:</label>
                    <input type="number" id="throttle" name="throttle" min="0" max="100" value="50" required>
                </div>
                
                <div class="form-group">
                    <label for="operator">Operator Name:</label>
                    <input type="text" id="operator" name="operator" value="John Smith" required>
                </div>
                
                <div class="form-group">
                    <label for="holdtime">Hold Time:</label>
                    <input type="text" id="holdtime" name="holdtime" value="30" required>
                </div>
                
                <div class="button-group">
                    <button type="submit">Run Test</button>
                    <button type="reset">Clear</button>
                </div>
            </form>
            </div>
            
            <div class="image-container">
                <img src="/image_1.png" alt="Test Image">
            </div>
        </div>
    </body>
    </html>
    """
    return Response(html, mimetype='text/html', status=200)

@app.route("/submit-test", methods=['POST'])
def submit_test():
    # Handle the form submission
    global current_test_id
    try:
        # Format the data according to the API specification
        configuration = {
            "test_id": request.form.get('testid'),
            "campaign_id": request.form.get('campaignid'),
            "environment_id": request.form.get('environmentid'),
            "sample_id": request.form.get('sampleid'),
            "operator": request.form.get('operator'),
            "sensors": {
                "throttle": {
                    "value": request.form.get('throttle')
                },
                "hold_time": {
                    "value": request.form.get('holdtime')
                },
                "battery": {
                    "id": request.form.get('batteryid')
                },
                "motor": {
                    "id": request.form.get('motorid')
                },
                "shroud": {
                    "id": request.form.get('shroudid')
                },
                "fan": {
                    "id": request.form.get('fanid')
                }
            },
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        logger.info(f"Test data formatted: {json.dumps(configuration)}")
        
        # Post the data to the HTTP API
        try:
            response = requests.post(
                test_api_url,
                json=configuration,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Test data posted successfully. Response: {response.text}")
            else:
                logger.warning(f"API returned status code {response.status_code}. Response: {response.text}")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to post test data to API: {str(e)}")
        
        # Post ECU data to a different API
        try:
            ecu_data = {
                "test_id": request.form.get('testid'),
                "speeds": [request.form.get('throttle')],
                "ramp_delay": request.form.get('holdtime')
            }
            
            logger.info(f"ECU data formatted: {json.dumps(ecu_data)}")
            
            ecu_response = requests.post(
                ecu_api_url,
                json=ecu_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if ecu_response.status_code in [200, 201]:
                logger.info(f"ECU data posted successfully. Response: {ecu_response.text}")
            else:
                logger.warning(f"ECU API returned status code {ecu_response.status_code}. Response: {ecu_response.text}")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to post ECU data to API: {str(e)}")
        
        # Increment the test ID for the next submission
        current_test_id = increment_test_id(current_test_id)
        
        # Redirect back to home page with incremented test ID
        return redirect("/")
    
    except Exception as e:
        logger.error(f"Error submitting test: {str(e)}")
        return Response("Error submitting test", status=500)

if __name__ == '__main__':
    serve(app, host="0.0.0.0", port=80)