import telebot
import time
import threading
import json
from datetime import datetime, timedelta

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

# 🔹 Soglie XP e Video Premi
video_premi = {
    250: "BAACAgQAAxkBAANRZ65g5avV2vGeKWB2sB7rYpL-z3QAAhYVAAK4hXFRQOWBHIJF29E2BA",
    500: "BAACAgQAAxkBAANTZ65hO01VjYtbcRdWzu4q3ZXhbUMAAiEVAAK4hXFRhpJ3Fxu4DaU2BA",
    1000: "BAACAgQAAxkBAAM4Z65g2S0WiMdVd7Ian8V0OZXfFGoAAiMVAAK4hXFRONGfYWcnLqk2BA"
}

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

# 🔹 Comandi amministrativi (solo OWNER_ID)
@bot.message_handler(commands=["lista_comandi"])
def list_commands(message):
    if message.from_user.id == OWNER_ID:
        bot.send_message(message.chat.id, "📌 **Lista comandi amministrativi:**\n"
            "- /totale → Utenti totali e ancora nel canale\n"
            "- /classifica → Distribuzione XP\n"
            "- /premi_riscossi → Lista utenti con premi riscossi\n"
            "- /attivi_oggi → Numero utenti attivi oggi\n"
            "- /ultimi_iscritti → Ultimi 10 utenti registrati\n"
            "- /reset_utente @username → Resetta XP di un utente\n"
            "- /log_attività → Ultime azioni registrate\n"
            "- /dm [messaggio] → Invia DM a tutti gli utenti")

# 🔹 Comando /totale per utenti registrati vs attivi nel canale
@bot.message_handler(commands=["totale"])
def total_users(message):
    if message.from_user.id == OWNER_ID:
        total = len(user_registered)
        active = sum(1 for user in user_registered if bot.get_chat_member(CHANNEL_ID, user).status in ["member", "administrator", "creator"])
        bot.send_message(message.chat.id, f"📊 Utenti registrati: {total}\n🔹 Ancora nel canale: {active}")

# 🔹 Comando per inviare DM a tutti gli utenti
@bot.message_handler(commands=["dm"])
def send_dm(message):
    if message.from_user.id == OWNER_ID:
        text = message.text.replace("/dm", "").strip()
        for user in user_registered:
            try:
                bot.send_message(user, text)
            except:
                continue
        bot.send_message(message.chat.id, "✅ Messaggio inviato a tutti gli utenti!")

# 🔹 Loop per il salvataggio periodico dei dati
def auto_save():
    while True:
        time.sleep(600)  # Salva ogni 10 minuti
        save_data()

# 🚀 Avvio processi paralleli
threading.Thread(target=auto_save, daemon=True).start()
print("🚀 Bot Glitchers XP attivo...")
bot.remove_webhook()
bot.polling(none_stop=True)
