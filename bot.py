import asyncio
import random
import string
from pyrogram import Client, filters, enums
from pyrogram.types import BotCommand
import logging
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
SOURCE_CHANNEL = "https://t.me/solo_leveling_manhwa_tamil"
STORAGE_CHANNEL = -1002585582507  # Make sure this is correct

# Initialize the Client
app = Client(
    "SoloLevelingManhwaTamilBot",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH
)

# User state management
user_states = {}

async def debug_channel_access():
    """Debug function to check channel access"""
    try:
        chat = await app.get_chat(STORAGE_CHANNEL)
        logger.info(f"Channel access successful. Channel info: {chat}")
        return True
    except Exception as e:
        logger.error(f"Failed to access channel: {e}")
        return False

def get_media_info(message):
    """Extract media information from message"""
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

async def store_file_in_channel(file_data):
    """Store file in private channel and return message ID"""
    try:
        if not await debug_channel_access():
            raise Exception("Cannot access storage channel")

        if file_data["file_type"] == "text":
            msg = await app.send_message(STORAGE_CHANNEL, file_data["file_name"])
        else:
            send_func = getattr(app, f"send_{file_data['file_type']}")
            msg = await send_func(
                STORAGE_CHANNEL,
                file_data["file_id"],
                caption=file_data.get("caption")
            )
        return msg.id
    except Exception as e:
        logger.error(f"Error storing file: {e}")
        raise

async def get_file_from_channel(message_id):
    """Retrieve file from storage channel"""
    try:
        return await app.get_messages(STORAGE_CHANNEL, message_id)
    except Exception as e:
        logger.error(f"Error retrieving file: {e}")
        raise

def shorten_url(long_url):
    """Shorten URL using GPLinks API"""
    try:
        params = {
            'api': SHORTENER_API,
            'url': urllib.parse.quote_plus(long_url),
            'format': 'json'
        }
        response = requests.get(SHORTENER_URL, params=params, timeout=10)
        if response.status_code == 200 and (data := response.json()).get("status") == "success":
            return data.get("shortenedUrl")
    except Exception as e:
        logger.error(f"URL shortening failed: {e}")
    return None

async def set_bot_commands():
    """Set bot commands menu"""
    commands = [
        BotCommand("start", "Show start message"),
        BotCommand("batch", "Upload files (Owner)"),
    ]
    await app.set_bot_commands(commands)
    logger.info("Bot commands set successfully")

@app.on_message(filters.command("start"))
async def start_handler(client, message):
    """Handle /start command"""
    try:
        if len(message.command) > 1:
            # Handle file access via start parameter
            file_id = message.command[1]
            try:
                msg = await get_file_from_channel(int(file_id))
                await msg.copy(message.chat.id)
            except:
                await message.reply("⚠️ File not found or inaccessible")
            return

        # Regular start message
        await message.reply(
            f"Hello {message.from_user.first_name}!\n\n"
            f"I'm a file sharing bot for Solo Leveling Manhwa Tamil.\n"
            f"Source: {SOURCE_CHANNEL}",
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Start handler error: {e}")

@app.on_message(filters.command("batch") & filters.user(OWNER_IDS))
async def batch_handler(client, message):
    """Handle batch upload initialization"""
    user_states[message.from_user.id] = {"mode": "batch"}
    await message.reply(
        "📤 Batch upload mode activated!\n"
        "Send me files or text messages to store.\n"
        "Use /cancel to exit this mode."
    )

@app.on_message(filters.command("cancel") & filters.user(OWNER_IDS))
async def cancel_handler(client, message):
    """Cancel current operation"""
    user_states.pop(message.from_user.id, None)
    await message.reply("❌ Operation cancelled")

@app.on_message(filters.private & (filters.media | filters.text) & filters.user(OWNER_IDS))
async def media_handler(client, message):
    """Handle media/files from owners"""
    user_id = message.from_user.id
    if user_states.get(user_id, {}).get("mode") != "batch":
        return

    try:
        if message.text and not message.text.startswith('/'):
            file_data = {
                "file_type": "text",
                "file_name": message.text,
                "file_id": None,
                "caption": None
            }
        else:
            file_data = get_media_info(message)
            if not file_data:
                return

        # Store the file
        file_id = await store_file_in_channel(file_data)
        bot_username = (await app.get_me()).username
        share_link = f"https://t.me/{bot_username}?start={file_id}"
        short_url = shorten_url(share_link) or share_link

        await message.reply(
            f"✅ File stored successfully!\n\n"
            f"🔗 Permanent Link: {share_link}\n"
            f"🔗 Short URL: {short_url}"
        )
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")
        logger.error(f"Media handler error: {e}")

async def main():
    """Main async function to run the bot"""
    await app.start()
    logger.info("Bot started successfully")
    await set_bot_commands()
    
    # Keep the bot running
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        loop.run_until_complete(app.stop())
        loop.close()
