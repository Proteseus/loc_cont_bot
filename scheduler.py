import schedule
import time
import subprocess
import sqlite3
from datetime import datetime, timedelta

def run_reports():
    subprocess.run(['python3', 'reports.py'])
    print("File Sent...")


def check_subscribers():
    print("subs")
    subprocess.run(['python3', 'subscription_notice.py'])

# Schedule the task to run at midnight
schedule.every().day.at("21:00").do(run_reports)

# Schedule the task to run at 6AM
schedule.every().day.at("13:07:00").do(check_subscribers)

while True:
    schedule.run_pending()
    time.sleep(1)
