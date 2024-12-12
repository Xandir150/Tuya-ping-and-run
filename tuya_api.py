import logging
from tuya_connector import (
    TuyaOpenAPI,
    TuyaOpenPulsar,
    TuyaCloudPulsarTopic,
    TUYA_LOGGER,
)
import json

TUYA_LOGGER.setLevel(logging.ERROR)

class TuyaGateController:
    def __init__(self, api_endpoint, access_id, access_key, mq_endpoint):
        logging.info(f"Initializing TuyaGateController with access_id: {access_id}")
        self.openapi = TuyaOpenAPI(api_endpoint, access_id, access_key)
        self.openapi.connect()
        
        # Test API connection
        try:
            response = self.openapi.get("/v1.0/statistics-datas-survey", dict())
            logging.info("API connection test successful")
        except Exception as e:
            logging.error(f"API connection test failed: {e}")
        
        self.pulsar = TuyaOpenPulsar(
            access_id, 
            access_key, 
            mq_endpoint, 
            TuyaCloudPulsarTopic.PROD
        )
        
        self._gate_status_callback = None
        logging.info("TuyaGateController initialized")
        
    def set_gate_status_callback(self, callback):
        """Set callback for gate status changes"""
        self._gate_status_callback = callback
        
    def _message_handler(self, msg):
        try:
            logging.debug(f"Received Pulsar message: {msg}")
            msg_json = json.loads(msg)
            if msg_json.get("devId") == self.gate_device_id:
                logging.debug(f"Message is for target device: {self.gate_device_id}")
                for status in msg_json.get("status", []):
                    if status.get("code") == "doorcontact_state":
                        logging.info(f"Received gate status update: {status['value']}")
                        if self._gate_status_callback:
                            self._gate_status_callback(status['value'])
            else:
                logging.debug(f"Message for different device: {msg_json.get('devId')}")
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error: {e}")
            
    def start_monitoring(self, gate_device_id):
        """Start gate status monitoring"""
        logging.info(f"Starting monitoring for gate device: {gate_device_id}")
        self.gate_device_id = gate_device_id
        
        self.pulsar.add_message_listener(self._message_handler)
        self.pulsar.start()
        logging.info("Pulsar monitoring started")
        
    def stop_monitoring(self):
        """Stop monitoring"""
        self.pulsar.stop()
        
    def get_device_state(self, device_id):
        """Get current device state"""
        try:
            response = self.openapi.get(f'/v1.0/iot-03/devices/{device_id}/status')
            if response.get('success', False):
                status = response.get('result', [])
                for state in status:
                    if state.get('code') == 'switch_3':
                        return state.get('value', False)
        except Exception as e:
            logging.error(f"Error getting device state: {str(e)}")
        return None
        
    def set_device_state(self, device_id, new_state):
        """Set device state"""
        try:
            commands = {'commands': [{'code': 'switch_3', 'value': new_state}]}
            response = self.openapi.post(f'/v1.0/iot-03/devices/{device_id}/commands', commands)
            if response.get('success', False):
                logging.info(f"Device successfully {'enabled' if new_state else 'disabled'}")
                return True
        except Exception as e:
            logging.error(f"Error setting device state: {str(e)}")
        return False 