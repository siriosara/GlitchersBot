import os
import telebot
import json
import time
import threading
from flask import Flask, request
from datetime import datetime

# 🔹 Token del bot e ID del canale
TOKEN = "7665636304:AAEsWwMX7QG4tVoC3IufpSjL-ZMjfspIphY"
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
OWNER_ID = 5543012634  # Tuo ID Telegram
CHANNEL_ID = -1001716099490  # ID del canale
CHANNEL_LINK = "https://t.me/+mcc19N6Idbs1OWJk"
db_file = "user_data.json"

# 🔹 URL del Webhook su Railway
WEBHOOK_URL = "https://worker-production-5371.up.railway.app/webhook"

# 🔹 File ID dei premi
video_premi = {
    250: "BAACAgQAAxkBAANRZ65g5avV2vGeKWB2sB7rYpL-z3QAAhYVAAK4hXFRQOWBHIJF29E2BA",
    500: "BAACAgQAAxkBAANTZ65hO01VjYtbcRdWzu4q3ZXhbUMAAiEVAAK4hXFRhpJ3Fxu4DaU2BA",
    1000: "BAACAgQAAxkBAAM4Z65g2S0WiMdVd7Ian8V0OZXfFGoAAiMVAAK4hXFRONGfYWcnLqk2BA"
}

# 🔹 Caricare i dati salvati
def load_data():
    if os.path.exists(db_file):
        try:
            with open(db_file, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"user_xp": {}, "user_registered": []}
    return {"user_xp": {}, "user_registered": []}

data = load_data()

# 🔹 Salvataggio persistente
def save_data():
    with open(db_file, "w") as f:
        json.dump(data, f, indent=4)

# 🔹 Controllo iscrizione al canale
def check_subscription(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        return status in ["member", "administrator", "creator"]
    except:
        return False

# 🔹 Invio automatico messaggio di benvenuto a nuovi membri
@bot.chat_member_handler()
def welcome_new_member(update):
    if update.new_chat_member and not update.new_chat_member.user.is_bot:
        user_id = update.new_chat_member.user.id
        bot.send_message(user_id, 
        "🔥 Vuoi entrare a far parte della community GLITCHERS?\n\n"
        "📌 **Regole:**\n"
        "- Reaction ai post: +5 XP (una volta per post)\n"
        "- Visualizzazione media: +5 XP (una volta per post)\n"
        "- Ogni ora il tuo XP viene aggiornato automaticamente e potrai verificare con il comando /status\n"
        "- Quando raggiungi una soglia, ricevi una parte del video esclusivo!\n\n"
        "🎯 **Soglie XP:**\n"
        "✅ 250 XP → Prima parte del video\n"
        "✅ 500 XP → Seconda parte del video\n"
        "✅ 1000 XP → Video completo\n\n"
        "👉 Rispondi con **SI** per partecipare!")

# 🔹 Comando /start
@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_id = str(message.from_user.id)
    
    if user_id not in data["user_xp"]:
        data["user_xp"][user_id] = {"xp": 0, "video_sbloccato": 0}
        if user_id not in data["user_registered"]:
            data["user_registered"].append(user_id)
        save_data()
        bot.send_message(user_id, "✅ Sei registrato! Inizia a guadagnare XP per sbloccare i premi! 🎉")
    else:
        bot.send_message(user_id, "✅ Sei già registrato! Continua a guadagnare XP! 🎉")

# 🔹 Comando /status (unico accessibile agli utenti normali)
@bot.message_handler(commands=["status"])
def check_status(message):
    user_id = str(message.from_user.id)
    if user_id in data["user_xp"]:
        xp = data["user_xp"][user_id]["xp"]
        video_sbloccati = data["user_xp"][user_id]["video_sbloccato"]
        bot.send_message(user_id, f"📊 Il tuo status:\n🔹 XP: {xp}\n🔹 Video sbloccati: {video_sbloccati}")
    else:
        bot.send_message(user_id, "❌ Non sei registrato. Usa /start per iscriverti.")

# 🔹 Comando /dm per inviare messaggi agli utenti registrati
@bot.message_handler(commands=["dm"])
def send_dm(message):
    if message.from_user.id != OWNER_ID:
        return bot.send_message(message.chat.id, "⛔ Non hai i permessi per usare questo comando.")

    text = message.text.replace("/dm", "").strip()
    if not text:
        return bot.send_message(message.chat.id, "⚠️ Usa il comando così: /dm [messaggio]")

    for user_id in data["user_registered"]:
        try:
            bot.send_message(user_id, text)
        except:
            pass
    bot.send_message(message.chat.id, "✅ Messaggio inviato a tutti gli utenti registrati.")

# 🔹 Comando /reset_utente con username
@bot.message_handler(commands=["reset_utente"])
def reset_user(message):
    if message.from_user.id != OWNER_ID:
        return bot.send_message(message.chat.id, "⛔ Non hai i permessi per usare questo comando.")

    try:
        username = message.text.split()[1].replace("@", "")
        for user_id, user_data in data["user_xp"].items():
            if user_data.get("username") == username:
                user_data["xp"] = 0
                user_data["video_sbloccato"] = 0
                save_data()
                bot.send_message(message.chat.id, f"✅ XP di @{username} azzerato con successo!")
                return
        bot.send_message(message.chat.id, "❌ Utente non trovato.")
    except IndexError:
        bot.send_message(message.chat.id, "⚠️ Usa il comando così: /reset_utente @username")

# 🔹 Comando /ban con username
@bot.message_handler(commands=["ban"])
def ban_user(message):
    if message.from_user.id != OWNER_ID:
        return bot.send_message(message.chat.id, "⛔ Non hai i permessi per usare questo comando.")

    try:
        username = message.text.split()[1].replace("@", "")
        for user_id, user_data in data["user_xp"].items():
            if user_data.get("username") == username:
                data["user_registered"].remove(user_id)
                del data["user_xp"][user_id]
                save_data()
                bot.kick_chat_member(CHANNEL_ID, int(user_id))
                bot.send_message(message.chat.id, f"🚨 Utente @{username} bannato con successo!")
                return
        bot.send_message(message.chat.id, "❌ Utente non trovato.")
    except IndexError:
        bot.send_message(message.chat.id, "⚠️ Usa il comando così: /ban @username")

# 🔹 Avvio Webhook per Railway
bot.remove_webhook()
time.sleep(1)
bot.set_webhook(url=WEBHOOK_URL)
print(f"✅ Webhook impostato su: {WEBHOOK_URL}")

# 🔹 Creazione del server Flask per Webhook
app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_str = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
                         
