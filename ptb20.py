import os
import queue
import asyncio
import logging
import tracemalloc
from threading import Thread
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, Bot
from telegram.ext import Application, CallbackContext, CallbackQueryHandler, CommandHandler, ConversationHandler, filters, MessageHandler, Updater

load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

queue_ = queue.Queue()

LOCATION, CONTACT, DONE = range(3)

async def start(update: Update, context: CallbackContext) -> int:
    """Prompt user to share location"""
    location_keyboard = KeyboardButton(text="Share Location", request_location=True)
    custom_keyboard = [[ location_keyboard ]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        'Hi! Please share your location by pressing the button below.',
        reply_markup=reply_markup
    )
    return LOCATION

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

async def contact(update: Update, context: CallbackContext) -> int:
    """Store user contact and end conversation"""
    user_contact = update.message.contact
    # Handle the case when contact is not provided
    if user_contact is None:
        await update.message.reply_text('No contact provided. Please share your contact.')
        return CONTACT

    context.user_data['contact'] = user_contact
    logger.info("Contact %s: %s", user_contact.first_name, user_contact.phone_number)

    # Use a callback function to send the location and contact details to the specified user
    async def send_details(update: Update, context: CallbackContext):
        username = '344776272'
        
        # Get user info
        fName = update.message.contact.first_name 
        lName = update.message.contact.last_name 
        # phone = update.message.contact.phone_number
        phone = '0911223344'

        # Get location 
        latitude = context.user_data['location'].latitude
        longitude = context.user_data['location'].longitude
        
        message = f"""Name: {fName + (' ' + lName if lName is not None else '')}\n Phone: {phone}
        [Open in Map](https://maps.google.com/?q={latitude},{longitude})"""
        await context.bot.send_message(
            chat_id=username,
            text=message,
            parse_mode='markdown'
        )
        
        # Send map and user details
        await context.bot.send_venue(
            chat_id=username, 
            latitude=latitude, 
            longitude=longitude,
            title=f"Name: {fName + (' ' + lName if lName is not None else '')}",
            address=f"Phone: {phone}"
        )

    await send_details(update, context)

    """End conversation"""
    await update.message.reply_text('Thank you, bye!')
    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

async def error_handler(update: Update, context: CallbackContext):
    """Log the error and handle it gracefully"""
    logger.error(msg="Exception occurred", exc_info=context.error)
    await update.message.reply_text('Sorry, an error occurred. Please try again.')

########################################################
def main():
    # bot runner
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LOCATION: [MessageHandler(filters.LOCATION, location)],
            CONTACT: [MessageHandler(filters.CONTACT, contact)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    # Commands
    application.add_handler(conv_handler)

    # Run bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    tracemalloc.start()
    
    main()
    
    tracemalloc.stop()
    print(tracemalloc.get_object_traceback())