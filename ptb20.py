import os
import queue
import asyncio
import logging
import tracemalloc
from pprint import pprint
from threading import Thread
import subprocess

from db import create_user_order, add_order, delete_order, track, session
from model import Order, Base

from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, Bot, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, MenuButtonCommands, MenuButton, BotCommandScopeChatMember, WebAppInfo
from telegram.ext import Application, CallbackContext, CallbackQueryHandler, CommandHandler, ConversationHandler, filters, MessageHandler, Updater

load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

queue_ = queue.Queue()

LOCALIZER, LOCATION, DETAILS, CONTACT, MORE_CONTACT, SUBSCRIPTION, SUBSCRIPTION_TYPE = range(7)

async def start(update: Update, context: CallbackContext) -> int:
    order = session.query(Order).filter(Order.username == update.effective_user.id).first()
    
    if str(update.effective_user.id) == os.getenv('USERNAME'):
        await update.message.reply_text(
            "ADMIN\n/generate_report\n/delete_subscriber",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    if order is None:
        Amharic = KeyboardButton(text="Amharic")
        English = KeyboardButton(text="English")
        
        custom_keyboard = [[ Amharic, English ]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        await update.message.reply_text(
            'Pick your preffered language:',
            reply_markup=reply_markup
        )
        
        return LOCALIZER
    else:
        await update.message.reply_text(
            "Order has been recieved, we'll call to confirm.\nThank you for choosing us.",
            reply_markup=ReplyKeyboardRemove()
        )
        key_mapping = {'username': 'user_id', 'fName': 'fName', 'lName': 'lName', 'primary_phone': 'phone', 'secondary_phone': 's_phone', 'address_details': 'add_details', 'latitude': 'latitude','longitude': 'longitude', 'order_count': 'count', 'lang': 'lang','subscription':'subscription_type'}
        
        # Populate a dictionary with values from the model instance
        order_dict = {new_key: getattr(order, old_key) for old_key, new_key in key_mapping.items()}
        order_dict['subscription'] = 'Yes'
        
        add_order(order.username)
        
        return await send_details(update, context, False, order_dict)

async def localizer(update: Update, context: CallbackContext) -> int:
    """Store user language preference and ask for details"""
    lang = update.effective_message.text
    context.user_data['lang'] = lang
    logger.info("Language: %s", lang)
    
    await context.bot.send_message(
        text="""
        *Pricing*

*Item*                              *Price*

*Tops*
- All shirts.....................50
- Polo.............................60
- Blouse
- Sweater......................100
- Jacket/filled hight...250/350
- Vest.............................50

*Bottoms*
- Trouser.........................80
- Skirt L/s.....................250/200
- Shorts..........................50
- Underwear..................60

*Full body*
- National dress................350
- Wedding dress L/S........2500/1800
- Coat/jeans coat............300/200
- Suit (jacket trouser).....400

*Household*
- Blanket Ex/L/m/s.........550/500/450/400
- Duvet cover...................190
- Comforter/duvet
- Table cloth s/m/l..........75/100/125
- Towel s/m/l....................30/40/60

*Accessories*
- Napkin............................30
- Pillow case.....................30
- Tie/scarf.........................30

*Button repair*
- Free

        """,
        chat_id=update.effective_chat.id,
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    
    if lang == "English":
        await update.message.reply_text(
        """Name\nName of your area""",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await update.message.reply_text(
        """ሙሉ ስም\nያሉበት ሰፈር ስም""",
            reply_markup=ReplyKeyboardRemove()
        )
        
    return DETAILS

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
        Just the number in 09xxxxxxxx format.""",
        reply_markup=ReplyKeyboardRemove()
    )
    
    return MORE_CONTACT

async def more_contact(update: Update, context: CallbackContext) -> int:
    """Store additional contact and end conversation"""
    user_additional_contact = update.message.text
    
    # regex to accept only numbers
    if not user_additional_contact.isnumeric():
        await update.message.reply_text(
            "Invalid input. Please enter only numbers."
        )
        logger.info("Invalid input: %s", user_additional_contact)
        
        return MORE_CONTACT
    
    context.user_data['more_contact'] = user_additional_contact
    logger.info("Additional contact: %s", user_additional_contact)
    
    subscribe = KeyboardButton(text="Subscribe")
    no = KeyboardButton(text="No")
    custom_keyboard = [[ subscribe, no ]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
    await context.bot.send_message(
        text="""Hi! Would you like to subscribe to our services:
        
*Benefits*:
*Ocean subscriber*

- Our simplest plan priced by the kilogram and always free pickup and delivery. Enjoy savings of up to 40% vs. order once in a while.
- Priced by the bag, as low as 1500/bag.
- If it fits 25 kg, we’ll clean it.
- Always free pickup and delivery.
- Next day rush service available for double price.

*Once in a while service*

If you only need our wash fold services every once in a while, this is the choice for you. It’s a great same service.

- Priced by the pieces.
- Free pickup and delivery with a minimum of 2000 birr.
- Next day rush service available for 250 birr delivery payment.
        """,
        chat_id=update.effective_chat.id,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return SUBSCRIPTION

async def subscription_optin(update: Update, context: CallbackContext) -> int:
    sub = update.effective_message.text
    if sub == 'Subscribe':
        context.user_data['subscription'] = 'Yes'
        
        weekly = KeyboardButton(text="Weekly")
        bi_weekly = KeyboardButton(text="Bi-Weekly")
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

async def cancel_sub(update: Update, context: CallbackContext):
    """Cancels and ends the conversation."""
    
    if str(update.effective_user.id) == os.getenv('USERNAME'):
        await update.message.reply_text(
            "ADMIN\n/generate_report\n/delete_subscriber",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
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
    order_details['lang'] = context.user_data['lang']
    
    if order_details['subscription'] == 'Yes':
        return await send_details(update, context, True, order_details)
    else:
        return await send_details(update, context, False, order_details)

async def send_details(update: Update, context: CallbackContext, sub: False, order_details:dict) -> int:
    if sub:
        # Register user if they opt-in for a subscription
        order = create_user_order(order_details['user_id'], order_details['fName'], order_details['lName'], order_details['phone'], order_details['s_phone'], order_details['add_details'], order_details['latitude'], order_details['longitude'], order_details['lang'], order_details['subscription_type'])
        logger.info("Subscription %s registered.", order.id)
        
        await update.message.reply_text(
            "Thank you for subscribing",
            reply_markup=ReplyKeyboardRemove())

    tracker_id = track(order_details['user_id'])

    await update.message.reply_text(
        text=f"""
        Order `#{tracker_id}` accepted

The courier will write you in advance about the time of the arrival.

Payment for the order occurs at the arrival of the washed items.

Orders will be picked on the day of the order

Repair service for missing or broken buttons is complementary with any ocean dry cleaning order.

We pick up and deliver 7 days a week, always between 6AM and 10PM.

*Pickup and delivery fees*
The 190 birr delivery fee will only be paid if your order is below 1000 birr.

*Free delivery*
Get unlimited free pickups and delivery by subscribing our packages

Become a subscriber now on *Ocean*.

Save time and your sanity when you leave the dry cleaning errands to us.

Call `4840` for any help
        """,
        parse_mode='markdown',
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
        str(order_details['longitude']),
        order_details['lang'])
    
    # message = f"""Name: {fName + (' ' + lName if lName is not None else '')}\nPhone: {phone}\nAlt: {s_phone}\nDetails: {add_details}\nSubscription: {subscription}\n[Open in Map](https://maps.google.com/?q={latitude},{longitude})"""
    await context.bot.send_message(
        chat_id=username,
        text=message,
        parse_mode='markdown'
    )
    logger.info("Order recieved and transmitted to %s.", username)
    return ConversationHandler.END

async def delete_subscriber(update: Update, context: CallbackContext):
    """Delete subscriber"""
    user_id = update.effective_user.id
    
    if str(user_id) == os.getenv('USERNAME'):
        user = context.args[0]
        
        order = session.query(Order).filter(Order.username == user).first()
        if order:
            try:
                delete_order(user)
                logger.info("Canceled subscription for user %s .", user)
                await update.message.reply_text(
                    f"Subscription cancelled for user {user}.",
                    reply_markup=ReplyKeyboardRemove()
                )
            except:
                pass
        else:
            # subscription not found
            logger.info("User %s's subscription was not found.", user_id)
            await update.message.reply_text(
                "Subscription not found."
            )
    else:
        await update.message.reply_text("YOU ARE NOT AN ADMIN")

async def generate_report(update: Update, context: CallbackContext):
    """Generate report"""
    if str(update.effective_user.id) == os.getenv('USERNAME'):
        order = session.query(Order).filter(Order.username == update.effective_user.id).first()
        if order:
            subprocess.run(['python3', 'reports.py'])
            logger.info("Report generated.")
        else:
            await update.message.reply_text("No subscribers to report on.")
            logger.info("Report not generated. No subscribers to report on.")
    else:
        await update.message.reply_text("YOU ARE NOT AN ADMIN")

async def get_chat_id(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    await update.message.reply_text(f"Your chat ID is {chat_id} - user ID is {user_id}")

async def about(update: Update, context: CallbackContext) -> int:
    """Sends a message with "about" info"""
    await context.bot.send_message(
    text="""*How it works*

1. *Order Placement*
   - We come and pick up your clothes when you make a call to our call center or directly make your order in our telegram bot. We then deliver it at the right time.

2. *Photo and Inventory*
   - We text you a photo and itemized inventory of what we pick up, so you remember what’s being cleaned and in what condition.

3. *Spot and Stain Inspection*
   - We carefully inspect for spots and stains. Our spotters have decades of experience in identifying and treating stains in the best way possible so your garments are returned pristine.

4. *Expert Cleaning*
   - We clean your clothes with expert care. We follow the care label (and know what all the symbols mean) so your clothes receive the optimal cleaning treatment and last for years to come.

5. *Pressing and Hanging*
   - We press and hang each of your items. Your clothes are crispy pressed, put on hangers, and placed in your protective garment bag, ready to wear when we deliver your dry cleaning to your door.

*Wash and Fold*

- Wash & fold is the perfect service to use if you want to avoid doing laundry and save your time and your sanity.
- Ocean will pick up, clean, and deliver your laundry right back to your door. Your clothes get their own machine, are cleaned according to your preference, and delivered neatly folded - we even pair your socks.
- Let ocean do your laundry for you so you can focus on more important things.

    *How it works*

    1. *Inspecting Clothes and Checking Pockets*
    - We inspect your clothes and check your pockets. We do pocket inspection for you so nothing ends up in the wash that shouldn’t. All pockets and clothes are inspected before being washed.

    2. *Careful Washing*
    - We clean your items with extra care. Your light and darks are separated and all your clothes are washed using cold water to preserve color (and save energy).

    3. *Customized Laundry*
    - We wash your loads according to your choices. Want a fabric softener? Just select the laundry preferences that are right for you.

    4. *Folding Service*
    - We fold everything so that you don’t have to. Your clothes are crisply folded, and your socks are paired, ready to be worn or put away when we deliver your clothes to your door.

""",
chat_id=update.effective_chat.id,
parse_mode='Markdown'
    )

async def subscription(update: Update, context: CallbackContext) -> int:
    """Sends a message with "about" info"""
    await context.bot.send_message(
    text="""
    # Subscription

    """,
    parse_mode='Markdown',
    chat_id=update.effective_chat.id
    )

async def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    
    if str(update.effective_user.id) == os.getenv('USERNAME'):
        await update.message.reply_text(
            "ADMIN\n/generate_report\n/delete_subscriber",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.",
        reply_markup=ReplyKeyboardRemove()
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
    
    # Commands
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LOCALIZER: [MessageHandler(filters.TEXT, localizer)],
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
    application.add_handler(CommandHandler("get_chat_id", get_chat_id))
    application.add_handler(CommandHandler("delete_subscriber", delete_subscriber))
    application.add_handler(CommandHandler("generate_report", generate_report))
    # application.add_handler(CommandHandler("subscription", subscription))
    application.add_handler(CommandHandler("about", about))

    # Run bot
    application.run_polling(allowed_updates=Update.ALL_TYPES, poll_interval=1.0)


if __name__ == '__main__':
    tracemalloc.start()
    
    main()
    
    tracemalloc.stop()
    print(tracemalloc.get_object_traceback())