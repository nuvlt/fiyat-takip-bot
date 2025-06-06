import os
import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from flask import Flask
import threading

# Logging ayarları
logging.basicConfig(level=logging.INFO)

# Flask app
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot aktif!"

# Telegram komutları
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Merhaba! Takip etmek istediğin ürün bağlantısını gönder.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Gönderdiğin mesaj: {update.message.text}")

# Telegram botu başlatma fonksiyonu
async def telegram_bot():
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    if not TOKEN:
        print("TELEGRAM_TOKEN bulunamadı!")
        return

    app_bot = ApplicationBuilder().token(TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await app_bot.run_polling()

# Thread ile hem Flask hem Telegram botu çalıştır
def main():
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8080)).start()
    asyncio.run(telegram_bot())

if __name__ == "__main__":
    main()
