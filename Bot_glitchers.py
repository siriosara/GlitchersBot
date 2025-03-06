import os
import time
import threading
import requests
import telebot
import psycopg2
from psycopg2 import pool
from datetime import datetime

# 🔹 Token del bot e ID del canale
TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
OWNER_ID = int(os.getenv("OWNER_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
CHANNEL_LINK = os.getenv("CHANNEL_LINK")  # Manca nel tuo codice precedente
URL = os.getenv("URL")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# 🔹 Database Connection Pool
try:
    db_pool = psycopg2.pool.SimpleConnectionPool(1, 10, dsn=DATABASE_URL, sslmode='allow')
    print("✅ Connessione al Database stabilita con il Pool!")
except Exception as e:
    raise RuntimeError(f"❌ Errore nella connessione al database: {e}")
    
# 🔹 Funzioni Database
def get_db():
    global db_pool
    try:
        conn = db_pool.getconn()
        if conn.closed:
            raise RuntimeError("Connessione chiusa, ricreazione necessaria.")
        return conn, conn.cursor()
    except Exception as e:
        print(f"❌ Errore nella connessione al database: {e}")
        db_pool.closeall()
        db_pool = psycopg2.pool.SimpleConnectionPool(1, 10, dsn=DATABASE_URL, sslmode='allow')
        return get_db()  # Riprova con il nuovo pool
    finally:
        if conn:
            db_pool.putconn(conn)  # Rilascia connessione sempre!
            
def release_db(conn, cur):
    """Rilascia la connessione e il cursore nel pool."""
    if cur:  
        cur.close()
    if conn:
        db_pool.putconn(conn)
        
def update_xp(user_id, xp_gained):
    conn, cur = get_db()
    try:
        cur.execute("UPDATE users SET xp = xp + %s WHERE user_id = %s RETURNING xp", (xp_gained, user_id))
        new_xp = cur.fetchone()
        conn.commit()
        if new_xp:
            print(f"✅ XP aggiornati per user_id={user_id}. Nuovo XP: {new_xp[0]}")
        else:
            print(f"⚠️ Nessun XP aggiornato per user_id={user_id}")
    except Exception as e:
        print(f"❌ Errore aggiornando XP: {e}")
    finally:
        release_db(conn, cur)

# 🔹 Definizione della funzione fetch_reactions()
def fetch_reactions():
    last_update_id = None
    
    while True:
        try:
            params = {"offset": last_update_id, "timeout": 30}
            response = requests.get(URL, params=params)

            if response.status_code != 200:
                print(f"❌ Errore nella richiesta API Telegram: {response.status_code}")
                continue  # Salta l'iterazione se c'è un errore
            
            data = response.json()
            
            if data.get("ok"):
                for update in data["result"]:
                    last_update_id = update["update_id"] + 1
                    
                    if "message" in update:
                        message = update["message"]
                        if "reaction" in message:
                            user_id = message["from"]["id"]
                            post_id = message["message_id"]
                            print(f"✅ Reaction registrata per user {user_id} su post {post_id}")
                            
                            bot.send_message(OWNER_ID, f"🔍 Reaction registrata: user_id={user_id}, post_id={post_id}")
                            
                            # Salviamo l'interazione nel database
                            add_xp_for_interaction(user_id, post_id, "reacted")

        except requests.exceptions.RequestException as e:
            print(f"❌ Errore di rete nel polling delle reaction: {e}")
        
        except Exception as e:
            print(f"❌ Errore generico nel polling delle reaction: {e}")

        time.sleep(5)
        
# 🔹 Avvia il thread SOLO DOPO la definizione della funzione
threading.Thread(target=fetch_reactions, daemon=True).start()

bot.remove_webhook()
time.sleep(5)
bot.set_webhook(url=WEBHOOK_URL)

# Imposta un delay tra le richieste per evitare il 429
bot = telebot.TeleBot(TOKEN, parse_mode="HTML", disable_notification=True, threaded=False)
bot.enable_save_next_step_handlers(delay=0.5)  # Aspetta 0.5s tra le richieste

# Controlla lo stato attuale del webhook
webhook_info = requests.get(f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo").json()
if webhook_info.get("result", {}).get("url") == WEBHOOK_URL:
    print("✅ Webhook già attivo, nessuna modifica necessaria.")
else:
    print("🔄 Reimposto il webhook...")
    bot.remove_webhook()
    time.sleep(5)
    bot.set_webhook(url=WEBHOOK_URL)
    
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

# 🔹 Nuove funzioni per tracciare interazioni
def user_has_interacted(user_id, post_id, interaction_type):
    """
    Controlla se l'utente ha già interagito con il post specificato.
    interaction_type può essere 'reacted' o 'viewed'.
    """
    conn, cur = get_db()
    cur.execute(f"SELECT {interaction_type} FROM interactions WHERE user_id = %s AND post_id = %s", 
                (user_id, post_id))
    result = cur.fetchone()
    release_db(conn, cur)
    
    return result and result[0]  # Se esiste e il valore è True, restituisce True

def mark_interaction(user_id, post_id, interaction_type):
    print(f"🔍 Registrando interazione: {interaction_type} per user_id={user_id} su post_id={post_id}")
    conn, cur = get_db()
    
    try:
        # Controlla se l'interazione esiste già
        cur.execute("SELECT * FROM interactions WHERE user_id = %s AND post_id = %s", (user_id, post_id))
        existing = cur.fetchone()
        print(f"🔍 Esiste già un'interazione? {existing}")  # Debug

        # Inserisce o aggiorna l'interazione
        query = f"""
            INSERT INTO interactions (user_id, post_id, {interaction_type}) 
            VALUES (%s, %s, TRUE)
            ON CONFLICT (user_id, post_id) DO UPDATE SET {interaction_type} = EXCLUDED.{interaction_type}
        """
        cur.execute(query, (user_id, post_id))
        conn.commit()
        
        print(f"✅ Interazione salvata per user_id={user_id}, post_id={post_id}, tipo={interaction_type}")
        
        # Debug Telegram
        bot.send_message(OWNER_ID, f"✅ Interazione salvata: {user_id} su {post_id}, tipo {interaction_type}")

    except Exception as e:
        print(f"❌ Errore registrando interazione: {e}")
        bot.send_message(OWNER_ID, f"❌ Errore salvando interazione: {e}")
    finally:
        release_db(conn, cur)
        
        
def add_xp_for_interaction(user_id, post_id, interaction_type):
    """
    Aggiunge XP solo se l'utente non ha già interagito con il post.
    """
    if not user_has_interacted(user_id, post_id, interaction_type):
        update_xp(user_id, 5)  # Aggiunge 5 XP
        mark_interaction(user_id, post_id, interaction_type)

@bot.channel_post_handler(func=lambda message: True)
def handle_reaction(message):
    print(f"🔍 Evento ricevuto: {message}")
    
    if not message or not message.from_user:
        print("⚠️ Nessun utente associato al messaggio, ignorato.")
        return

    user_id = message.from_user.id
    post_id = message.message_id
    interaction_type = "reacted"

    print(f"✅ Ricevuta reaction da user_id={user_id} su post_id={post_id}")
    
    # Debug per verificare se il bot riceve correttamente le reazioni
    bot.send_message(OWNER_ID, f"🔍 Debug: Reaction registrata - user_id={user_id}, post_id={post_id}")

    add_xp_for_interaction(user_id, post_id, interaction_type)

def add_xp_for_interaction(user_id, post_id, interaction_type):
    if not user_has_interacted(user_id, post_id, interaction_type):
        print(f"✅ Aggiungendo XP per {interaction_type} su post {post_id} dell'utente {user_id}")  # DEBUG
        update_xp(user_id, 5)
        mark_interaction(user_id, post_id, interaction_type)
    else:
        print(f"⚠️ L'utente {user_id} ha già interagito con il post {post_id}")  # DEBUG
        
# 🔹 Gestione XP per visualizzazione media nel canale
@bot.channel_post_handler(content_types=["photo", "video"])
def handle_media_view(message):
    """
    Assegna XP quando un utente visualizza un video o una foto.
    """
    user_id = message.from_user.id
    post_id = message.message_id  # L'ID del post che contiene il media

    print(f"➡️ Registrazione interazione: user_id={user_id}, post_id={post_id}, type={interaction_type}")
    
    add_xp_for_interaction(user_id, post_id, "viewed")
    
def check_rewards_for_user(user_id):
    conn, cur = get_db()
    try:
        cur.execute("SELECT xp, video_sbloccato FROM users WHERE user_id = %s FOR UPDATE", (user_id,))
        result = cur.fetchone()

        if result:
            xp, video_sbloccato = result
            for soglia, file_id in video_premi.items():
                if xp >= soglia and video_sbloccato < soglia:
                    bot.send_video(user_id, file_id, caption=f"🎉 Hai sbloccato il premio da {soglia} XP!")
                    cur.execute("UPDATE users SET video_sbloccato = %s WHERE user_id = %s", (soglia, user_id))
                    conn.commit()
    except Exception as e:
        print(f"⚠️ Errore aggiornando premi XP per {user_id}: {e}")
    finally:
        release_db(conn, cur)

# 🔹 Comando /status per mostrare il punteggio attuale dell'utente
@bot.message_handler(commands=["status"])
def user_status(message):
    user_id = message.from_user.id
    conn, cur = get_db()

    # Recupera XP e premi sbloccati dell'utente
    cur.execute("SELECT xp, video_sbloccato FROM users WHERE user_id = %s", (user_id,))
    result = cur.fetchone()
    
    if result:
        xp, video_sbloccato = result
        response = f"📊 <b>Il tuo status XP</b>:\n" \
                   f"🏆 XP Attuali: {xp}\n" \
                   f"🔓 Video sbloccato fino a: {video_sbloccato} XP\n\n" \
                   f"🎯 Prossima soglia XP:\n"

        # Trova la prossima soglia
        next_threshold = min((soglia for soglia in video_premi.keys() if soglia > xp), default=None)
        if next_threshold:
            response += f"➡️ {next_threshold} XP per sbloccare il prossimo premio!"
        else:
            response += "✅ Hai sbloccato tutti i premi disponibili!"

    else:
        response = "❌ Non sei ancora registrato nel sistema XP! Usa /start per iniziare."

    bot.send_message(user_id, response, parse_mode="HTML")
    release_db(conn, cur)
    
def force_update_xp(message):
    """Forza l'aggiornamento manuale degli XP."""
    conn, cur = get_db()

    # Esegui la query per aggiornare gli XP
    cur.execute("""
        UPDATE users
        SET xp = xp + (
            SELECT COALESCE(SUM(
                CASE WHEN reacted = TRUE THEN 5 ELSE 0 END +
                CASE WHEN viewed = TRUE THEN 5 ELSE 0 END
            ), 0)
            FROM interactions
            WHERE interactions.user_id = users.user_id
        )
        WHERE EXISTS (
            SELECT 1 FROM interactions WHERE interactions.user_id = users.user_id
        )
        RETURNING user_id, xp;
    """)
    
    updated_users = cur.fetchall()  # Ora la variabile esiste

    if updated_users:
        for user in updated_users:
            print(f"✅ XP aggiornati per user_id={user[0]}. Nuovo XP: {user[1]}")
        bot.reply_to(message, f"✅ XP aggiornati per {len(updated_users)} utenti!")

    else:
        bot.reply_to(message, "⚠️ Nessuna nuova interazione trovata. Nessun XP aggiornato.")
        print("⚠️ Nessuna nuova interazione trovata. Nessun XP aggiornato.")

    release_db(conn, cur)

# Registra il comando nel bot
@bot.message_handler(commands=['refresh'])
def handle_refresh_command(message):
    """Comando per aggiornare manualmente gli XP."""
    thread = threading.Thread(target=force_update_xp, args=(message,))
    thread.start()

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
    cur.execute("SELECT user_id FROM users WHERE username = %s", (username,))
    user_exists = cur.fetchone()

    if not user_exists:
        bot.reply_to(message, f"⚠️ L'utente @{username} non è registrato nel database.")
    else:
        cur.execute("DELETE FROM users WHERE username = %s", (username,))
        conn.commit()
        bot.reply_to(message, f"✅ L'utente @{username} è stato rimosso dal database del bot.")

    release_db(conn, cur)
    
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
        user_id = user[0]
        try:
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
        except Exception as e:
            failed_count += 1
            print(f"⚠️ Errore inviando DM a {user_id}: {e}")

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

def update_xp_periodically():
    while True:
        conn, cur = get_db()
        try:
            cur.execute("SELECT COUNT(*) FROM interactions WHERE reacted = TRUE OR viewed = TRUE")
            total_interactions = cur.fetchone()[0]

            if total_interactions > 0:
                cur.execute("""
                    UPDATE users
                    SET xp = xp + (
                        SELECT COALESCE(SUM(
                            CASE WHEN reacted = TRUE THEN 5 ELSE 0 END +
                            CASE WHEN viewed = TRUE THEN 5 ELSE 0 END
                        ), 0)
                        FROM interactions
                        WHERE interactions.user_id = users.user_id
                    )
                    WHERE EXISTS (
                        SELECT 1 FROM interactions WHERE interactions.user_id = users.user_id
                    )
                    RETURNING user_id, xp;
                """)
                updated_users = cur.fetchall()
                conn.commit()
                
                for user in updated_users:
                    print(f"✅ XP aggiornati per user_id={user[0]}. Nuovo XP: {user[1]}")

            else:
                print("⚠️ Nessuna nuova interazione trovata. Nessun XP aggiornato.")

        except Exception as e:
            print(f"❌ Errore nell'aggiornamento XP: {e}")

        finally:
            release_db(conn, cur)  # 🔹 Rilascia sempre la connessione

        time.sleep(3600)  # Aspetta 1 ora prima del prossimo aggiornamento
        
