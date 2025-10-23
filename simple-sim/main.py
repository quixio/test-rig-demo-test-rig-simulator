import requests
from datetime import datetime
import time
import traceback
import json


class PostResponse:
    def __init__(self, message, status_code = -1):
        self.status_code = status_code
        self.message = message


def strip_trailing_slash(path):
    """Remove a single trailing forward slash if it exists."""
    if path.endswith('/'):
        return path[:-1]
    return path


def publish_test_configuration(api_url, data):
    success = False

    try:
        configuration = {
            "test_id": data["test_id"],
            "campaign_id": data["campaign_id"],
            "environment_id": data["environment_id"],
            "sample_id": data["sample_id"],
            "operator": data["operator"],
            "sensors":{
                "throttle": {
                    "value": data["throttle"]
                },
                "hold_time": {
                    "value": data["hold_time"]
                },
                "battery": {
                    "id": data["bat_id"]
                    # "capacity_mah": data["bat_mah"],
                    # "cells": data["bat_cells"],
                    # "manufacturer": data["bat_manuf"],
                    # "partnumber": data["bat_part_no"],
                    # "connector": data["bat_connector_type"],
                },
                "motor":{
                    "id": data["motor_id"]
                    # "kv": data["motor_kv"],
                    # "diameter": data["motor_dia"]
                },
                "shroud":{
                    "id": data["shroud_id"]
                    # "diameter": data["shroud_dia"],
                    # "material": data["shroud_material"]
                },
                "fan":{
                    "id": data["fan_id"]
                    # "diameter": data["fan_dia"],
                    # "blades": data["fan_blade_count"],
                    # "material": data["fan_material"]
                }
            }
        }

        response = requests.post(f"{api_url}", json=configuration)
        # return response
        return PostResponse(response.text, response.status_code)

    except Exception as e:
        # Create a mock response object for error cases
        class ErrorResponse:
            def __init__(self, error_msg):
                self.status_code = -1
                self.message = error_msg
           
            def json(self):
                return {"error": self.error_message}
       
        return ErrorResponse(f'publish_test_configuration ERROR: {e}')

def start_test( ecu_api_url,
                configuration_service_api,
                test_id,
                campaign_id,
                sample_id,
                environment_id,
                operator,
                bat_id,
                motor_id,
                shroud_id,
                fan_id,
                throttle,
                hold_time,
                debug_on):
   
    # 1. publish config
    # 2. start test

    try:
        throttle = int(throttle)
        hold_time = int(hold_time)

        config_data = {
                "test_id": test_id,
                "campaign_id": campaign_id,
                "sample_id": sample_id,
                "environment_id": environment_id,
                "operator": operator,
                "bat_id": bat_id,
                "motor_id": motor_id,
                "shroud_id": shroud_id,
                "fan_id": fan_id,
                "throttle": throttle,
                "hold_time": hold_time
            }
           
        configuration_service_api = strip_trailing_slash(configuration_service_api)
        cfg_result = publish_test_configuration(configuration_service_api, config_data)

        if cfg_result.status_code != 200:
            raise Exception("publish_test_configuration failed: " + cfg_result.message)

        if throttle > 1:
            thr = throttle / 100
        else:
           raise Exception("Throttle must be between 0 and 100")

        ecu_data = {
            "test_id": test_id,
            "speeds": [thr],
            "ramp_delay": hold_time
        }
       
        # return f'{cfg_result.status_code} -- {cfg_result.message}'
        ecu_api_url = strip_trailing_slash(ecu_api_url)
        ecu_result = requests.post(f"{ecu_api_url}", json=ecu_data)
       
        test_results = {
            "ECU_message": str(ecu_result.json()),
            "ECU_status_code": str(ecu_result.status_code),
            "Config_message": str(cfg_result.message),
            "Config_status_code": str(cfg_result.status_code),
        }

        return json.dumps(test_results)

    except Exception as e:
        print(traceback.format_exc())
        return f'start_test ERROR: {e}'
    finally:
        print(debug_on)
        counter = 0
        seconds_to_show_debug = 2
        while(debug_on and counter < seconds_to_show_debug):
            print("waiting for test to finish")
            time.sleep(1)
            counter += 1