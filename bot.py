from flask import Flask
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from tinydb import TinyDB
import os
import threading
import requests
from bs4 import BeautifulSoup
import time

# Flask uygulaması (Render'da ayakta kalmak için)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot aktif!"

# Ortam değişkeninden token'ı al
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Veritabanı
db = TinyDB("data.json")

# Telegram bot komutları
def start(update, context):
    update.message.reply_text("👋 Merhaba! Hepsiburada veya Trendyol ürün linki gönder, fiyatı takip edelim!")

def is_valid_url(text):
    return "hepsiburada.com" in text or "trendyol.com" in text

def handle_message(update, context):
    url = update.message.text.strip()
    chat_id = update.message.chat_id

    if is_valid_url(url):
        # Varsa tekrar eklenmesin
        existing = db.search((TinyDB.table('default')['chat_id'] == chat_id) & (TinyDB.table('default')['url'] == url))
        if not existing:
            db.insert({"chat_id": chat_id, "url": url})
            update.message.reply_text("✅ Ürün başarıyla takibe alındı.")
        else:
            update.message.reply_text("🔁 Bu ürün zaten takibe alınmış.")
    else:
        update.message.reply_text("❌ Sadece Hepsiburada veya Trendyol linklerini gönderebilirsiniz.")

# Fiyat çekme (şimdilik sadece Hepsiburada için)
def scrape_price_hepsiburada(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        tag = soup.find("span", attrs={"data-bind": "markupText:'currentPriceBeforePoint'"})
        frac = soup.find("span", attrs={"data-bind": "markupText:'currentPriceAfterPoint'"})
        if tag and frac:
            price = f"{tag.text.strip()}.{frac.text.strip()}"
            return float(price.replace(".", "").replace(",", "."))
    except Exception as e:
        print("Scrape error:", e)
    return None

# Arka planda fiyat kontrolü
def check_prices():
    while True:
        print("🔄 Fiyat kontrolü başladı...")
        for entry in db.all():
            url = entry["url"]
            chat_id = entry["chat_id"]

            if "hepsiburada.com" in url:
                price = scrape_price_hepsiburada(url)
            else:
                continue  # Trendyol desteklenmiyor (şimdilik)

            if price is None:
                print("❌ Fiyat çekilemedi:", url)
                continue

            # İlk defa kayıt yapılacaksa
            if 'price' not in entry:
                db.update({'price': price}, doc_ids=[entry.doc_id])
                continue

            old_price = entry['price']
            if price < old_price:
                try:
                    updater.bot.send_message(
                        chat_id=chat_id,
                        text=f"📉 Fiyat düştü!\n{url}\n\n💸 Eski: {old_price} TL\n🆕 Yeni: {price} TL"
                    )
                    db.update({'price': price}, doc_ids=[entry.doc_id])
                except Exception as e:
                    print("Bildirim hatası:", e)

        print("⏸️ Kontrol tamamlandı. 6 saat uyku...")
        time.sleep(21600)  # 6 saat

# Telegram botu başlat
def main():
    global updater
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    print("🤖 Bot çalışıyor...")

    # Arka planda fiyat kontrol thread'i başlat
    threading.Thread(target=check_prices).start()

    updater.idle()

# Hem Flask hem Telegram botu çalıştır
if __name__ == "__main__":
    threading.Thread(target=main).start()
    app.run(host="0.0.0.0", port=10000)
