import os
from dotenv import load_dotenv
import asyncio
import sqlite3
from datetime import datetime, timedelta

from db import session
from model import Order

from telegram import Bot, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import Updater
from sqlalchemy import func

load_dotenv()

def check_subscribers():
    today = datetime.today().strftime('%d')
    subscribers = session.query(Order).filter(func.strftime('%d', Order.subscription_date) == today).all()
    if subscribers:
        return subscribers

async def send_to_admin(message):
    bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
    chat_id = os.getenv('USERNAME')
    
    await bot.send_message(chat_id=chat_id, text=message)

async def send_to_subscribers(subscribers):
    subscribers_list = get_subscribers(subscribers)
    
    bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
    
    Accept = KeyboardButton(text="Accept")
    Skip = KeyboardButton(text="Skip")
    Cancel = KeyboardButton(text="Cancel")
    
    custom_keyboard = [[ Accept, Skip, Cancel  ]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        
    for subscriber in subscribers_list:
        await bot.send_message(
            chat_id=subscriber['username'],
            text="Your subscription date has arrived! Please respond to this message with the following options:\nAccept: to continue with order\nSkip: to skip order for this round.\nCancel: to cancel subscription\n",
            reply_markup=reply_markup
        )
        

def format_subscribers(subscribers):
    formatted_message = ""
    
    subscriber_list = get_subscribers(subscribers)
    
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
    
    return subscriber_list

if __name__ == '__main__':
    subs = check_subscribers()
    asyncio.run(send_to_admin(format_subscribers(subs)))
    asyncio.run(send_to_subscribers(format_subscribers(subs)))