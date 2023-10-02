import schedule
import time
import subprocess

def run_reports():
    subprocess.run(['python3', 'reports.py'])
    print("File Sent...")

# Schedule the task to run at midnight
schedule.every().day.at("21:00").do(run_reports)

# Schedule the task to run every 5 minutes
# schedule.every(2).minutes.do(run_reports)

while True:
    schedule.run_pending()
    time.sleep(1)
