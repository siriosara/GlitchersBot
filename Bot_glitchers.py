import telebot
import json
import time
import threading
from datetime import datetime

# 🔹 Token del bot e ID del canale
TOKEN = "7665636304:AAEsWwMX7QG4tVoC3IufpSjL-ZMjfspIphY"
OWNER_ID = 123456789  # Sostituisci con il tuo Telegram ID
CHANNEL_ID = -1001716099490  # ID del canale Telegram
CHANNEL_LINK = "https://t.me/+mcc19N6Idbs1OWJk"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

db_file = "user_data.json"

# 🔹 File ID dei premi
video_premi = {
    250: "BAACAgQAAxkBAANRZ65g5avV2vGeKWB2sB7rYpL-z3QAAhYVAAK4hXFRQOWBHIJF29E2BA",
    500: "BAACAgQAAxkBAANTZ65hO01VjYtbcRdWzu4q3ZXhbUMAAiEVAAK4hXFRhpJ3Fxu4DaU2BA",
    1000: "BAACAgQAAxkBAAM4Z65g2S0WiMdVd7Ian8V0OZXfFGoAAiMVAAK4hXFRONGfYWcnLqk2BA"
}

# 🔹 Caricare i dati salvati
def load_data():
    try:
        with open(db_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"user_xp": {}, "user_registered": []}

data = load_data()

# 🔹 Salvataggio persistente
def save_data():
    with open(db_file, "w") as f:
        json.dump(data, f)

# 🔹 Controllo iscrizione al canale
def check_subscription(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        return status in ["member", "administrator", "creator"]
    except:
        return False

# 🔹 Comando /start
@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_id = message.from_user.id
    if not check_subscription(user_id):
        bot.send_message(user_id, f"🔥 Devi essere iscritto al canale per partecipare!\n👉 <a href='{CHANNEL_LINK}'>Iscriviti qui</a>")
        return
    if str(user_id) not in data["user_xp"]:
        data["user_xp"][str(user_id)] = {"xp": 0, "video_sbloccato": 0}
        data["user_registered"].append(user_id)
        save_data()
        bot.send_message(user_id, "✅ Sei registrato! Inizia a guadagnare XP per sbloccare i premi! 🏆")
    else:
        bot.send_message(user_id, "🔥 Sei già registrato nel sistema XP!")

# 🔹 Comando /status
@bot.message_handler(commands=["status"])
def check_status(message):
    user_id = str(message.from_user.id)
    if user_id in data["user_xp"]:
        xp = data["user_xp"][user_id]["xp"]
        bot.send_message(message.chat.id, f"📊 Il tuo XP attuale: {xp}")
    else:
        bot.send_message(message.chat.id, "❌ Non sei registrato. Usa /start per iscriverti.")

# 🔹 Comando /dm
@bot.message_handler(commands=["dm"])
def send_dm(message):
    if message.from_user.id != OWNER_ID:
        return
    text = message.text.replace("/dm", "").strip()
    if not text:
        bot.send_message(message.chat.id, "❌ Scrivi un messaggio da inviare a tutti gli utenti registrati.")
        return
    for user_id in data["user_registered"]:
        try:
            bot.send_message(user_id, text)
        except:
            continue
    bot.send_message(message.chat.id, "✅ Messaggio inviato a tutti gli utenti!")

# 🔹 Comando /totale
@bot.message_handler(commands=["totale"])
def total_users(message):
    if message.from_user.id != OWNER_ID:
        return
    total = len(data["user_registered"])
    bot.send_message(message.chat.id, f"📊 Utenti registrati: {total}")

# 🔹 Comando /classifica
@bot.message_handler(commands=["classifica"])
def leaderboard(message):
    if message.from_user.id != OWNER_ID:
        return
    sorted_users = sorted(data["user_xp"].items(), key=lambda x: x[1]["xp"], reverse=True)
    top_users = "\n".join([f"{i+1}. <b>{user[0]}</b>: {user[1]['xp']} XP" for i, user in enumerate(sorted_users[:10])])
    bot.send_message(message.chat.id, f"🏆 <b>Top 10 Utenti XP</b>:\n{top_users}", parse_mode="HTML")

# 🔹 Rimozione webhook
bot.remove_webhook()
print("Webhook rimosso con successo!")

# 🔹 Avvio salvataggio dati in un thread separato
def save_data_periodically():
    while True:
        time.sleep(3600)  # Salva ogni ora
        save_data()
        print("Database salvato.")

thread = threading.Thread(target=save_data_periodically, daemon=True)
thread.start()

# 🔹 Avvio bot 
bot.infinity_polling()
