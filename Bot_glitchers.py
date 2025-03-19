import os
import random
import telebot
import time
from flask import Flask, request

TOKEN = os.getenv("BOT_TOKEN")  # Il token del bot
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # ID del canale

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
app = Flask(__name__)

# Set di emoji per le reazioni casuali
REACTION_EMOJIS = ["🔥", "🍓", "🍌", "❤️", "🆒", "😍", "😁", "💯", "👍", "🤩", "🎉", "👀"]

# Dizionario per tenere traccia delle reazioni già aggiunte ai messaggi
reaction_tracker = {}

def add_random_reactions(message_id, count=6):
    try:
        # Recupera le reazioni già aggiunte, se presenti
        existing_reactions = reaction_tracker.get(message_id, [])

        # Se il messaggio ha già il numero massimo di reazioni, non aggiungere altro
        if len(existing_reactions) >= 6:
            print(f"⚠️ Il messaggio {message_id} ha già il massimo di 6 reazioni.")
            return
        
        # Calcola quante nuove reazioni possiamo aggiungere senza superare il limite
        max_new_reactions = min(count, 6 - len(existing_reactions))

        # Seleziona nuove reazioni evitando duplicati
        new_reactions = random.sample([e for e in REACTION_EMOJIS if e not in existing_reactions], max_new_reactions)

        # Combina le reazioni attuali con quelle nuove
        all_reactions = existing_reactions + new_reactions

        # Aggiorna il tracker con tutte le reazioni
        reaction_tracker[message_id] = all_reactions

        # Invia tutte le reazioni al messaggio
        bot.set_message_reaction(
            chat_id=CHANNEL_ID,
            message_id=message_id,
            reaction=[telebot.types.ReactionTypeEmoji(emoji=emoji) for emoji in all_reactions]
        )

        print(f"✅ Aggiunte {len(new_reactions)} nuove reazioni al post {message_id}")

    except Exception as e:
        print(f"❌ Errore nell'aggiungere le reazioni: {e}")
      
# Quando viene pubblicato un nuovo post, aggiunge 10 reazioni random
@bot.channel_post_handler(func=lambda message: True)
def auto_add_reactions(message):
    add_random_reactions(message.message_id)

# Comando /add per aggiungere altre 10 reazioni random a un post esistente
@bot.message_handler(commands=["add"])
def manual_add_reactions(message):
    if message.chat.type != "private":
        return  # Evitiamo che venga usato nei gruppi

    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ Usa il comando così: /add ID_POST", parse_mode="Markdown")
            return

        post_id = int(args[1])
        add_random_reactions(post_id)
        bot.reply_to(message, f"✅ Aggiunte 10 reazioni random al post {post_id}!")
    except Exception as e:
        bot.reply_to(message, f"❌ Errore: {e}")

# Endpoint Webhook per Railway
@app.route("/", methods=["GET"])
def home():
    return "✅ Il bot è attivo!", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        json_str = request.get_data().decode("utf-8")
        if not json_str:
            return "Empty request", 400
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
    except Exception as e:
        print(f"Errore Webhook: {e}")
        return f"Errore: {str(e)}", 500
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
