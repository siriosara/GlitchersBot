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

# 🔹 Invio automatico messaggio di benvenuto a nuovi membri
@bot.message_handler(content_types=["new_chat_members"])
def welcome_new_member(message):
    for user in message.new_chat_members:
        if not user.is_bot:
            bot.send_message(
                user.id, 
                "🔥 Vuoi entrare a far parte della community GLITCHERS?\n\n"
                "📌 **Regole:**\n"
                "- Reaction ai post: +5 XP (una volta per post)\n"
                "- Visualizzazione media: +5 XP (una volta per post)\n"
                "- Ogni ora il tuo XP viene aggiornato automaticamente e puoi verificare con il comando /status\n"
                "- Quando raggiungi una soglia, ricevi una parte del video esclusivo!\n\n"
                "🎯 **Soglie XP:**\n"
                "✅ 250 XP → Prima parte del video\n"
                "✅ 500 XP → Seconda parte del video\n"
                "✅ 1000 XP → Video completo\n\n"
                "👉 Rispondi con **SI** per partecipare!"
            )

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

# 🔹 Comandi disponibili solo per OWNER
def owner_only(func):
    def wrapper(message):
        if message.from_user.id != OWNER_ID:
            return bot.send_message(message.chat.id, "⛔ Non hai i permessi per usare questo comando.")
        return func(message)
    return wrapper

@bot.message_handler(commands=["dm"])
def send_dm(message):
    if message.from_user.id != OWNER_ID:
        return bot.send_message(message.chat.id, "⛔ Non hai i permessi per usare questo comando.")

    if message.reply_to_message:  
        # Se il comando è una risposta a un messaggio, inoltra il messaggio a tutti gli utenti registrati
        for user_id in data["user_registered"]:
            try:
                bot.copy_message(user_id, message.chat.id, message.reply_to_message.message_id)
            except Exception:
                pass
        bot.send_message(message.chat.id, "✅ Messaggio inoltrato a tutti gli utenti registrati.")
    else:
        text = message.text.replace("/dm", "").strip()
        if text:
            # Se il comando include del testo, invialo a tutti gli utenti
            for user_id in data["user_registered"]:
                try:
                    bot.send_message(user_id, text)
                except Exception:
                    pass
            bot.send_message(message.chat.id, "✅ Messaggio inviato a tutti gli utenti registrati.")
        else:
            bot.send_message(message.chat.id, "⚠️ Usa il comando così: /dm [messaggio] o rispondi a un messaggio per inoltrarlo.")
            

# 🔹 Comando /classifica con username
@bot.message_handler(commands=["classifica"])
def leaderboard(message):
    if message.from_user.id != OWNER_ID:
        return

    sorted_users = sorted(data["user_xp"].items(), key=lambda x: x[1]["xp"], reverse=True)
    top_users = []

    for i, (user_id, user_data) in enumerate(sorted_users[:10]):
        try:
            chat_member = bot.get_chat_member(CHANNEL_ID, int(user_id))
            username = f"@{chat_member.user.username}" if chat_member.user.username else f"ID: {user_id}"
        except:
            username = f"ID: {user_id}"
        top_users.append(f"{i+1}. {username}: {user_data['xp']} XP")

    response = "🏆 <b>Top 10 Utenti XP</b>:\n" + "\n".join(top_users) if top_users else "Nessun utente in classifica."
    bot.send_message(message.chat.id, response, parse_mode="HTML")
    
    

@bot.message_handler(commands=["totale"])
def total_users(message):
    if message.from_user.id != OWNER_ID:
        return bot.send_message(message.chat.id, "⛔ Non hai i permessi per usare questo comando.")

    total_registered = len(data["user_registered"])
    still_in_channel = sum(1 for user_id in data["user_registered"] if check_subscription(user_id))

    bot.send_message(
        message.chat.id,
        f"👥 <b>Utenti registrati nel bot:</b> {total_registered}\n"
        f"📢 <b>Utenti ancora nel canale:</b> {still_in_channel}",
        parse_mode="HTML"
    )
    
# 🔹 Comando /reset_utente
@bot.message_handler(commands=["reset_utente"])
def reset_user(message):
    if message.from_user.id != OWNER_ID:
        return

    try:
        username = message.text.split()[1].replace("@", "").strip()
        user_id = next((uid for uid, info in data["user_xp"].items() if info.get("username") == username), None)

        if user_id:
            data["user_xp"][user_id]["xp"] = 0
            data["user_xp"][user_id]["video_sbloccato"] = 0
            save_data()
            bot.send_message(message.chat.id, f"✅ XP di @{username} azzerati con successo!")
        else:
            bot.send_message(message.chat.id, f"❌ Utente @{username} non trovato.")

    except IndexError:
        bot.send_message(message.chat.id, "⚠️ Usa il comando così: /reset_utente @username")
        

bot.remove_webhook()
time.sleep(1)
bot.set_webhook(url=WEBHOOK_URL)

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
        
