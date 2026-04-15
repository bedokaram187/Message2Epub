import os
import textwrap
import uuid

from dotenv import load_dotenv
from ebooklib import epub
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")


def make_epub(title: str, text: str) -> str:
    html_content = f"<p>{text.replace(chr(10), '<br/>')}</p>"

    book = epub.EpubBook()
    book.set_identifier(str(uuid.uuid4()))
    book.set_title(title)
    book.set_language("en")

    chapter = epub.EpubHtml(title=title, file_name="content.xhtml", lang="en")
    chapter.content = f"<h1>{title}</h1>{html_content}"

    book.add_item(chapter)
    book.toc = [epub.Link("content.xhtml", title, "content")]
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav", chapter]

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

    title = textwrap.shorten(text, width=60, placeholder="...")
    path = make_epub(title, text)

    with open(path, "rb") as f:
        await msg.reply_document(
            f, filename=f"{title[:50]}.epub", caption="here's the epub file"
        )

    os.remove(path)


app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.ALL, handle_message))

print("i am running...")
app.run_polling()
