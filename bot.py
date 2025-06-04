from flask import Flask
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from tinydb import TinyDB
import os
import threading

# Flask uygulaması (Render'ın web service olarak görmesi için)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot aktif!"

# Telegram bot ayarları
TOKEN = os.getenv("TELEGRAM_TOKEN")
db = TinyDB("data.json")

def is_valid_url(text):
    return "hepsiburada.com" in text or "trendyol.com" in text

def start(update, context):
    update.message.reply_text("👋 Merhaba! Hepsiburada veya Trendyol ürün linki gönder, fiyatı takip edelim!")

def handle_message(update, context):
    url = update.message.text.strip()
    chat_id = update.message.chat_id

    if is_valid_url(url):
        db.insert({"chat_id": chat_id, "url": url})
        update.message.reply_text("✅ Ürün başarıyla takibe alındı.")
    else:
        update.message.reply_text("❌ Sadece Hepsiburada veya Trendyol linklerini gönderebilirsiniz.")

# Bu fonksiyon artık var
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    print("Bot çalışıyor...")
    updater.idle()

# Hem Flask hem Telegram botu başlat
if __name__ == "__main__":
    threading.Thread(target=main).start()
    app.run(host="0.0.0.0", port=10000)
