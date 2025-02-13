import telebot
import time
import threading
from datetime import datetime, timedelta

# 🔹 Inserisci il tuo Token API qui
TOKEN = "7665636304:AAEsWwMX7QG4tVoC3IufpSjL-ZMjfspIphY"
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# 🔹 ID del canale Glitchers
CHANNEL_ID = -1001716099490  
CHANNEL_LINK = "https://t.me/+mcc19N6Idbs1OWJk"

# 🔹 Database XP (simulato con un dizionario per ora)
user_xp = {}  # {user_id: {"xp": 0, "last_active": data, "video_sbloccato": 0}}
user_registered = set()  # Utenti che hanno accettato di partecipare

# 🔹 Soglie XP e Video Premi
video_premi = {
    250: "video_parte1.mp4",
    500: "video_parte2.mp4",
    1000: "video_parte3.mp4"
}

# 📌 1. Benvenuto e Registrazione
@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_id = message.from_user.id
    if user_id in user_registered:
        bot.send_message(user_id, "🔥 Sei già registrato nel sistema XP!")
    else:
        bot.send_message(
            user_id,
            "🔥 Vuoi entrare a far parte della community GLITCHERS? Avrai un meritato premio...\n\n"
            "📌 Ecco come funziona:\n"
            "- Guadagna XP con le reaction ai post (+5 XP)\n"
            "- Guarda i media nei post (+5 XP)\n"
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
        user_xp[user_id] = {"xp": 0, "last_active": datetime.now(), "video_sbloccato": 0}
        bot.send_message(
            user_id,
            "✅ Sei dentro! Inizia a interagire con i post per guadagnare XP e sbloccare i tuoi premi!\n\n"
            "🔍 Usa il comando **/status** per controllare i tuoi XP!"
        )

# 📌 2. Comando /status per verificare gli XP
@bot.message_handler(commands=["status"])
def check_xp(message):
    user_id = message.from_user.id
    if user_id in user_xp:
        xp = user_xp[user_id]["xp"]
        bot.send_message(user_id, f"🔥 @user, attualmente hai {xp}/1000 XP. Continua a interagire per sbloccare il prossimo premio!")
    else:
        bot.send_message(user_id, "⚠️ Non sei registrato nel sistema XP. Rispondi 'SI' per entrare!")

# 📌 3. Tracking XP ogni ora
def update_xp():
    while True:
        time.sleep(3600)  # Attendi 1 ora
        for user_id in user_xp:
            user_xp[user_id]["xp"] += 10  # Simuliamo reaction + visualizzazione (+5 +5)
            check_rewards(user_id)
        print("✅ XP aggiornato per tutti gli utenti!")

# 📌 4. Controllo e invio dei premi sbloccati
def check_rewards(user_id):
    xp = user_xp[user_id]["xp"]
    last_video = user_xp[user_id]["video_sbloccato"]

    for threshold, video_file in video_premi.items():
        if xp >= threshold and last_video < threshold:
            user_xp[user_id]["video_sbloccato"] = threshold
            bot.send_message(user_id, f"🎉 Hai sbloccato un nuovo premio! Guarda il video:")
            bot.send_document(user_id, open(video_file, "rb"))

# 📌 5. Messaggio motivazionale ogni 7 giorni
def send_motivation():
    while True:
        time.sleep(604800)  # Attendi 7 giorni
        for user_id in user_xp:
            last_active = user_xp[user_id]["last_active"]
            if datetime.now() - last_active > timedelta(days=7):
                bot.send_message(user_id, "🔥 Hey @user, ti sei fermato? Continua a guadagnare XP per sbloccare i tuoi premi!")

# 📌 6. Restrizione per chi lascia il canale
@bot.message_handler(func=lambda message: True)
def check_membership(message):
    user_id = message.from_user.id
    try:
        chat_member = bot.get_chat_member(CHANNEL_ID, user_id)
        if chat_member.status not in ["member", "administrator", "creator"]:
            bot.send_message(
                user_id,
                f"⚠️ Per continuare a guadagnare XP e riscattare i premi, devi essere nel canale GLITCHERS.\n\n"
                f"Clicca qui per rientrare: {CHANNEL_LINK}\n"
                "Dopo essere stato approvato, potrai continuare da dove avevi lasciato!"
            )
    except:
        bot.send_message(
            user_id,
            f"⚠️ Per continuare nel sistema XP, unisciti al canale: {CHANNEL_LINK}"
        )

# 🚀 Avvio processi paralleli
threading.Thread(target=update_xp).start()
threading.Thread(target=send_motivation).start()

# Avvia il bot
print("🚀 Bot Glitchers XP attivo...")
bot.polling()
