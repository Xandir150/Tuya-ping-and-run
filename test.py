import os
import time
import logging
from tuya_connector import TuyaOpenAPI
import ntplib  # Add new import
from telegram_helper import TelegramNotifier

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

ACCESS_ID = os.getenv('TUYA_ACCESS_ID')
ACCESS_KEY = os.getenv('TUYA_ACCESS_KEY')
API_ENDPOINT = 'https://openapi.tuyaeu.com'
DEVICE_ID = os.getenv('TUYA_DEVICE_ID')
GATE_DEVICE_ID = os.getenv('TUYA_GATE_DEVICE_ID')  # Changed to environment variable

hostname = os.getenv('PING_HOSTNAME')
# hostname = "192.168.1.74"

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Initialize Telegram notifier
telegram = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)

# Add variable to track previous gate state
previous_gate_state = None

def sync_time():
    """Function to synchronize time with NTP server"""
    try:
        ntp_client = ntplib.NTPClient()
        response = ntp_client.request('pool.ntp.org', version=3)
        os.system(f'date -s "@{int(response.tx_time)}"')
        logging.info("Time successfully synchronized")
    except Exception as e:
        logging.error(f"Time sync error: {str(e)}")

# Add time synchronization before API connection
sync_time()

# Setup Tuya OpenAPI connection
openapi = TuyaOpenAPI(API_ENDPOINT, ACCESS_ID, ACCESS_KEY)
openapi.connect()

def get_device_state():
    """Function to get current device state"""
    try:
        response = openapi.get(f'/v1.0/iot-03/devices/{DEVICE_ID}/status')
        if response.get('success', False):
            status = response.get('result', [])
            for state in status:
                if state.get('code') == 'switch_3':
                    return state.get('value', False)
    except Exception as e:
        logging.error(f"""
╔══════════════════════════════════════════════════════════════════════════════
║ ERROR GETTING DEVICE STATE: {str(e)}
╚══════════════════════════════════════════════════════════════════════════════""")
    return None

# Проверка начального статуса
initial_status = get_device_state()
if initial_status is not None:
    logging.info(f"Initial device state: {'ON' if initial_status else 'OFF'}")
else:
    logging.error("Failed to get initial device state")

def set_device_state(new_state):
    """Function to set device state"""
    try:
        current_state = get_device_state()
        
        # If failed to get current state or it differs from desired
        if current_state is None or current_state != new_state:
            commands = {'commands': [{'code': 'switch_3', 'value': new_state}]}
            response = openapi.post(f'/v1.0/iot-03/devices/{DEVICE_ID}/commands', commands)
            if response.get('success', False):
                logging.info(f"Successfully set device to {'ON' if new_state else 'OFF'}")
            else:
                logging.error(f"""
╔══════════════════════════════════════════════════════════════════════════════
║ FAILED TO SET DEVICE STATE. Error: {response.get('msg', 'Unknown error')}
╚══════════════════════════════════════════════════════════════════════════════""")
        else:
            logging.info(f"Device already in desired state: {'ON' if new_state else 'OFF'}")
    except Exception as e:
        logging.error(f"""
╔══════════════════════════════════════════════════════════════════════════════
║ UNEXPECTED ERROR: {str(e)}
╚══════════════════════════════════════════════════════════════════════════════""")

def ping(host):
    """Function to perform ping"""
    return os.system(f"ping -c 1 {host}") == 0

def get_gate_status():
    """Function to get gate device status
    Returns:
        - True: Gate is open/moving
        - False: Gate is closed
        - None: Error getting status
    """
    try:
        response = openapi.get(f'/v1.0/iot-03/devices/{GATE_DEVICE_ID}/status')
        if response.get('success', False):
            status = response.get('result', [])
            for state in status:
                if state.get('code') == 'doorcontact_state':
                    is_open = state.get('value', False)
                    status_text = "OPEN/MOVING" if is_open else "CLOSED"
                    logging.info(f"Gate is currently {status_text}")
                    return is_open
    except Exception as e:
        logging.error(f"""
╔══════════════════════════════════════════════════════════════════════════════
║ ERROR GETTING GATE STATUS: {str(e)}
╚══════════════════════════════════════════════════════════════════════════════""")
    return None

def main():
    global previous_gate_state
    
    while True:
        # Check gate status first
        gate_status = get_gate_status()
        logging.info("Checking gate status...")
        
        # Send Telegram notification if gate status changed
        if gate_status is not None and gate_status != previous_gate_state:
            telegram.send_gate_status(gate_status)
            previous_gate_state = gate_status
        
        # Check ping as before
        if ping(hostname):
            logging.info(f"{hostname} is up!")
            set_device_state(True)  # Device ON
        else:
            logging.info(f"{hostname} is down!")
            set_device_state(False)  # Device OFF

        time.sleep(30)  # Wait before next check

if __name__ == "__main__":
    main()