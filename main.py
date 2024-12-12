import os
import time
import logging
import ntplib
from telegram_helper import TelegramNotifier
from tuya_api import TuyaGateController
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration for logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration from environment variables
ACCESS_ID = os.getenv('TUYA_ACCESS_ID')
ACCESS_KEY = os.getenv('TUYA_ACCESS_KEY')
API_ENDPOINT = 'https://openapi.tuyaeu.com'
MQ_ENDPOINT = 'wss://mqe.tuyaeu.com:8285/'
DEVICE_ID = os.getenv('TUYA_DEVICE_ID')
GATE_DEVICE_ID = os.getenv('TUYA_GATE_DEVICE_ID')
PING_HOSTNAME = os.getenv('PING_HOSTNAME')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def sync_time():
    """Function to synchronize time with NTP server"""
    try:
        ntp_client = ntplib.NTPClient()
        response = ntp_client.request('pool.ntp.org', version=3)
        os.system(f'date -s "@{int(response.tx_time)}"')
        logging.info("Time successfully synchronized")
    except Exception as e:
        logging.error(f"Time sync error: {str(e)}")

def ping(host):
    """Check host availability"""
    return os.system(f"ping -c 1 {host}") == 0

def main():
    # Time synchronization
    sync_time()
    
    # Initialize components
    telegram = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    tuya = TuyaGateController(API_ENDPOINT, ACCESS_ID, ACCESS_KEY, MQ_ENDPOINT)
    
    # Set callback for gate status changes
    def gate_status_changed(is_open):
        telegram.send_gate_status(is_open)
        logging.info(f"Gate status: {'OPEN' if is_open else 'CLOSED'}")
    
    tuya.set_gate_status_callback(gate_status_changed)
    
    # Start gate monitoring
    tuya.start_monitoring(GATE_DEVICE_ID)
    
    try:
        while True:
            if ping(PING_HOSTNAME):
                logging.info(f"{PING_HOSTNAME} is up!")
                tuya.set_device_state(DEVICE_ID, True)
            else:
                logging.info(f"{PING_HOSTNAME} is down!")
                tuya.set_device_state(DEVICE_ID, False)
            
            time.sleep(30)
    except KeyboardInterrupt:
        logging.info("Shutting down...")
        tuya.stop_monitoring()

if __name__ == "__main__":
    main() 