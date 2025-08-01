import time
import uuid
import logging
import firebase_admin
from firebase_admin import credentials, db
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
# Render Web Service ke liye zaroori libraries
import threading
from flask import Flask

# =========================================================================
# === CONFIG (SECRETS ARE HARDCODED - 🚨 EXTREMELY UNSAFE! 🚨) ===
# =========================================================================
# Aapka NAYA Bot Token
BOT_TOKEN = "8326586625:AAGgz-XVjX4fRfpSR5iNrDhcZh8POvAQIm8"

# Public config
CHANNELS = [
    ("@skillneastreal", "https://t.me/skillneastreal"),
    ("@skillneast", "https://t.me/skillneast")
]
OWNER_LINK = "https://t.me/neasthub"
SITE_LINK = "https://skillneastauth.vercel.app/"

# --- Firebase Configuration ---
FIREBASE_DATABASE_URL = "https://adminneast-default-rtdb.firebaseio.com"

# Credentials ka template (bina private key ke)
FIREBASE_CREDENTIALS_TEMPLATE = {
  "type": "service_account",
  "project_id": "adminneast",
  "private_key_id": "5abfa705c2d4f161b0d72b0be87f708ca8bb0f80",
  "client_email": "firebase-adminsdk-fbsvc@adminneast.iam.gserviceaccount.com",
  "client_id": "102397019138291957016",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40adminneast.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

# ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
# YAHAN APNI PRIVATE KEY DAALEIN (BILKUL JAISA COPY KIYA HAI, WAISA HI)
# ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
PRIVATE_KEY_RAW = r"""-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQC7h7lpfJIy0Svk
Fo0/XJhakX8P/Phck+OZeBlXDsAHAAlDIWz47G9c2bdzV2ZrheQFw+mI/tiRW4E0
vuIISN+fNmWxh2SLX9dusX1c7oYT8rHip4HgSq04/VoHK6TcLHkqXVHVTfCoGE2k
dsTI4LTihFeq9JDKij2xlcUA0zEQzCPiEwE7mAQ5edF9YXxexZgezXMPuox5CUvA
Xk9TKDn916mks/IQuNoPrJcjPNNRnie5Ql9RpWnMnHXaIjsCMk+dslsS3NQaPzRZ
YR0WzEgskexW3zRbWDz/XiaCDM7jLnp9sIIE7GAwcEzAHePjl3yaNkSMPLjn85Gr
CNaTi/pjAgMBAAECggEAHhru2BFogwHzct1v9YEO8FM1O8LXuD0Bp8yQ/NngV/9Y
fU9raBbE1foZqkmYpqBK9+X4osaOy98NwgL21G+mfq/D6Zkbugg71Ihn4LhmC+PF
TOapQfGbF3AMuOP3xmTZWsS6c2zcuo+UP1fVxY3VXBv02vwCFpHUz6KEitpcoR5t
wnZP4+qiZszDCiQFwItQ6jchRA6FZiUOMN6Z7I3fVZcdjnDd18ZON2Hw91XaFnyL
M4MNDCT3kXu6c8a3/4gJRPnZpKrb0RTgUwtfs+OAn5TjZtpBlMV5VZVMHX7ZZg6d
08n2r8ORA4RJWamZUamT2vz2z/x7kltaVyQTJjLhuQKBgQD1dcNzbJurq54bEcdn
3sDldy50ZJHpXcUOBgLExaeMO6+x69TTO5xrgtuXt0zXH49KeeFdyMRzMGR8GXXQ
xMc4/ANLlAMlQpGb9l1glAEM+jt1SiVLuYhw0NSGfQxEg9My56NiHV6gVekCUoU0
GRs3ZTI4nLRr5ypmkWvvbrAu9QKBgQDDlSm1ansJUVDHdI39UmsBBCGfhlljULzl
kuuFOF5yKErIme9X2gwB/KsH6Ch/rdIv5ysScNzJACTmkQbW2mjOVw3FZB8K5Jsk
OfL0B+LxWJmZJULwB0aogl8NCIG/Xthf7tIPAAzXpglTYjXM+7yLLEjvqarQklfo
r2qsi5B89wKBgC564EnpFQlK9CN4GGRo3+oTyW4s5RxlrzzakoekTffWDY0JdUGS
liodm2t9QEW0KjQWJEDYFasiTMTbJV4lBPybbBxRqM7TbjM0UbZKEHDeqYeqRKm0
Nkv2n2fgIgSPWdzX1C5uFU8TNY5FBgg5gNfah8oEkn2kRnkprGCoeyBJAoGAM2wx
hihT5xRBJ9/mQTd9OMwsRvQc5nbg439oeyNh+aPMXcfTXQbQZ2lWUoLguwkpnTyr
X3LbKeHm0dRJtw2/xpiu3zo+yy9l9vVhgnXcXlZMNC7O1askEcQNV7Dn5Df8reRt
yFHcDoryIsFMofOCFBl1p8W1Spdfk6cjZfBf8esCgYBTL9DE0DbEk0XwL5ycbfxv
/n0i0NJiC9ZUb+N+pmVTE1Doope/UQqVccEUdqWKlf4yY7DgLgpDE0JLPgUWpm2g
QNNV1FS3vDNoPNBlcOETkrs/+Y7lJ8yiT4TYd1siqfz5+k0v82k0J/7jPleupDx6
8ujxOm9a7rEXQSTA3u8Yeg==
-----END PRIVATE KEY-----"""
# ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

# === LOGGING SETUP ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

# === FIREBASE INITIALIZATION (Updated to use Raw String) ===
def initialize_firebase():
    try:
        logging.info("Initializing Firebase using Raw String method...")
        creds_dict = FIREBASE_CREDENTIALS_TEMPLATE.copy()
        creds_dict['private_key'] = PRIVATE_KEY_RAW
        
        cred = credentials.Certificate(creds_dict)
        firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DATABASE_URL})
        logging.info("Firebase has been initialized successfully!")
        return True
    except Exception as e:
        logging.error(f"Failed to initialize Firebase: {e}")
        return False

