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
OWNER_ID = 5543012634  # ⚠️ Assicurati che sia il tuo vero ID
CHANNEL_ID = -1001716099490
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

# 🔹 Controllo se l'utente è admin
def is_admin(user_id):
    return str(user_id) == str(OWNER_ID)

# 🔹 Messaggio di benvenuto automatico
@bot.chat_member_handler()
def welcome_message(member):
    if member.new_chat_member.status in ["member", "administrator"]:
        bot.send_message(member.chat.id, f"""
🔥 Vuoi entrare a far parte della community GLITCHERS?

📌 **Regole:**
- Reaction ai post: +5 XP (una volta per post)
- Visualizzazione media: +5 XP (una volta per post)
- Ogni ora il tuo XP viene aggiornato automaticamente
- Quando raggiungi una soglia, ricevi una parte del video esclusivo!

🎯 **Soglie XP:**
✅ 250 XP → Prima parte del video
✅ 500 XP → Seconda parte del video
✅ 1000 XP → Video completo

👀 utilizza il comando /status per verificare il tuo punteggio 
👉 Rispondi con **SI** per partecipare!
        """)

# 🔹 Comando /status (unico disponibile per tutti)
@bot.message_handler(commands=["status"])
def check_status(message):
    user_id = str(message.from_user.id)
    if user_id in data["user_xp"]:
        xp = data["user_xp"][user_id]["xp"]
        video_sbloccati = data["user_xp"][user_id]["video_sbloccato"]
        bot.send_message(user_id, f"📊 Il tuo status:\n🔹 XP: {xp}\n🔹 Video sbloccati: {video_sbloccati}")
    else:
        bot.send_message(user_id, "❌ Non sei registrato. Usa /start per iscriverti.")

# 🔹 Comando /dm (invia un messaggio a tutti gli utenti registrati)
@bot.message_handler(commands=["dm"])
def send_dm(message):
    if not is_admin(message.from_user.id):
        return
    text = message.text.replace("/dm ", "")
    for user_id in data["user_registered"]:
        try:
            bot.send_message(user_id, text)
        except:
            pass

# 🔹 Comando /classifica
@bot.message_handler(commands=["classifica"])
def leaderboard(message):
    if not is_admin(message.from_user.id):
        return
    sorted_users = sorted(data["user_xp"].items(), key=lambda x: x[1]["xp"], reverse=True)
    top_users = "\n".join([f"{i+1}. @{user[0]}: {user[1]['xp']} XP" for i, user in enumerate(sorted_users[:10])])
    bot.send_message(message.chat.id, f"🏆 <b>Top 10 Utenti XP</b>:\n{top_users}", parse_mode="HTML")

# 🔹 Comando /ban
@bot.message_handler(commands=["ban"])
def ban_user(message):
    if not is_admin(message.from_user.id):
        return
    try:
        user_id = int(message.text.split()[1])
        if str(user_id) in data["user_registered"]:
            data["user_registered"].remove(str(user_id))
            del data["user_xp"][str(user_id)]
            save_data()
            bot.kick_chat_member(CHANNEL_ID, user_id)
            bot.send_message(message.chat.id, f"🚨 Utente {user_id} bannato con successo!")
    except:
        bot.send_message(message.chat.id, "⚠️ Usa il comando così: /ban user_id")

# 🔹 Altri comandi admin
@bot.message_handler(commands=["totale", "premi_riscossi", "attivi_oggi", "ultimi_iscritti", "reset_utente", "log_attività"])
def admin_commands(message):
    if not is_admin(message.from_user.id):
        return

    cmd = message.text.split()[0][1:]

    if cmd == "totale":
        bot.send_message(message.chat.id, f"👥 Utenti registrati: {len(data['user_registered'])}")

    elif cmd == "premi_riscossi":
        redeemed = [f"🔹 @{user}" for user in data["user_xp"] if data["user_xp"][user]["video_sbloccato"] > 0]
        response = "\n".join(redeemed) if redeemed else "Nessun utente ha riscattato premi."
        bot.send_message(message.chat.id, response)

    elif cmd == "attivi_oggi":
        today_active = sum(1 for user in data["user_xp"] if data["user_xp"][user]["xp"] > 0)
        bot.send_message(message.chat.id, f"📊 Utenti attivi oggi: {today_active}")

    elif cmd == "ultimi_iscritti":
        last_users = data["user_registered"][-10:]
        response = "\n".join([f"🔹 @{user}" for user in last_users]) if last_users else "Nessun nuovo utente registrato."
        bot.send_message(message.chat.id, response)

    elif cmd == "reset_utente":
        try:
            username = message.text.split()[1]
            if username in data["user_xp"]:
                data["user_xp"][username]["xp"] = 0
                data["user_xp"][username]["video_sbloccato"] = 0
                save_data()
                bot.send_message(message.chat.id, f"✅ XP di {username} azzerato con successo!")
        except:
            bot.send_message(message.chat.id, "⚠️ Usa il comando così: /reset_utente @username")

# 🔹 Avvio Webhook
bot.remove_webhook()
time.sleep(1)
bot.set_webhook(url=WEBHOOK_URL)

# 🔹 Creazione server Flask
app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
                
