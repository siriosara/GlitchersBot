import os
import telebot
import time
import threading
import json
from datetime import datetime, timedelta
from flask import Flask, request

# 🔹 Recupero delle variabili d'ambiente
TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TOKEN or not WEBHOOK_URL:
    raise ValueError("❌ ERRORE: TOKEN o WEBHOOK_URL non trovati nelle variabili d'ambiente!")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# 🔹 ID del canale Glitchers
CHANNEL_ID = -1001716099490  
CHANNEL_LINK = "https://t.me/+mcc19N6Idbs1OWJk"

# 🔹 File per la memorizzazione dei dati persistenti
database_file = "user_data.json"

# 🔹 Database XP
user_xp = {}
user_registered = set()

# 🔹 Soglie XP e Video Premi
video_premi = {
    250: "BAACAgQAAxkBAANRZ65g5avV2vGeKWB2sB7rYpL-z3QAAhYVAAK4hXFRQOWBHIJF29E2BA",
    500: "BAACAgQAAxkBAANTZ65hO01VjYtbcRdWzu4q3ZXhbUMAAiEVAAK4hXFRhpJ3Fxu4DaU2BA",
    1000: "BAACAgQAAxkBAAM4Z65g2S0WiMdVd7Ian8V0OZXfFGoAAiMVAAK4hXFRONGfYWcnLqk2BA"
}

# 🔹 Flask per il Webhook
app = Flask(__name__)

@app.route(f"/{TOKEN}", methods=["POST"])
def receive_update():
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
    if message.from_user.id == 123456789:  # Sostituisci con il tuo Telegram ID
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

# 🔹 Invio automatico dei premi
def check_rewards():
    for user, data in user_xp.items():
        xp = data["xp"]
        for soglia, file_id in video_premi.items():
            if xp >= soglia and data["video_sbloccato"] < soglia:
                try:
                    bot.send_video(user, file_id)
                    data["video_sbloccato"] = soglia
                    save_data()
                    time.sleep(1)  # Evita il flood limit
                except Exception:
                    continue

# 🔹 Comando amministrativo per vedere gli utenti registrati
@bot.message_handler(commands=["totale"])
def total_users(message):
    if message.from_user.id == 123456789:  # Sostituisci con il tuo Telegram ID
        total = len(user_registered)
        bot.send_message(message.chat.id, f"📊 Utenti registrati: {total}")

@bot.message_handler(commands=["dm"])
def send_dm(message):
    if message.from_user.id == 123456789:  # Sostituisci con il tuo Telegram ID
        text = message.text.replace("/dm", "").strip()
        for user in user_registered:
            try:
                bot.send_message(user, text)
                time.sleep(0.5)  # Ritardo per evitare il blocco
            except:
                continue
        bot.send_message(message.chat.id, "✅ Messaggio inviato a tutti gli utenti!")

# 🔹 Loop per il salvataggio periodico dei dati e verifica premi
def auto_save():
    while True:
        time.sleep(600)  # Salva ogni 10 minuti
        save_data()
        check_rewards()

# 🚀 Avvio processi paralleli
threading.Thread(target=auto_save, daemon=True).start()

# 🔹 Imposta il Webhook
bot.remove_webhook()
time.sleep(2)
bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")

# 🔹 Avvia il server Flask
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
