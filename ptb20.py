import os
import queue
import asyncio
import logging
import tracemalloc
from pprint import pprint
from threading import Thread
from db import create_user_order, add_order, delete_order, track, session
from model import Order, Base

from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackContext, CallbackQueryHandler, CommandHandler, ConversationHandler, filters, MessageHandler, Updater

load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

queue_ = queue.Queue()

LOCATION, DETAILS, CONTACT, MORE_CONTACT, SUBSCRIPTION, SUBSCRIPTION_TYPE = range(6)

async def start(update: Update, context: CallbackContext) -> int:
    order = session.query(Order).filter(Order.username == update.effective_user.id).first()
    if order is None:
        """Prompt user to share location"""
        await update.message.reply_text(
        """Specify the service you want.\nIf its is a hotel or a guest house\nplease specify the name and the room or villa number""",
            reply_markup=ReplyKeyboardRemove()
        )
        return DETAILS
    else:
        await update.message.reply_text(
            "Order has been recieved, we'll call to confirm.\nThank you for choosing us.",
            reply_markup=ReplyKeyboardRemove()
        )
        key_mapping = {'username': 'user_id', 'fName': 'fName', 'lName': 'lName', 'primary_phone': 'phone', 'secondary_phone': 's_phone', 'address_details': 'add_details', 'latitude': 'latitude','longitude': 'longitude', 'order_count': 'count', 'subscription':'subscription_type'}
        
        # Populate a dictionary with values from the model instance
        order_dict = {new_key: getattr(order, old_key) for old_key, new_key in key_mapping.items()}
        order_dict['subscription'] = 'Yes'
        
        add_order(order.username)
        
        return await send_details(update, context, False, order_dict)

async def location(update: Update, context: CallbackContext) -> int:
    """Store user location and ask for contact"""
    user_location = update.message.location
    # Handle the case when location is not provided
    if user_location is None:
        await update.message.reply_text('No location provided. Please share your location.')
        return LOCATION
    
    context.user_data['location'] = user_location
    logger.info("Location %f / %f", user_location.latitude, user_location.longitude)

    contact_keyboard = KeyboardButton(text="Share Contact", request_contact=True)
    custom_keyboard = [[ contact_keyboard ]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        'Hi! Please share your contact by pressing the button below.',
        reply_markup=reply_markup
    )

    return CONTACT

async def details(update: Update, context: CallbackContext) -> int:
    """Store details and ask for contact"""
    user_details = update.message.text
    logger.info("Details: %s", user_details)
    
    context.user_data['details'] = user_details
    
    location_keyboard = KeyboardButton(text="Share Location", request_location=True)
    custom_keyboard = [[ location_keyboard ]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        'Hi! Please share your location by pressing the button below.',
        reply_markup=reply_markup
    )
    
    return LOCATION

async def contact(update: Update, context: CallbackContext) -> int:
    """Store user contact and ask for additional"""
    user_contact = update.message.contact
    # Handle the case when contact is not provided
    if user_contact is None:
        await update.message.reply_text('No contact provided. Please share your contact.')
        return CONTACT

    context.user_data['contact'] = user_contact
    logger.info("Contact %s: %s", user_contact.first_name, user_contact.phone_number)

    await update.message.reply_text(
        """If you wish to add another number for pickup by a different person or if we can't reach you on the first number. 
        Just the number.""",
        reply_markup=ReplyKeyboardRemove()
    )
    
    return MORE_CONTACT

async def more_contact(update: Update, context: CallbackContext) -> int:
    """Store additional contact and end conversation"""
    user_additional_contact = update.message.text
    context.user_data['more_contact'] = user_additional_contact
    logger.info("Additional contact: %s", user_additional_contact)
    
    subscribe = KeyboardButton(text="Subscribe")
    no = KeyboardButton(text="No")
    custom_keyboard = [[ subscribe, no ]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        'Hi! Would you like to subscribe to our services:',
        reply_markup=reply_markup
    )
    
    return SUBSCRIPTION

