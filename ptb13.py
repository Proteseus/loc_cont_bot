import os
import logging
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, KeyboardButton, Bot
from telegram.ext import (
    Updater,
    CommandHandler,
    ConversationHandler,
    CallbackContext,
    MessageHandler,
    Filters,
)
from queue import Queue
from threading import Thread

# Create a queue to hold the updates
update_queue = Queue()

def worker():
    while True:
        # Get the next update from the queue
        update = update_queue.get()

        # Process the update
        try:
            handle_update(update)
        except Exception as e:
            logger.error(f"Error handling update: {e}")

        # Mark the task as done
        update_queue.task_done()

# Start the worker thread
worker_thread = Thread(target=worker)
worker_thread.start()

# Enable logging
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

LOCATION, CONTACT, DONE = range(3)

def start(update: Update, context: CallbackContext) -> int:
    """Prompt user to share location"""
    location_keyboard = KeyboardButton(text="Share Location", request_location=True)
    custom_keyboard = [[ location_keyboard ]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
    update.message.reply_text(
        'Hi! Please share your location by pressing the button below.',
        reply_markup=reply_markup
    )
    return LOCATION

def location(update: Update, context: CallbackContext) -> int:
    """Store user location and ask for contact"""
    user_location = update.message.location
    if user_location is None:
        # Handle the case when location is not provided
        update.message.reply_text('No location provided. Please share your location.')
        return LOCATION
    
    context.user_data['location'] = user_location
    logger.info("Location %f / %f", user_location.latitude, user_location.longitude)

    contact_keyboard = KeyboardButton(text="Share Contact", request_contact=True)
    custom_keyboard = [[ contact_keyboard ]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
    update.message.reply_text(
        'Thank you! Please now share your contact info by pressing the button below.',
        reply_markup=reply_markup
    )
    return CONTACT

def contact(update: Update, context: CallbackContext) -> int:
    """Store user contact and end conversation"""
    user_contact = update.message.contact
    if user_contact is None:
        # Handle the case when contact is not provided
        update.message.reply_text('No contact provided. Please share your contact.')
        return CONTACT

    context.user_data['contact'] = user_contact
    logger.info("Contact %s: %s", user_contact.first_name, user_contact.phone_number)

    update.message.reply_text(
        'Thank you! I have your location and contact details.',
        reply_markup=ReplyKeyboardRemove()
    )

    # Send location and contact to specified user
    username = '344776272'
    
    # Get user info
    fName = update.message.contact.first_name 
    lName = update.message.contact.last_name 
    phone = update.message.contact.phone_number

    # Get location 
    latitude = context.user_data['location'].latitude
    longitude = context.user_data['location'].longitude
    
    message = f"""Name: {fName + (' ' + lName if lName is not None else '')}\n Phone: {phone}
    [Open in Map](https://maps.google.com/?q={latitude},{longitude})"""
    context.bot.send_message(
        chat_id=username,
        text=message,
        parse_mode='markdown'
    )
    

    # Send map and user details
    context.bot.send_venue(
    chat_id=username, 
    latitude=latitude, 
    longitude=longitude,
    title=f"Name: {fName + (' ' + lName if lName is not None else '')}",
    address=f"Phone: {phone}"
    )

    return DONE

def done(update: Update, context: CallbackContext) -> int:
    """End conversation"""
    update.message.reply_text('Thank you, bye!')

    return ConversationHandler.END

# Define your error handlers
def error_handler(update: Update, context: CallbackContext) -> None:
    """Log the error and handle it gracefully"""
    logger.error(msg="Exception occurred", exc_info=context.error)

def main() -> None:
    """Start the bot."""
    bot = Bot(token=TOKEN)
    updater = Updater(bot=bot, use_context=True, request_kwargs={'read_timeout': 20, 'connect_timeout': 20, 'pool_size': 100})

    dispatcher = updater.dispatcher
    dispatcher.add_error_handler(error_handler)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LOCATION: [MessageHandler(Filters.location, location)],
            CONTACT: [MessageHandler(Filters.contact, contact)],
            DONE: [MessageHandler(Filters.text, done)]
        },
        fallbacks=[CommandHandler('done', done)]
    )

    dispatcher.add_handler(conv_handler)

    # Start the Bot
    print("Bot starting.....")
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
