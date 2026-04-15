import os
import re
import textwrap
import uuid

from dotenv import load_dotenv
from ebooklib import epub
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")


def make_epub(title: str, text: str) -> str:
    html_content = f"<div>{text.replace(chr(10), '<br/>')}</div>"

    book = epub.EpubBook()
    book.set_identifier(str(uuid.uuid4()))
    book.set_title(title)
    book.set_language("en")

    chapter = epub.EpubHtml(title=title, file_name="content.xhtml", lang="en")
    chapter.content = html_content

    book.add_item(chapter)
    book.spine = [chapter]

    # Use a unique ID for the actual disk path to avoid collisions
    path = f"/tmp/{uuid.uuid4()}.epub"
    epub.write_epub(path, book)
    return path


async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    text = msg.text or msg.caption or ""

    if not text:
        await msg.reply_text("Forward me a text message and I'll turn it into an EPUB.")
        return

    # 1. Create a clean title for the metadata
    title_metadata = textwrap.shorten(text, width=60, placeholder="...")

    # 2. Create a safe filename using the first few words
    # This removes non-alphanumeric characters so the filename doesn't break
    first_words = " ".join(text.split()[:5])
    safe_name = re.sub(r"[^\w\s-]", "", first_words).strip().replace(" ", "_")

    # Fallback if the message is only emojis/symbols
    if not safe_name:
        safe_name = "document"

    path = make_epub(title_metadata, text)

    try:
        with open(path, "rb") as f:
            await msg.reply_document(
                f, filename=f"{safe_name[:40]}.epub", caption="Here is your EPUB file!"
            )
    finally:
        if os.path.exists(path):
            os.remove(path)


app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

print("Bot is running...")
app.run_polling()
