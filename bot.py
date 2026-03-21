import instaloader
import os
import shutil
import time
import ffmpeg
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler

# 🔐 Telegram token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# 📸 Instagram loader
L = instaloader.Instaloader(download_videos=True, save_metadata=False)

# 🔐 Instagram login (optional but recommended)
USERNAME = os.getenv("IG_USERNAME")
PASSWORD = os.getenv("IG_PASSWORD")

if USERNAME and PASSWORD:
    try:
        L.login(USERNAME, PASSWORD)
        print("Instagram login successful")
    except Exception as e:
        print("Instagram login failed:", e)

# 🟢 Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send Instagram Reel/Post link")

# 🔁 Retry fetch
def get_post(shortcode, retries=3):
    for i in range(retries):
        try:
            return instaloader.Post.from_shortcode(L.context, shortcode)
        except:
            time.sleep(5)
    return None

# 📥 Download handler
async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    await update.message.reply_text("Downloading...")

    try:
        if not ("instagram.com" in url):
            await update.message.reply_text("Invalid Instagram link ❌")
            return

        # 🧹 Clean folder
        if os.path.exists("downloads"):
            shutil.rmtree("downloads")
        os.makedirs("downloads")

        shortcode = url.split("/")[-2]
        post = get_post(shortcode)

        if not post:
            await update.message.reply_text("Failed to fetch post. Try later ⏳")
            return

        caption = post.caption if post.caption else "No caption"

        # 📥 Download post
        L.download_post(post, target="downloads")
        time.sleep(2)

        # 📄 Save caption as document
        caption_file = "downloads/caption.txt"
        with open(caption_file, "w", encoding="utf-8") as f:
            f.write(caption)
        await update.message.reply_document(document=open(caption_file, "rb"))

        # 🎥 Send media (video/images), multiple slides supported
        video_path = None
        for file in os.listdir("downloads"):
            path = os.path.join("downloads", file)

            if file.endswith(".mp4"):
                video_path = path
                await update.message.reply_video(video=open(path, "rb"))
                await update.message.reply_document(document=open(path, "rb"))

            elif file.endswith(".jpg"):
                await update.message.reply_photo(photo=open(path, "rb"))
                await update.message.reply_document(document=open(path, "rb"))

        # 🎵 Extract audio if video exists (ffmpeg-python)
        if video_path:
            audio_path = "downloads/audio.mp3"
            (
                ffmpeg
                .input(video_path)
                .output(audio_path, format='mp3', acodec='libmp3lame')
                .run(overwrite_output=True)
            )
            await update.message.reply_audio(audio=open(audio_path, "rb"))

    except Exception as e:
        if "metadata" in str(e):
            await update.message.reply_text("Instagram blocked request. Try again later 🚫")
        else:
            await update.message.reply_text("Error: " + str(e))

# 🤖 App setup
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download))

print("Bot is running...")
app.run_polling()
