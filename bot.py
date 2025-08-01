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
# ▼▼▼ YAHAN AAPKE NAYE CREDENTIALS DAAL DIYE GAYE HAIN ▼▼▼
FIREBASE_CREDENTIALS_TEMPLATE = {
  "type": "service_account",
  "project_id": "adminneast",
  "private_key_id": "db5b89e71efd742e330f5a1118dfe1979924ef70",
  "client_email": "firebase-adminsdk-fbsvc@adminneast.iam.gserviceaccount.com",
  "client_id": "102397019138291957016",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40adminneast.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

# ▼▼▼ YAHAN AAPKI NAYI PRIVATE KEY DAAL DI GAYI HAI ▼▼▼
PRIVATE_KEY_RAW = r"""-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDFCooUCLf/Zs8h
prpHvyfvrpinEsovN2VEPAl8hT4O+psgO6YsoUatB0PYK9xlD/D9ncpBaAfNNPOx
hMFCRZ6n+W+OqK/93rr/N2n+LU5R598XIi0ff7JPipkdZL8xw2WGChRSfk+Lp19d
lDvHzbQDFdtBZKGOB1AUbbYI/OOKSigCACTa90ec6qWbPlHBjcp4HV1cZqIyy8mP
lRku9JbsVNBCDOt2L4GCK1Whqs4JBrWtFnRzCJZ6AJOEYS9X4ke/BBkxwL2Y4RMV
fvwcs+conrGUf47fcMuY1LjX2TLDxep5oBVprpBNGR6BAg76gcRuowAz8V2wirOg
zJCMDyNNAgMBAAECggEAFqNO2N1lklzT+FhI95xBMNrc4/kXLJSPOGczadB/IEZv
kyT3QxJmZdO7Wjcz05Kgy+qYhao3lz55rxADCiOohkD0ra24xpCT6GWL8m1vHZ7n
tScyivdnW5cfX06nXsbFv8AhtJaZegCJRt2UfrCl+WLF9X3jx8cUTryKGP9A/y6x
TW3Wctfu4R7k0ILv3xV6XyzL9fLBkhrEbGGOmkNsWRw3VK2nEDeHgvNImmjw4n23
lLgp4D4WFhn7LmHODtXiER9ROI+odgOiL8apILEmoQSUgZ+FRYs41Sr0SplNfffK
Y7K8ZEzpkdsaRg+BjtjNqciXdh4GGsy099XdJiFfIQKBgQDg8k+6jVQTnznufCq8
sjet+gPryzFQ8HIzQfG9JWJg2PJEfI3I43rC18rwjQj948T+gfsoBlcuidq8JIsS
W1IVf/s1JSYzgYiINbbBoTK6tSNqP+HV3rUBedxegZzHXYqr6IarQdr/iAWtwQ5H
tpJR34SBA1dxMLfZdBbrZPO60QKBgQDgPgr12TW72f+Yup26BEqnqiyUrjPa04ik
QUwD3ZMkdnl/aoxaSS3CM8JHIypYb2xh7vytvBD8Fb/Dz+78aQHK0brd96n90epc
JQ+/+EpoB5f9j72RHoAbgLWP4mnFm6tP2yEPv9hl2mv87LQGbLSgukGGbLaLP9wb
qAx/ZXqHvQKBgCMSZI/nfRZaGwQt49PrzXaYpofa9GN0Obn4LCKbc406Bfvbl5ec
sAU08/UxaBd9rbcouOnyoyEkaTAwWmaQSmoDvDz6/8vEBG+IQGhMI8ase0sTjrhz
srD6OPubJcCHuxk2ddi5udVhddEzanCP7JxLRzN+O+HwAJos2W32HXIhAoGBALa1
Fo0V+9ghWUaB1v23fXR7DXPfNFT5wf3DTkJgCQHOnlQY5l6x/Vyce5Emr9v6fV6W
ML8F2vjqZ6MOCvUSQemVVSKCJrmujbuiXuDVVxrIBSkOMzDInyzJhCXGHtRpb/3S
129TqufiPdaIrm4FqG7FE5qJfXqb/6VxGS2760gpAoGBANN8NdcaKCv1Nas7s11H
QDGquIA+8EKIH8lBLaS7cOBdX0A/+z23i24MxT2ikbO6Al/rWq3AuDaNBr3HyxJ+
dUP3nxcQJjb7b5YDIz0iM7wsPhKCgpF8jANG+EDn8iXTh53cDI5IzQK1SaPOEVuX
jI7AQ4/KoOpNVedx4D1E+CBD
-----END PRIVATE KEY-----"""
# ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

# === LOGGING SETUP ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

# === FIREBASE INITIALIZATION ===
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
