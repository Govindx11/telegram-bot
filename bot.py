from flask import Flask
import threading
import os
import instaloader
import shutil
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler

# ------------------- 🌐 FLASK SERVER -------------------

web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is running ✅"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_web, daemon=True).start()

# ------------------- 🤖 TELEGRAM BOT -------------------

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ BOT_TOKEN not found!")
else:
    print("✅ BOT_TOKEN loaded")

# Instagram loader
L = instaloader.Instaloader(download_videos=True, save_metadata=False)

# Instagram login (optional)
USERNAME = os.getenv("IG_USERNAME")
PASSWORD = os.getenv("IG_PASSWORD")

if USERNAME and PASSWORD:
    try:
        L.login(USERNAME, PASSWORD)
        print("Instagram login successful")
    except Exception as e:
        print("Instagram login failed:", e)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send Instagram Reel/Post link")

# Retry fetch
def get_post(shortcode, retries=5):
    for i in range(retries):
        try:
            print(f"Trying {i+1} time...")
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            return post
        except Exception as e:
            print(f"Retry {i+1} failed:", e)
            time.sleep(10)   # delay badha diya
    return None
# Download handler
async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Message received:", update.message.text)
    url = update.message.text
    await update.message.reply_text("Downloading...")

    try:
        if "instagram.com" not in url:
            await update.message.reply_text("Invalid Instagram link ❌")
            return

        # Clean folder
        if os.path.exists("downloads"):
            shutil.rmtree("downloads")
        os.makedirs("downloads")

        shortcode = url.split("?")[0].split("/")[-2]
        post = get_post(shortcode)

        if not post:
            await update.message.reply_text("Failed to fetch post. Try later ⏳")
            return

        caption = post.caption if post.caption else "No caption"

        # Download post
        L.download_post(post, target="downloads")
        time.sleep(2)

        # Save caption
        caption_file = "downloads/caption.txt"
        with open(caption_file, "w", encoding="utf-8") as f:
            f.write(caption)

        await update.message.reply_document(document=open(caption_file, "rb"))

        # Send media
        for file in os.listdir("downloads"):
            path = os.path.join("downloads", file)

            if file.endswith(".mp4"):
                await update.message.reply_video(video=open(path, "rb"))
                await update.message.reply_document(document=open(path, "rb"))

            elif file.endswith(".jpg"):
                await update.message.reply_photo(photo=open(path, "rb"))
                await update.message.reply_document(document=open(path, "rb"))

    except Exception as e:
        if "metadata" in str(e):
            await update.message.reply_text("Instagram blocked request 🚫")
        else:
            await update.message.reply_text("Error: " + str(e))

# Bot setup
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.ALL,download))

print("🚀 Bot started...")
app.run_polling()
