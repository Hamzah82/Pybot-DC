import json
import random
import requests
import discord
from discord import app_commands

# --- CONFIGURATION ---
# Load configuration from a 'cfg.json' file in the same directory.
try:
    with open('cfg.json', 'r') as f:
        config = json.load(f)
    DISCORD_BOT_TOKEN = config['DISCORD_BOT_TOKEN']
except FileNotFoundError:
    print("FATAL ERROR: 'cfg.json' not found. Please create this file.")
    exit()
except KeyError:
    print("FATAL ERROR: 'DISCORD_BOT_TOKEN' is missing from your 'cfg.json' file.")
    exit()

# --- BOT SETUP ---
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

# --- API ENDPOINTS ---
DOG_API_URL = "https://dog.ceo/api/breeds/image/random"
CAT_API_URL = "https://api.thecatapi.com/v1/images/search"

# --- HELPER FUNCTION ---
async def fetch_and_send_animal(interaction: discord.Interaction, animal_type: str):
    """A helper function to fetch and send an animal picture."""
    # Immediately acknowledge the command to prevent it from "failing"
    await interaction.response.defer(thinking=True)

    try:
        if animal_type == 'dog':
            api_url = DOG_API_URL
            title = "Woof! Here's a random doggo!"
            color = discord.Color.blue()
        elif animal_type == 'cat':
            api_url = CAT_API_URL
            title = "Meow! Here's a random kitty!"
            color = discord.Color.orange()
        else:
            await interaction.followup.send("Sorry, I don't know that animal.")
            return

        # Fetch the image from the API
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
        data = response.json()

        # Extract the image URL (APIs have different structures)
        if animal_type == 'dog':
            image_url = data.get('message')
        elif animal_type == 'cat':
            image_url = data[0].get('url')

        if image_url:
            # Create a rich 'embed' to send in Discord
            embed = discord.Embed(title=title, color=color)
            embed.set_image(url=image_url)
            embed.set_footer(text=f"Powered by {animal_type} APIs")
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("Sorry, the API didn't provide an image URL.")

    except requests.RequestException as e:
        print(f"Error fetching {animal_type} image: {e}")
        await interaction.followup.send(f"Sorry, I couldn't fetch a {animal_type} picture right now.")

# --- EVENTS ---
@client.event
async def on_ready():
    """This function runs when the bot has successfully connected to Discord."""
    await tree.sync()
    print("------------------------------------------------------")
    print(f'Logged in as: {client.user} (ID: {client.user.id})')
    print("Bot is ready and commands are synced.")
    print("Available commands: /dog, /cat, /random")
    print("------------------------------------------------------")

# --- SLASH COMMANDS ---
@tree.command(name="dog", description="Fetches a random picture of a dog.")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def dog_command(interaction: discord.Interaction):
    """Calls the helper function to get a dog picture."""
    await fetch_and_send_animal(interaction, 'dog')

@tree.command(name="cat", description="Fetches a random picture of a cat.")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def cat_command(interaction: discord.Interaction):
    """Calls the helper function to get a cat picture."""
    await fetch_and_send_animal(interaction, 'cat')

@tree.command(name="random", description="Fetches a random picture of a cat OR a dog.")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def random_command(interaction: discord.Interaction):
    """Randomly chooses between a cat or a dog and sends a picture."""
    chosen_animal = random.choice(['dog', 'cat'])
    await fetch_and_send_animal(interaction, chosen_animal)

# --- RUN THE BOT ---
if __name__ == "__main__":
    try:
        client.run(DISCORD_BOT_TOKEN)
    except discord.errors.LoginFailure:
        print("\nFATAL ERROR: Login failed. The token in your 'cfg.json' is likely invalid.")
        print("Please ensure you have reset your token and copied the new one correctly.")
