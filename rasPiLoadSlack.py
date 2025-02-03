import psutil
import time
from slack_sdk import WebClient
from datetime import datetime
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

def get_cpu_temperature():
    try:
        # Try to read CPU temperature from thermal zone
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as temp_file:
            temp = float(temp_file.read()) / 1000.0
            return round(temp, 1)
    except:
        return None

def get_system_metrics():
    # Check if slackSignUp.py is running
    slack_signup_running = False
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower():
                cmdline = proc.info.get('cmdline', [])
                if any('slackSignUp.py' in cmd for cmd in cmdline if cmd):
                    slack_signup_running = True
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    metrics = {
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_percent': psutil.disk_usage('/').percent,
        'cpu_temp': get_cpu_temperature(),
        'slack_signup_running': slack_signup_running
    }
    return metrics

def format_slack_message(metrics):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"*System Metrics at {timestamp}*\n"
    message += f"🌡️ CPU Temperature: {metrics['cpu_temp']}°C\n" if metrics['cpu_temp'] else ""
    message += f"💻 CPU Usage: {metrics['cpu_percent']}%\n"
    message += f"🧠 Memory Usage: {metrics['memory_percent']}%\n"
    message += f"💾 Disk Usage: {metrics['disk_percent']}%\n"
    message += f"🤖 SlackSignUp.py: {'Running ✅' if metrics['slack_signup_running'] else 'Not Running ❌'}\n"
    
    # Add warning emojis for high values
    if metrics['cpu_percent'] > 80 or metrics['memory_percent'] > 80:
        message = "⚠️ *HIGH USAGE ALERT*\n" + message
    
    if not metrics['slack_signup_running']:
        message = "⚠️ *SLACK SIGNUP PROCESS NOT RUNNING*\n" + message
    
    return message

def wait_for_internet_connection():
    """Wait until internet connection is available"""
    logger = logging.getLogger(__name__)
    while True:
        try:
            # Try to connect to Slack's API endpoint
            import socket
            socket.create_connection(("slack.com", 443), timeout=5)
            logger.info("Internet connection established")
            return
        except OSError:
            logger.warning("No internet connection. Waiting 30 seconds...")
            time.sleep(30)

def monitor_system(token, channel_id, interval_minutes=2):
    """
    Monitor system metrics and send to Slack channel
    
    Args:
        token (str): Slack OAuth token
        channel_id (str): Target channel ID
        interval_minutes (int): Time between updates in minutes
    """
    client = WebClient(token=token)
    logger = logging.getLogger(__name__)
    
    # Wait for internet connection before starting
    wait_for_internet_connection()
    
    while True:
        try:
            # Get system metrics
            metrics = get_system_metrics()
            
            # Format and send message
            message = format_slack_message(metrics)
            client.chat_postMessage(
                channel=channel_id,
                text=message
            )
            logger.info("Metrics sent successfully")
            
        except Exception as e:
            logger.error(f"Error sending metrics: {str(e)}")
            # If connection fails, wait for internet before continuing
            wait_for_internet_connection()
        
        # Wait for next update
        time.sleep(interval_minutes * 60)

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('system_monitor.log'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)

    # Load environment variables
    USER_TOKEN = os.environ.get('SLACK_USER_TOKEN')
    CHANNEL_ID = os.environ.get('TEMP_CHANNEL_ID')
    
    if not USER_TOKEN or not CHANNEL_ID:
        logger.error("Please set SLACK_USER_TOKEN and CHANNEL_ID in .env file")
        raise ValueError("Please set SLACK_USER_TOKEN and CHANNEL_ID in .env file")

    # Start monitoring
    logger.info("Starting system monitoring")
    monitor_system(
        token=USER_TOKEN,
        channel_id=CHANNEL_ID,
        interval_minutes=5  # Send updates every 5 minutes
    )
