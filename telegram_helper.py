import requests
import logging
from datetime import datetime

class TelegramNotifier:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        # If chat_id starts with @, it's a channel username
        # If it's a number (as string), it's a chat ID
        # Otherwise, add @ for username
        if isinstance(chat_id, str):
            if chat_id.startswith('@'):
                self.chat_id = chat_id
            elif chat_id.replace('-', '').isdigit():  # Check if it's a number (can be negative)
                self.chat_id = chat_id
            else:
                self.chat_id = f"@{chat_id}"
        else:
            self.chat_id = str(chat_id)  # If number was passed
        
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.last_message_id = None
        self.last_message_date = None

    def send_gate_status(self, is_open):
        """
        Send or edit gate status message
        Args:
            is_open (bool): True if gate is open, False if closed
        """
        try:
            current_date = datetime.now().date()
            message_text = "🔴 Открыто" if is_open else "🟢 Закрыто"

            # If it's a new day or no message exists, send new message
            if not self.last_message_id or (self.last_message_date and self.last_message_date != current_date):
                response = requests.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": message_text,
                        "disable_notification": True
                    }
                ).json()

                if response.get("ok"):
                    new_message_id = response["result"]["message_id"]
                    
                    # Pin new message silently and suppress pin message
                    requests.post(
                        f"{self.base_url}/pinChatMessage",
                        json={
                            "chat_id": self.chat_id,
                            "message_id": new_message_id,
                            "disable_notification": True
                        }
                    )
                    
                    # Delete pin notification message
                    try:
                        requests.post(
                            f"{self.base_url}/deleteMessage",
                            json={
                                "chat_id": self.chat_id,
                                "message_id": new_message_id + 1
                            }
                        )
                    except Exception:
                        pass

                    # Delete previous message if exists
                    if self.last_message_id:
                        try:
                            requests.post(
                                f"{self.base_url}/deleteMessage",
                                json={
                                    "chat_id": self.chat_id,
                                    "message_id": self.last_message_id
                                }
                            )
                        except Exception:
                            pass
                    
                    self.last_message_id = new_message_id
                    self.last_message_date = current_date
                else:
                    logging.error(f"""
╔══════════════════════════════════════════════════════════════════════════════
║ TELEGRAM ERROR: Failed to send message: {response.get('description')}
╚══════════════════════════════════════════════════════════════════════════════""")

            # If message exists and it's the same day, edit existing message
            else:
                response = requests.post(
                    f"{self.base_url}/editMessageText",
                    json={
                        "chat_id": self.chat_id,
                        "message_id": self.last_message_id,
                        "text": message_text
                    }
                ).json()

                if not response.get("ok"):
                    logging.error(f"""
╔══════════════════════���═══════════════════════════════════════════════════════
║ TELEGRAM ERROR: Failed to edit message: {response.get('description')}
╚══════════════════════════════════════════════════════════════════════════════""")

        except Exception as e:
            logging.error(f"""
╔══════════════════════════════════════════════════════════════════════════════
║ TELEGRAM ERROR: {str(e)}
╚══════════════════════════════════════════════════════════════════════════════""") 