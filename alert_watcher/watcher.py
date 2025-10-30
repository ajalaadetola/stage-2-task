#!/usr/bin/env python3
import os
import time
import requests
import logging
from collections import deque

# ==============================
# 🔧 Configuration
# ==============================
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')
ERROR_RATE_THRESHOLD = float(os.getenv('ERROR_RATE_THRESHOLD', 2.0))
WINDOW_SIZE = int(os.getenv('WINDOW_SIZE', 200))
ALERT_COOLDOWN_SEC = int(os.getenv('ALERT_COOLDOWN_SEC', 300))
NGINX_HOST = os.getenv('NGINX_HOST', 'nginx')
NGINX_PORT = int(os.getenv('NGINX_PORT', 8080))

# ==============================
# 🧠 State
# ==============================
last_alert_time = 0
current_pool = "blue"
error_window = deque(maxlen=WINDOW_SIZE)
request_count = 0


# ==============================
# 📝 Logging Setup
# ==============================
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


# ==============================
# 🚨 Slack Alerts
# ==============================
def send_slack_alert(message, alert_type="failover"):
    global last_alert_time
    current_time = time.time()

    if current_time - last_alert_time < ALERT_COOLDOWN_SEC:
        logging.info(f"Alert cooldown active, skipping: {message}")
        return False

    if not SLACK_WEBHOOK_URL:
        logging.error("No SLACK_WEBHOOK_URL configured")
        return False

    if alert_type == "failover":
        color = "warning"
        title = "🚨 Failover Detected"
    else:
        color = "danger"
        title = "⚠️ High Error Rate"

    payload = {
        "text": f"{title}\n{message}",
        "username": "alert-WATCHER",
        "icon_emoji": ":whale:",
        "attachments": [
            {
                "color": color,
                "fields": [
                    {"title": "Alert Type", "value": title, "short": True},
                    {"title": "Time", "value": time.strftime('%Y-%m-%d %H:%M:%S'), "short": True},
                    {"title": "Current Pool", "value": current_pool, "short": True},
                    {"title": "Requests Monitored", "value": str(request_count), "short": True}
                ],
                "footer": "Blue/Green Deployment Monitor",
                "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
                "ts": time.time()
            }
        ]
    }

    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
        if response.status_code == 200:
            last_alert_time = current_time
            logging.info(f"✅ Alert sent: {message}")
            return True
        else:
            logging.error(f"Webhook error {response.status_code}: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        logging.error(f"Network error sending alert: {e}")
        return False


# ==============================
# 👀 Monitor Function
# ==============================
def monitor_services():
    global current_pool, error_window, request_count

    nginx_url = f"http://{NGINX_HOST}:{NGINX_PORT}/version"
    logging.info("🚀 Starting HTTP-based Blue/Green Monitor")
    logging.info(f"Config: ERROR_RATE_THRESHOLD={ERROR_RATE_THRESHOLD}%, WINDOW_SIZE={WINDOW_SIZE}")
    logging.info(f"Nginx target: {nginx_url}")

    # Test Slack webhook
    logging.info("Testing webhook configuration...")
    try:
        test_response = requests.post(SLACK_WEBHOOK_URL, json={"text": "🔧 Watcher started successfully!"})
        if test_response.status_code == 200:
            logging.info("✅ Slack webhook verified successfully")
        else:
            logging.warning(f"⚠️ Slack webhook test returned {test_response.status_code}")
    except Exception as e:
        logging.warning(f"⚠️ Slack webhook test failed: {e}")

    # Main monitoring loop
    while True:
        try:
            response = requests.get(nginx_url, timeout=5)
            new_pool = response.headers.get('X-App-Pool', 'unknown')
            status_code = response.status_code
            is_error = status_code >= 500

            request_count += 1
            error_window.append(1 if is_error else 0)

            # Failover detection
            if current_pool and new_pool != current_pool and new_pool != 'unknown':
                message = f"Traffic automatically switched from *{current_pool}* → *{new_pool}*.\nAll client requests now served by `{new_pool}` pool."
                send_slack_alert(message, "failover")
                logging.info(f"📊 Failover detected: {current_pool} → {new_pool}")
                current_pool = new_pool

            # Error rate detection
            if len(error_window) >= 10:
                error_rate = (sum(error_window) / len(error_window)) * 100
                if error_rate > ERROR_RATE_THRESHOLD:
                    message = f"Error rate exceeded threshold: *{error_rate:.1f}%* (limit {ERROR_RATE_THRESHOLD}%)"
                    send_slack_alert(message, "error_rate")
                    logging.info(f"⚠️ Error rate alert: {error_rate:.1f}%")
                    error_window.clear()

            # Periodic log
            if request_count % 20 == 0:
                error_rate = (sum(error_window) / len(error_window)) * 100 if error_window else 0
                logging.info(f"📈 {request_count} reqs | Pool: {current_pool} | Error rate: {error_rate:.1f}%")

            time.sleep(3)

        except requests.exceptions.RequestException as e:
            logging.warning(f"🌐 Request failed: {e}")
            error_window.append(1)
            time.sleep(5)
        except Exception as e:
            logging.error(f"💥 Monitor error: {e}")
            time.sleep(10)


# ==============================
# ▶️ Entrypoint
# ==============================
if __name__ == '__main__':
    setup_logging()
    logging.info("🔧 Initializing Blue/Green Alert Monitor...")
    time.sleep(15)
    monitor_services()
