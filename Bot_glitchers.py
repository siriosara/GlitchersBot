import os
import time
import threading
import requests  # ✅ AGGIUNTO: Necessario per gestire il webhook di Telegram

import telebot
import psycopg2

from flask import Flask, request
from datetime import datetime

def check_env_variables():
    required_vars = ["TOKEN", "DATABASE_URL", "WEBHOOK_URL", "OWNER_ID", "CHANNEL_ID"]
    for var in required_vars:
        value = os.getenv(var, "").strip()
        print(f"🔍 {var}: {'✅ OK' if value else '❌ NON TROVATA'}")

check_env_variables()  # Debug delle variabili d'ambiente

# Controllo dettagliato delle variabili
def check_env_variables():
    required_vars = ["TOKEN", "DATABASE_URL", "WEBHOOK_URL", "OWNER_ID", "CHANNEL_ID"]
    for var in required_vars:
        value = os.getenv(var, "NON TROVATA").strip()
        print(f"🔍 {var}: {repr(value)}")  # Stampa il valore esatto

check_env_variables()

# 🔹 Token del bot e ID del canale
TOKEN = os.getenv("TOKEN", "").strip()
DATABASE_URL = os.getenv("DATABASE_URL")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
OWNER_ID = int(os.getenv("OWNER_ID", 5543012634))  # Default al tuo ID Telegram
CHANNEL_ID = int(os.getenv("CHANNEL_ID", -1001716099490))  # Default al tuo canale
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/+mcc19N6Idbs1OWJk")
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

TOKEN = os.getenv("TOKEN", "").strip()  # Rimuove eventuali spazi
if not TOKEN:
    raise ValueError("❌ TOKEN non trovato! Verifica le variabili di ambiente.")

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL non trovato! Verifica le variabili di ambiente.")

if not WEBHOOK_URL:
    raise ValueError("❌ ERRORE: La variabile WEBHOOK_URL non è stata trovata!")

# 🔹 Connessione al database con retry automatico
def connect_db():
    global conn, cur
    for _ in range(5):
        try:
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            cur = conn.cursor()
            print("✅ Connessione a PostgreSQL riuscita!")
            return
        except Exception as e:
            print(f"❌ Errore nella connessione a PostgreSQL: {e}")
            time.sleep(5)

connect_db()

# 🔹 Mantiene viva la connessione
def keep_db_alive():
    while True:
        try:
            cur.execute("SELECT 1")
            conn.commit()
        except Exception:
            print("🔄 Tentativo di riconnessione...")
            connect_db()
        time.sleep(600)

threading.Thread(target=keep_db_alive, daemon=True).start()


# 🔹 Creazione delle tabelle se non esistono
cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT PRIMARY KEY,
        username TEXT,
        xp INTEGER DEFAULT 0,
        video_sbloccato INTEGER DEFAULT 0
    )