# === TOKEN GENERATOR (Interacts with Firebase) ===
async def generate_and_save_token(user_id: int) -> str | None:
    try:
        token = str(uuid.uuid4())
        current_timestamp = int(time.time())
        expiry_timestamp = current_timestamp + (15 * 60) # 15 minutes expiry
        token_data = {'user_id': user_id, 'created_at': current_timestamp, 'expiry_timestamp': expiry_timestamp, 'used': False}
        ref = db.reference(f'tokens/{token}')
        ref.set(token_data)
        logging.info(f"Token {token} for user {user_id} saved to Firebase.")
        return token
    except Exception as e:
        logging.error(f"Failed to generate/save token: {e}")
        return None

# === START HANDLER (Updated description) ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logging.info(f"User {user_id} started the bot.")
    joined_all, _ = await check_all_channels(context, user_id)
    if joined_all:
        await send_token(update, context)
    else:
        welcome_text = (
            "🚀 𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝗦𝗸𝗶𝗹𝗹𝗻𝗲𝗮𝘀𝘁!\n\n"
            "📚 𝗚𝗲𝘁 𝗙𝗿𝗲𝗲 𝗔𝗰𝗰𝗲𝘀𝘀 𝘁𝗼 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗖𝗼𝗻𝘁𝗲𝗻𝘁 —\n"
            "𝗖𝗼𝘂𝗿𝘀𝗲𝘀, 𝗣𝗗𝗙 𝗕𝗼𝗼𝗸𝘀, 𝗣𝗮𝗶𝗱 𝗧𝗶𝗽𝘀 & 𝗧𝗿𝗶𝗰𝗸𝘀, 𝗦𝗸𝗶𝗹𝗹-𝗕𝗮𝘀𝗲𝗱 𝗠𝗮𝘁𝗲𝗿𝗶𝗮𝗹 & 𝗠𝗼𝗿𝗲!\n\n"
            "🧠 𝗠𝗮𝘀𝘁𝗲𝗿 𝗡𝗲𝘄 𝗦𝗸𝗶𝗹𝗹𝘀 & 𝗟𝗲𝗮𝗿𝗻 𝗪𝗵𝗮𝘁 𝗥𝗲𝗮𝗹𝗹𝘆 𝗠𝗮𝘁𝘁𝗲𝗿𝘀 — 𝟭𝟬𝟬% 𝗙𝗥𝗘𝗘!\n\n"
            "💸 𝗔𝗹𝗹 𝗧𝗼𝗽 𝗖𝗿𝗲𝗮𝘁𝗼𝗿𝘀' 𝗣𝗮𝗶𝗱 𝗖𝗼𝘂𝗿𝘀𝗲𝘀 𝗮𝘁 𝗡𝗼 𝗖𝗼𝘀𝘁!\n\n"
            "🔐 𝗔𝗰𝗰𝗲𝘀𝘀 𝗶𝘀 𝘀𝗲𝗰𝘂𝗿𝗲𝗱 𝘃𝗶𝗮 𝗰𝗵𝗮𝗻𝗻𝗲𝗹 𝗺𝗲𝗺𝗯𝗲𝗿𝘀𝗵𝗶𝗽.\n\n"
            "👉 𝗣𝗹𝗲𝗮𝘀𝗲 𝗷𝗼𝗶𝗻 𝘁𝗵𝗲 𝗯𝗲𝗹𝗼𝘄 𝗰𝗵𝗮𝗻𝗻𝗲𝗹𝘀 𝘁𝗼 𝘂𝗻𝗹𝗼𝗰𝗸 𝘆𝗼𝘂𝗿 𝗱𝗮𝗶𝗹𝘆 𝗮𝗰𝗰𝗲𝘀𝘀 𝘁𝗼𝗸𝗲𝗻 👇"
        )
        keyboard = [[InlineKeyboardButton(f"📥 Join {name[1:]}", url=url)] for name, url in CHANNELS]
        keyboard.append([InlineKeyboardButton("✅ I Joined", callback_data="check"), InlineKeyboardButton("👑 Owner", url=OWNER_LINK)])
        await update.message.reply_text(welcome_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# === VERIFY BUTTON HANDLER ===
async def check_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    joined_all, not_joined = await check_all_channels(context, user_id)
    if joined_all:
        await query.edit_message_text("✅ Channels verified!\n⏳ Generating your access token...", parse_mode="HTML")
        await send_token(query, context, edit=True)
    else:
        not_joined_list = "\n".join([f"🔸 {ch[1:]}" for ch, _ in not_joined])
        keyboard = [[InlineKeyboardButton("🔁 Retry", callback_data="check")], [InlineKeyboardButton("👑 Owner Profile", url=OWNER_LINK)]]
        await query.edit_message_text(f"❌ You still haven’t joined:\n\n<code>{not_joined_list}</code>\n\n" "📛 Access will be revoked if you leave any channel.", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# === CHECK MEMBERSHIP ===
async def check_all_channels(context, user_id):
    not_joined = []
    for username, url in CHANNELS:
        try:
            member = await context.bot.get_chat_member(username, user_id)
            if member.status not in ['member', 'administrator', 'creator']: not_joined.append((username, url))
        except Exception as e:
            logging.warning(f"Error checking {username} for user {user_id}: {e}")
            not_joined.append((username, url))
    return len(not_joined) == 0, not_joined

# === SEND TOKEN ===
async def send_token(obj, context, edit=False):
    user_id = obj.effective_user.id
    token = await generate_and_save_token(user_id)
    if not token:
        error_text = "❌ Sorry, an error occurred. Please try again later."
        if edit: await obj.edit_message_text(error_text)
        else: await obj.message.reply_text(error_text)
        return
    keyboard = [[InlineKeyboardButton("🔐 Access Website", url=SITE_LINK)], [InlineKeyboardButton("👑 Owner", url=OWNER_LINK)]]
    text = ("<b>🎉 Access Granted!</b>\n\n" "Here is your temporary access token:\n\n" f"<code>{token}</code>\n\n" "✅ Paste this on the website to continue!\n" "⚠️ <b>Note: This token is valid for 15 minutes only and can be used once.</b>")
    try:
        if edit: await obj.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        else: await obj.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        logging.info(f"Firebase token sent to user {user_id}")
    except Exception as e: logging.error(f"Failed to send token: {e}")

# === ERROR HANDLER ===
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Update {update} caused error {context.error}")

# === WEB SERVER SETUP FOR RENDER FREE PLAN ===
web_app = Flask(__name__)
@web_app.route('/')
def index(): return "Bot is alive and running!"
def run_web_server(): web_app.run(host='0.0.0.0', port=10000)

def main():
    if not initialize_firebase():
        logging.critical("CRITICAL: Bot cannot start without Firebase.")
        return
    web_thread = threading.Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()
    logging.info("Web server started in a background thread.")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_channels, pattern="^check$"))
    app.add_error_handler(error_handler)
    logging.info("Starting Telegram bot polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
