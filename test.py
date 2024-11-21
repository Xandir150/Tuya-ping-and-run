import os
import time
import logging
from tuya_connector import TuyaOpenAPI

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')



ACCESS_ID = os.getenv('TUYA_ACCESS_ID')
ACCESS_KEY = os.getenv('TUYA_ACCESS_KEY')
API_ENDPOINT = 'https://openapi.tuyaeu.com'
DEVICE_ID = os.getenv('TUYA_DEVICE_ID')

hostname = os.getenv('PING_HOSTNAME')
# hostname = "192.168.1.74"

# Настройка соединения с Tuya OpenAPI
openapi = TuyaOpenAPI(API_ENDPOINT, ACCESS_ID, ACCESS_KEY)
openapi.connect()

def get_device_state():
    """Функция для получения текущего состояния устройства"""
    try:
        response = openapi.get(f'/v1.0/iot-03/devices/{DEVICE_ID}/status')
        logging.info(f"Current device status: {response}")
        if response.get('success', False):
            status = response.get('result', [])
            for state in status:
                if state.get('code') == 'switch_3':
                    return state.get('value', False)
    except Exception as e:
        logging.error(f"Error getting device state: {str(e)}")
    return None

# Проверка начального статуса
initial_status = get_device_state()
if initial_status is not None:
    logging.info(f"Initial device state: {'ON' if initial_status else 'OFF'}")
else:
    logging.error("Failed to get initial device state")

def set_device_state(new_state):
    """Функция для установки состояния устройства"""
    try:
        current_state = get_device_state()
        
        # Если не удалось получить текущее состояние или оно отличается от желаемого
        if current_state is None or current_state != new_state:
            commands = {'commands': [{'code': 'switch_3', 'value': new_state}]}
            response = openapi.post(f'/v1.0/iot-03/devices/{DEVICE_ID}/commands', commands)
            logging.info(f"API Response: {response}")
            if response.get('success', False):
                logging.info(f"Successfully set device to {'ON' if new_state else 'OFF'}")
            else:
                logging.error(f"Failed to set device state. Error: {response.get('msg', 'Unknown error')}")
        else:
            logging.info(f"Device already in desired state: {'ON' if new_state else 'OFF'}")
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")

def ping(host):
    """Функция для выполнения пинга"""
    return os.system(f"ping -c 1 {host}") == 0

def main():
    while True:
        if ping(hostname):
            logging.info(f"{hostname} is up!")
            set_device_state(True)  # Устройство включено
        else:
            logging.info(f"{hostname} is down!")
            set_device_state(False)  # Устройство выключено

        time.sleep(30)  # Ожидание перед следующей проверкой

if __name__ == "__main__":
    main()