#!/usr/bin/env python3
import os
import time
import re
from collections import deque
import requests
import logging

# Configuration from environment
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')
ERROR_RATE_THRESHOLD = float(os.getenv('ERROR_RATE_THRESHOLD', 2.0))
WINDOW_SIZE = int(os.getenv('WINDOW_SIZE', 200))
ALERT_COOLDOWN_SEC = int(os.getenv('ALERT_COOLDOWN_SEC', 300))
LOG_FILE = '/var/log/nginx/access.log'

# State tracking
last_alert_time = 0
current_pool = None
error_window = deque(maxlen=WINDOW_SIZE)

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def send_slack_alert(message):
    """Send alert to Slack"""
    global last_alert_time
    
    current_time = time.time()
    if current_time - last_alert_time < ALERT_COOLDOWN_SEC:
        logging.info(f"Alert cooldown active, skipping: {message}")
        return False
    
    if not SLACK_WEBHOOK_URL:
        logging.error("SLACK_WEBHOOK_URL not configured")
        return False
    
    payload = {
        "text": f"🚨 *Blue/Green Alert*\n{message}",
        "username": "Blue-Green Monitor",
        "icon_emoji": ":whale:"
    }
    
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=5)
        if response.status_code == 200:
            last_alert_time = current_time
            logging.info(f"Alert sent to Slack: {message}")
            return True
        else:
            logging.error(f"Slack API error: {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"Failed to send Slack alert: {e}")
        return False

def parse_log_line(line):
    """Parse Nginx log line and extract fields"""
    try:
        # Parse key=value pairs from log format
        fields = {}
        for match in re.finditer(r'(\w+)=([^|]+)', line):
            fields[match.group(1)] = match.group(2)
        
        return {
            'pool': fields.get('pool', 'unknown'),
            'status': fields.get('status', '000'),
            'upstream_status': fields.get('upstream_status', '000'),
            'upstream_addr': fields.get('upstream_addr', 'unknown'),
            'timestamp': fields.get('time', ''),
            'is_error': fields.get('upstream_status', '000').startswith('5') or fields.get('status', '000').startswith('5')
        }
    except Exception as e:
        logging.debug(f"Failed to parse log line: {e}")
        return None

def monitor_logs_tail():
    """Monitor logs using tail-like approach (no seeking)"""
    global current_pool, error_window
    
    logging.info("Starting Nginx log monitor (tail mode)...")
    logging.info(f"Config: ERROR_RATE_THRESHOLD={ERROR_RATE_THRESHOLD}%, WINDOW_SIZE={WINDOW_SIZE}")
    
    buffer = ""
    
    while True:
        try:
            with open(LOG_FILE, 'r') as file:
                # Read any existing content first
                initial_content = file.read()
                if initial_content:
                    lines = initial_content.split('\n')
                    for line in lines:
                        if line.strip():
                            log_data = parse_log_line(line)
                            if log_data:
                                process_log_entry(log_data)
                
                # Now monitor for new lines
                while True:
                    chunk = file.read(4096)
                    if chunk:
                        buffer += chunk
                        lines = buffer.split('\n')
                        # Keep the last incomplete line in buffer
                        buffer = lines[-1]
                        
                        for line in lines[:-1]:
                            if line.strip():
                                log_data = parse_log_line(line)
                                if log_data:
                                    process_log_entry(log_data)
                    else:
                        time.sleep(0.1)
        except FileNotFoundError:
            logging.warning(f"Log file not found: {LOG_FILE}. Waiting...")
            time.sleep(5)
        except Exception as e:
            logging.error(f"Log monitoring error: {e}")
            time.sleep(5)

def process_log_entry(log_data):
    """Process a single log entry for alerts"""
    global current_pool, error_window
    
    pool = log_data['pool']
    is_error = log_data['is_error']
    
    # Track errors for rate calculation
    error_window.append(1 if is_error else 0)
    
    # Detect pool changes (failover)
    if current_pool and pool != current_pool and pool != 'unknown':
        message = f"Failover detected: *{current_pool}* → *{pool}*\n"
        message += f"Time: {log_data['timestamp']}\n"
        message += f"Upstream: {log_data['upstream_addr']}"
        if send_slack_alert(message):
            logging.info(f"Failover alert sent: {current_pool} → {pool}")
    
    current_pool = pool if pool != 'unknown' else current_pool
    
    # Check error rate threshold
    if len(error_window) >= WINDOW_SIZE // 2:  # Wait for reasonable sample size
        error_rate = (sum(error_window) / len(error_window)) * 100
        if error_rate > ERROR_RATE_THRESHOLD:
            message = f"High error rate detected: *{error_rate:.1f}%* (threshold: {ERROR_RATE_THRESHOLD}%)\n"
            message += f"Sample window: {len(error_window)} requests\n"
            message += f"Current pool: {current_pool}"
            if send_slack_alert(message):
                logging.info(f"Error rate alert sent: {error_rate:.1f}%")
                # Clear window after alert to avoid spam
                error_window.clear()

if __name__ == '__main__':
    setup_logging()
    # Wait a bit for Nginx to fully start
    time.sleep(10)
    monitor_logs_tail()
