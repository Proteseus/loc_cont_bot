#!/usr/bin/python3
import os
import csv
import glob
import time
import asyncio

from db import create_user_order, add_order, session
from model import Order

from telegram import Bot
from telegram.ext import Updater

def delete_old_csv_files():
    files = glob.glob('*.csv')
    for file in files:
        if os.stat(file).st_mtime < time.time() - 7 * 24 * 60 * 60:
            os.remove(file)

def iterate_orders(csv_file_path):
    delete_old_csv_files()
    orders = session.query(Order).all()
    data = []
    for order in orders:
        order_data = []
        for column in Order.__table__.columns:
            order_data.append(str(getattr(order, column.name)))
        data.append(order_data)
    
    # Write the data to a CSV file
    with open(csv_file_path, 'w', newline='') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow([column.name for column in Order.__table__.columns])
        csv_writer.writerows(data)

async def send_csv_to_user(csv_file_path):
    bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
    chat_id = os.getenv('USERNAME')
    
    with open(csv_file_path, 'rb') as file:
        await bot.send_document(chat_id=chat_id, document=file)

if __name__ == '__main__':
    csv_file_path = f'{time.strftime("%Y-%m-%d")}.csv'
    
    iterate_orders(csv_file_path)
    asyncio.run(send_csv_to_user(csv_file_path))
