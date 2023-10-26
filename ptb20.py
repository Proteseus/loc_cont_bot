import os
import queue
import asyncio
import logging
import tracemalloc
from pprint import pprint
from threading import Thread
import subprocess

from db import create_user_order, add_order, delete_order, change_lang, track, session
from model import Order, Base

from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, Bot, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, BotCommandScopeChat
from telegram.ext import Application, CallbackContext, CallbackQueryHandler, CommandHandler, ConversationHandler, filters, MessageHandler, Updater

load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
# TOKEN = os.getenv('TESTER')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

queue_ = queue.Queue()

LOCALIZER, LOCATION, NAME, DETAILS, CONTACT, MORE_CONTACT_CONFIRM, MORE_CONTACT, SUBSCRIPTION, SUBSCRIPTION_TYPE = range(9)

async def start(update: Update, context: CallbackContext):
    if str(update.effective_chat.id) == os.getenv('USERNAME') or str(update.effective_chat.id) == os.getenv('USERNAME_Y') or str(update.effective_chat.id) == os.getenv('USERNAME_S'):
    # if str(update.effective_chat.id) == os.getenv('USERNAME') or str(update.effective_chat.id) == os.getenv('USERNAME_Y'):
        await context.bot.set_my_commands(
            commands=[
                BotCommand('generate_report_subs', 'Generate subs report'),
                BotCommand('generate_report_orders', 'Generate orders report'),
                BotCommand('generate_report_all_orders', 'Generate all orders report'),
                BotCommand('delete_subscriber', 'Delete subscriber')
            ],
            scope=BotCommandScopeChat(chat_id=update.effective_chat.id)
        )
    else:
        await context.bot.set_my_commands(
            commands=[
                BotCommand("cancel", "end conversation"),
                BotCommand("change_language", "change language"),
                BotCommand("contact_us", "contact us"),
                BotCommand("cancel_subscription", "cancel subscription"),
                BotCommand("about","info")
            ],
            scope=BotCommandScopeChat(chat_id=update.effective_chat.id)
        )
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="""Welcome to Ocean Laundry service
ወደ ኦሽን የልብስ እጥበት አገልግሎት እንኳን በደህና መጡ።

👇
Select a language to access the service.
አገልግሎቱን ለማግኘት ቋንቋ ይምረጡ""",
            reply_markup=ReplyKeyboardRemove()
        )
        
        Amharic = KeyboardButton(text="Amharic")
        English = KeyboardButton(text="English")
        
        custom_keyboard = [[ Amharic, English ]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        await update.message.reply_text(
            text="Pick your preffered language:",
            reply_markup=reply_markup
        )
        
        return LOCALIZER

async def localizer(update: Update, context: CallbackContext) -> int:
    """Store user language preference and ask for details"""
    lang = update.effective_message.text
    context.user_data['lang'] = lang
    logger.info("Language: %s", lang)
    
    if lang == "Amharic":
        await update.message.reply_text(
            text="""ይህ ቦት ምን ማድረግ ይችላል?

ኦሽን ልብስ ማጠቢያ - የንብረቶቻችሁን ንፅህናን የማረጋገጥ አገልግሎት።

በሁሉም የአዲስ አበባ አከባቢዎች ነፃ መረከብ እና ማድረስ በትንሹ ትእዛዝ ከ1,200 ብር ጀምሮ ያገኛሉ።

🔗 ቆሻሻ ማስወገድ እና ልብሶን በጥንቃቄ መያዝ

🛠 የምንሰጣቸው አገልግሎቶች :

✅ መታጠብ እና ማጠፍ
✅ የደረቅ እጥበት

📍ባዘዙ በ24 ሰአትውስጥ ልብስዎን እንሰበስባለን።
📍በጥቂት ቀናት ውስጥ ማድረስ።

              100% ጥራትና ዋስት

ስልክ - 09######## - 09########""",
            reply_markup=ReplyKeyboardRemove()
        )
        text = "ይዘዙን"
    elif lang == "English":
        await update.message.reply_text(
            text="""What can this bot do?

𝗢𝗰𝗲𝗮𝗻 𝗟𝗮𝘂𝗻𝗱𝗮𝗿𝘆 - a service for ensuring the cleanliness of your belongings.

Free Pickup and Delivery available in all areas of Addis Ababa, with a minimum order of 1,000 ETB birr.

🔗 Stains removed; Clothes handled with care.

🛠 The services we provide :

✅ ﻿Wash and fold*
✅ ﻿Dry cleaning*

📍We will collect your clothes within 24 hours of your order.
📍Delivery within a few days.

              100% 𝖖𝖚𝖆𝖑𝖎𝖙𝖞 𝖌𝖚𝖆𝖗𝖆𝖓𝖙𝖊𝖊

Contact - 09######## - 09########""",
            reply_markup=ReplyKeyboardRemove()
        )
        text = "Order us"
        
    order_laundry = KeyboardButton(text="order_laundry")
        
    custom_keyboard = [[ order_laundry ]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        text=text,
        reply_markup=reply_markup
    )
        
    return ConversationHandler.END


async def order_laundry(update: Update, context: CallbackContext) -> int:
    order = session.query(Order).filter(Order.userid == update.effective_user.id).first()
    
    if str(update.effective_user.id) == os.getenv('USERNAME'):
        await update.message.reply_text(
            "ADMIN\n/generate_report\n/delete_subscriber",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    if order is None:
        lang = context.user_data['lang']
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
            """✅ Please give us details below:\n\nName""",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await update.message.reply_text(
            """ሙሉ ስም""",
                reply_markup=ReplyKeyboardRemove()
            )
        return NAME
    else:
        key_mapping = {'userid': 'user_id', 'username': 'user_name', 'Name': 'name', 'primary_phone': 'phone', 'secondary_phone': 's_phone', 'address_details': 'add_details', 'latitude': 'latitude','longitude': 'longitude', 'order_count': 'count', 'language': 'lang','subscription':'subscription_type'}
        
        # Populate a dictionary with values from the model instance
        order_dict = {new_key: getattr(order, old_key) for old_key, new_key in key_mapping.items()}
        order_dict['subscription'] = 'Yes'
        
        add_order(order.username)
        
        return await send_details(update, context, False, order_dict)


async def name(update: Update, context: CallbackContext) -> int:
    """Store user name and ask for details"""
    user_name = update.message.text
    logger.info("Name: %s", user_name)
    
    context.user_data['name'] = user_name
    
    lang = context.user_data['lang']
    
    if lang == "English":
        await update.message.reply_text(
        """Name of your area""",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await update.message.reply_text(
        """ያሉበት ሰፈር ስም""",
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
    
    yes_button = KeyboardButton(text="Yes")
    no_button = KeyboardButton(text="No")
    custom_keyboard = [[yes_button, no_button]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        'Would you like to add an alternative number?',
        reply_markup=reply_markup
    )
    
    return MORE_CONTACT_CONFIRM

async def more_contact_confirm(update: Update, context: CallbackContext) -> int:
    if update.effective_message.text == 'Yes':
        context.user_data['more_contact'] = 'Yes'
        
        await update.message.reply_text(
            """Add another number for pickup by a different person or if we can't reach you on the first number. 
            Just the number in 09xxxxxxxx format.""",
            reply_markup=ReplyKeyboardRemove()
        )
        logger.info("Additional contact required")
        return MORE_CONTACT
    
    else:
        logger.info("No additional contact provided.")
        context.user_data['more_contact'] = None
        
        return await subscription_prompt(update, context)

async def more_contact(update: Update, context: CallbackContext) -> int:
    """Store additional contact and end conversation"""
    print(context.user_data['more_contact'])
    if context.user_data['more_contact'] == 'Yes':
        user_additional_contact = update.message.text
        
        # regex to accept only numbers
        if not user_additional_contact.isnumeric() or len(user_additional_contact) != 10:
            await update.message.reply_text(
                "Invalid input. Please enter a 10-digit number."
            )
            logger.info("Invalid input: %s", user_additional_contact)
            
            return MORE_CONTACT
        
        context.user_data['more_contact'] = user_additional_contact
        logger.info("Additional contact: %s", user_additional_contact)
    
    return await subscription_prompt(update, context)

async def subscription_prompt(update: Update, context: CallbackContext) -> int:
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
        
        start = KeyboardButton(text="Restart")
        start_keyboard = [[ start ]]
        await update.message.reply_text(
            # subscription cancel message
            "Subscription cancelled.\nThank you for using Ocean.\nTo restart use the button.",
            reply_markup=ReplyKeyboardMarkup(start_keyboard, resize_keyboard=True)
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
    order_details['user_name'] = str(update.effective_chat.username)
    order_details['name'] = context.user_data['name']
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
        order = create_user_order(order_details['user_id'], order_details['user_name'], order_details['name'], order_details['phone'], order_details['s_phone'], order_details['add_details'], order_details['latitude'], order_details['longitude'], order_details['lang'], order_details['subscription_type'])
        logger.info("Subscription %s registered.", order.id)
        
        await update.message.reply_text(
            "Thank you for subscribing",
            reply_markup=ReplyKeyboardRemove())

    tracker_id = track(order_details['user_id'])
    
    reorder_ = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Reorder")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

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
        reply_markup=reorder_)
    
    message = "Order: #{}\nName: {}\nPhone: {}\nAlt: {}\nDetails: {}\nSubscription: {}\nSubscription type: {}\n[Open in Map](https://maps.google.com/?q={},{})".format(
        tracker_id,
        order_details['name'],
        order_details['phone'],
        order_details['s_phone'],
        order_details['add_details'],
        order_details['subscription'],
        order_details['subscription_type'] if order_details['subscription_type'] is not None else 'No',
        str(order_details['latitude']),
        str(order_details['longitude']))

    chat_id = os.getenv('USERNAME'), os.getenv('USERNAME_Y'), os.getenv('USERNAME_S')
    
    for user in chat_id:
        await context.bot.send_message(
            chat_id=user,
            text=message,
            parse_mode='markdown'
        )
        logger.info("Order recieved and transmitted to %s.", user)
    
    return ConversationHandler.END

async def reorder(update: Update, context: CallbackContext):
    """Reorder"""
    if update.effective_message.text == 'Reorder':
        return await order_laundry(update, context)

async def delete_subscriber(update: Update, context: CallbackContext):
    """Delete subscriber"""
    user_id = update.effective_user.id
    
    if str(update.effective_chat.id) == os.getenv('USERNAME') or str(update.effective_chat.id) == os.getenv('USERNAME_Y') or str(update.effective_chat.id) == os.getenv('USERNAME_S'):
    
    # if str(user_id) == os.getenv('USERNAME'):
        try:
            user = context.args[0]
        except:
            await update.message.reply_text("Please follow format:\n /delete_subscriber <user_id>.")
            return ConversationHandler.END
        
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

async def generate_report_sub(update: Update, context: CallbackContext):
    """Generate report"""
    if str(update.effective_chat.id) == os.getenv('USERNAME') or str(update.effective_chat.id) == os.getenv('USERNAME_Y') or str(update.effective_chat.id) == os.getenv('USERNAME_S'):
    # if str(update.effective_user.id) == os.getenv('USERNAME'):
        order = session.query(Order)
        
        if order:
            subprocess.run(['python3', 'reports.py', f'{update.effective_chat.id}', 'sub'])
            logger.info("Report generated.")
        else:
            await update.message.reply_text("No subscribers to report on.")
            logger.info("Report not generated. No subscribers to report on.")
    else:
        await update.message.reply_text("YOU ARE NOT AN ADMIN")

async def generate_report_ord(update: Update, context: CallbackContext):
    """Generate report"""
    if str(update.effective_chat.id) == os.getenv('USERNAME') or str(update.effective_chat.id) == os.getenv('USERNAME_Y') or str(update.effective_chat.id) == os.getenv('USERNAME_S'):
    # if str(update.effective_user.id) == os.getenv('USERNAME'):
        order = session.query(Order)
        
        if order:
            subprocess.run(['python3', 'reports.py', f'{update.effective_chat.id}', 'ord'])
            logger.info("Report generated.")
        else:
            await update.message.reply_text("No subscribers to report on.")
            logger.info("Report not generated. No subscribers to report on.")
    else:
        await update.message.reply_text("YOU ARE NOT AN ADMIN")

async def generate_report_all_ord(update: Update, context: CallbackContext):
    """Generate report"""
    if str(update.effective_chat.id) == os.getenv('USERNAME') or str(update.effective_chat.id) == os.getenv('USERNAME_Y') or str(update.effective_chat.id) == os.getenv('USERNAME_S'):
    # if str(update.effective_user.id) == os.getenv('USERNAME'):
        order = session.query(Order)
        
        if order:
            subprocess.run(['python3', 'reports.py', f'{update.effective_chat.id}', 'ord_all'])
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

async def contact_us(update: Update, context: CallbackContext):
    """Contact Us"""
    user_id = update.message.from_user.id
    await context.bot.send_message(
        chat_id=user_id,
        text="Please contact us at [Ocean Support](https://t.me/Ocean_bot).",
        parse_mode="markdown"
    )

async def change_language(update: Update, context: CallbackContext):
    """Change Language"""
    order = session.query(Order).filter(Order.username == update.message.from_user.id).first()
    if order:
        Amharic = KeyboardButton(text="Amharic")
        English = KeyboardButton(text="English")
        
        custom_keyboard = [[ Amharic, English ]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        await update.message.reply_text(
            'Pick your preffered language:',
            reply_markup=reply_markup
        )
        
        return await change_language_set(update, context)
    else:
        await update.message.reply_text(
            "You need to make an order first."
        )
        return ConversationHandler.END

async def change_language_set(update: Update, context: CallbackContext):
    lang = update.message.text
    user_id = update.message.from_user.id
    
    lang_change = change_lang(user_id, lang)
    
    if lang_change:
        logger.info("Language changed to %s for user %s.", lang, user_id)
        if lang == 'Amharic':
            await update.message.reply_text(
                "ቋንቋ በአማርኛ ተቀይሯል።"                
            )
        else:
            await update.message.reply_text(
                "Language changed to English."
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

async def skip_order(update: Update, context: CallbackContext):
    """Skip order"""
    user_id = update.effective_user.id
    logger.info("Order skipped for user %s.", user_id)
    await update.message.reply_text(
        "Order skipped.",
        reply_markup=ReplyKeyboardRemove()
    )
    
    await context.bot.send_message(
        chat_id=os.getenv('USERNAME'),
        text=f"Order skipped for this cycle only by subscriber  {user_id}.",
        parse_mode='markdown'
    )
    
    return ConversationHandler.END

async def sub_notice_handle(update: Update, context: CallbackContext):
    """Handle subscription notice"""
    if update.effective_message.text == 'Accept':
        return await order_laundry(update, context)
    elif update.effective_message.text == 'Skip':
        return await skip_order(update, context)
    elif update.effective_message.text == 'Cancel':
        return await cancel_sub(update, context)


    user_id = update.effective_user.id
    logger.info("Subscription notice sent to %s.", user_id)
    if update.effective_message.text == 'Reorder':
        return await order_laundry(update, context)

async def error_handler(update: Update, context: CallbackContext):
    """Log the error and handle it gracefully"""
    logger.error(msg="Exception occurred", exc_info=context.error)
    await update.message.reply_text('Sorry, an error occurred. Please try again.')

########################################################
def main():
    # bot runner
    application = Application.builder().token(TOKEN).build()
    
    # Commands
    lang_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r'^(Restart)$') & ~filters.COMMAND, start), CommandHandler('start', start)],
        states={
            LOCALIZER: [MessageHandler(filters.TEXT & ~filters.COMMAND, localizer)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r'^(order_laundry)$') & ~filters.COMMAND, order_laundry)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
            DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, details)],
            LOCATION: [MessageHandler(filters.LOCATION, location)],
            CONTACT: [MessageHandler(filters.CONTACT, contact)],
            MORE_CONTACT_CONFIRM: [MessageHandler(filters.Regex(r'^(Yes|No)$') & ~filters.COMMAND, more_contact_confirm)],
            MORE_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, more_contact)],
            SUBSCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, subscription_optin)],
            SUBSCRIPTION_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, subscription_type)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    application.add_handler(lang_conv)
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.Regex(r'^(Reorder)$'), reorder))
    application.add_handler(MessageHandler(filters.Regex(r'^(Accept|Cancel|Skip)$'), sub_notice_handle))
    application.add_handler(CommandHandler('cancel_subscription', cancel_sub))
    application.add_handler(CommandHandler("get_chat_id", get_chat_id))
    application.add_handler(CommandHandler("delete_subscriber", delete_subscriber))
    application.add_handler(CommandHandler("generate_report_subs", generate_report_sub))
    application.add_handler(CommandHandler("generate_report_orders", generate_report_ord))
    application.add_handler(CommandHandler("generate_report_all_orders", generate_report_all_ord))
    application.add_handler(CommandHandler("change_language", change_language))
    application.add_handler(CommandHandler("contact_us", contact_us))
    application.add_handler(CommandHandler("about", about))

    # Run bot
    application.run_polling(allowed_updates=Update.ALL_TYPES, poll_interval=1.0)


if __name__ == '__main__':
    tracemalloc.start()
    
    main()
    
    tracemalloc.stop()
    print(tracemalloc.get_object_traceback())
