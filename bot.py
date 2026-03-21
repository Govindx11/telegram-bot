import instaloader
import os
import shutil
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler

# ✅ FIXED TOKEN
BOT_TOKEN = os.getenv("BOT_TOKEN")

L = instaloader.Instaloader(download_videos=True, save_metadata=False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send Instagram Reel/Post link")

async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    await update.message.reply_text("Downloading...")

    try:
        # 🧹 Purana data delete
        if os.path.exists("downloads"):
            shutil.rmtree("downloads")
        os.makedirs("downloads")

        shortcode = url.split("/")[-2]
        post = instaloader.Post.from_shortcode(L.context, shortcode)

        # Caption
        caption = post.caption if post.caption else "No caption"

        # Download post
        L.download_post(post, target="downloads")

        # 📄 Caption file save
        caption_file = "downloads/caption.txt"
        with open(caption_file, "w", encoding="utf-8") as f:
            f.write(caption)

        # 📤 Caption text send
        await update.message.reply_text("📄 Caption:\n\n" + caption[:4000])

        # 📤 Caption as document
        await update.message.reply_document(document=open(caption_file, "rb"))

        # 📤 All media send (carousel support)
        for file in os.listdir("downloads"):
            path = os.path.join("downloads", file)

            if file.endswith(".mp4"):
                # 🎥 Video normal
                await update.message.reply_video(video=open(path, "rb"))

                # 📁 Video as file
                await update.message.reply_document(document=open(path, "rb"))

            elif file.endswith(".jpg"):
                # 🖼️ Image normal
                await update.message.reply_photo(photo=open(path, "rb"))

                # 📁 Image as file
                await update.message.reply_document(document=open(path, "rb"))

    except Exception as e:
        await update.message.reply_text("Error: " + str(e))

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download))

print("Bot is running...")
app.run_polling()
