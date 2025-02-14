import os
import telebot
import time
import threading
import json
from datetime import datetime
from flask import Flask, request

# 🔹 Inserisci il tuo Token API qui
TOKEN = "7665636304:AAEsWwMX7QG4tVoC3IufpSjL-ZMjfspIphY"
OWNER_ID = 123456789  # Sostituisci con il tuo Telegram ID
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# 🔹 ID del canale Glitchers
CHANNEL_ID = -1001716099490  
CHANNEL_LINK = "https://t.me/+mcc19N6Idbs1OWJk"

# 🔹 File per la memorizzazione dei dati persistenti
database_file = "user_data.json"

# 🔹 Database XP
user_xp = {}
user_registered = set()

# 🔹 Flask Web Server per Railway
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Glitchers Bot is running!"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

# 🔹 Caricare i dati salvati
def load_data():
    global user_xp, user_registered
    try:
        with open(database_file, "r") as f:
            data = json.load(f)
            user_xp = data.get("user_xp", {})
            user_registered = set(data.get("user_registered", []))
    except FileNotFoundError:
        save_data()

def save_data():
    with open(database_file, "w") as f:
        json.dump({"user_xp": user_xp, "user_registered": list(user_registered)}, f)

load_data()

# 🔹 Comando per ottenere il file_id di un video
@bot.message_handler(content_types=['video'])
def get_file_id(message):
    if message.from_user.id == OWNER_ID:
        file_id = message.video.file_id
        bot.reply_to(message, f"📌 File ID: `{file_id}`")

# 🔹 Comando di benvenuto
@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_id = message.from_user.id
    if user_id in user_registered:
        bot.send_message(user_id, "🔥 Sei già registrato nel sistema XP!")
    else:
        bot.send_message(
            user_id,
            "🔥 Vuoi entrare a far parte della community GLITCHERS?\n\n"
            "📌 **Regole:**\n"
            "- Reaction ai post: +5 XP (una volta per post)\n"
            "- Visualizzazione media: +5 XP (una volta per post)\n"
            "- Ogni ora il tuo XP viene aggiornato automaticamente\n"
            "- Quando raggiungi una soglia, ricevi una parte del video esclusivo!\n\n"
            "🎯 **Soglie XP:**\n"
            "✅ 250 XP → Prima parte del video\n"
            "✅ 500 XP → Seconda parte del video\n"
            "✅ 1000 XP → Video completo\n\n"
            "👉 Rispondi con **SI** per partecipare!"
        )

@bot.message_handler(func=lambda message: message.text.lower() == "si")
def register_user(message):
    user_id = message.from_user.id
    if user_id not in user_registered:
        user_registered.add(user_id)
        user_xp[user_id] = {"xp": 0, "last_active": str(datetime.now()), "video_sbloccato": 0}
        save_data()
        bot.send_message(user_id, "✅ Sei registrato! Inizia a guadagnare XP per sbloccare i premi! 🏆")

# 🔹 Loop per il salvataggio periodico dei dati
def auto_save():
    while True:
        time.sleep(600)  # Salva ogni 10 minuti
        save_data()

# 🔹 Avvia il loop di Flask e Polling in parallelo
if __name__ == "__main__":
    threading.Thread(target=auto_save, daemon=True).start()
    
    # Imposta Webhook per Railway
    bot.remove_webhook()
    bot.set_webhook(url=f"https://worker-production-566f.up.railway.app/{TOKEN}")
    
    # Usa la variabile di ambiente PORT per Railway
    PORT = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=PORT)
    
