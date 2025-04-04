import asyncio
import random
import string
import json
import os
import firebase_admin
from firebase_admin import credentials, db
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
BOT_TOKEN = "7889340330:AAFHxWrrcOi3-x4z7V9j2qj-Fp3KaNgOs4Y"
API_ID = 24360857
API_HASH = "0924b59c45bf69cdfafd14188fb1b778"
OWNER_IDS = [5891854177, 6611564855]

# Channel information - Properly defined as lists
CHANNEL_IDS = [
    -1002180565285,  # TEAMTDSTAMILFANDUB
    -1002241070786,  # Shopping_Offers_Deals_And_Loot
    -1002472888393,  # Team_Tda_Network
    -1002149857870   # Additional channel
]

CHANNEL_LINKS = [
    "https://t.me/TEAMTDSTAMILFANDUB",
    "https://t.me/Shopping_Offers_Deals_And_Loot",
    "https://t.me/+jsC6K05AbIA2NDRl",
    "https://t.me/Team_Tda_Network"
]

SOURCE_CHANNEL = "https://t.me/+jsC6K05AbIA2NDRl"

# Initialize Firebase
try:
    firebase_config = os.getenv("FIREBASE_CONFIG")
    if not firebase_config:
        raise ValueError("FIREBASE_CONFIG environment variable is not set!")
    
    cred = credentials.Certificate(json.loads(firebase_config))
    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://telegrambotdb-1895e-default-rtdb.firebaseio.com/"
    })
    logger.info("Firebase initialized successfully!")
except Exception as e:
    logger.error(f"Firebase initialization error: {e}")
    raise

app = Client("bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

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
                "file_type": media_type
            }
    return None

