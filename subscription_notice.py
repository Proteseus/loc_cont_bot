import os
from dotenv import load_dotenv
import asyncio
import sqlite3
from datetime import datetime, timedelta

from db import session
from model import Order

from telegram import Bot
from telegram.ext import Updater
from sqlalchemy import func

load_dotenv()


def check_subscribers():
    today = datetime.today().strftime('%d')
    subscribers = session.query(Order).filter(func.strftime('%d', Order.subscription_date) == today).all()
    if subscribers:
        return get_subscribers(subscribers)

async def send_to_user(message):
    bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
    chat_id = os.getenv('USERNAME')
    
    await bot.send_message(chat_id=chat_id, text=message)

def format_subscribers(subscriber_list):
    formatted_message = ""
    
    for subscriber in subscriber_list:
        formatted_message += f"Username: {subscriber['username']}\n"
        formatted_message += f"Primary Phone: {subscriber['primary_phone']}\n"
        
        if subscriber['secondary_phone']:
            formatted_message += f"Secondary Phone: {subscriber['secondary_phone']}\n"
        formatted_message += "\n"
    
    return formatted_message.strip()

def get_subscribers(subscribers):
    subscriber_list = []
    for subscriber in subscribers:
        subscriber_info = {
            'username': subscriber.username,
            'primary_phone': subscriber.primary_phone,
            'secondary_phone': subscriber.secondary_phone
        }
        subscriber_list.append(subscriber_info)
    session.close()
    
    return format_subscribers(subscriber_list)

if __name__ == '__main__':
    asyncio.run(send_to_user(check_subscribers()))