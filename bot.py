from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
import requests
import os
import re
import asyncio

BOT_TOKEN = os.environ["BOT_TOKEN"]

# Fast session
session = requests.Session()


# Extract all YouTube video IDs
def extract_video_ids(text):
    pattern = r"(?:youtu\.be/|youtube\.com/watch\?v=|m\.youtube\.com/watch\?v=|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})"
    return list(dict.fromkeys(re.findall(pattern, text)))


# Fast title fetch
def get_video_title(video_id):
    try:
        url = (
            f"https://www.youtube.com/oembed"
            f"?url=https://www.youtube.com/watch?v={video_id}&format=json"
        )

        response = session.get(url, timeout=5)

        if response.status_code == 200:
            return response.json().get("title")

    except:
        pass

    return None


# Direct thumbnail URL
def get_thumbnail(video_id):
    return f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"


async def process_video(update, video_id):

    # Run title fetch in background thread
    title = await asyncio.to_thread(get_video_title, video_id)

    if not title:
        return

    thumbnail = get_thumbnail(video_id)

    final_text = (
        f"<b>{title}</b>\n"
        f"<b>https://youtu.be/{video_id}</b>"
    )

    # Try sending thumbnail
    try:
        await update.message.reply_photo(photo=thumbnail)
    except:
        pass

    # ALWAYS send output text
    try:
        await update.message.reply_text(
            final_text,
            parse_mode="HTML"
        )
    except:
        pass


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text or update.message.caption

    if not text:
        return

    video_ids = extract_video_ids(text)

    if not video_ids:
        return

    # Process all links faster
    tasks = [process_video(update, vid) for vid in video_ids]
    await asyncio.gather(*tasks)


app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(
    MessageHandler(filters.ALL, handle_message)
)

print("Bot running fast...")
app.run_polling()
