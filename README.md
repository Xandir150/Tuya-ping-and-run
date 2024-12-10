# Smart Home Device Monitor

This service monitors the status of smart home devices (gates and switches) via Tuya API and provides status notifications through Telegram.

## Features

- Monitors gate status (open/closed)
- Sends silent Telegram notifications when gate status changes
- Pins latest status message in Telegram
- Monitors network device availability through ping
- Controls switch based on ping results
- Automatic time synchronization via NTP

## Requirements

- Docker
- Docker Compose
- Tuya IoT Platform account
- Telegram Bot Token

## Configuration

Copy `docker-compose.template.yml` to `docker-compose.yml` and fill in your values: 

### Environment Variables

- `TUYA_ACCESS_ID`: Tuya IoT Platform Access ID
- `TUYA_ACCESS_KEY`: Tuya IoT Platform Access Key
- `TUYA_DEVICE_ID`: ID of the Tuya switch device
- `TUYA_GATE_DEVICE_ID`: ID of the Tuya gate sensor
- `PING_HOSTNAME`: IP address to monitor (controls switch state)
- `TELEGRAM_BOT_TOKEN`: Telegram Bot API token
- `TELEGRAM_CHAT_ID`: Telegram chat ID for notifications

## Installation

1. Clone the repository
2. Copy configuration file:
   ```bash
   cp docker-compose.template.yml docker-compose.yml
   ```
3. Edit `docker-compose.yml` with your values
4. Start the service:
   ```bash
   docker-compose up -d
   ```

## Monitoring

View logs:
```bash
docker-compose logs
```

## Telegram Notifications

The service will send and pin messages in the following format:
- 🟢 Closed - when gate is closed
- 🔴 Open - when gate is open/moving

Messages are sent silently (no notification sound) and automatically pinned in the chat.

## License

MIT