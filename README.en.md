# nof1.ai Alpha Arena AI Trading Monitor

This project monitors AI large models' crypto trading on Alpha Arena and sends notifications when changes are detected. It also provides a simple Flask web page to display current positions across models.

- Disclaimer: For learning and research only. No investment advice.

## Features

- Scheduled fetch: fetch positions every minute
- Change detection: analyze position diffs and detect trading actions
- Notifications: WeChat Work bot and Telegram (optional; send if configured)
- Positions web page: built-in Flask app showing positions in a table; auto refresh every 15s; language switch (zh/en)
- Detailed logs and flexible configuration via environment variables

## Installation

```bash
# Activate virtualenv
source venv/bin/activate

# Install deps
pip install -r requirements.txt
```

## Configuration (.env)

```env
# WeChat Work bot webhook (optional)
WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_WEBHOOK_KEY

# Telegram (optional; enabled if both are present)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
# Telegram proxy, default 127.0.0.1:7890
TELEGRAM_PROXY=127.0.0.1:7890

# Models to monitor (comma separated). Empty = all models
MONITORED_MODELS=

# API base
API_URL=https://nof1.ai/api

# Save history to data/ directory
SAVE_HISTORY_DATA=False
```

## Usage

### Start monitoring

```bash
source venv/bin/activate
python main.py
```

### Positions web page (Flask)

```bash
source venv/bin/activate
python web.py  # default port 5010
# zh: http://127.0.0.1:5010/
# en: http://127.0.0.1:5010/?lang=en (toggle on page)
```

### Test notification

```bash
python main.py --test
```

## How it works

- Fetch positions via API every minute
- Compare with previous data in last.json
- Generate trade events
- Send notifications to configured channels (WeChat, Telegram)
- Update last.json

## License

MIT

