import os
import requests
import telebot
import mysql.connector
from mysql.connector import pooling
from datetime import datetime, timedelta
from flask import Flask, request
from waitress import serve

# Configurazione
TOKEN = os.getenv("BOT_TOKEN")
MYSQL_HOST = os.getenv("MYSQL_HOST", "metro.proxy.rlwy.net")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "iYWRnmakNkEktIMGjjoOOdXFPPXuXEkY")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "railway")
OWNER_ID = int(os.getenv("OWNER_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
CHANNEL_LINK = os.getenv("CHANNEL_LINK")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8080))

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# Connessione al Database
db_pool = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=10,
    host=MYSQL_HOST,
    port=int(os.getenv("MYSQL_PORT", 21928)),
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=MYSQL_DATABASE
)

def get_db():
    conn = db_pool.get_connection()
    return conn, conn.cursor()

def release_db(conn, cur):
    if cur: cur.close()
    if conn: conn.close()

# Comando /start
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, f"Benvenuto! Usa /sega per guadagnare XP.")

# Comando /sega
@bot.message_handler(commands=["sega"])
def claim_xp(message):
    user_id = message.from_user.id
    conn, cur = get_db()
    cur.execute("SELECT last_claim, streak, xp FROM users WHERE user_id = %s", (user_id,))
    user = cur.fetchone()
    now = datetime.now()
    if user:
        last_claim, streak, xp = user
        if last_claim and (now - last_claim).total_seconds() < 86400:
            remaining = timedelta(seconds=86400 - (now - last_claim).total_seconds())
            bot.send_message(user_id, f"⏳ Aspetta ancora {remaining} prima di riscattare di nuovo!")
            release_db(conn, cur)
            return
        streak = streak + 1 if (now - last_claim).total_seconds() < 172800 else 1
        new_xp = xp + 10
        cur.execute("UPDATE users SET xp = %s, last_claim = %s, streak = %s WHERE user_id = %s", (new_xp, now, streak, user_id))
    else:
        cur.execute("INSERT INTO users (user_id, xp, last_claim, streak) VALUES (%s, 10, %s, 1)", (user_id, now))
    conn.commit()
    release_db(conn, cur)
    bot.send_message(user_id, "✅ Hai guadagnato 10 XP!")

# Comando /status
@bot.message_handler(commands=["status"])
def check_status(message):
    user_id = message.from_user.id
    conn, cur = get_db()
    cur.execute("SELECT xp, last_claim, streak FROM users WHERE user_id = %s", (user_id,))
    user = cur.fetchone()
    release_db(conn, cur)
    if user:
        xp, last_claim, streak = user
        bot.send_message(user_id, f"📊 XP: {xp}\n🔥 Serie giornaliera: {streak}/7")
    else:
        bot.send_message(user_id, "❌ Non sei ancora registrato nel sistema XP! Usa /start per iniziare.")

# Comando /ban
@bot.message_handler(commands=["ban"])
def ban_user(message):
    if message.from_user.id != OWNER_ID:
        return
    try:
        user_id = int(message.text.split()[1])
        conn, cur = get_db()
        cur.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        conn.commit()
        release_db(conn, cur)
        bot.send_message(message.chat.id, f"❌ Utente {user_id} bannato!")
    except:
        bot.send_message(message.chat.id, "⚠️ Uso corretto: /ban <user_id>")

# Comando /dm
@bot.message_handler(commands=["dm"])
def send_dm(message):
    if message.from_user.id != OWNER_ID:
        return
    try:
        parts = message.text.split(None, 2)
        user_id, text = int(parts[1]), parts[2]
        bot.send_message(user_id, text)
        bot.send_message(message.chat.id, "✅ Messaggio inviato!")
    except:
        bot.send_message(message.chat.id, "⚠️ Uso corretto: /dm <user_id> <messaggio>")

# Comando /classifica
@bot.message_handler(commands=["classifica"])
def leaderboard(message):
    conn, cur = get_db()
    cur.execute("SELECT user_id, xp FROM users ORDER BY xp DESC LIMIT 10")
    leaderboard = cur.fetchall()
    release_db(conn, cur)
    text = "🏆 Classifica XP:\n" + "\n".join([f"{i+1}. {uid} - {xp} XP" for i, (uid, xp) in enumerate(leaderboard)])
    bot.send_message(message.chat.id, text)

# Comando /totali
@bot.message_handler(commands=["totali"])
def total_xp(message):
    if message.from_user.id != OWNER_ID:
        return
    conn, cur = get_db()
    cur.execute("SELECT SUM(xp) FROM users")
    total = cur.fetchone()[0]
    release_db(conn, cur)
    bot.send_message(message.chat.id, f"📊 XP Totale: {total}")

# Flask API per il Webhook
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "✅ Flask è attivo!", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=PORT)
  
