import asyncio
import random
import string
from pyrogram import Client, filters, enums
from pyrogram.types import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = "YOUR_BOT_TOKEN"
API_ID = 1234567
API_HASH = "YOUR_API_HASH"
OWNER_IDS = [12345678, 87654321]  # Replace with your owner IDs

# Channel information
SOURCE_CHANNEL = "your_channel_username"  # Without @
STORAGE_CHANNEL = -1001234567890  # Your storage channel ID

app = Client("FileSharingBot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

# User state management
user_states = {}
user_database = set()

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

async def check_user_joined_channel(client, user_id):
    """Check if user has joined the required channel"""
    try:
        try:
            member = await client.get_chat_member(SOURCE_CHANNEL, user_id)
            return member.status not in [enums.ChatMemberStatus.LEFT, enums.ChatMemberStatus.BANNED]
        except Exception as e:
            logger.error(f"Error checking channel membership: {e}")
            return False
    except Exception as e:
        logger.error(f"Error in check_user_joined_channel: {e}")
        return False

# Command Handlers
@app.on_message(filters.command("start"))
async def start(client, message):
    user = message.from_user
    user_database.add(user.id)
    
    has_joined = await check_user_joined_channel(client, user.id)
    image_id = "YOUR_START_IMAGE_ID"  # Replace with your image ID
    
    if len(message.command) == 1:
        if not has_joined:
            join_button = InlineKeyboardMarkup([[
                InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{SOURCE_CHANNEL}")
            ]])
            
            caption = f"""
*Hello {user.first_name}*

You must join our channel to access the files.

Please join the channel below:
            """
            await client.send_photo(
                chat_id=message.chat.id,
                photo=image_id,
                caption=caption,
                reply_markup=join_button,
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            caption = f"""
*Hello {user.first_name}*

I am a File Sharing Bot. I will give you files from our channel.

Channel: @{SOURCE_CHANNEL}
            """
            await client.send_photo(
                chat_id=message.chat.id,
                photo=image_id,
                caption=caption,
                parse_mode=enums.ParseMode.MARKDOWN
            )
    
    elif len(message.command) > 1:
        unique_id = message.command[1]
        
        if not has_joined:
            join_button = InlineKeyboardMarkup([[
                InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{SOURCE_CHANNEL}"),
                InlineKeyboardButton("📥 Get File", callback_data=f"getfile_{unique_id}")
            ]])
            
            caption = f"""
*Hello {user.first_name}*

You must join our channel to access this file.

Please join the channel below:
            """
            await client.send_photo(
                chat_id=message.chat.id,
                photo=image_id,
                caption=caption,
                reply_markup=join_button,
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            try:
                # Get the batch message
                batch_message = await client.get_messages(STORAGE_CHANNEL, int(unique_id))
                
                if not batch_message:
                    await message.reply("❌ Batch not found!")
                    return
                
                # Get all files in this batch (replies to the batch message)
                batch_files = []
                async for msg in client.get_chat_history(
                    chat_id=STORAGE_CHANNEL,
                    limit=100,
                    offset_id=int(unique_id),
                    reverse=True
                ):
                    if msg.reply_to_message_id == batch_message.id:
                        batch_files.append(msg)
                
                if not batch_files:
                    await message.reply("❌ No files found in this batch!")
                    return
                
                # Send each file to user
                for file_msg in batch_files:
                    try:
                        if file_msg.text:
                            await client.send_message(message.chat.id, file_msg.text)
                        elif file_msg.document:
                            await file_msg.copy(message.chat.id)
                        elif file_msg.video:
                            await file_msg.copy(message.chat.id)
                        elif file_msg.photo:
                            await file_msg.copy(message.chat.id)
                        elif file_msg.audio:
                            await file_msg.copy(message.chat.id)
                        # Small delay between files
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        logger.error(f"Error sending file: {e}")
                        continue
                
                await message.reply("✅ All files have been sent!")
                
            except Exception as e:
                logger.error(f"Error in batch retrieval: {e}")
                await message.reply("❌ Failed to retrieve files. They may have been deleted.")

@app.on_message(filters.command("batch") & filters.user(OWNER_IDS))
async def batch_command(client, message):
    user_id = message.from_user.id
    user_states[user_id] = {"mode": "batch", "files": []}
    await message.reply(
        "📤 Batch Upload Mode Activated!\n\n"
        "Send me multiple files (documents, videos, photos, audio, or text).\n"
        "When finished, send /done to generate a single link for all files.\n"
        "To cancel, send /cancel.",
        parse_mode=enums.ParseMode.MARKDOWN
    )

@app.on_message(filters.command(["done", "cancel"]) & filters.user(OWNER_IDS))
async def handle_actions(client, message):
    user_id = message.from_user.id
    if user_id not in user_states:
        await message.reply("❌ No active operation to complete or cancel.")
        return

    state = user_states[user_id]
    action = message.command[0]

    if action == "cancel":
        user_states.pop(user_id, None)
        await message.reply("❌ Operation canceled.")
        return

    if action == "done":
        if state["mode"] == "batch":
            if not state["files"]:
                await message.reply("❌ No files received! Operation canceled.")
                user_states.pop(user_id, None)
                return

            try:
                bot_username = (await client.get_me()).username
                
                # Create batch header message
                batch_message = await client.send_message(
                    STORAGE_CHANNEL,
                    f"📦 Batch Files Collection\n\n"
                    f"• Total files: {len(state['files'])}\n"
                    f"• Created at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                
                # Upload all files as replies
                for file_data in state["files"]:
                    try:
                        if file_data["file_type"] == "text":
                            await client.send_message(
                                STORAGE_CHANNEL,
                                file_data["file_name"],
                                reply_to_message_id=batch_message.id
                            )
                        else:
                            await getattr(client, f"send_{file_data['file_type']}")(
                                STORAGE_CHANNEL,
                                file_data["file_id"],
                                caption=file_data.get("caption"),
                                reply_to_message_id=batch_message.id
                            )
                        # Small delay between uploads
                        await asyncio.sleep(1)
                    except Exception as e:
                        logger.error(f"Error uploading file: {e}")
                        continue
                
                # Generate share link
                share_link = f"https://t.me/{bot_username}?start={batch_message.id}"
                
                await message.reply(
                    f"✅ Batch Upload Complete!\n\n"
                    f"🔗 Share this link:\n`{share_link}`\n\n"
                    f"Total files: {len(state['files'])}",
                    parse_mode=enums.ParseMode.MARKDOWN
                )
            except Exception as e:
                await message.reply(f"❌ Error creating batch: {str(e)}")
            
            user_states.pop(user_id, None)

@app.on_message(filters.private & (filters.media | filters.text) & filters.user(OWNER_IDS))
async def media_text_handler(client, message):
    user_id = message.from_user.id
    state = user_states.get(user_id, {})

    if not state:
        return

    if state["mode"] == "batch":
        if message.text and not message.text.startswith('/'):
            file_data = {
                "file_id": None, 
                "file_name": message.text, 
                "file_type": "text",
                "caption": None
            }
            state["files"].append(file_data)
            await message.reply(f"✅ Text added to batch! Total files: {len(state['files'])}\nSend /done when ready.")
        
        elif media := get_media_info(message):
            state["files"].append(media)
            await message.reply(f"✅ Media added to batch! Total files: {len(state['files'])}\nSend /done when ready.")

async def set_commands():
    await app.set_bot_commands([
        BotCommand("start", "Show start message"),
        BotCommand("batch", "Upload multiple files (Owner)"),
    ])

app.start()
print("Bot started!")
app.loop.run_until_complete(set_commands())

try:
    asyncio.get_event_loop().run_forever()
except KeyboardInterrupt:
    print("Bot stopped!")