""")
conn.commit()

# 🔹 File ID dei premi
video_premi = {
    250: "BAACAgQAAxkBAANRZ65g5avV2vGeKWB2sB7rYpL-z3QAAhYVAAK4hXFRQOWBHIJF29E2BA",
    500: "BAACAgQAAxkBAANTZ65hO01VjYtbcRdWzu4q3ZXhbUMAAiEVAAK4hXFRhpJ3Fxu4DaU2BA",
    1000: "BAACAgQAAxkBAAM4Z65g2S0WiMdVd7Ian8V0OZXfFGoAAiMVAAK4hXFRONGfYWcnLqk2BA"
}

# 🔹 Funzioni database
def add_user(user_id, username):
    cur.execute("INSERT INTO users (user_id, username) VALUES (%s, %s) ON CONFLICT (user_id) DO NOTHING", (user_id, username))
    conn.commit()

def get_user_status(user_id):
    cur.execute("SELECT xp, video_sbloccato FROM users WHERE user_id = %s", (user_id,))
    return cur.fetchone()

def update_xp(user_id, xp):
    cur.execute("UPDATE users SET xp = xp + %s WHERE user_id = %s", (xp, user_id))
    conn.commit()

def reset_xp(user_id):
    cur.execute("UPDATE users SET xp = 0, video_sbloccato = 0 WHERE user_id = %s", (user_id,))
    conn.commit()

# 🔹 Messaggio di benvenuto
def send_welcome_message(user_id):
    bot.send_message(user_id, 
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
        "👉 Il video diviso in tre parti è inedito e non presente in nessuna delle nostre piattaforme, "
        "realizzato appositamente per questa esperienza.\n"
        "📤 Ci saranno dei nuovi premi nella prossima stagione con nuovi video inediti.\n"
        "👍 Collezionali tutti!\n"
        "🚫 Se tutto ciò non è di tuo interesse, blocca semplicemente il bot e ognuno per la sua strada.\n"
        "❤️ Rimani iscritto nel canale per poter partecipare, altrimenti gli XP non saranno conteggiati.\n"
        "💌 Periodicamente manderò dei DM zozzi come messaggio qui sul bot per coccolare i miei fan."
                    )
    
# 🔹 Messaggio di benvenuto automatico quando un utente entra nel canale
@bot.chat_member_handler()
def welcome_new_member(update):
    if update.new_chat_member and not update.new_chat_member.user.is_bot:
        user_id = update.new_chat_member.user.id
        send_welcome_message(user_id)

# 🔹 Comando /start
@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username if message.from_user.username else None

    add_user(user_id, username)

    bot.send_message(user_id, "✅ Sei registrato! Inizia a guadagnare XP per sbloccare i premi! 🎉")
    send_welcome_message(user_id)

# 🔹 Comando /status
@bot.message_handler(commands=["status"])
def check_status(message):
    user_id = message.from_user.id
    user_status = get_user_status(user_id)

    if user_status:
        xp, video_sbloccati = user_status
        bot.send_message(user_id, f"📊 Il tuo status:\n🔹 XP: {xp}\n🔹 Video sbloccati: {video_sbloccati}")
    else:
        bot.send_message(user_id, "❌ Non sei registrato. Usa /start per iscriverti.")

# 🔹 Comando /classifica
@bot.message_handler(commands=["classifica"])
def leaderboard(message):
    if message.from_user.id != OWNER_ID:
        return

    cur.execute("SELECT username, xp FROM users ORDER BY xp DESC LIMIT 10")
    top_users = cur.fetchall()

    response = "🏆 <b>Top 10 Utenti XP</b>:\n" + "\n".join([f"{i+1}. @{user[0]}: {user[1]} XP" for i, user in enumerate(top_users)]) if top_users else "Nessun utente in classifica."
    bot.send_message(message.chat.id, response, parse_mode="HTML")

@bot.message_handler(commands=["reset_utente"])
def reset_user(message):
    if message.from_user.id != OWNER_ID:
        return bot.send_message(message.chat.id, "⛔ Non hai i permessi per usare questo comando.")

    try:
        # 🔹 Estrai username o ID dal comando
        username_or_id = message.text.split()[1].replace("@", "").strip()

        # 🔹 Cerca l'utente nel database
        cur.execute("SELECT user_id FROM users WHERE username = %s OR CAST(user_id AS TEXT) = %s", (username_or_id, username_or_id))
        result = cur.fetchone()

        if result:
            user_id = result[0]
            cur.execute("UPDATE users SET xp = 0, video_sbloccato = 0 WHERE user_id = %s", (user_id,))
            conn.commit()
            bot.send_message(message.chat.id, f"✅ XP e premi di @{username_or_id} azzerati con successo!")
        else:
            bot.send_message(message.chat.id, f"❌ Utente @{username_or_id} non trovato nel database.")

    except IndexError:
        bot.send_message(message.chat.id, "⚠️ Usa il comando così: /reset_utente @username o /reset_utente user_id")
        
# 🔹 Comando /totale
@bot.message_handler(commands=["totale"])
def total_users(message):
    if message.from_user.id != OWNER_ID:
        return bot.send_message(message.chat.id, "⛔ Non hai i permessi per usare questo comando.")

    cur.execute("SELECT COUNT(*) FROM users")
    total_registered = cur.fetchone()[0]

    bot.send_message(message.chat.id, f"👥 <b>Utenti registrati nel bot:</b> {total_registered}", parse_mode="HTML")

# 🔹 Comando /attivi_oggi
@bot.message_handler(commands=["attivi_oggi"])
def active_today(message):
    if message.from_user.id != OWNER_ID:
        return

    cur.execute("SELECT COUNT(*) FROM users WHERE xp > 0")
    active_users = cur.fetchone()[0]

    bot.send_message(message.chat.id, f"📊 Utenti attivi oggi: {active_users}")

@bot.message_handler(commands=["dm"])
def send_dm(message):
    if message.from_user.id != OWNER_ID:
        return bot.send_message(message.chat.id, "⛔ Non hai i permessi per usare questo comando.")

    cur.execute("SELECT user_id FROM users")
    user_ids = cur.fetchall()

    if message.reply_to_message:
        for user_id in user_ids:
            try:
                bot.copy_message(user_id[0], message.chat.id, message.reply_to_message.message_id)
            except:
                pass
        bot.send_message(message.chat.id, "✅ Messaggio inoltrato a tutti gli utenti registrati.")
    else:
        text = message.text.replace("/dm", "").strip()
        if text:
            for user_id in user_ids:
                try:
                    bot.send_message(user_id[0], text)
                except:
                    pass
            bot.send_message(message.chat.id, "✅ Messaggio inviato a tutti gli utenti registrati.")
        else:
            bot.send_message(message.chat.id, "⚠️ Usa il comando così: /dm [messaggio] o rispondi a un messaggio.")
            
# 🔹 Comando /ban
@bot.message_handler(commands=["ban"])
def ban_user(message):
    if message.from_user.id != OWNER_ID:
        return bot.send_message(message.chat.id, "⛔ Non hai i permessi per usare questo comando.")

    try:
        username_or_id = message.text.split()[1].replace("@", "").strip()
        cur.execute("DELETE FROM users WHERE username = %s OR CAST(user_id AS TEXT) = %s RETURNING user_id", (username_or_id, username_or_id))
        result = cur.fetchone()

        if result:
            user_id = result[0]
            bot.kick_chat_member(CHANNEL_ID, user_id)
            conn.commit()  # 🔹 Assicura che il database sia aggiornato
            bot.send_message(message.chat.id, f"🚨 Utente @{username_or_id} bannato con successo!")
        else:
            bot.send_message(message.chat.id, f"❌ Utente @{username_or_id} non trovato.")
    except IndexError:
        bot.send_message(message.chat.id, "⚠️ Usa il comando così: /ban @username o /ban user_id")

# 🔹 Configura il Webhook solo se necessario
def setup_webhook():
    print("🔄 Controllo dello stato del webhook...")
    response = requests.get(f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo").json()
    current_url = response.get("result", {}).get("url", "")

    if current_url == WEBHOOK_URL:
        print(f"ℹ️ Webhook già attivo su {WEBHOOK_URL}")
        return  

    print("🔄 Webhook non corrispondente, lo aggiorno...")
    bot.remove_webhook()
    time.sleep(1)
    if bot.set_webhook(url=WEBHOOK_URL):
        print(f"✅ Webhook aggiornato su {WEBHOOK_URL}")
    else:
        print("❌ Errore nell'impostazione del webhook!")

# 🔹 Inizializza Flask per il Webhook
app = Flask(__name__)

@app.route("/")
def index():
    return "Bot attivo!", 200  

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
        bot.process_new_updates([update])
        return "OK", 200
    except Exception as e:
        print(f"❌ Errore nel webhook: {e}")
        return "Errore interno", 500

setup_webhook()
