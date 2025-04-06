import asyncio
import random
import string
from pyrogram import Client, filters, enums
from pyrogram.types import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton
import logging
from datetime import datetime
import os

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

# Channel information
STORAGE_CHANNEL_ID = -1002585582507  # Your private channel for file storage
REQUIRED_CHANNEL = "@solo_leveling_manhwa_tamil"  # Only one required channel
REQUIRED_CHANNEL_LINK = "https://t.me/solo_leveling_manhwa_tamil"

app = Client("tdafilesharebot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

# User state management
user_states = {}
file_storage = {}  # In-memory storage for file references

def generate_unique_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

def get_media_info(message):
    media_info = None
    caption = message.caption if message.caption else None
    
    for media_type in ["document", "video", "photo", "audio"]:
        if media := getattr(message, media_type, None):
            media_info = {
                "file_id": media.file_id,
                "file_name": getattr(media, "file_name", f"{media_type}_{media.file_id[:6]}"),
                "file_type": media_type,
                "caption": caption
            }
            break
    
    return media_info

async def check_channel_membership(client, user_id, channel):
    try:
        member = await client.get_chat_member(channel, user_id)
        return member.status not in [enums.ChatMemberStatus.LEFT, enums.ChatMemberStatus.BANNED]
    except Exception as e:
        logger.error(f"Error checking channel {channel}: {e}")
        return False

async def send_individual_file(client, chat_id, files):
    for file in files:
        try:
            if file["file_type"] == "text":
                await client.send_message(chat_id, file["file_name"])
            else:
                if file["file_type"] == "photo":
                    await client.send_photo(
                        chat_id=chat_id,
                        photo=file["file_id"],
                        caption=file.get("caption", None)
                    )
                elif file["file_type"] == "video":
                    await client.send_video(
                        chat_id=chat_id,
                        video=file["file_id"],
                        caption=file.get("caption", None)
                    )
                elif file["file_type"] == "document":
                    await client.send_document(
                        chat_id=chat_id,
                        document=file["file_id"],
                        caption=file.get("caption", None)
                    )
                elif file["file_type"] == "audio":
                    await client.send_audio(
                        chat_id=chat_id,
                        audio=file["file_id"],
                        caption=file.get("caption", None)
                    )
        except Exception as e:
            logger.error(f"Error sending file: {e}")
            await client.send_message(chat_id, f"Error sending file: {e}")

# Command Handlers
@app.on_message(filters.command("start"))
async def start(client, message):
    user = message.from_user
    has_joined = await check_channel_membership(client, user.id, REQUIRED_CHANNEL)
    
    image_id = "AgACAgUAAxkBAAIB5GfyOawwpZD9TlziQtEHwccx98qsAAIzwjEbs7aQV_IRtSBrISN8AAgBAAMCAAN4AAceBA"
    image_id1 = "AgACAgUAAxkBAAICMWfyPdeBpVdBUzcaTvivBon4a-32AAI7wjEbs7aQVxPJtV8TqXdUAAgBAAMCAAN4AAceBA"
    
    join_button = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 JOIN CHANNEL", url=REQUIRED_CHANNEL_LINK)]
    ])
    
    if len(message.command) == 1:
        if not has_joined:
            caption = f"""
*Hᴇʟʟᴏ {user.first_name}*

*You must join our channel to get anime files*

*Please join the channel below:*
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
*Hᴇʟʟᴏ {user.first_name}*

*I Aᴍ Aɴɪᴍᴇ Bᴏᴛ I Wɪʟʟ Gɪᴠᴇ Yᴏᴜ Aɴɪᴍᴇ Fɪʟᴇs*
            """
            await client.send_photo(
                chat_id=message.chat.id,
                photo=image_id1,
                caption=caption,
                parse_mode=enums.ParseMode.MARKDOWN
            )
    
    elif len(message.command) > 1:
        unique_id = message.command[1]
        
        if not has_joined:
            caption = f"""
*Hᴇʟʟᴏ {user.first_name}*

*You must join our channel to get this file*

*Please join the channel below:*
            """
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 JOIN CHANNEL", url=REQUIRED_CHANNEL_LINK)],
                [InlineKeyboardButton("📥 GET FILE", callback_data=f"getfile_{unique_id}")]
            ])
            
            await client.send_photo(
                chat_id=message.chat.id,
                photo=image_id,
                caption=caption,
                reply_markup=buttons,
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            # Check in-memory storage for the file
            if unique_id in file_storage:
                try:
                    file_data = file_storage[unique_id]
                    await send_individual_file(client, message.chat.id, file_data["files"])
                except Exception as e:
                    logger.error(f"Error retrieving file: {e}")
                    await message.reply("❌ Error retrieving file!")
            else:
                await message.reply("❌ File not found or expired!")

@app.on_callback_query(filters.regex("^getfile_"))
async def handle_getfile(client, callback_query):
    user_id = callback_query.from_user.id
    unique_id = callback_query.data.split("_")[1]
    
    has_joined = await check_channel_membership(client, user_id, REQUIRED_CHANNEL)
    
    if has_joined:
        if unique_id in file_storage:
            try:
                file_data = file_storage[unique_id]
                await callback_query.message.delete()
                await send_individual_file(client, callback_query.message.chat.id, file_data["files"])
            except Exception as e:
                logger.error(f"Error retrieving file: {e}")
                await callback_query.answer("❌ Error retrieving file!", show_alert=True)
        else:
            await callback_query.answer("❌ File not found or expired!", show_alert=True)
    else:
        await callback_query.answer("❌ Please join our channel first!", show_alert=True)

@app.on_message(filters.command("batch") & filters.user(OWNER_IDS))
async def batch_command(client, message):
    user_id = message.from_user.id
    user_states[user_id] = {"mode": "batch", "files": []}
    await message.reply(
        "📤 *Batch Mode Activated!*\n\n"
        "Send me multiple files (documents, videos, photos, audio, or text).\n"
        "When finished, send /done to generate a link.\n"
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

    state = user_states[user_id]
    action = message.command[0]

    if action == "done":
        if state["mode"] == "batch":
            if not state["files"]:
                await message.reply("❌ No files or text received! Batch canceled.")
                user_states.pop(user_id, None)
                return

            unique_id = generate_unique_id()
            file_data = {
                "files": state["files"],
                "uploaded_by": user_id,
                "created_at": datetime.now().isoformat()
            }

            try:
                # Store in memory
                file_storage[unique_id] = file_data
                
                # Also store in channel for persistence (optional)
                await client.send_message(
                    STORAGE_CHANNEL_ID,
                    f"FileID:{unique_id}\nFiles:{len(file_data['files'])}"
                )
            except Exception as e:
                await message.reply(f"❌ Error saving file: {e}")
                return

            bot_username = (await client.get_me()).username
            share_link = f"https://t.me/{bot_username}?start={unique_id}"
            
            await message.reply(
                f"✅ *Batch Upload Complete!*\n\n"
                f"🔗 Share Link: `{share_link}`\n\n"
                f"📌 Files will be stored permanently.",
                parse_mode=enums.ParseMode.MARKDOWN
            )
            user_states.pop(user_id, None)
    
    elif action == "cancel":
        user_states.pop(user_id, None)
        await message.reply("❌ Operation canceled.")

@app.on_message(filters.private & (filters.media | filters.text) & filters.user(OWNER_IDS))
async def media_text_handler(client, message):
    user_id = message.from_user.id
    state = user_states.get(user_id, {})

    if not state:
        await message.reply("ℹ Please use /batch first to start uploading.")
        return

    if state["mode"] == "batch":
        if message.text and not message.text.startswith('/'):
            state["files"].append({
                "file_id": None, 
                "file_name": message.text, 
                "file_type": "text",
                "caption": None
            })
            await message.reply(f"✅ Text added to batch! Total items: {len(state['files'])}\nSend /done when ready.")
        
        elif media := get_media_info(message):
            state["files"].append(media)
            reply_text = f"✅ Media added to batch! Total items: {len(state['files'])}"
            if media["caption"]:
                reply_text += f"\nCaption: {media['caption']}"
            reply_text += "\nSend /done when ready."
            await message.reply(reply_text)

async def set_commands():
    await app.set_bot_commands([
        BotCommand("start", "Show start message"),
        BotCommand("batch", "Upload files (Owner)")
    ])

@app.on_message(filters.chat(STORAGE_CHANNEL_ID) & filters.text)
async def store_file_reference(client, message):
    """Store file references from the storage channel"""
    try:
        if message.text.startswith("FileID:"):
            parts = message.text.split("\n")
            if len(parts) >= 2:
                unique_id = parts[0].split(":")[1]
                # We just store the message ID as reference
                file_storage[unique_id] = {
                    "message_id": message.id,
                    "channel_id": STORAGE_CHANNEL_ID
                }
    except Exception as e:
        logger.error(f"Error processing storage message: {e}")

async def load_existing_files():
    """Load existing file references from storage channel"""
    try:
        async for message in client.get_chat_history(STORAGE_CHANNEL_ID, limit=100):
            if message.text and message.text.startswith("FileID:"):
                parts = message.text.split("\n")
                if len(parts) >= 2:
                    unique_id = parts[0].split(":")[1]
                    file_storage[unique_id] = {
                        "message_id": message.id,
                        "channel_id": STORAGE_CHANNEL_ID
                    }
    except Exception as e:
        logger.error(f"Error loading existing files: {e}")

app.start()
print("Bot started!")
app.loop.run_until_complete(set_commands())
app.loop.run_until_complete(load_existing_files())

try:
    asyncio.get_event_loop().run_forever()
except KeyboardInterrupt:
    print("Bot stopped!")
