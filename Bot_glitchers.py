import os
import requests
import telebot
import mysql.connector
from mysql.connector import pooling
from datetime import datetime, timedelta
from flask import Flask, request
from waitress import serve

# 🔹 Configurazione
TOKEN = os.getenv("BOT_TOKEN")
MYSQL_HOST = os.getenv("MYSQLHOST")
MYSQL_USER = os.getenv("MYSQLUSER")
MYSQL_PASSWORD = os.getenv("MYSQLPASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
OWNER_ID = int(os.getenv("OWNER_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
CHANNEL_LINK = os.getenv("CHANNEL_LINK")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8080))

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# 🔹 Connessione al Database
db_pool = pooling.MySQLConnectionPool(
        pool_name="mypool",
            pool_size=10,
                host=os.getenv("MYSQL_HOST", "metro.proxy.rlwy.net"),  # Host corretto
                    port=int(os.getenv("MYSQL_PORT", 21928)),  # Porta corretta
                        user=os.getenv("MYSQL_USER", "root"),
                            password=os.getenv("MYSQL_PASSWORD", "iYWRnmakNkEktIMGjjoOOdXFPPXuXEkY"),
                                database=os.getenv("MYSQL_DATABASE", "railway")
)

def get_db():
    conn = db_pool.get_connection()
    return conn, conn.cursor()

def release_db(conn, cur):
    if cur: cur.close()
    if conn: conn.close()

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

# 🔹 Flask API per il Webhook
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
    serve(app, host="0.0.0.0", port=8080)
      