async def subscription_optin(update: Update, context: CallbackContext) -> int:
    sub = update.effective_message.text
    if sub == 'Subscribe':
        context.user_data['subscription'] = 'Yes'
        
        weekly = KeyboardButton(text="Weekly")
        bi_weekly = KeyboardButton(text="By-Weekly")
        monthly = KeyboardButton(text="Monthly")
        
        custom_keyboard = [[ weekly, bi_weekly, monthly  ]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        await update.message.reply_text(
            'Pick your preffered subscription type:',
            reply_markup=reply_markup
        )
        
        return SUBSCRIPTION_TYPE
    elif sub == 'No':
        context.user_data['subscription'] = 'No'
        return await order_detail(update, context)

async def subscription_type(update: Update, context: CallbackContext) -> int:
    """Store subscription type"""
    sub_type = update.effective_message.text
    context.user_data['subscription_type'] = sub_type
    logger.info("Subscription type: %s", sub_type)

    await update.message.reply_text(
        'Thank you for subscribing to Ocean. We will call you back to confirm your subscription.',
        reply_markup=ReplyKeyboardRemove()
    )
    
    return await order_detail(update, context)

async def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

async def cancel_sub(update: Update, context: CallbackContext):
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s wants to cancel their subscription.", f"{user.first_name}: {user.id}")
    
    sub = delete_order(user.id)
    
    if sub:    
        logger.info("User %s canceled their subscription.", user.first_name)
        await update.message.reply_text(
            # subscription cancel message
            "Subscription cancelled.\nThank you for using Ocean.",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        # subscription not found
        logger.info("User %s tried to cancel their subscription but it was not found.", user.first_name)
        await update.message.reply_text(
            "Subscription not found.\nYou can't cancel a subscription that you don't have.\nIf you want to subscribe, please reply with /start.",
        )

async def error_handler(update: Update, context: CallbackContext):
    """Log the error and handle it gracefully"""
    logger.error(msg="Exception occurred", exc_info=context.error)
    await update.message.reply_text('Sorry, an error occurred. Please try again.')

async def order_detail(update: Update, context: CallbackContext) -> int:
    """Store details and pass them to admins"""
    order_details = {}
    order_details['user_id'] = context.user_data['contact'].user_id
    order_details['fName'] = context.user_data['contact'].first_name 
    order_details['lName'] = context.user_data['contact'].last_name
    order_details['phone'] = context.user_data['contact'].phone_number
    order_details['s_phone'] = context.user_data['more_contact'] if 'more_contact' in context.user_data.keys() else None
    order_details['add_details'] = context.user_data['details'].replace('\n', ' ')

    # Get location 
    order_details['latitude'] = context.user_data['location'].latitude 
    order_details['longitude'] = context.user_data['location'].longitude
    
    # Get Subscription
    order_details['subscription'] = context.user_data['subscription']
    order_details['subscription_type'] = context.user_data['subscription_type'] if 'subscription_type' in context.user_data.keys() else None
    
    if order_details['subscription'] == 'Yes':
        return await send_details(update, context, True, order_details)
    else:
        return await send_details(update, context, False, order_details)

async def send_details(update: Update, context: CallbackContext, sub: False, order_details:dict) -> int:
    if sub:
        # Register user if they opt-in for a subscription
        order = create_user_order(order_details['user_id'], order_details['fName'], order_details['lName'], order_details['phone'], order_details['s_phone'], order_details['add_details'], order_details['latitude'], order_details['longitude'], order_details['subscription_type'])
        logger.info("Subscription %s registered.", order.id)
        
        await update.message.reply_text(
            "Thank you for subscribing",
            reply_markup=ReplyKeyboardRemove())

    tracker_id = track(order_details['user_id'])

    await update.message.reply_text(
        f"Your order #{tracker_id} has been submitted.\nWe'll be in touch!",
        reply_markup=ReplyKeyboardRemove())
    
    username = os.getenv('USERNAME')
    
    message = "Order: #{}\nName: {}\nPhone: {}\nAlt: {}\nDetails: {}\nSubscription: {}\nSubscription type: {}\n[Open in Map](https://maps.google.com/?q={},{})".format(
        tracker_id,
        order_details['fName'] + (' ' + order_details['lName'] if order_details['lName'] is not None else ''),
        order_details['phone'],
        order_details['s_phone'],
        order_details['add_details'],
        order_details['subscription'],
        order_details['subscription_type'] if order_details['subscription_type'] is not None else 'No',
        str(order_details['latitude']),
        str(order_details['longitude']))
    
    # message = f"""Name: {fName + (' ' + lName if lName is not None else '')}\nPhone: {phone}\nAlt: {s_phone}\nDetails: {add_details}\nSubscription: {subscription}\n[Open in Map](https://maps.google.com/?q={latitude},{longitude})"""
    await context.bot.send_message(
        chat_id=username,
        text=message,
        parse_mode='markdown'
    )
    logger.info("Order recieved and transmitted to %s.", username)
    return ConversationHandler.END

########################################################
def main():
    # bot runner
    application = Application.builder().token(TOKEN).build()

    # Commands
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            DETAILS: [MessageHandler(filters.TEXT, details)],
            LOCATION: [MessageHandler(filters.LOCATION, location)],
            CONTACT: [MessageHandler(filters.CONTACT, contact)],
            MORE_CONTACT: [MessageHandler(filters.TEXT, more_contact)],
            SUBSCRIPTION: [MessageHandler(filters.TEXT, subscription_optin)],
            SUBSCRIPTION_TYPE: [MessageHandler(filters.TEXT, subscription_type)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    application.add_handler(CommandHandler('cancel_subscription', cancel_sub))
    application.add_handler(conv_handler)

    # Run bot
    application.run_polling(allowed_updates=Update.ALL_TYPES, poll_interval=1.0)


if __name__ == '__main__':
    tracemalloc.start()
    
    main()
    
    tracemalloc.stop()
    print(tracemalloc.get_object_traceback())