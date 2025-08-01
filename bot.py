import hmac, hashlib, random, string, logging, os, threading
from datetime import datetime
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# === DUMMY WEB SERVER (to keep Render's Web Service alive) ===
app = Flask(__name__)

@app.route('/')
def home():
    """A simple route to respond to Render's health checks."""
    return "Bot is alive and running!"

def run_flask():
    """Runs the Flask web server in a separate thread."""
    # Render provides the PORT environment variable.
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# === BOT CONFIG (SECRETS ARE HARDCODED - NOT SAFE!) ===
# DANGER: These secrets can be exposed if the code is on a public repository.
BOT_TOKEN = "8326586625:AAGA9NX8XB7ZnXqvM2-ANOO9TYfLsZeAgvQ"
SECRET_KEY = "STUDYERA2025"

# Public config
CHANNELS = [
    ("@skillneastreal", "https://t.me/skillneastreal"),
    ("@skillneast", "https://t.me/skillneast")
]
OWNER_LINK = "https://t.me/neasthub"
SITE_LINK = "https://skillneastauth.vercel.app/"

# === LOGGING SETUP ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("werkzeug").setLevel(logging.WARNING) # Quiets down Flask's default logs

# === TOKEN GENERATOR ===
def generate_token():
    """Generates a secure, date-based token."""
    now = datetime.now()
    base = now.strftime('%a').upper()[:3] + "-" + now.strftime('%d') + now.strftime('%b').upper()
    digest = hmac.new(SECRET_KEY.encode(), base.encode(), hashlib.sha256).hexdigest().upper()
    prefix = digest[:8]
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}/{suffix}"

# === START HANDLER ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
    user_id = update.effective_user.id
    logging.info(f"User {user_id} started the bot.")
    
    joined_all, _ = await check_all_channels(context, user_id)

    if joined_all:
        await send_token(update, context)
    else:
        keyboard = [[InlineKeyboardButton(f"📥 Join {name[1:]}", url=url)] for name, url in CHANNELS]
        keyboard.append([
            InlineKeyboardButton("✅ I Joined", callback_data="check"),
            InlineKeyboardButton("👑 Owner", url=OWNER_LINK)
        ])
        await update.message.reply_text(
            "<b>🚀 Welcome to StudyEra!</b>\n\n"
            "📚 Free Educational Resources — Notes, PYQs, Live Batches, Test Series & more!\n\n"
            "🔐 Access is secured via channel membership.\n\n"
            "👉 Please join the below channels to unlock your daily access token 👇",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# === VERIFY BUTTON HANDLER ===
async def check_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the 'I Joined' button click."""
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    logging.info(f"User {user_id} clicked the check button.")
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

# === CHECK MEMBERSHIP ===
async def check_all_channels(context, user_id):
    """Checks if the user is a member of all required channels."""
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

# === SEND TOKEN ===
async def send_token(obj, context, edit=False):
    """Generates and sends the access token."""
    token = generate_token()
    keyboard = [
        [InlineKeyboardButton("🔐 Access Website", url=SITE_LINK)],
        [InlineKeyboardButton("👑 Owner", url=OWNER_LINK)]
    ]
    text = (
        "<b>🎉 Access Granted!</b>\n\n"
        "Here is your <u>one-time token</u> for today:\n\n"
        f"<code>{token}</code>\n\n"
        "✅ Paste this on the website to continue!\n"
        "⚠️ Note: If you leave any channel later, your access will be revoked automatically."
    )
    
    # BUG FIX: Get user_id correctly for both message and callback_query
    user_id = obj.from_user.id if hasattr(obj, 'from_user') else obj.effective_user.id
    
    try:
        if edit:
            await obj.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        else: # This branch is for when /start is used by an already-joined user
            await obj.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        logging.info(f"Token sent to user {user_id}")
    except Exception as e:
        logging.error(f"Failed to send token to {user_id}: {e}")

# === ERROR HANDLER ===
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log Errors, but ignore 'Message is not modified'."""
    if "Message is not modified" in str(context.error):
        return
    logging.error(f"Update {update} caused error {context.error}")

# === BOT STARTER FUNCTION ===
def run_bot():
    """Initializes and runs the Telegram bot."""
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(check_channels, pattern="^check$"))
    application.add_error_handler(error_handler)
    
    logging.info("Starting bot polling...")
    application.run_polling()

# === MAIN ENTRY POINT ===
if __name__ == "__main__":
    # Run the Flask web server in a background thread
    logging.info("Starting Flask server in a background thread...")
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Run the bot in the main thread
    run_bot()
