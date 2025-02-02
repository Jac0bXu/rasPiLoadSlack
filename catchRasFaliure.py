import os
import time
import subprocess
import systemd.journal
from slack_sdk import WebClient
from datetime import datetime
import logging
from dotenv import load_dotenv

# Load environment variables with absolute path
load_dotenv('/home/pol4/rasPiLoadSlack/.env')

def setup_slack_client():
    """Initialize Slack client with error handling"""
    token = os.environ.get('SLACK_USER_TOKEN')
    if not token:
        raise ValueError("SLACK_USER_TOKEN not found in environment variables")
    return WebClient(token=token)

def send_slack_alert(client, channel_id, message, severity="error"):
    """Send formatted alert to Slack"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Choose emoji based on severity
    emoji_map = {
        "error": "🚨",
        "warning": "⚠️",
        "info": "ℹ️",
        "shutdown": "🔴"
    }
    emoji = emoji_map.get(severity, "⚠️")
    
    formatted_message = f"{emoji} *System Alert* {emoji}\n"
    formatted_message += f"*Timestamp:* {timestamp}\n"
    formatted_message += f"*Type:* {severity.upper()}\n"
    formatted_message += f"*Message:* {message}\n"

    try:
        client.chat_postMessage(
            channel=channel_id,
            text=formatted_message
        )
        logging.info(f"Alert sent to Slack: {severity} - {message}")
    except Exception as e:
        logging.error(f"Failed to send Slack message: {str(e)}")

def monitor_system_events():
    """Monitor system events and logs for critical issues"""
    client = setup_slack_client()
    channel_id = os.environ.get('FAIL_CHANNEL_ID')
    
    if not channel_id:
        raise ValueError("CHANNEL_ID not found in environment variables")

    # Initialize systemd journal reader
    j = systemd.journal.Reader()
    j.this_boot()  # Only get messages from this boot
    j.log_level(systemd.journal.LOG_ERR)  # Only get error messages and above

    # Get the current journal cursor
    j.seek_tail()
    j.get_previous()
    
    while True:
        try:
            # Check for system shutdown signals
            if os.path.exists("/run/systemd/shutdown/scheduled"):
                with open("/run/systemd/shutdown/scheduled") as f:
                    shutdown_info = f.read()
                send_slack_alert(
                    client,
                    channel_id,
                    f"System shutdown scheduled:\n{shutdown_info}",
                    "shutdown"
                )

            # Monitor journal for new error messages
            for entry in j:
                message = entry.get('MESSAGE', 'No message content')
                unit = entry.get('_SYSTEMD_UNIT', 'System')
                
                # Filter and send critical errors
                if any(critical_term in message.lower() for critical_term in 
                    ['error', 'critical', 'failure', 'failed', 'crash']):
                    alert_message = f"Unit: {unit}\nDetails: {message}"
                    send_slack_alert(client, channel_id, alert_message, "error")

            # Check system temperature
            try:
                with open("/sys/class/thermal/thermal_zone0/temp", "r") as temp_file:
                    temp = float(temp_file.read()) / 1000.0
                    if temp > 80:  # Temperature threshold (80°C)
                        send_slack_alert(
                            client,
                            channel_id,
                            f"High CPU temperature detected: {temp}°C",
                            "warning"
                        )
            except:
                pass  # Temperature monitoring not available on all systems

            # Check disk space
            disk_usage = subprocess.check_output(['df', '-h', '/']).decode()
            if any(line.split()[-2].rstrip('%').isdigit() and 
                  int(line.split()[-2].rstrip('%')) > 90 
                  for line in disk_usage.split('\n')[1:] if line):
                send_slack_alert(
                    client,
                    channel_id,
                    f"Critical disk space usage:\n{disk_usage}",
                    "warning"
                )

        except Exception as e:
            logging.error(f"Monitoring error: {str(e)}")
            try:
                send_slack_alert(
                    client,
                    channel_id,
                    f"Monitoring script error: {str(e)}",
                    "error"
                )
            except:
                pass

        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('system_alerts.log'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)

    logger.info("Starting system alert monitoring")
    monitor_system_events()
