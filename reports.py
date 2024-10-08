import sys
import os
import csv
import glob
import time
import asyncio
import logging
from datetime import datetime, timedelta

from db import create_user_order, add_order, session
from model import Order, Trackable

from telegram import Bot
from telegram.ext import Updater
import telegram

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

def delete_old_csv_files():
    files = glob.glob('*.csv')
    for file in files:
        if os.stat(file).st_mtime < time.time() - 7 * 24 * 60 * 60:
            os.remove(file)

def iterate_subscribers(csv_file_path_subs):
    delete_old_csv_files()
    orders = session.query(Order).all()
    data = []
    for order in orders:
        order_data = []
        for column in Order.__table__.columns:
            order_data.append(str(getattr(order, column.name)))
        data.append(order_data)
    
    # Write the data to a CSV file
    with open(csv_file_path_subs, 'w', newline='') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow([column.name for column in Order.__table__.columns])
        csv_writer.writerows(data)

def iterate_orders(csv_file_path_orders):
    delete_old_csv_files()
    # orders = session.query(Trackable).all()
    
    now = datetime.now()
    start_time = datetime(now.year, now.month, now.day, 9, 0, 0) - timedelta(days=1)
    end_time = datetime(now.year, now.month, now.day, 9, 0, 0)
    orders = session.query(Trackable).filter(Trackable.date >= start_time, Trackable.date <= end_time)
    
    
    data = []
    for order in orders:
        order_data = []
        for column in Trackable.__table__.columns:
            order_data.append(str(getattr(order, column.name)))
        data.append(order_data)
    
    # Write the data to a CSV file
    with open(csv_file_path_orders, 'w', newline='') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow([column.name for column in Trackable.__table__.columns])
        csv_writer.writerows(data)

def iterate_all_orders(csv_file_path_orders):
    delete_old_csv_files()
    orders = session.query(Trackable).all()
    
    data = []
    for order in orders:
        order_data = []
        for column in Trackable.__table__.columns:
            order_data.append(str(getattr(order, column.name)))
        data.append(order_data)
    
    # Write the data to a CSV file
    with open(csv_file_path_orders, 'w', newline='') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow([column.name for column in Trackable.__table__.columns])
        csv_writer.writerows(data)

async def send_csv_to_user(csv_file_path, user):
    bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
    chat_id = os.getenv('USERNAME_Y'), os.getenv('USERNAME_S')
    
    if user in chat_id:
        try:
            with open(csv_file_path, 'rb') as file:
                await bot.send_document(chat_id=user, document=file)
        except telegram.error.BadRequest:
            logger.info('Error sending CSV to %f', user)


if __name__ == '__main__':
    user = sys.argv[1]
    opt = sys.argv[2]
    
    csv_file_path_subs = f'{time.strftime("%Y-%m-%d")}_subs.csv'
    csv_file_path_orders  = f'{time.strftime("%Y-%m-%d")}_orders.csv'
    
    if opt == 'sub':
        iterate_subscribers(csv_file_path_subs)
        asyncio.run(send_csv_to_user(csv_file_path_subs, user))
    elif opt == 'ord':
        iterate_orders(csv_file_path_orders)
        asyncio.run(send_csv_to_user(csv_file_path_orders, user))
    elif opt == 'ord_all':
        iterate_all_orders(csv_file_path_orders)
        asyncio.run(send_csv_to_user(csv_file_path_orders, user))
