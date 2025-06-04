from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot aktif!"

# Aşağıdaki kod en alta eklenmeli:
if __name__ == "__main__":
    threading.Thread(target=main).start()
    app.run(host="0.0.0.0", port=10000)

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from tinydb import TinyDB
import os

# TOKEN'ı ortam değişkeninden alıyoruz (güvenlik için)
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Veritabanı dosyası
db = TinyDB("data.json")

# URL geçerliliği kontrolü
def is_valid_url(text):
    return "hepsiburada.com" in text or "trendyol.com" in text

# /start komutu
def start(update, context):
    update.message.reply_text("👋 Merhaba! Hepsiburada veya Trendyol ürün linki gönder, fiyatı takip edelim!")

# Mesaj geldiğinde
def handle_message(update, context):
    url = update.message.text.strip()
    chat_id = update.message.chat_id

    if is_valid_url(url):
        db.insert({"chat_id": chat_id, "url": url})
        update.message.reply_text("✅ Ürün başarıyla takibe alındı.")
    else:
        update.message.reply_text("❌ Sadece Hepsiburada veya Trendyol linklerini gönderebilirsiniz.")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    print("Bot çalışıyor...")
    updater.idle()

if __name__ == "__main__":
    main()
