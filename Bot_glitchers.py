import os
import time
import threading
import requests
import telebot
import psycopg2
from psycopg2 import pool
from datetime import datetime, timedelta
from flask import Flask, request

# 🔹 Configurazione
TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
OWNER_ID = int(os.getenv("OWNER_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
CHANNEL_LINK = os.getenv("CHANNEL_LINK")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8080))

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

db_pool = psycopg2.pool.SimpleConnectionPool(1, 10, dsn=DATABASE_URL, sslmode='allow')

def get_db():
    conn = db_pool.getconn()
    return conn, conn.cursor()

def release_db(conn, cur):
    if cur: cur.close()
    if conn: db_pool.putconn(conn)

# 🔹 Verifica iscrizione al canale
def is_user_in_channel(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        return status in ["member", "administrator", "creator"]
    except:
        return False

# 🔹 Comando /sega
@bot.message_handler(commands=["sega"])
def claim_xp(message):
    user_id = message.from_user.id
    if not is_user_in_channel(user_id):
        bot.send_message(user_id, f"⚠️ Devi essere iscritto al canale per usare il bot! [Clicca qui per unirti]({CHANNEL_LINK})")
        return

    conn, cur = get_db()
    cur.execute("SELECT last_claim, streak, xp FROM users WHERE user_id = %s", (user_id,))
    user = cur.fetchone()
    
    now = datetime.now()
    if user:
        last_claim, streak, xp = user
        if last_claim and (now - last_claim).total_seconds() < 86400:
            remaining = timedelta(seconds=86400 - (now - last_claim).total_seconds())
            bot.send_message(user_id, f"⏳ Devi aspettare ancora {remaining} prima di riscattare di nuovo!")
            release_db(conn, cur)
            return
        
        streak = streak + 1 if (now - last_claim).total_seconds() < 172800 else 1
        bonus = 30 if streak == 7 else 0
        new_xp = xp + 10 + bonus
        cur.execute("UPDATE users SET xp = %s, last_claim = %s, streak = %s WHERE user_id = %s", (new_xp, now, streak, user_id))
    else:
        cur.execute("INSERT INTO users (user_id, xp, last_claim, streak) VALUES (%s, 10, %s, 1)", (user_id, now))
    
    conn.commit()
    release_db(conn, cur)
    bot.send_message(user_id, f"✅ Hai guadagnato 10 XP! {'🎉 Bonus 30 XP per 7 giorni consecutivi!' if bonus else ''}")

# 🔹 Comando /status
@bot.message_handler(commands=["status"])
def check_status(message):
    user_id = message.from_user.id
    conn, cur = get_db()
    cur.execute("SELECT xp, last_claim, streak FROM users WHERE user_id = %s", (user_id,))
    user = cur.fetchone()
    release_db(conn, cur)
    
    if user:
        xp, last_claim, streak = user
        remaining = "Disponibile ora!" if (datetime.now() - last_claim).total_seconds() > 86400 else f"Aspetta ancora {timedelta(seconds=86400 - (datetime.now() - last_claim).total_seconds())}"
        bot.send_message(user_id, f"📊 XP: {xp}\n🔥 Prossima /sega: {remaining}\n🏆 Serie giornaliera: {streak}/7")
    else:
        bot.send_message(user_id, "❌ Non sei ancora registrato nel sistema XP! Usa /start per iniziare.")

# 🔹 Altri comandi
@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.send_message(message.chat.id, "🔥 Benvenuto nel sistema XP! Usa /regole per scoprire di più.")

@bot.message_handler(commands=["regole"])
def send_rules(message):
    bot.send_message(message.chat.id, "📜 Regole:\n- Usa /sega una volta al giorno per 10 XP.\n- Dopo 7 giorni consecutivi, ottieni un bonus di 30 XP!\n- Controlla il tuo status con /status.\n- Puoi abbandonare il sistema con /abbandona.")

@bot.message_handler(commands=["abbandona"])
def leave_system(message):
    user_id = message.from_user.id
    conn, cur = get_db()
    cur.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
    conn.commit()
    release_db(conn, cur)
    bot.send_message(user_id, "👋 Sei stato rimosso dal sistema XP. Puoi sempre tornare con /start!")

# 🔹 Admin Commands
@bot.message_handler(commands=["ban"])
def ban_user(message):
    if message.from_user.id != OWNER_ID:
        return
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "❌ Usa il comando così: /ban @username")
        return
    username = args[1].replace("@", "")
    conn, cur = get_db()
    cur.execute("DELETE FROM users WHERE username = %s", (username,))
    conn.commit()
    release_db(conn, cur)
    bot.reply_to(message, f"✅ L'utente @{username} è stato bannato dal bot.")

@bot.message_handler(commands=["totali"])
def total_users(message):
    if message.from_user.id != OWNER_ID:
        return
    conn, cur = get_db()
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]
    release_db(conn, cur)
    bot.send_message(message.chat.id, f"📊 Totale utenti: {total_users}")

@bot.message_handler(commands=["classifica"])
def leaderboard(message):
    conn, cur = get_db()
    cur.execute("SELECT username, xp FROM users ORDER BY xp DESC LIMIT 10")
    top_users = cur.fetchall()
    response = "🏆 <b>Top 10 Utenti XP</b>:\n" + "\n".join([f"{i+1}. @{user[0]}: {user[1]} XP" for i, user in enumerate(top_users)])
    bot.send_message(message.chat.id, response, parse_mode="HTML")
    release_db(conn, cur)

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "✅ Flask è attivo!", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    print(f"📩 Ricevuto update: {json_str}")  # Debug
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200
    
app.run(host="127.0.0.1", port=8080, use_reloader=False)
