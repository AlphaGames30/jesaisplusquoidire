import json
import threading
from flask import Flask, render_template, request
from flask_socketio import SocketIO
import discord
from discord.ext import commands
import os

# -----------------------
# Flask app
# -----------------------
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

DATA_FILE = "data.json"

# Charge les données persistantes
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        connected_channels = json.load(f)
else:
    connected_channels = {}  # {token: [channel_id, ...]}

# Tous les bots actifs
bots = {}

# Sauvegarde des données
def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(connected_channels, f)

# -----------------------
# Fonction pour lancer un bot
# -----------------------
def start_bot(token):
    intents = discord.Intents.default()
    intents.messages = True
    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready():
        print(f"{bot.user} connecté !")

    @bot.event
    async def on_message(message):
        if message.author.bot:
            return
        if token not in connected_channels:
            return
        if str(message.channel.id) not in connected_channels[token]:
            return

        # Relay message to all other channels of all bots
        for tkn, bot_instance in bots.items():
            for ch_id in connected_channels.get(tkn, []):
                if tkn == token and ch_id == str(message.channel.id):
                    continue
                try:
                    channel = bot_instance.get_channel(int(ch_id))
                    if channel:
                        await channel.send(f"[{message.guild.name}] {message.author}: {message.content}")
                except Exception as e:
                    print(f"Erreur en envoyant le message: {e}")

    bots[token] = bot
    try:
        bot.run(token)
    except Exception as e:
        print(f"Erreur avec le bot {token}: {e}")

# -----------------------
# Routes Flask
# -----------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/connect", methods=["POST"])
def connect():
    token = request.form.get("token")
    channel_id = request.form.get("channel_id")
    if not token or not channel_id:
        return "Token ou channel manquant", 400

    if token not in connected_channels:
        connected_channels[token] = []
        threading.Thread(target=start_bot, args=(token,), daemon=True).start()

    if channel_id not in connected_channels[token]:
        connected_channels[token].append(channel_id)
        save_data()

    return "Bot et salon connectés !"

# -----------------------
# Run Flask
# -----------------------
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
