import instaloader
import os
import shutil
import time
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler, CallbackQueryHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")

L = instaloader.Instaloader(download_videos=True, save_metadata=False)

# 🔐 Instagram login (optional but recommended)
USERNAME = os.getenv("IG_USERNAME")
PASSWORD = os.getenv("IG_PASSWORD")

if USERNAME and PASSWORD:
    try:
        L.login(USERNAME, PASSWORD)
        print("Instagram login successful")
    except Exception as e:
        print("Login failed:", e)

# 🟢 Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send Instagram Reel/Post link")

# 🔘 Buttons
def get_buttons(url):
    keyboard = [
        [InlineKeyboardButton("📥 Download", callback_data=f"dl|{url}")],
        [InlineKeyboardButton("🎵 Audio", callback_data=f"audio|{url}")],
        [InlineKeyboardButton("📄 Caption", callback_data=f"caption|{url}")]
    ]
    return InlineKeyboardMarkup(keyboard)

# 📩 Handle link
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "instagram.com" not in url:
        await update.message.reply_text("Invalid link ❌")
        return

    await update.message.reply_text("Choose option 👇", reply_markup=get_buttons(url))

# 🔁 Retry fetch
def get_post(shortcode, retries=3):
    for i in range(retries):
        try:
            return instaloader.Post.from_shortcode(L.context, shortcode)
        except:
            time.sleep(5)
    return None

# 🎯 Button actions
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, url = query.data.split("|")
    shortcode = url.split("/")[-2]

    await query.message.reply_text("Processing... ⏳")

    try:
        # साफ folder
        if os.path.exists("downloads"):
            shutil.rmtree("downloads")
        os.makedirs("downloads")

        post = get_post(shortcode)

        if not post:
            await query.message.reply_text("Failed. Try later 🚫")
            return

        caption = post.caption if post.caption else "No caption"

        # 📥 Download
        L.download_post(post, target="downloads")
        time.sleep(3)

        video_path = None

        for file in os.listdir("downloads"):
            if file.endswith(".mp4"):
                video_path = os.path.join("downloads", file)

        # 📥 DOWNLOAD OPTION
        if action == "dl":
            for file in os.listdir("downloads"):
                path = os.path.join("downloads", file)

                if file.endswith(".mp4"):
                    await query.message.reply_video(video=open(path, "rb"))

                elif file.endswith(".jpg"):
                    await query.message.reply_photo(photo=open(path, "rb"))

        # 🎵 AUDIO OPTION
        elif action == "audio":
            if video_path:
                audio_path = "downloads/audio.mp3"
                subprocess.run([
                    "ffmpeg", "-i", video_path,
                    "-q:a", "0", "-map", "a", audio_path
                ])
                await query.message.reply_audio(audio=open(audio_path, "rb"))
            else:
                await query.message.reply_text("No audio found ❌")

        # 📄 CAPTION OPTION
        elif action == "caption":
            await query.message.reply_text("📄 " + caption[:4000])

    except Exception as e:
        await query.message.reply_text("Error: " + str(e))

# 🤖 App
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(button_handler))

print("Bot running 🚀")
app.run_polling()
