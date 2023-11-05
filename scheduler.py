import schedule
import time
import subprocess
import sqlite3
from datetime import datetime, timedelta

def run_subs_reports():
    subprocess.run(['python3', 'reports.py', 'sub'])
    print("File Sent...")

def run_ord_reports():
    subprocess.run(['python3', 'reports.py', 'ord'])
    print("File Sent...")


def check_subscribers():
    print("subs")
    subprocess.run(['python3', 'subscription_notice.py'])

# Schedule the task to run at 10PM
schedule.every().day.at("19:00").do(run_subs_reports)

# Schedule the task to run at 6AM
schedule.every().day.at("03:00").do(run_ord_reports)

# Schedule the task to run at 12PM
schedule.every().day.at("09:00").do(run_ord_reports)

# Schedule the task to run at 6AM
schedule.every().day.at("03:00").do(check_subscribers)

while True:
    schedule.run_pending()
    time.sleep(1)
