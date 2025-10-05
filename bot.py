# bot.py
import discord
from discord.ext import commands
from flask import Flask, jsonify, request
import threading
import time
import requests

# ====================
# CONFIGURATION
# ====================
BOT_TOKEN = "TON_BOT_TOKEN_ICI"  # Remplace par ton token
PORT = 5000  # Port du serveur Flask

# Stockage simple des salons connectés (en mémoire)
connected_channels = set()

# ====================
# FLASK WEB SERVER
# ====================
app = Flask(__name__)

@app.route("/")
def index():
    return "Bot Global Chat en ligne !"

@app.route("/health")
def health():
    return jsonify({"status": "OK"})

@app.route("/register_channel", methods=["POST"])
def register_channel():
    """
    Expects JSON: {"channel_id": 1234567890}
    """
    data = request.get_json()
    channel_id = data.get("channel_id")
    if channel_id:
        connected_channels.add(int(channel_id))
        return jsonify({"status": "ok", "registered_channel": channel_id})
    return jsonify({"status": "error", "message": "channel_id manquant"}), 400

def run_flask():
    app.run(host="0.0.0.0", port=PORT)

# ====================
# DISCORD BOT
# ====================
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # Nécessaire pour lire le contenu des messages

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot connecté en tant que {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Ignore les messages des bots

    if message.channel.id in connected_channels:
        for channel_id in connected_channels:
            if channel_id != message.channel.id:  # Ne renvoie pas dans le même salon
                channel = bot.get_channel(channel_id)
                if channel:
                    try:
                        await channel.send(f"[{message.guild.name} - {message.channel.name}] {message.author}: {message.content}")
                    except Exception as e:
                        print(f"Erreur en envoyant le message: {e}")
    await bot.process_commands(message)

# ====================
# KEEP ALIVE THREAD
# ====================
def keep_alive():
    while True:
        try:
            requests.get(f"http://127.0.0.1:{PORT}/health")
        except:
            pass
        time.sleep(300)  # Ping toutes les 5 minutes

# ====================
# LANCEMENT
# ====================
if __name__ == "__main__":
    # Lancer Flask dans un thread séparé
    threading.Thread(target=run_flask).start()
    # Lancer le thread keep_alive
    threading.Thread(target=keep_alive).start()
    # Lancer le bot Discord
    bot.run(BOT_TOKEN)
