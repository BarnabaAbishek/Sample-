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

# Channel information - FIXED FORMAT
SOURCE_CHANNEL = "solo_leveling_manhwa_tamil"  # Just the username without @
STORAGE_CHANNEL = -1002585582507  # Using "me" sends to saved messages, or use a valid channel ID

app = Client("Solo_Leveling_Manhwa_tamil_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

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

async def check_user_joined_channel(client, user_id):
    """Check if user has joined the required channel"""
    try:
        # Alternative method that doesn't require admin privileges
        try:
            chat = await client.get_chat(SOURCE_CHANNEL)
            invite_link = chat.invite_link
            return True
        except:
            # If we can't get invite link, use a different approach
            try:
                await client.join_chat(SOURCE_CHANNEL)
                return True
            except:
                return False
    except Exception as e:
        logger.error(f"Error checking channel membership: {e}")
        return False

# Command Handlers
@app.on_message(filters.command("start"))
async def start(client, message):
    user = message.from_user
    user_database.add(user.id)  # Add user to broadcast database
    
    # Check if user has joined channel
    has_joined = await check_user_joined_channel(client, user.id)
    
    image_id = "AgACAgUAAxkBAAMJZ_CtleL6YOgZ07mHjUFGm74AAXSZAAI0xDEbSH-BV_h91mGMeTcBAAgBAAMCAAN4AAceBA"
    
    if len(message.command) == 1:
        if not has_joined:
            join_button = InlineKeyboardMarkup([[
                InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{SOURCE_CHANNEL}")
            ]])
            
            caption = f"""
*Hᴇʟʟᴏ {user.first_name}*

*You must join our channel to access the files*

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

*I Aᴍ Aɴɪᴍᴇ Bᴏᴛ I Wɪʟʟ Gɪᴠᴇ Yᴏᴜ Aɴɪᴍᴇ Fɪʟᴇs Fʀᴏᴍ* [Tᴀᴍɪʟ Dubbed Aɴɪᴍᴇ](https://t.me/{SOURCE_CHANNEL})
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
*Hᴇʟʟᴏ {user.first_name}*

*You must join our channel to access this file*

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
            try:
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
    
    # Check if user has joined channel
    has_joined = await check_user_joined_channel(client, user_id)
    
    if not has_joined:
        await callback_query.answer("❌ Please join the channel first!", show_alert=True)
        return
    
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
    user_states[user_id] = {"mode": "batch", "files": []}
    await message.reply(
        "📤 *Batch Upload Mode Activated!*\n\n"
        "Send me multiple files (documents, videos, photos, audio, or text).\n"
        "When finished, send /done to generate a single link for all files.\n"
        "To cancel, send /cancel.",
        parse_mode=enums.ParseMode.MARKDOWN
    )

@app.on_message(filters.command("broadcast") & filters.user(OWNER_IDS))
async def broadcast_command(client, message):
    user_id = message.from_user.id
    user_states[user_id] = {"mode": "broadcast", "content": []}
    await message.reply(
        "📢 *Broadcast Mode Activated!*\n\n"
        "Send me the message or media you want to broadcast.\n"
        "It will be sent to all users who have started the bot.\n"
        "When finished, send /done to send.\n"
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

            bot_username = (await client.get_me()).username
            
            # Store all files in a single message in the storage channel
            try:
                caption = "📦 *Batch Files Collection*\n\n"
                for i, file_data in enumerate(state["files"], 1):
                    caption += f"{i}. {file_data.get('file_name', 'Unnamed')}\n"
                
                # Store the caption message in the channel
                message_id = await client.send_message(
                    STORAGE_CHANNEL,
                    caption
                ).id
                
                # Store all files in the channel
                for file_data in state["files"]:
                    try:
                        if file_data["file_type"] == "text":
                            await client.send_message(
                                STORAGE_CHANNEL,
                                file_data["file_name"],
                                reply_to_message_id=message_id
                            )
                        else:
                            await getattr(client, f"send_{file_data['file_type']}")(
                                STORAGE_CHANNEL,
                                file_data["file_id"],
                                caption=file_data.get("caption"),
                                reply_to_message_id=message_id
                            )
                    except Exception as e:
                        logger.error(f"Error storing file in batch: {e}")
                
                # Generate single share link
                share_link = f"https://t.me/{bot_username}?start={message_id}"
                
                await message.reply(
                    f"✅ *Batch Upload Complete!*\n\n"
                    f"🔗 Single Link for all files:\n`{share_link}`",
                    parse_mode=enums.ParseMode.MARKDOWN
                )
            except Exception as e:
                await message.reply(f"❌ Error creating batch: {e}")
            
            user_states.pop(user_id, None)

        elif state["mode"] == "broadcast":
            if not state["content"]:
                await message.reply("❌ No content to broadcast! Operation canceled.")
                user_states.pop(user_id, None)
                return

            # Send broadcast to all users
            success = 0
            failed = 0
            total = len(user_database)
            
            status_msg = await message.reply(f"📢 Starting broadcast to {total} users...")
            
            for user_id in user_database:
                try:
                    for content in state["content"]:
                        if content["type"] == "text":
                            await client.send_message(user_id, content["content"])
                        elif content["type"] == "photo":
                            await client.send_photo(
                                user_id,
                                content["file_id"],
                                caption=content.get("caption")
                            )
                        elif content["type"] == "video":
                            await client.send_video(
                                user_id,
                                content["file_id"],
                                caption=content.get("caption")
                            )
                        elif content["type"] == "document":
                            await client.send_document(
                                user_id,
                                content["file_id"],
                                caption=content.get("caption")
                            )
                        elif content["type"] == "audio":
                            await client.send_audio(
                                user_id,
                                content["file_id"],
                                caption=content.get("caption")
                            )
                    success += 1
                except Exception as e:
                    failed += 1
                    logger.error(f"Error broadcasting to {user_id}: {e}")
                
                # Small delay to avoid flooding
                await asyncio.sleep(0.1)
            
            await status_msg.edit_text(
                f"✅ Broadcast completed!\n\n"
                f"• Total users: {total}\n"
                f"• Successfully sent: {success}\n"
                f"• Failed: {failed}"
            )
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

    elif state["mode"] == "broadcast":
        if message.text and not message.text.startswith('/'):
            state["content"].append({
                "type": "text",
                "content": message.text
            })
            await message.reply(f"✅ Text added to broadcast!\nSend /done when ready.")
        
        elif media := get_media_info(message):
            state["content"].append({
                "type": media["file_type"],
                "file_id": media["file_id"],
                "caption": media["caption"]
            })
            await message.reply(f"✅ Media added to broadcast!\nSend /done when ready.")

async def set_commands():
    await app.set_bot_commands([
        BotCommand("start", "Show start message"),
        BotCommand("batch", "Upload multiple files (Owner)"),
        BotCommand("broadcast", "Send message to all users (Owner)"),
    ])

app.start()
print("Bot started!")
app.loop.run_until_complete(set_commands())

try:
    asyncio.get_event_loop().run_forever()
except KeyboardInterrupt:
    print("Bot stopped!")
