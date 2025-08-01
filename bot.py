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

# =========================================================================
# === CONFIG (SECRETS ARE HARDCODED - 🚨 EXTREMELY UNSAFE! 🚨) ===
# =========================================================================
# DANGER: Yeh secrets public ho sakte hain agar code GitHub par hai.
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE" # <<< Apna Telegram Bot Token yahan daalein

# Public config
CHANNELS = [
    ("@skillneastreal", "https://t.me/skillneastreal"),
    ("@skillneast", "https://t.me/skillneast")
]
OWNER_LINK = "https://t.me/neasthub"
SITE_LINK = "https://skillneastauth.vercel.app/"

# --- Firebase Configuration (HARDCODED) ---
FIREBASE_DATABASE_URL = "https://adminneast-default-rtdb.firebaseio.com" # <<< Aapka Database URL

# ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
# <<< IMPORTANT: Apni download ki hui Firebase Service Account JSON file ka
# poora content neeche diye gaye dictionary me paste karein.
# ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
FIREBASE_CREDENTIALS_DICT = {
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "your-private-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR-PRIVATE-KEY-HERE\n-----END PRIVATE KEY-----\n",
  "client_email": "your-client-email@your-project-id.iam.gserviceaccount.com",
  "client_id": "your-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-client-email.iam.gserviceaccount.com"
}
# ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
# ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲


# === LOGGING SETUP ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

# === FIREBASE INITIALIZATION ===
def initialize_firebase():
    try:
        cred = credentials.Certificate(FIREBASE_CREDENTIALS_DICT)
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

        token_data = {
            'user_id': user_id,
            'created_at': current_timestamp,
            'expiry_timestamp': expiry_timestamp,
            'used': False
        }
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
        keyboard.append([
            InlineKeyboardButton("✅ I Joined", callback_data="check"),
            InlineKeyboardButton("👑 Owner", url=OWNER_LINK)
        ])
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
        keyboard = [
            [InlineKeyboardButton("🔁 Retry", callback_data="check")],
            [InlineKeyboardButton("👑 Owner Profile", url=OWNER_LINK)]
        ]
        await query.edit_message_text(
            f"❌ You still haven’t joined:\n\n<code>{not_joined_list}</code>\n\n"
            "📛 Access will be revoked if you leave any channel.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# === CHECK MEMBERSHIP (No changes) ===
async def check_all_channels(context, user_id):
    not_joined = []
    for username, url in CHANNELS:
        try:
            member = await context.bot.get_chat_member(username, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                not_joined.append((username, url))
        except Exception as e:
            logging.warning(f"Error checking {username} for user {user_id}: {e}")
            not_joined.append((username, url))
    return len(not_joined) == 0, not_joined

# === SEND TOKEN (Updated for Firebase) ===
async def send_token(obj, context, edit=False):
    user_id = obj.effective_user.id
    token = await generate_and_save_token(user_id)
    if not token:
        error_text = "❌ Sorry, an error occurred. Please try again later."
        if edit:
            await obj.edit_message_text(error_text)
        else:
            await obj.message.reply_text(error_text)
        return

    keyboard = [[InlineKeyboardButton("🔐 Access Website", url=SITE_LINK)], [InlineKeyboardButton("👑 Owner", url=OWNER_LINK)]]
    text = (
        "<b>🎉 Access Granted!</b>\n\n"
        "Here is your temporary access token:\n\n"
        f"<code>{token}</code>\n\n"
        "✅ Paste this on the website to continue!\n"
        "⚠️ <b>Note: This token is valid for 15 minutes only and can be used once.</b>"
    )
    try:
        if edit:
            await obj.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await obj.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        logging.info(f"Firebase token sent to user {user_id}")
    except Exception as e:
        logging.error(f"Failed to send token: {e}")

# === ERROR HANDLER ===
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Update {update} caused error {context.error}")

# === RUN THE BOT ===
def main():
    if not initialize_firebase():
        logging.critical("CRITICAL: Bot cannot start without Firebase. Check credentials.")
        return
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_channels, pattern="^check$"))
    app.add_error_handler(error_handler)
    
    logging.info("Starting bot with HARDCODED Firebase credentials...")
    app.run_polling()

if __name__ == "__main__":
    main()
