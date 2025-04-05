import asyncio
import random
import string
from pyrogram import Client, filters, enums
from pyrogram.types import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton, Message
import logging
from datetime import datetime

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
SOURCE_CHANNEL = "solo_leveling_manhwa_tamil"  # Without @
STORAGE_CHANNEL = "SoloLevelingStorage"  # Use username or make sure bot is admin in channel

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
        member = await client.get_chat_member(SOURCE_CHANNEL, user_id)
        return member.status in [
            enums.ChatMemberStatus.OWNER,
            enums.ChatMemberStatus.ADMINISTRATOR,
            enums.ChatMemberStatus.MEMBER
        ]
    except Exception as e:
        logger.error(f"Error checking channel membership: {e}")
        return False

async def send_file_to_user(client, stored_message, chat_id):
    """Send the appropriate file type to user"""
    try:
        if stored_message.text:
            await client.send_message(chat_id, stored_message.text)
        elif stored_message.document:
            await stored_message.copy(chat_id)
        elif stored_message.video:
            await stored_message.copy(chat_id)
        elif stored_message.photo:
            await stored_message.copy(chat_id)
        elif stored_message.audio:
            await stored_message.copy(chat_id)
        return True
    except Exception as e:
        logger.error(f"Error sending file to user: {e}")
        return False

# Command Handlers
@app.on_message(filters.command("start"))
async def start(client, message):
    user = message.from_user
    user_database.add(user.id)
    
    has_joined = await check_user_joined_channel(client, user.id)
    
    image_id = "AgACAgUAAxkBAAMJZ_CtleL6YOgZ07mHjUFGm74AAXSZAAI0xDEbSH-BV_h91mGMeTcBAAgBAAMCAAN4AAceBA"
    
    if len(message.command) == 1:
        if not has_joined:
            join_button = InlineKeyboardMarkup([[
                InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{SOURCE_CHANNEL}")
            ]])
            
            await client.send_photo(
                chat_id=message.chat.id,
                photo=image_id,
                caption=f"Hello {user.first_name}!\n\nYou must join our channel to access the files.",
                reply_markup=join_button
            )
        else:
            await client.send_photo(
                chat_id=message.chat.id,
                photo=image_id,
                caption=f"Hello {user.first_name}!\n\nI'm a file sharing bot for [our channel](https://t.me/{SOURCE_CHANNEL})."
            )
    
    elif len(message.command) > 1:
        unique_id = message.command[1]
        
        if not has_joined:
            join_button = InlineKeyboardMarkup([[
                InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{SOURCE_CHANNEL}"),
                InlineKeyboardButton("📥 Get File", callback_data=f"getfile_{unique_id}")
            ]])
            
            await client.send_photo(
                chat_id=message.chat.id,
                photo=image_id,
                caption=f"Hello {user.first_name}!\n\nYou must join our channel to access this file.",
                reply_markup=join_button
            )
        else:
            try:
                message_id = int(unique_id)
                stored_message = await get_file_from_channel(client, message_id)
                await send_file_to_user(client, stored_message, message.chat.id)
            except Exception as e:
                await message.reply("❌ Failed to retrieve file. It may have been deleted.")

@app.on_callback_query(filters.regex("^getfile_"))
async def handle_getfile(client, callback_query):
    user_id = callback_query.from_user.id
    message_id = int(callback_query.data.split("_")[1])
    
    has_joined = await check_user_joined_channel(client, user_id)
    
    if not has_joined:
        await callback_query.answer("❌ Please join the channel first!", show_alert=True)
        return
    
    try:
        stored_message = await get_file_from_channel(client, message_id)
        await callback_query.message.delete()
        await send_file_to_user(client, stored_message, callback_query.message.chat.id)
    except Exception as e:
        await callback_query.answer("❌ File not found or deleted!", show_alert=True)

@app.on_message(filters.command("batch") & filters.user(OWNER_IDS))
async def batch_command(client, message):
    user_id = message.from_user.id
    user_states[user_id] = {"mode": "batch", "files": []}
    await message.reply(
        "📤 Batch Upload Mode Activated!\n\n"
        "Send me multiple files (documents, videos, photos, audio, or text).\n"
        "When finished, send /done to generate a single link for all files.\n"
        "To cancel, send /cancel."
    )

@app.on_message(filters.command("broadcast") & filters.user(OWNER_IDS))
async def broadcast_command(client, message):
    user_id = message.from_user.id
    user_states[user_id] = {"mode": "broadcast", "content": []}
    await message.reply(
        "📢 Broadcast Mode Activated!\n\n"
        "Send me the message or media you want to broadcast.\n"
        "It will be sent to all users who have started the bot.\n"
        "When finished, send /done to send.\n"
        "To cancel, send /cancel."
    )

@app.on_message(filters.private & ~filters.user(OWNER_IDS) & ~filters.command("start"))
async def reject_messages(client, message):
    await message.reply("❌ I'm a file sharing bot. Please use the shared links to access files.")

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
            batch_id = generate_unique_id()
            batch_message = f"📦 Batch Files - {batch_id}\n\n"
            
            file_ids = []
            for file_data in state["files"]:
                try:
                    message_id = await store_file_in_channel(client, file_data)
                    file_ids.append(str(message_id))
                    batch_message += f"📄 {file_data.get('file_name', 'Unnamed')}\n"
                except Exception as e:
                    batch_message += f"❌ Error uploading file: {e}\n"
            
            batch_message_obj = await client.send_message(STORAGE_CHANNEL, batch_message)
            share_link = f"https://t.me/{bot_username}?start={batch_message_obj.id}"
            
            await message.reply(
                f"✅ Batch Upload Complete!\n\n"
                f"🔗 Single Link for all files:\n{share_link}\n\n"
                f"Total files: {len(state['files'])}"
            )
            user_states.pop(user_id, None)

        elif state["mode"] == "broadcast":
            if not state["content"]:
                await message.reply("❌ No content to broadcast! Operation canceled.")
                user_states.pop(user_id, None)
                return

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

async def main():
    await app.start()
    print("Bot started!")
    await set_commands()
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped!")
