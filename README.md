# Raspberry Pi Load Monitor for Slack

A comprehensive monitoring system designed specifically for Raspberry Pi devices that need constant supervision. This tool is essential for:
- Maintaining 24/7 Raspberry Pi servers
- Preventing system failures through early warning
- Monitoring critical Pi-based services
- Remote temperature and resource management
- Automatic failure detection and notification

Features
- Real-time CPU, memory, and disk usage monitoring
- CPU temperature tracking with overheating alerts
- Process monitoring (specifically tracks mission-critical processes)
- Automatic failure detection and instant Slack alerts
- Network connectivity monitoring with downtime alerts
- Scheduled status updates for regular health checks
- Shutdown detection and notification

Components
1. System Metrics Monitor (rasPiLoadSlack.py)
   - Monitors and reports system vitals every 5 minutes
   - Tracks CPU temperature to prevent thermal throttling
   - Monitors specific process status (e.g., slackSignUp.py)
   - Reports memory leaks and disk space issues

2. Failure Detection (catchRasFaliure.py)
   - Monitors system journal for critical errors
   - Detects and reports unexpected shutdowns
   - Sends immediate alerts for hardware issues
   - Monitors for network connectivity problems
   - Tracks system service failures

Installation
1. Install dependencies:
   pip install -r requirements.txt

2. Create .env file with:
   SLACK_USER_TOKEN=xoxb-your-token
   CHANNEL_ID=metrics-channel-id
   FAIL_CHANNEL_ID=alerts-channel-id

Usage
Run the metrics monitor:
python3 rasPiLoadSlack.py

Run the failure detection:
python3 catchRasFaliure.py

Auto-start (using systemd):
1. Create service files in /etc/systemd/system/
2. Enable and start services:
   sudo systemctl enable raspi-load
   sudo systemctl start raspi-load

Alert Thresholds
- CPU Temperature: >80°C
- CPU Usage: >90% for 5 minutes
- Memory Usage: >90%
- Disk Space: <10% free
- Process Missing: Immediate alert
- Network: >30 seconds downtime

License
MIT License