async def store_user_info(user_id, username, first_name, last_name):
    try:
        db.reference(f"users/{user_id}").set({
            "username": username or "",
            "first_name": first_name or "",
            "last_name": last_name or "",
            "last_seen": datetime.now().isoformat(),
            "registered_at": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error storing user info: {e}")

async def check_channel_membership(client, user_id, channel_id):
    try:
        member = await client.get_chat_member(channel_id, user_id)
        return member.status not in [enums.ChatMemberStatus.LEFT, enums.ChatMemberStatus.BANNED]
    except Exception as e:
        logger.error(f"Error checking channel {channel_id}: {e}")
        return False

async def is_user_joined(client, user_id):
    try:
        results = await asyncio.gather(
            *[check_channel_membership(client, user_id, channel_id) for channel_id in CHANNEL_IDS]
        )
        return all(results)
    except Exception as e:
        logger.error(f"Error in is_user_joined: {e}")
        return False

async def send_message_with_buttons(chat_id, text, buttons=None):
    try:
        await app.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=buttons,
            parse_mode=enums.ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Error sending message: {e}")

async def send_individual_file(client, chat_id, files):
    for file in files:
        try:
            if file["file_type"] == "text":
                await client.send_message(chat_id, file["file_name"])
            else:
                await getattr(client, f"send_{file['file_type']}")(
                    chat_id, file["file_id"]
                )
        except Exception as e:
            logger.error(f"Error sending file: {e}")
            await client.send_message(chat_id, f"Error sending file: {e}")

# Command Handlers
@app.on_message(filters.command("start"))
async def start(client, message):
    user = message.from_user
    await store_user_info(user.id, user.username, user.first_name, user.last_name)
    has_joined = await is_user_joined(client, user.id)
    
    image_id = "AgACAgUAAxkBAAICRWfqFJqlsCxtBPc1-1MHYmKtWx-0AAKtxzEbBMZIVxk4Ddl2zCrnAAgBAAMCAAN4AAceBA"
    image_id1 = "AgACAgUAAxkBAAICRWfqFJqlsCxtBPc1-1MHYmKtWx-0AAKtxzEbBMZIVxk4Ddl2zCrnAAgBAAMCAAN4AAceBA"
    
    join_buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 CHANNEL 1", url=CHANNEL_LINKS[0])],
        [InlineKeyboardButton("📢 CHANNEL 2", url=CHANNEL_LINKS[1])],
        [InlineKeyboardButton("📢 CHANNEL 3", url=CHANNEL_LINKS[2])],
        [InlineKeyboardButton("📢 CHANNEL 4", url=CHANNEL_LINKS[3])]
    ])
    
    if len(message.command) == 1:
        if not has_joined:
            caption = f"""
*Hᴇʟʟᴏ {user.first_name}*

*You must join ALL 4 channels to get anime files*

*Please join all channels below:*
            """
            await client.send_photo(
                chat_id=message.chat.id,
                photo=image_id,
                caption=caption,
                reply_markup=join_buttons,
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            caption = f"""
*Hᴇʟʟᴏ {user.first_name}*

*I Aᴍ Aɴɪᴍᴇ Bᴏᴛ I Wɪʟʟ Gɪᴠᴇ Yᴏᴜ Aɴɪᴍᴇ Fɪʟᴇs Fʀᴏᴍ* [Tᴀᴍɪʟ Dubbed Aɴɪᴍᴇ]({SOURCE_CHANNEL})
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

*You must join ALL 4 channels to get this file*

*Please join all channels below:*
            """
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 CHANNEL 1", url=CHANNEL_LINKS[0])],
                [InlineKeyboardButton("📢 CHANNEL 2", url=CHANNEL_LINKS[1])],
                [InlineKeyboardButton("📢 CHANNEL 3", url=CHANNEL_LINKS[2])],
                [InlineKeyboardButton("📢 CHANNEL 4", url=CHANNEL_LINKS[3])],
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
            file_data = db.reference(f"files/{unique_id}").get()
            if file_data and not file_data.get("deleted"):
                await send_individual_file(client, message.chat.id, file_data["files"])

@app.on_callback_query(filters.regex("^getfile_"))
async def handle_getfile(client, callback_query):
    user_id = callback_query.from_user.id
    unique_id = callback_query.data.split("_")[1]
    
    has_joined = await is_user_joined(client, user_id)
    
    if has_joined:
        file_data = db.reference(f"files/{unique_id}").get()
        if file_data and not file_data.get("deleted"):
            await callback_query.message.delete()
            await send_individual_file(client, callback_query.message.chat.id, file_data["files"])
        else:
            await callback_query.answer("❌ File not found or deleted!", show_alert=True)
    else:
        await callback_query.answer("❌ Please join all 4 channels first!", show_alert=True)

# ... [rest of your command handlers remain unchanged] ...

async def set_commands():
    await app.set_bot_commands([
        BotCommand("start", "Show start message"),
        BotCommand("batch", "Upload files (Owner)"),
        BotCommand("broadcast", "Send to all users (Owner)"),
        BotCommand("users", "List users (Owner)")
    ])

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

@app.on_message(filters.command("broadcast") & filters.user(OWNER_IDS))
async def broadcast_command(client, message):
    user_id = message.from_user.id
    user_states[user_id] = {"mode": "broadcast", "content": []}
    await message.reply(
        "📢 *Broadcast Mode Activated!*\n\n"
        "Send me the message or media you want to broadcast to all users.\n"
        "When finished, send /done to send to all users.\n"
        "To cancel, send /cancel.",
        parse_mode=enums.ParseMode.MARKDOWN
    )

@app.on_message(filters.command("users") & filters.user(OWNER_IDS))
async def list_users(client, message):
    try:
        users_ref = db.reference("users")
        users = users_ref.get() or {}
        
        if not users:
            await message.reply("No users found in the database!")
            return
        
        response = "📊 *Registered Users*\n\n"
        for user_id, user_data in users.items():
            username = user_data.get('username', 'N/A')
            first_name = user_data.get('first_name', '')
            last_name = user_data.get('last_name', '')
            name = f"{first_name} {last_name}".strip()
            
            response += f"🆔: `{user_id}`\n"
            response += f"👤: {name}\n"
            response += f"📛: @{username}\n"
            response += "――――――――――――――――――\n"
        
        # Split the message if too long
        for i in range(0, len(response), 4096):
            part = response[i:i+4096]
            await message.reply(part, parse_mode=enums.ParseMode.MARKDOWN)
            
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        await message.reply(f"❌ Error listing users: {e}")

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
                "deleted": False,
                "created_at": datetime.now().isoformat()
            }

            try:
                db.reference(f"files/{unique_id}").set(file_data)
            except Exception as e:
                await message.reply(f"❌ Error saving file: {e}")
                return

            bot_username = (await client.get_me()).username
            share_link = f"https://t.me/{bot_username}?start={unique_id}"
            await message.reply(
                f"✅ *Batch Upload Complete!*\n\n"
                f"🔗 Download Link: {share_link}\n\n"
                f"📌 Files will be stored permanently until deleted.",
                parse_mode=enums.ParseMode.MARKDOWN
            )
            user_states.pop(user_id, None)

        elif state["mode"] == "broadcast":
            if not state["content"]:
                await message.reply("❌ No content to broadcast! Operation canceled.")
                user_states.pop(user_id, None)
                return

            users_ref = db.reference("users")
            users = users_ref.get() or {}
            
            if not users:
                await message.reply("❌ No users to broadcast to!")
                user_states.pop(user_id, None)
                return
            
            total_users = len(users)
            success = 0
            failed = 0
            
            status_msg = await message.reply(f"📢 Starting broadcast to {total_users} users...")
            
            for user_id in users.keys():
                try:
                    for item in state["content"]:
                        if item["type"] == "text":
                            await client.send_message(int(user_id), item["content"])
                        else:
                            method = {
                                "document": client.send_document,
                                "video": client.send_video,
                                "photo": client.send_photo,
                                "audio": client.send_audio
                            }.get(item["type"])
                            if method:
                                await method(int(user_id), item["file_id"])
                    success += 1
                except Exception as e:
                    logger.error(f"Error broadcasting to {user_id}: {e}")
                    failed += 1
                await asyncio.sleep(0.5)  # Rate limiting
            
            await status_msg.edit_text(
                f"✅ Broadcast completed!\n\n"
                f"• Total users: {total_users}\n"
                f"• Successfully sent: {success}\n"
                f"• Failed: {failed}"
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
        await message.reply("ℹ Please use /batch or /broadcast first to start uploading.")
        return

    if state["mode"] == "batch":
        if message.text and not message.text.startswith('/'):
            state["files"].append({"file_id": None, "file_name": message.text, "file_type": "text"})
            await message.reply(f"✅ Text added to batch! Total items: {len(state['files'])}\nSend /done when ready.")
        elif media := get_media_info(message):
            state["files"].append(media)
            await message.reply(f"✅ Media added to batch! Total items: {len(state['files'])}\nSend /done when ready.")

    elif state["mode"] == "broadcast":
        if message.text and not message.text.startswith('/'):
            state["content"].append({"type": "text", "content": message.text})
            await message.reply(f"✅ Text added to broadcast! Total items: {len(state['content'])}\nSend /done when ready.")
        elif media := get_media_info(message):
            state["content"].append({
                "type": media["file_type"],
                "file_id": media["file_id"],
                "file_name": media["file_name"]
            })
            await message.reply(f"✅ Media added to broadcast! Total items: {len(state['content'])}\nSend /done when ready.")


app.start()
print("Bot started!")
app.loop.run_until_complete(set_commands())

try:
    asyncio.get_event_loop().run_forever()
except KeyboardInterrupt:
    print("Bot stopped!")
