import os
import time
import threading
import requests
import telebot
import psycopg2
from psycopg2 import pool
from flask import Flask
from datetime import datetime

app = Flask(__name__)

# 🔹 Token del bot e ID del canale
TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
OWNER_ID = int(os.getenv("OWNER_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
CHANNEL_LINK = os.getenv("CHANNEL_LINK")  # Manca nel tuo codice precedente

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

bot.remove_webhook()
time.sleep(1)  # Aspetta un secondo per evitare problemi di tempistica

# 🔹 Database Connection Pool
try:
    db_pool = psycopg2.pool.SimpleConnectionPool(1, 10, DATABASE_URL, sslmode='require')
    print("✅ Connessione al Database stabilita con il Pool!")
except Exception as e:
    raise RuntimeError(f"❌ Errore nella connessione al database: {e}")

# 🔹 Funzioni Database
def get_db():
    conn = db_pool.getconn()
    return conn, conn.cursor()

def release_db(conn, cur):
    cur.close()
    db_pool.putconn(conn)

def update_xp(user_id, xp_gained):
    conn, cur = get_db()
    cur.execute("UPDATE users SET xp = xp + %s WHERE user_id = %s", (xp_gained, user_id))
    conn.commit()
    release_db(conn, cur)

    # Controlla subito se l'utente ha sbloccato premi
    check_rewards_for_user(user_id)
    
# Connessione al database
def connect_db():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    return conn, cur
    
# 🔹 File ID dei Premi XP
video_premi = {
    250: "BAACAgQAAxkBAANRZ65g5avV2vGeKWB2sB7rYpL-z3QAAhYVAAK4hXFRQOWBHIJF29E2BA",
    500: "BAACAgQAAxkBAANTZ65hO01VjYtbcRdWzu4q3ZXhbUMAAiEVAAK4hXFRhpJ3Fxu4DaU2BA",
    1000: "BAACAgQAAxkBAAM4Z65g2S0WiMdVd7Ian8V0OZXfFGoAAiMVAAK4hXFRONGfYWcnLqk2BA"
}

# 🔹 Comando di benvenuto
@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_id = message.from_user.id
    conn, cur = get_db()

    cur.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
    user_exists = cur.fetchone()

    if user_exists:
        bot.send_message(user_id, "🔥 Sei già registrato nel sistema XP!")
    else:
        bot.send_message(
            user_id,
            f"🔥 Vuoi entrare a far parte della community GLITCHERS?\n\n"
            f"📌 **Regole:**\n"
            f"- Reaction ai post: +5 XP (una volta sola per post)\n"
            f"- Visualizzazione media: +5 XP (una volta per post)\n"
            f"- Ogni ora il tuo XP viene aggiornato automaticamente\n"
            f"- Quando raggiungi una soglia, ricevi una parte del video esclusivo!\n\n"
            f"🎯 **Soglie XP:**\n"
            f"✅ 250 XP → Prima parte del video\n"
            f"✅ 500 XP → Seconda parte del video\n"
            f"✅ 1000 XP → Video completo\n\n"
            f"👉 Rispondi con **SI** per partecipare!\n\n🔗 [Canale Telegram]({CHANNEL_LINK})"
        )

@bot.message_handler(func=lambda message: message.text.lower() == "si")
def register_user(message):
    user_id = message.from_user.id
    conn, cur = get_db()

    cur.execute("INSERT INTO users (user_id, username, xp, video_sbloccato) VALUES (%s, %s, 0, 0) ON CONFLICT DO NOTHING",
                (user_id, message.from_user.username))
    conn.commit()
    bot.send_message(user_id, "✅ Sei registrato! Inizia a guadagnare XP per sbloccare i premi! 🏆")

    release_db(conn, cur)

@bot.message_handler(func=lambda message: message.text in ["❤️", "🔥", "👍", "💯"])
def reaction_xp(message):
    update_xp(message.from_user.id, 5)
    bot.reply_to(message, "✅ Hai guadagnato 5 XP!")

def check_rewards_for_user(user_id):
    conn, cur = get_db()
    cur.execute("SELECT xp, video_sbloccato FROM users WHERE user_id = %s", (user_id,))
    result = cur.fetchone()

    if result:
        xp, video_sbloccato = result
        for soglia, file_id in video_premi.items():
            if xp >= soglia and video_sbloccato < soglia:
                bot.send_video(user_id, file_id, caption=f"🎉 Hai sbloccato il premio da {soglia} XP!")
                cur.execute("UPDATE users SET video_sbloccato = %s WHERE user_id = %s", (soglia, user_id))
                conn.commit()

    release_db(conn, cur)

@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ Non hai i permessi per eseguire questo comando.")
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
    
    bot.reply_to(message, f"✅ L'utente @{username} è stato rimosso dal database del bot.")


@bot.message_handler(commands=['dm'])
def send_dm(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ Non hai i permessi per eseguire questo comando.")
        return

    conn, cur = get_db()
    cur.execute("SELECT user_id FROM users")
    users = cur.fetchall()
    release_db(conn, cur)
    
    if not users:
        bot.reply_to(message, "⚠️ Nessun utente registrato nel bot.")
        return
    
    if not message.reply_to_message:
        bot.reply_to(message, "❌ Rispondi a un messaggio (testo o media) con /dm per inviarlo a tutti gli utenti.")
        return
    
    sent_count = 0
    failed_count = 0

    for user in users:
        try:
            user_id = user[0]
            if message.reply_to_message.text:
                bot.send_message(user_id, message.reply_to_message.text, parse_mode="HTML")
            elif message.reply_to_message.photo:
                bot.send_photo(user_id, message.reply_to_message.photo[-1].file_id, caption=message.reply_to_message.caption or "")
            elif message.reply_to_message.video:
                bot.send_video(user_id, message.reply_to_message.video.file_id, caption=message.reply_to_message.caption or "")
            elif message.reply_to_message.document:
                bot.send_document(user_id, message.reply_to_message.document.file_id, caption=message.reply_to_message.caption or "")
            elif message.reply_to_message.animation:
                bot.send_animation(user_id, message.reply_to_message.animation.file_id, caption=message.reply_to_message.caption or "")
            sent_count += 1
        except Exception:
            failed_count += 1

    bot.reply_to(message, f"📩 Messaggio inviato a {sent_count} utenti. ❌ Falliti: {failed_count}")
    
# 🔹 Comando /totali
@bot.message_handler(commands=["totali"])
def total_users(message):
    if message.from_user.id != OWNER_ID:
        return

    conn, cur = get_db()
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]

    cur.execute("SELECT user_id FROM users")
    all_users = cur.fetchall()
    
    active_users = sum(1 for user in all_users if bot.get_chat_member(CHANNEL_ID, user[0]).status in ["member", "administrator", "creator"])

    bot.send_message(message.chat.id, f"📊 Totale utenti: {total_users}\n🔹 Ancora nel canale: {active_users}")
    release_db(conn, cur)

# 🔹 Comando `/classifica`
@bot.message_handler(commands=["classifica"])
def leaderboard(message):
    conn, cur = get_db()
    cur.execute("SELECT username, xp FROM users ORDER BY xp DESC LIMIT 10")
    top_users = cur.fetchall()

    response = "🏆 <b>Top 10 Utenti XP</b>:\n" + "\n".join([
        f"{i+1}. @{user[0]}: {user[1]} XP" for i, user in enumerate(top_users)
    ]) if top_users else "🏆 Nessun utente in classifica."

    bot.send_message(message.chat.id, response, parse_mode="HTML")
    release_db(conn, cur)

# 🔹 Controllo XP e invio Premi
def check_rewards():
    while True:
        conn, cur = get_db()
        cur.execute("SELECT user_id, xp, video_sbloccato FROM users")
        users = cur.fetchall()

        for user_id, xp, video_sbloccato in users:
            for soglia, file_id in video_premi.items():
                if xp >= soglia and video_sbloccato < soglia:
                    bot.send_video(user_id, file_id, caption=f"🎉 Hai sbloccato il premio da {soglia} XP!")
                    cur.execute("UPDATE users SET video_sbloccato = %s WHERE user_id = %s", (soglia, user_id))
                    conn.commit()

        release_db(conn, cur)
        time.sleep(3600)  # Controllo ogni ora

threading.Thread(target=check_rewards, daemon=True).start()

def start_polling():
    while True:
        try:
            print("🚀 Avvio bot...")
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"⚠️ Errore nel polling: {e}")
            time.sleep(5)

if __name__ == "__main__":
    start_polling()
