import telebot
import json
import time
from datetime import datetime
# 🔹 Token del bot e ID del canale
TOKEN = "7665636304:AAEsWwMX7QG4tVoC3IufpSjL-ZMjfspIphY" 
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
OWNER_ID = 123456789 # Sostituisci con il tuo 
CHANNEL_ID = -1001716099490 # ID del 
CHANNEL_LINK = "https://t.me/+mcc19N6Idbs1OWJk" 
telebot.TeleBot(TOKEN, parse_mode="HTML") 
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
        return {
            "user_xp": {},
            "user_registered": []
        }

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
    user_id = str(message.from_user.id)  # Converte user_id in stringa per uniformità nel database

    if not check_subscription(user_id):
        bot.send_message(user_id, f"🔥 Devi essere iscritto al canale per partecipare!\n👍 <a href='{CHANNEL_LINK}'>Iscriviti qui</a>", parse_mode="HTML")
        return

    if user_id not in data["user_xp"]:  # Controllo corretto
        data["user_xp"][user_id] = {"xp": 0, "video_sbloccato": 0}
        data["user_registered"].append(user_id)
        save_data()
        bot.send_message(user_id, "✅ Sei registrato! Inizia a guadagnare XP per sbloccare i premi! 🎉")
    else:
        bot.send_message(message.chat.id, "❌ Non sei registrato. Usa /start per iscriverti.")


@bot.message_handler(commands=["dm"])
def send_dm(message):
    user_id = str(message.from_user.id)
    if user_id not in data["user_xp"]:
        data["user_xp"][user_id] = {"xp": 0, "video_sbloccato": 0}
        bot.send_message(user_id, "📩 Il tuo DM è stato registrato!")
# 🔹 Comando /classifica
@bot.message_handler(commands=["classifica"])
def leaderboard(message):
    if message.from_user.id != OWNER_ID:
        return
 
    sorted_users = sorted(data["user_xp"].items(), key=lambda x: x[1]["xp"], reverse=True)
    top_users = "\n".join([f"{i+1}. <b>{user[0]}</b>: {user[1]['xp']} XP" for i, user in enumerate(sorted_users[:10])])
 
    bot.send_message(message.chat.id, f"🏆 <b>Top 10 Utenti XP</b>:\n{top_users}", parse_mode="HTML")
# 🔹 Comando /totale → Mostra il numero di utenti registrati e ancora nel canale
@bot.message_handler(commands=["totale"])
def total_users(message):
    total = len(data["user_registered"])
    bot.send_message(message.chat.id, f"👥 Utenti registrati: {total}")
# 🔹 Comando /premi_riscossi → Mostra la lista utenti con premi riscossi
@bot.message_handler(commands=["premi_riscossi"])
def redeemed_rewards(message):
    redeemed = [f"🔹 {user}" for user in data["user_xp"] if data["user_xp"][user]["video_sbloccato"] > 0]
    response = "\n".join(redeemed) if redeemed else "Nessun utente ha riscattato premi."
    bot.send_message(message.chat.id, response)
# 🔹 Comando /attivi_oggi → Mostra numero utenti attivi oggi
@bot.message_handler(commands=["attivi_oggi"])
def active_today(message):
    today_active = sum(1 for user in data["user_xp"] if data["user_xp"][user]["xp"] > 0)
    bot.send_message(message.chat.id, f"📊 Utenti attivi oggi: {today_active}")
# 🔹 Comando /ultimi_iscritti → Mostra gli ultimi 10 utenti registrati
@bot.message_handler(commands=["ultimi_iscritti"])
def last_registered(message):
    last_users = data["user_registered"][-10:]
    response = "\n".join([f"🔹 {user}" for user in last_users]) if last_users else "Nessun nuovo utente registrato."
    bot.send_message(message.chat.id, response)
# 🔹 Comando /reset_utente → Resetta XP di un utente specifico
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
# 🔹 Comando /log_attività → Mostra le ultime azioni registrate
@bot.message_handler(commands=["log_attività"])
def activity_log(message):
    log = "\n".join([f"{user}: {data['user_xp'][user]['xp']} XP" for user in list(data["user_xp"].keys())[-10:]])
    response = log if log else "Nessuna attività registrata."
    bot.send_message(message.chat.id, f"📜 Ultime attività:\n{response}")
# 🔹 Comando /ban → Bannare un utente dal bot e dal canale
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
# 🔹 Rimuove Webhook prima di avviare il bot
bot.remove_webhook()
print("Webhook rimosso con successo!")
# Loop per il salvataggio dati periodico
def periodic_save():
    while True:
        time.sleep(3600)  # Salva ogni ora
        save_data()
        print("Database salvato.")
# Avvio thread separato per il salvataggio dati
import threading
threading.Thread(target=periodic_save, daemon=True).start()
# Avvio bot con gestione errori
time.sleep(1)  # Aspetta un secondo per sicurezza
try:
    bot.polling(none_stop=True)
except Exception as e:
    print(f"Errore durante il polling: {e}")

<<<<<<< HEAD
# 🔹 Rimuove Webhook prima di avviare il bot
bot.remove_webhook()
print("Webhook rimosso con successo!")

# 🔹 Loop per il salvataggio dati periodico
def periodic_save():
    while True:
        time.sleep(3600)  # Salva ogni ora
        save_data()
        print("Database salvato.")

# 🔹 Avvio thread separato per il salvataggio dati
import threading
threading.Thread(target=periodic_save, daemon=True).start()

# 🔹 Avvio bot con gestione errori
time.sleep(1)  # Aspetta un secondo per sicurezza

try:
    bot.polling(none_stop=True)
except Exception as e:
    print(f"Errore durante il polling: {e}")
