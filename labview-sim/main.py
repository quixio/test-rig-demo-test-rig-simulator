import os
import datetime
import json
import requests
from flask import Flask, request, Response, redirect, jsonify
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

@app.route("/video.mp4")
def serve_video():
    return app.send_static_file('video.mp4')

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

            .video-container {{
                flex-shrink: 0;
                display: none;
            }}

            .video-container video {{
                border: 2px outset #dfdfdf;
                border-right-color: #808080;
                border-bottom-color: #808080;
                background-color: #000000;
                max-width: 500px;
                height: auto;
            }}

            #status-message {{
                margin-top: 10px;
                padding: 8px;
                font-size: 11px;
                display: none;
                border: 2px inset #dfdfdf;
                border-right-color: #808080;
                border-bottom-color: #808080;
            }}

            #status-message.success {{
                background-color: #90EE90;
                color: #008000;
                display: block;
            }}

            #status-message.error {{
                background-color: #FFB6C6;
                color: #8B0000;
                display: block;
            }}
        </style>
    </head>
    <body>
        <h1>LabTECH</h1>
        <div class="main-container">
            <div class="form-container">
            <div class="title-bar">
                <span>Test Data Entry</span>
                <span>_</span>
            </div>
            <form id="testForm">
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
                    <input type="text" id="holdtime" name="holdtime" value="30000" required>
                </div>
                
                <div id="status-message"></div>
                
                <div class="button-group">
                    <button type="button" id="runBtn">Run Test</button>
                    <button type="reset">Clear</button>
                </div>
            </form>
            </div>
            
            <div class="image-container" id="imageContainer">
                <img src="/image_1.png" alt="Test Image">
            </div>

            <div class="video-container" id="videoContainer">
                <video id="testVideo" controls autoplay>
                    <source src="/video.mp4" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
            </div>
        </div>

        <script>
            function incrementTestId(testId) {{
                const parts = testId.split('-');
                if (parts.length === 2 && /^\d+$/.test(parts[1])) {{
                    const number = parseInt(parts[1]) + 1;
                    return parts[0] + '-' + String(number).padStart(3, '0');
                }}
                return testId;
            }}

            document.getElementById('runBtn').addEventListener('click', async function(e) {{
                e.preventDefault();
                
                const formData = new FormData(document.getElementById('testForm'));
                const data = {{
                    testid: formData.get('testid'),
                    campaignid: formData.get('campaignid'),
                    sampleid: formData.get('sampleid'),
                    environmentid: formData.get('environmentid'),
                    batteryid: formData.get('batteryid'),
                    fanid: formData.get('fanid'),
                    motorid: formData.get('motorid'),
                    shroudid: formData.get('shroudid'),
                    throttle: formData.get('throttle'),
                    operator: formData.get('operator'),
                    holdtime: formData.get('holdtime')
                }};
                
                // Show video and hide image immediately
                document.getElementById('imageContainer').style.display = 'none';
                document.getElementById('videoContainer').style.display = 'block';
                document.getElementById('testVideo').play();
                
                try {{
                    const response = await fetch('/api/submit-test', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify(data)
                    }});
                    
                    const result = await response.json();
                    const statusMsg = document.getElementById('status-message');
                    
                    if (response.ok) {{
                        statusMsg.className = 'success';
                        statusMsg.textContent = 'Test submitted successfully!';
                        
                        // Increment the test ID on the client side
                        const currentId = document.getElementById('testid').value;
                        document.getElementById('testid').value = incrementTestId(currentId);
                    }} else {{
                        statusMsg.className = 'error';
                        statusMsg.textContent = 'Error: ' + (result.error || 'Failed to submit test');
                    }}
                }} catch (error) {{
                    const statusMsg = document.getElementById('status-message');
                    statusMsg.className = 'error';
                    statusMsg.textContent = 'Error: ' + error.message;
                }}
            }});
        </script>
    </body>
    </html>
    """
    return Response(html, mimetype='text/html', status=200)

@app.route("/api/submit-test", methods=['POST'])
def api_submit_test():
    # Handle the AJAX form submission
    global current_test_id
    try:
        data = request.get_json()
        
        # Format the data according to the API specification
        configuration = {
            "test_id": data.get('testid'),
            "campaign_id": data.get('campaignid'),
            "environment_id": data.get('environmentid'),
            "sample_id": data.get('sampleid'),
            "operator": data.get('operator'),
            "sensors": {
                "throttle": {
                    "value": data.get('throttle')
                },
                "hold_time": {
                    "value": data.get('holdtime')
                },
                "battery": {
                    "id": data.get('batteryid')
                },
                "motor": {
                    "id": data.get('motorid')
                },
                "shroud": {
                    "id": data.get('shroudid')
                },
                "fan": {
                    "id": data.get('fanid')
                }
            },
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        logger.info(f"Test data formatted: {json.dumps(configuration)}")
        
        # Post test data to the HTTP API
        try:
            response = requests.post(
                test_api_url,
                json=configuration,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code not in [200, 201]:
                logger.warning(f"Test API returned status code {response.status_code}. Response: {response.text}")
                return jsonify({"error": f"Test API failed with status {response.status_code}"}), 400
            
            logger.info(f"Test data posted successfully. Response: {response.text}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to post test data to API: {str(e)}")
            return jsonify({"error": "Failed to submit test data"}), 500
        
        # Post ECU data to a different API
        try:
            ecu_data = {
                "test_id": data.get('testid'),
                "speeds": [data.get('throttle')],
                "ramp_delay": data.get('holdtime')
            }
            
            logger.info(f"ECU data formatted: {json.dumps(ecu_data)}")
            
            ecu_response = requests.post(
                ecu_api_url,
                json=ecu_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if ecu_response.status_code not in [200, 201]:
                logger.warning(f"ECU API returned status code {ecu_response.status_code}. Response: {ecu_response.text}")
                return jsonify({"error": f"ECU API failed with status {ecu_response.status_code}"}), 400
            
            logger.info(f"ECU data posted successfully. Response: {ecu_response.text}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to post ECU data to API: {str(e)}")
            return jsonify({"error": "Failed to submit ECU data"}), 500
        
        # Only increment test ID after both API calls succeed
        current_test_id = increment_test_id(current_test_id)
        
        return jsonify({"success": True, "next_test_id": current_test_id}), 200
    
    except Exception as e:
        logger.error(f"Error submitting test: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    serve(app, host="0.0.0.0", port=80)