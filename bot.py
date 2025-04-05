import asyncio
import random
import string
from pyrogram import Client, filters, enums
from pyrogram.types import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton
import logging
from datetime import datetime
import requests
import urllib.parse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = "8047171670:AAE6F8uClZBXD33HozUeAUAe2USxNWMyu50"
API_ID = 24360857
API_HASH = "0924b59c45bf69cdfafd14188fb1b778"
OWNER_IDS = [5891854177, 6611564855]
SHORTENER_API = "3884abaadd7698d75583946b89a88d7430594432"
SHORTENER_URL = "https://api.gplinks.com/api"

# Channel information
SOURCE_CHANNEL = "https://t.me/solo_leveling_manhwa_tamil"

# Storage channel (private channel where files will be stored)
STORAGE_CHANNEL = -1002585582507  # Replace with your private channel ID

app = Client("Solo Leveling Manhwa tamil", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

# User state management
user_states = {}

def generate_unique_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

def get_media_info(message):
    for media_type in ["document", "video", "photo", "audio"]:
        if media := getattr(message, media_type, None):
            return {
                "file_id": media.file_id,
                "file_name": getattr(media, "file_name", f"{media_type}_{media.file_id[:6]}"),
                "file_type": media_type,
                "caption": message.caption,
                "mime_type": getattr(media, "mime_type", None),
                "file_size": getattr(media, "file_size", None)
            }
    return None

async def store_file_in_channel(client, file_data):
    """Store file in private channel and return message ID"""
    try:
        if file_data["file_type"] == "text":
            message = await client.send_message(
                STORAGE_CHANNEL,
                file_data["file_name"]
            )
        else:
            message = await getattr(client, f"send_{file_data['file_type']}")(
                STORAGE_CHANNEL,
                file_data["file_id"],
                caption=file_data.get("caption")
            )
        return message.id
    except Exception as e:
        logger.error(f"Error storing file in channel: {e}")
        raise

async def get_file_from_channel(client, message_id):
    """Retrieve file from storage channel"""
    try:
        return await client.get_messages(STORAGE_CHANNEL, message_id)
    except Exception as e:
        logger.error(f"Error retrieving file from channel: {e}")
        raise

def shorten_url(long_url):
    """Shorten a URL using GPLinks API"""
    try:
        encoded_url = urllib.parse.quote_plus(long_url)
        params = {
            'api': SHORTENER_API,
            'url': encoded_url,
            'format': 'json'
        }
        
        response = requests.get(SHORTENER_URL, params=params, timeout=10)
        response_data = response.json()
        
        if response.status_code == 200 and response_data.get("status") == "success":
            return response_data.get("shortenedUrl")
        return None
            
    except Exception as e:
        logger.error(f"Error shortening URL: {e}")
        return None

# Command Handlers
@app.on_message(filters.command("start"))
async def start(client, message):
    user = message.from_user
    
    image_id = "AgACAgUAAxkBAAMJZ_CtleL6YOgZ07mHjUFGm74AAXSZAAI0xDEbSH-BV_h91mGMeTcBAAgBAAMCAAN4AAceBA"
    
    if len(message.command) == 1:
        caption = f"""
*Hᴇʟʟᴏ {user.first_name}*

*I Aᴍ Aɴɪᴍᴇ Bᴏᴛ I Wɪʟʟ Gɪᴠᴇ Yᴏᴜ Aɴɪᴍᴇ Fɪʟᴇs Fʀᴏᴍ* [Tᴀᴍɪʟ Dubbed Aɴɪᴍᴇ]({SOURCE_CHANNEL})
        """
        await client.send_photo(
            chat_id=message.chat.id,
            photo=image_id,
            caption=caption,
            parse_mode=enums.ParseMode.MARKDOWN
        )
    
    elif len(message.command) > 1:
        unique_id = message.command[1]
        try:
            # Retrieve file from storage channel
            message_id = int(unique_id)
            stored_message = await get_file_from_channel(client, message_id)
            
            if stored_message.text:
                await client.send_message(message.chat.id, stored_message.text)
            elif stored_message.document:
                await stored_message.copy(message.chat.id)
            elif stored_message.video:
                await stored_message.copy(message.chat.id)
            elif stored_message.photo:
                await stored_message.copy(message.chat.id)
            elif stored_message.audio:
                await stored_message.copy(message.chat.id)
        except Exception as e:
            await message.reply("❌ Failed to retrieve file. It may have been deleted.")

@app.on_callback_query(filters.regex("^getfile_"))
async def handle_getfile(client, callback_query):
    user_id = callback_query.from_user.id
    message_id = int(callback_query.data.split("_")[1])
    
    try:
        stored_message = await get_file_from_channel(client, message_id)
        await callback_query.message.delete()
        
        if stored_message.text:
            await client.send_message(callback_query.message.chat.id, stored_message.text)
        elif stored_message.document:
            await stored_message.copy(callback_query.message.chat.id)
        elif stored_message.video:
            await stored_message.copy(callback_query.message.chat.id)
        elif stored_message.photo:
            await stored_message.copy(callback_query.message.chat.id)
        elif stored_message.audio:
            await stored_message.copy(callback_query.message.chat.id)
    except Exception as e:
        await callback_query.answer("❌ File not found or deleted!", show_alert=True)

@app.on_message(filters.command("batch") & filters.user(OWNER_IDS))
async def batch_command(client, message):
    user_id = message.from_user.id
    user_states[user_id] = {"mode": "batch"}
    await message.reply(
        "📤 *File Upload Mode Activated!*\n\n"
        "Send me a file (document, video, photo, audio, or text).\n"
        "I will generate a shareable link for it.\n"
        "To cancel, send /cancel.",
        parse_mode=enums.ParseMode.MARKDOWN
    )

@app.on_message(filters.private & ~filters.user(OWNER_IDS) & ~filters.command("start"))
async def reject_messages(client, message):
    await message.reply("❌ Don't Send Me Messages Directly. I'm Only a File Sharing Bot!")

@app.on_message(filters.command(["done", "cancel"]) & filters.user(OWNER_IDS))
async def handle_actions(client, message):
    user_id = message.from_user.id
    if user_id not in user_states:
        await message.reply("❌ No active operation to complete or cancel.")
        return

    action = message.command[0]

    if action == "cancel":
        user_states.pop(user_id, None)
        await message.reply("❌ Operation canceled.")
        return

@app.on_message(filters.private & (filters.media | filters.text) & filters.user(OWNER_IDS))
async def media_text_handler(client, message):
    user_id = message.from_user.id
    state = user_states.get(user_id, {})

    if not state or state.get("mode") != "batch":
        return

    if message.text and not message.text.startswith('/'):
        file_data = {
            "file_id": None, 
            "file_name": message.text, 
            "file_type": "text",
            "caption": None
        }
    elif media := get_media_info(message):
        file_data = media
    else:
        return

    try:
        # Store file in private channel
        message_id = await store_file_in_channel(client, file_data)
        
        # Generate shareable link
        bot_username = (await client.get_me()).username
        share_link = f"https://t.me/{bot_username}?start={message_id}"
        short_link = shorten_url(share_link) or share_link
        
        await message.reply(
            f"✅ *File Upload Complete!*\n\n"
            f"🔗 Permanent Link: `{share_link}`\n"
            f"🪄 Short Link: `{short_link}`",
            parse_mode=enums.ParseMode.MARKDOWN
        )
        
        user_states.pop(user_id, None)
    except Exception as e:
        await message.reply(f"❌ Error uploading file: {e}")

async def set_commands():
    await app.set_bot_commands([
        BotCommand("start", "Show start message"),
        BotCommand("batch", "Upload files (Owner)"),
    ])

app.start()
print("Bot started!")
app.loop.run_until_complete(set_commands())

try:
    asyncio.get_event_loop().run_forever()
except KeyboardInterrupt:
    print("Bot stopped!")
