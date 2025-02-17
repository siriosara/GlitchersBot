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
OWNER_ID = 123456789  # Sostituisci con il tuo
CHANNEL_ID = -1001716099490  # ID del canale
CHANNEL_LINK = "https://t.me/+mcc19N6Idbs1OWJk" 
db_file = "user_data.json"

# 🔹 URL del Webhook su Railway
WEBHOOK_URL = "https://worker-production-5371.up.railway.app/webhook"

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

# 🔹 Comando /start
@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_id = str(message.from_user.id)

    if not check_subscription(user_id):
        bot.send_message(user_id, f"🔥 Devi essere iscritto al canale per partecipare!\n👍 <a href='{CHANNEL_LINK}'>Iscriviti qui</a>", parse_mode="HTML")
        return

    if user_id not in data["user_xp"]:
        data["user_xp"][user_id] = {"xp": 0, "video_sbloccato": 0}
        if user_id not in data["user_registered"]:
            data["user_registered"].append(user_id)
        save_data()
        bot.send_message(user_id, "✅ Sei registrato! Inizia a guadagnare XP per sbloccare i premi! 🎉")
    else:
        bot.send_message(user_id, "✅ Sei già registrato! Continua a guadagnare XP! 🎉")

# 🔹 Comando /status
@bot.message_handler(commands=["status"])
def check_status(message):
    user_id = str(message.from_user.id)

    if user_id in data["user_xp"]:
        xp = data["user_xp"][user_id]["xp"]
        video_sbloccati = data["user_xp"][user_id]["video_sbloccato"]
        bot.send_message(user_id, f"📊 Il tuo status:\n🔹 XP: {xp}\n🔹 Video sbloccati: {video_sbloccati}")
    else:
        bot.send_message(user_id, "❌ Non sei registrato. Usa /start per iscriverti.")

# 🔹 Comando /dm (ora invia un messaggio a tutti gli utenti registrati)
@bot.message_handler(commands=["dm"])
def send_dm(message):
    if message.from_user.id != OWNER_ID:
        return
        
# 🔹 Comando /classifica
@bot.message_handler(commands=["classifica"])
def leaderboard(message):
    if message.from_user.id != OWNER_ID:
        return
 
    sorted_users = sorted(data["user_xp"].items(), key=lambda x: x[1]["xp"], reverse=True)
    top_users = "\n".join([f"{i+1}. <b>{user[0]}</b>: {user[1]['xp']} XP" for i, user in enumerate(sorted_users[:10])])
 
    bot.send_message(message.chat.id, f"🏆 <b>Top 10 Utenti XP</b>:\n{top_users}", parse_mode="HTML")

# 🔹 Comando /totale
@bot.message_handler(commands=["totale"])
def total_users(message):
    total = len(data["user_registered"])
    bot.send_message(message.chat.id, f"👥 Utenti registrati: {total}")

# 🔹 Comando /premi_riscossi
@bot.message_handler(commands=["premi_riscossi"])
def redeemed_rewards(message):
    redeemed = [f"🔹 {user}" for user in data["user_xp"] if data["user_xp"][user]["video_sbloccato"] > 0]
    response = "\n".join(redeemed) if redeemed else "Nessun utente ha riscattato premi."
    bot.send_message(message.chat.id, response)

# 🔹 Comando /attivi_oggi
@bot.message_handler(commands=["attivi_oggi"])
def active_today(message):
    today_active = sum(1 for user in data["user_xp"] if data["user_xp"][user]["xp"] > 0)
    bot.send_message(message.chat.id, f"📊 Utenti attivi oggi: {today_active}")

# 🔹 Comando /ultimi_iscritti
@bot.message_handler(commands=["ultimi_iscritti"])
def last_registered(message):
    last_users = data["user_registered"][-10:]
    response = "\n".join([f"🔹 @{data['user_xp'][user]['username']}" if user in data["user_xp"] else f"🔹 {user}" for user in last_users]) if last_users else "Nessun nuovo utente registrato."
    bot.send_message(message.chat.id, response)
    

# 🔹 Comando /reset_utente
@bot.message_handler(commands=["reset_utente"])
def reset_user(message):
    try:
        username = message.text.split()[1]
        if username in data["user_xp"]:
            data["user_xp"][username]["xp"] = 0
            data["user_xp"][username]["video_sbloccato"] = 0
            save_data()
            bot.send_message(message.chat.id, f"✅ XP di {username} azzerato con successo!")
        else:
            bot.send_message(message.chat.id, "❌ Utente non trovato.")
    except IndexError:
        bot.send_message(message.chat.id, "⚠️ Usa il comando così: /reset_utente @username")

# 🔹 Comando /log_attività
@bot.message_handler(commands=["log_attività"])
def activity_log(message):
    log = "\n".join([f"{user}: {data['user_xp'][user]['xp']} XP" for user in list(data["user_xp"].keys())[-10:]])
    response = log if log else "Nessuna attività registrata."
    bot.send_message(message.chat.id, f"📜 Ultime attività:\n{response}")

# 🔹 Comando /ban
@bot.message_handler(commands=["ban"])
def ban_user(message):
    try:
        user_id = int(message.text.split()[1])
        if user_id in data["user_registered"]:
            data["user_registered"].remove(user_id)
            del data["user_xp"][str(user_id)]
            save_data()
            bot.kick_chat_member(CHANNEL_ID, user_id)
            bot.send_message(message.chat.id, f"🚨 Utente {user_id} bannato con successo!")
        else:
            bot.send_message(message.chat.id, "❌ Utente non trovato.")
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, "⚠️ Usa il comando così: /ban user_id")

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
