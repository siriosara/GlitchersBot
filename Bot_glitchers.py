import os
import time
import threading
import requests
import telebot
import psycopg2
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

# 🔹 Token del bot e ID del canale
TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
OWNER_ID = int(os.getenv("OWNER_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
CHANNEL_LINK = os.getenv("CHANNEL_LINK")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

if not TOKEN:
    raise ValueError("❌ TOKEN non trovato! Controlla la configurazione.")
if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL non configurato!")

# 🔹 Connessione al database
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
    raise RuntimeError("❌ Impossibile connettersi al database dopo 5 tentativi.")

connect_db()

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

# 🔹 Funzione per registrare un utente
def register_user(user_id, username):
    cur.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users (user_id, username) VALUES (%s, %s)", (user_id, username))
        conn.commit()
        return True
    return False

# 🔹 Comando di benvenuto
@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username or f"utente_{user_id}"
    
    if register_user(user_id, username):
        bot.send_message(
            user_id,
            "🔥 Benvenuto nella community GLITCHERS!\n\n"
            "📌 **Regole XP:**\n"
            "- Reaction ai post: +5 XP\n"
            "- Visualizzazione media: +5 XP\n"
            "- Ogni ora il tuo XP viene aggiornato\n"
            "- Sblocca video con XP!\n\n"
            "🎯 **Premi XP:**\n"
            "✅ 250 XP → Prima parte\n"
            "✅ 500 XP → Seconda parte\n"
            "✅ 1000 XP → Video completo\n\n"
            "👉 Rispondi con **SI** per partecipare!"
        )
    else:
        bot.send_message(user_id, "🔥 Sei già registrato!")

@bot.message_handler(func=lambda message: message.text.lower() == "si")
def confirm_registration(message):
    bot.send_message(message.chat.id, "✅ Sei registrato! Guadagna XP per sbloccare i premi! 🏆")

    # 🔹 Comando /classifica - Mostra i migliori utenti XP
@bot.message_handler(commands=["classifica"])
def leaderboard(message):
    cur.execute("SELECT username, xp FROM users ORDER BY xp DESC LIMIT 10")
    top_users = cur.fetchall()

    if not top_users:
        response = "🏆 <b>Top 10 Utenti XP</b>:\n Nessun utente in classifica."
    else:
        response = "🏆 <b>Top 10 Utenti XP</b>:\n" + "\n".join([
            f"{i+1}. @{user[0]}: {user[1]} XP" for i, user in enumerate(top_users)
        ])

    bot.send_message(message.chat.id, response, parse_mode="HTML")

# 🔹 Funzione per aggiungere XP
def add_xp(user_id, amount):
    cur.execute("UPDATE users SET xp = xp + %s WHERE user_id = %s", (amount, user_id))
    conn.commit()

# 🔹 Comando per verificare il proprio XP
@bot.message_handler(commands=["xp"])
def check_xp(message):
    user_id = message.from_user.id
    cur.execute("SELECT xp FROM users WHERE user_id = %s", (user_id,))
    xp = cur.fetchone()

    if xp:
        bot.send_message(message.chat.id, f"🔹 Il tuo XP attuale: {xp[0]}")
    else:
        bot.send_message(message.chat.id, "❌ Non sei registrato nel sistema XP.")

# 🔹 Comando amministrativo: Reset XP di un utente
@bot.message_handler(commands=["reset_xp"])
def reset_xp(message):
    if message.from_user.id == OWNER_ID:
        args = message.text.split()
        if len(args) < 2:
            bot.send_message(message.chat.id, "⚠️ Usa: /reset_xp @username")
            return

        username = args[1].strip("@")
        cur.execute("UPDATE users SET xp = 0 WHERE username = %s", (username,))
        conn.commit()
        bot.send_message(message.chat.id, f"✅ XP di @{username} resettato.")

# 🔹 Comando per inviare un messaggio a tutti gli utenti
@bot.message_handler(commands=["broadcast"])
def broadcast_message(message):
    if message.from_user.id == OWNER_ID:
        text = message.text.replace("/broadcast", "").strip()
        cur.execute("SELECT user_id FROM users")
        users = cur.fetchall()

        for user in users:
            try:
                bot.send_message(user[0], text)
            except:
                continue

        bot.send_message(message.chat.id, "✅ Messaggio inviato a tutti gli utenti registrati!")

# 🔹 Comando /ban
@bot.message_handler(commands=["ban"])
def ban_user(message):
    if message.from_user.id != OWNER_ID:
        return

    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "⚠️ Usa: /ban @username")
        return

    username = args[1].strip("@")
    cur.execute("DELETE FROM users WHERE username = %s", (username,))
    conn.commit()
    bot.send_message(message.chat.id, f"🚫 Utente @{username} bannato!")

# 🔹 Comando /totali - utenti registrati vs attivi nel canale
@bot.message_handler(commands=["totali"])
def total_users(message):
    if message.from_user.id != OWNER_ID:
        return

    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]

    active_users = sum(
        1 for user in cur.execute("SELECT user_id FROM users").fetchall()
        if bot.get_chat_member(CHANNEL_ID, user[0]).status in ["member", "administrator", "creator"]
    )

    bot.send_message(message.chat.id, f"📊 Utenti registrati: {total_users}\n🔹 Ancora nel canale: {active_users}")

# 🔹 Comando /attivi_oggi - utenti attivi nelle ultime 24 ore
@bot.message_handler(commands=["attivi_oggi"])
def active_today(message):
    if message.from_user.id != OWNER_ID:
        return

    cur.execute("SELECT COUNT(*) FROM users WHERE last_active > NOW() - INTERVAL '1 day'")
    active_users = cur.fetchone()[0]
    bot.send_message(message.chat.id, f"📊 Utenti attivi oggi: {active_users}")

# 🔹 Comando /premi_riscossi - utenti che hanno riscattato video
@bot.message_handler(commands=["premi_riscossi"])
def claimed_rewards(message):
    if message.from_user.id != OWNER_ID:
        return

    cur.execute("SELECT username, video_sbloccato FROM users WHERE video_sbloccato > 0 ORDER BY video_sbloccato DESC")
    users = cur.fetchall()

    if not users:
        bot.send_message(message.chat.id, "🎥 Nessun utente ha ancora riscattato un premio.")
    else:
        response = "🎥 <b>Premi riscossi:</b>\n" + "\n".join(
            f"🔹 @{user[0]} → {user[1]} video sbloccati" for user in users
        )
        bot.send_message(message.chat.id, response, parse_mode="HTML")
        

# 🔹 Avvio Bot con Polling
if __name__ == "__main__":
    print("🚀 Bot Glitchers XP attivo con polling...")
    bot.remove_webhook()
    bot.infinity_polling()
    
