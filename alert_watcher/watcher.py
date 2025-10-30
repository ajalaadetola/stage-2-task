#!/usr/bin/env python3
import os
import time
import requests
import logging
from collections import deque

# Configuration
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')
ERROR_RATE_THRESHOLD = float(os.getenv('ERROR_RATE_THRESHOLD', 2.0))
WINDOW_SIZE = int(os.getenv('WINDOW_SIZE', 200))
ALERT_COOLDOWN_SEC = int(os.getenv('ALERT_COOLDOWN_SEC', 300))

# State
last_alert_time = 0
current_pool = "blue"  # Start with default
error_window = deque(maxlen=WINDOW_SIZE)
request_count = 0

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def send_slack_alert(message, alert_type="failover"):
    global last_alert_time
    current_time = time.time()
    
    if current_time - last_alert_time < ALERT_COOLDOWN_SEC:
        logging.info(f"Alert cooldown active, skipping: {message}")
        return False
    
    if not SLACK_WEBHOOK_URL:
        logging.error("No SLACK_WEBHOOK_URL configured")
        return False
    
    # Enhanced message format with better styling
    if alert_type == "failover":
        color = "warning"
        title = "🚨 Failover Detected"
        icon = ":arrows_counterclockwise:"
    else:  # error_rate
        color = "danger" 
        title = "⚠️ High Error Rate"
        icon = ":x:"
    
    payload = {
        "text": f"{title}\n{message}",
        "username": "alert-WATCHER",
        "icon_emoji": ":whale:",
        "attachments": [
            {
                "color": color,
                "fields": [
                    {
                        "title": "Alert Type",
                        "value": "Failover" if alert_type == "failover" else "High Error Rate",
                        "short": True
                    },
                    {
                        "title": "Time", 
                        "value": time.strftime('%Y-%m-%d %H:%M:%S'),
                        "short": True
                    },
                    {
                        "title": "Current Pool",
                        "value": current_pool,
                        "short": True
                    },
                    {
                        "title": "Requests Monitored",
                        "value": str(request_count),
                        "short": True
                    }
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
    except Exception as e:
        logging.error(f"Unexpected error sending alert: {e}")
        return False

def monitor_services():
    """Monitor services by making HTTP requests directly"""
    global current_pool, error_window, request_count
    
    logging.info("🚀 Starting HTTP-based Blue/Green Monitor")
    logging.info(f"Config: ERROR_RATE_THRESHOLD={ERROR_RATE_THRESHOLD}%, WINDOW_SIZE={WINDOW_SIZE}")
    
    # Initial webhook test
    logging.info("Testing webhook configuration...")
    test_payload = {
        "text": "🔧 *Blue/Green Monitor Started Successfully*\nSystem is now monitoring for failovers and errors.",
        "username": "Blue-Green Monitor"
    }
    try:
        test_response = requests.post(SLACK_WEBHOOK_URL, json=test_payload, timeout=5)
        if test_response.status_code == 200:
            logging.info("✅ Webhook test successful")
        else:
            logging.warning(f"⚠️ Webhook test returned {test_response.status_code}")
    except Exception as e:
        logging.warning(f"⚠️ Webhook test failed: {e}")
    
    while True:
        try:
            # Monitor through Nginx (main endpoint)
            response = requests.get("http://nginx:8080/version", timeout=5)
            new_pool = response.headers.get('X-App-Pool', 'unknown')
            status_code = response.status_code
            is_error = status_code >= 500
            
            request_count += 1
            
            # Track errors
            error_window.append(1 if is_error else 0)
            
            # Detect failover
            if current_pool and new_pool != current_pool and new_pool != 'unknown':
                message = f"Traffic automatically switched from *{current_pool}* to *{new_pool}*\n"
                message += f"All client requests are now being served by the {new_pool} pool"
                if send_slack_alert(message, "failover"):
                    logging.info(f"📊 Failover detected: {current_pool} → {new_pool}")
                else:
                    logging.warning(f"Failed to send failover alert: {current_pool} → {new_pool}")
            
            current_pool = new_pool
            
            # Check error rate
            if len(error_window) >= 10:  # Minimum sample size
                error_rate = (sum(error_window) / len(error_window)) * 100
                if error_rate > ERROR_RATE_THRESHOLD:
                    message = f"Error rate has exceeded threshold: *{error_rate:.1f}%* (threshold: {ERROR_RATE_THRESHOLD}%)\n"
                    message += f"Sample size: {len(error_window)} requests\n"
                    message += f"Immediate investigation recommended"
                    if send_slack_alert(message, "error_rate"):
                        logging.info(f"⚠️ Error rate alert sent: {error_rate:.1f}%")
                        error_window.clear()  # Reset after alert
            
            # Log status periodically
            if request_count % 20 == 0:
                error_rate = (sum(error_window) / len(error_window)) * 100 if error_window else 0
                logging.info(f"📈 Status: {request_count} requests, Pool: {current_pool}, Error rate: {error_rate:.1f}%")
            
            time.sleep(3)  # Check every 3 seconds
            
        except requests.exceptions.RequestException as e:
            logging.warning(f"🌐 Request failed: {e}")
            error_window.append(1)  # Count connection errors as failures
            time.sleep(5)
        except Exception as e:
            logging.error(f"💥 Monitor error: {e}")
            time.sleep(10)

if __name__ == '__main__':
    setup_logging()
    logging.info("🔧 Initializing Blue/Green Alert Monitor...")
    time.sleep(15)  # Wait for all services to start
    monitor_services()
