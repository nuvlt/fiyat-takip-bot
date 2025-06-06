from flask import Flask
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from tinydb import TinyDB
import os
import threading
import requests
from bs4 import BeautifulSoup
import time

# Flask (Render botu ayakta tutmak için)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot aktif!"

# Ortam değişkeni
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Veritabanı
db = TinyDB("data.json")

# Telegram komutları
def start(update, context):
    update.message.reply_text("👋 Merhaba! Hepsiburada veya Trendyol ürün linki gönder, fiyatı takip edelim!")

def is_valid_url(text):
    return "hepsiburada.com" in text or "trendyol.com" in text

def handle_message(update, context):
    url = update.message.text.strip()
    chat_id = update.message.chat_id

    if is_valid_url(url):
        # Aynı kullanıcı aynı linki tekrar eklemesin
        existing = db.search((TinyDB.table('default')['chat_id'] == chat_id) & (TinyDB.table('default')['url'] == url))
        if not existing:
            db.insert({"chat_id": chat_id, "url": url})
            update.message.reply_text("✅ Ürün başarıyla takibe alındı.")
        else:
            update.message.reply_text("🔁 Bu ürün zaten takibe alınmış.")
    else:
        update.message.reply_text("❌ Lütfen sadece Hepsiburada veya Trendyol ürün linki gönderin.")

# Fiyat çekme fonksiyonları
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
        print("Hepsiburada scrape error:", e)
    return None

def scrape_price_trendyol(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        price_tag = soup.find("span", class_="prc-dsc")
        if not price_tag:
            price_tag = soup.find("span", class_="prc-org")
        if price_tag:
            price_text = price_tag.text.strip().replace("TL", "").replace(".", "").replace(",", ".")
            return float(price_text)
    except Exception as e:
        print("Trendyol scrape error:", e)
    return None

# Fiyat kontrol fonksiyonu (arka planda döner)
def check_prices():
    while True:
        print("🔄 Fiyat kontrolü başlıyor...")
        for entry in db.all():
            url = entry["url"]
            chat_id = entry["chat_id"]

            if "hepsiburada.com" in url:
                price = scrape_price_hepsiburada(url)
            elif "trendyol.com" in url:
                price = scrape_price_trendyol(url)
            else:
                continue

            if price is None:
                print("⚠️ Fiyat alınamadı:", url)
                continue

            if "price" not in entry:
                db.update({"price": price}, doc_ids=[entry.doc_id])
                continue

            old_price = entry["price"]
            if price < old_price:
                try:
                    updater.bot.send_message(
                        chat_id=chat_id,
                        text=f"📉 Fiyat düştü!\n{url}\n\n💸 Eski: {old_price} TL\n🆕 Yeni: {price} TL"
                    )
                    db.update({"price": price}, doc_ids=[entry.doc_id])
                except Exception as e:
                    print("Bildirim hatası:", e)

        print("⏸️ Kontrol tamamlandı. 6 saat bekleniyor...")
        time.sleep(21600)  # 6 saat

# Telegram bot başlatma
def main():
    global updater
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    print("🤖 Bot çalışıyor...")

    # Fiyat kontrol döngüsünü başlat
    threading.Thread(target=check_prices).start()

    updater.idle()

# Ana giriş
from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def home():
    return 'Bot aktif!'

if __name__ == '__main__':
    threading.Thread(target=main).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
