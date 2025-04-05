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
BOT_TOKEN = "8047171670:AAE6F8uClZBXD33HozUeAUAe2USxNWMyu50"
API_ID = 24360857
API_HASH = "0924b59c45bf69cdfafd14188fb1b778"
OWNER_IDS = [5891854177, 6611564855]

# Channel information
SOURCE_CHANNEL = "solo_leveling_manhwa_tamil"  # Without @
STORAGE_CHANNEL = -1002585582507  # Your private channel ID where bot is admin

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
                chat_id=STORAGE_CHANNEL,
                text=file_data["file_name"]
            )
        else:
            send_method = getattr(client, f"send_{file_data['file_type']}")
            message = await send_method(
                chat_id=STORAGE_CHANNEL,
                file_id=file_data["file_id"],
                caption=file_data.get("caption")
            )
        return message.id
    except Exception as e:
        logger.error(f"Error storing file in channel: {e}")
        raise

async def get_file_from_channel(client, message_id):
    """Retrieve file from storage channel"""
    try:
        return await client.get_messages(
            chat_id=STORAGE_CHANNEL,
            message_ids=message_id
        )
    except Exception as e:
        logger.error(f"Error retrieving file from channel: {e}")
        raise

async def check_user_joined_channel(client, user_id):
    """Check if user has joined the required channel"""
    try:
        # Try to get chat member (requires bot to be admin)
        try:
            member = await client.get_chat_member(SOURCE_CHANNEL, user_id)
            return member.status not in [enums.ChatMemberStatus.LEFT, enums.ChatMemberStatus.BANNED]
        except Exception as admin_error:
            logger.warning(f"Admin check failed, trying alternative method: {admin_error}")
            
            # Alternative method using invite links
            try:
                chat = await client.get_chat(SOURCE_CHANNEL)
                if chat.invite_link:
                    # Try to join (will fail if already member)
                    try:
                        await client.join_chat(chat.invite_link)
                        return True
                    except:
                        # If join fails, assume already member
                        return True
            except Exception as e:
                logger.error(f"Alternative check failed: {e}")
                return False
    except Exception as e:
        logger.error(f"Error checking channel membership: {e}")
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

            # Store all files and create a single message with all file links
            bot_username = (await client.get_me()).username
            result_message = "📦 *Batch Upload Complete!*\n\n"
            result_message += "🔗 *Single Download Link:*\n"
            
            # Create a message containing all files
            try:
                if len(state["files"]) == 1:
                    # Single file - just forward it
                    file_data = state["files"][0]
                    if file_data["file_type"] == "text":
                        msg = await client.send_message(STORAGE_CHANNEL, file_data["file_name"])
                    else:
                        send_method = getattr(client, f"send_{file_data['file_type']}")
                        msg = await send_method(
                            STORAGE_CHANNEL,
                            file_data["file_id"],
                            caption=file_data.get("caption")
                        )
                    message_id = msg.id
                else:
                    # Multiple files - send as media group if possible
                    media_group = []
                    for file_data in state["files"]:
                        if file_data["file_type"] in ["photo", "video"]:
                            media_group.append((
                                enums.MessageMediaType(file_data["file_type"].upper()),
                                file_data["file_id"],
                                {"caption": file_data.get("caption")}
                            ))
                    
                    if media_group:
                        # Send as media group
                        sent_messages = await client.send_media_group(STORAGE_CHANNEL, media_group)
                        message_id = sent_messages[0].id
                    else:
                        # Fallback to text message with file links
                        text_content = "\n\n".join(
                            f"📄 {file.get('file_name', 'File')}" 
                            for file in state["files"]
                        )
                        msg = await client.send_message(STORAGE_CHANNEL, text_content)
                        message_id = msg.id
                
                # Generate single share link
                share_link = f"https://t.me/{bot_username}?start={message_id}"
                result_message += f"`{share_link}`\n\n"
                result_message += f"📦 *Contains {len(state['files'])} items*"

                await message.reply(
                    result_message,
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
            await message.reply(f"✅ Text added to batch! Total items: {len(state['files'])}\nSend /done when ready.")
        
        elif media := get_media_info(message):
            state["files"].append(media)
            reply_text = f"✅ Media added to batch! Total items: {len(state['files'])}"
            if media["caption"]:
                reply_text += f"\nCaption: {media['caption']}"
            reply_text += "\nSend /done when ready."
            await message.reply(reply_text)

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
            reply_text = f"✅ Media added to broadcast!"
            if media["caption"]:
                reply_text += f"\nCaption: {media['caption']}"
            reply_text += "\nSend /done when ready."
            await message.reply(reply_text)

async def set_commands():
    await app.set_bot_commands([
        BotCommand("start", "Show start message"),
        BotCommand("batch", "Upload multiple files (Owner)"),
        BotCommand("broadcast", "Send message to all users (Owner)"),
    ])

# Initialize and run the bot
async def main():
    await app.start()
    print("Bot started!")
    await set_commands()
    
    # Verify storage channel access
    try:
        test_msg = await app.send_message(STORAGE_CHANNEL, "Bot started and storage channel verified!")
        await test_msg.delete()
        logger.info("Storage channel access verified successfully")
    except Exception as e:
        logger.error(f"Failed to access storage channel: {e}")
        print("CRITICAL: Could not access storage channel. Please ensure:")
        print("1. The channel ID is correct (with -100 prefix)")
        print("2. The bot is added as admin in the channel")
        print("3. The channel is not deleted or restricted")
        await app.stop()
        return
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped!")
