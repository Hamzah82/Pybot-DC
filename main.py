import os
import json
import base64
import requests
import discord
import random # Added for animal commands
import hashlib # Added for encrypt/decrypt commands
from discord.ext import commands
from dotenv import load_dotenv
from cryptography.fernet import Fernet
from ddgs import DDGS
from typing import Optional
import database # Added for setprefix command

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

# Bot setup
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent

bot = commands.Bot(command_prefix=None, intents=intents, help_command=None)

# TogetherAI configuration
API_URL = "https://api.together.xyz/v1/chat/completions"
MODEL_FILE = "https://raw.githubusercontent.com/Hamzah82/pybot/main/Model_Encrypt.json"

# Load model from URL Base64
def load_model():
    try:
        response = requests.get(MODEL_FILE)
        response.raise_for_status()
        encoded_data = response.text
        decoded_json = base64.b64decode(encoded_data).decode("utf-8")
        return json.loads(decoded_json)
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to fetch model: {e}")
        return []
    except Exception:
        print("❌ Model corrupted or unreadable!")
        return []

# Load model instructions
model_instructions = load_model()

def chat_with_together(user_input):
    system_message = model_instructions if isinstance(model_instructions, list) else []
    messages = system_message + [{"role": "user", "content": user_input}]

    payload = {
        "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        "messages": messages,
        "temperature": 0.7
    }

    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        return result.get("choices", [{}])[0].get("message", {}).get("content", "An error occurred in AI response!")
    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('------')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

@bot.tree.command(name="ping", description="Checks if the bot is alive.")
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

class TicTacToeGame:
    def __init__(self, player1_id: int, player2_id: Optional[int] = None, difficulty: Optional[str] = None):
        self.board = [" " for _ in range(9)]
        self.game_over = False

        if player2_id and difficulty is None:
            self.game_type = "pvp"
            self.players = {player1_id: "X", player2_id: "O"}
            self.current_player_id = player1_id
            self.current_player_symbol = "X"
        elif difficulty and player2_id is None:
            self.game_type = "pve"
            self.difficulty = difficulty
            self.player_id = player1_id # Human player
            self.current_player_symbol = "X"
        else:
            raise ValueError("Invalid game initialization. Provide either opponent or difficulty.")

    def make_move(self, index, player_id=None):
        if self.game_type == "pvp":
            if player_id != self.current_player_id:
                return False # Not current player's turn
            symbol = self.players[player_id]
        else: # pve
            symbol = self.current_player_symbol

        if self.board[index] == " " and not self.game_over:
            self.board[index] = symbol
            if self.check_winner(self.board):
                self.game_over = True
                return True
            if self.check_draw(self.board):
                self.game_over = True
                return True
            
            if self.game_type == "pvp":
                # Switch turn for PvP
                player_ids_list = list(self.players.keys())
                if self.current_player_id == player_ids_list[0]:
                    self.current_player_id = player_ids_list[1]
                else:
                    self.current_player_id = player_ids_list[0]
            else: # pve
                self.current_player_symbol = "O" if self.current_player_symbol == "X" else "X"
            return True
        return False

    def check_winner(self, board):
        winning_combinations = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
            (0, 4, 8), (2, 4, 6)              # Diagonals
        ]
        for combo in winning_combinations:
            if (board[combo[0]] == board[combo[1]] == board[combo[2]] != " "):
                return True
        return False

    def check_draw(self, board):
        return " " not in board and not self.check_winner(board)

    def get_empty_cells(self, board):
        return [i for i, cell in enumerate(board) if cell == " "]

    def ai_move(self):
        if self.difficulty == "easy":
            return self._ai_move_easy()
        elif self.difficulty == "medium":
            return self._ai_move_medium()
        elif self.difficulty == "hard":
            return self._ai_move_hard()

    def _ai_move_easy(self):
        empty_cells = self.get_empty_cells(self.board)
        if empty_cells:
            import random
            return random.choice(empty_cells)
        return None

    def _ai_move_medium(self):
        # Try to win, then block, then random
        move = self._find_winning_move("O")
        if move is not None:
            return move
        move = self._find_winning_move("X")
        if move is not None:
            return move
        return self._ai_move_easy()

    def _ai_move_hard(self):
        # Minimax algorithm
        best_score = -float('inf')
        best_move = None
        for cell in self.get_empty_cells(self.board):
            self.board[cell] = "O"
            score = self._minimax(self.board, 0, False)
            self.board[cell] = " "
            if score > best_score:
                best_score = score
                best_move = cell
        return best_move

    def _find_winning_move(self, player):
        for cell in self.get_empty_cells(self.board):
            self.board[cell] = player
            if self.check_winner(self.board):
                self.board[cell] = " "
                return cell
            self.board[cell] = " "
        return None

    def _minimax(self, board, depth, is_maximizing):
        if self.check_winner(board):
            return 1 if is_maximizing else -1
        if self.check_draw(board):
            return 0

        if is_maximizing:
            best_score = -float('inf')
            for cell in self.get_empty_cells(board):
                board[cell] = "O"
                score = self._minimax(board, depth + 1, False)
                board[cell] = " "
                best_score = max(score, best_score)
            return best_score
        else:
            best_score = float('inf')
            for cell in self.get_empty_cells(board):
                board[cell] = "X"
                score = self._minimax(board, depth + 1, True)
                board[cell] = " "
                best_score = min(score, best_score)
            return best_score

    

class TicTacToeView(discord.ui.View):
    def __init__(self, game: TicTacToeGame):
        super().__init__(timeout=180)
        self.game = game
        self.message = None
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        for i in range(9):
            button = discord.ui.Button(
                label=self.game.board[i] if self.game.board[i] != " " else "\u200b",
                style=discord.ButtonStyle.gray,
                row=i // 3,
                custom_id=f"tictactoe_{i}"
            )
            button.callback = self.button_callback
            if self.game.board[i] != " " or self.game.game_over:
                button.disabled = True
            self.add_item(button)

    async def button_callback(self, interaction: discord.Interaction):
        if self.game.game_type == "pvp":
            if interaction.user.id not in self.game.players:
                await interaction.response.send_message("This is not your game!", ephemeral=True)
                return
            if interaction.user.id != self.game.current_player_id:
                await interaction.response.send_message(f"It's not your turn! It's <@{self.game.current_player_id}>'s turn.", ephemeral=True)
                return
            player_id_for_move = interaction.user.id
            current_player_display = f"<@{self.game.current_player_id}> ({self.game.players[self.game.current_player_id]})"
        else: # pve
            if interaction.user.id != self.game.player_id:
                await interaction.response.send_message("This is not your game!", ephemeral=True)
                return
            if self.game.current_player_symbol == "O": # AI's turn
                await interaction.response.send_message("Wait for AI's turn!", ephemeral=True)
                return
            player_id_for_move = None # Not used for PVE make_move
            current_player_display = f"It's {self.game.current_player_symbol}'s turn."

        index = int(interaction.data["custom_id"].split("_")[1])
        if self.game.make_move(index, player_id_for_move):
            self.update_buttons()
            if self.game.check_winner(self.game.board):
                if self.game.game_type == "pvp":
                    winner_id = interaction.user.id
                    await interaction.response.edit_message(content=f"<@{winner_id}> ({self.game.players[winner_id]}) wins!", view=self)
                else:
                    await interaction.response.edit_message(content=f"Player {self.game.current_player_symbol} wins!", view=self)
                self.stop()
            elif self.game.check_draw(self.game.board):
                await interaction.response.edit_message(content="It's a draw!", view=self)
                self.stop()
            else:
                # Re-evaluate current_player_display AFTER the move has been made and turn switched
                if self.game.game_type == "pvp":
                    next_player_display = f"<@{self.game.current_player_id}> ({self.game.players[self.game.current_player_id]})"
                else: # pve
                    next_player_display = f"It's {self.game.current_player_symbol}'s turn."
                
                await interaction.response.edit_message(content=f"It's {next_player_display}'s turn.", view=self)
                
                if self.game.game_type == "pve" and self.game.current_player_symbol == "O": # AI's turn
                    await self.message.edit(content="AI's turn...")
                    ai_move_index = self.game.ai_move()
                    if ai_move_index is not None:
                        self.game.make_move(ai_move_index)
                        self.update_buttons()
                        if self.game.check_winner(self.game.board):
                            await self.message.edit(content=f"AI wins!", view=self)
                            self.stop()
                        elif self.game.check_draw(self.game.board):
                            await self.message.edit(content="It's a draw!", view=self)
                            self.stop()
                        else:
                            # After AI move, it's human's turn again (X)
                            await self.message.edit(content=f"It's {self.game.current_player_symbol}'s turn.", view=self)
        else:
            await interaction.response.send_message("This cell is already taken or the game is over.", ephemeral=True)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        await self.message.edit(content="Game ended due to timeout.", view=self)

@bot.tree.command(name="tictactoe", description="Starts a Tic-Tac-Toe game.")
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@discord.app_commands.describe(
    opponent="The user you want to play against (leave empty to play against AI)."
)
@discord.app_commands.choices(difficulty=[
    discord.app_commands.Choice(name="Easy", value="easy"),
    discord.app_commands.Choice(name="Medium", value="medium"),
    discord.app_commands.Choice(name="Hard", value="hard"),
])
async def tictactoe(interaction: discord.Interaction, opponent: Optional[discord.User] = None, difficulty: Optional[discord.app_commands.Choice[str]] = None):
    if opponent and difficulty:
        await interaction.response.send_message("You cannot specify both an opponent and a difficulty. Please choose one mode.", ephemeral=True)
        return

    if opponent:
        if opponent.bot:
            await interaction.response.send_message("You cannot play against a bot as an opponent.", ephemeral=True)
            return
        if opponent.id == interaction.user.id:
            await interaction.response.send_message("You cannot play against yourself!", ephemeral=True)
            return
        game = TicTacToeGame(interaction.user.id, opponent.id)
        view = TicTacToeView(game)
        await interaction.response.send_message(f"Tic-Tac-Toe started! <@{interaction.user.id}> (X) vs <@{opponent.id}> (O). It's <@{game.current_player_id}>'s turn.", view=view)
    elif difficulty:
        game = TicTacToeGame(interaction.user.id, difficulty=difficulty.value)
        view = TicTacToeView(game)
        await interaction.response.send_message(f"Tic-Tac-Toe started! You (X) vs AI (O). It's your turn.", view=view)
    else:
        await interaction.response.send_message("Please specify either an opponent or a difficulty to start the game.", ephemeral=True)
        return

    view.message = await interaction.original_response()
    game = TicTacToeGame(difficulty.value)
    view = TicTacToeView(game, interaction.user.id)
    await interaction.response.send_message(f"Tic-Tac-Toe started! It's {game.current_player}'s turn.", view=view)
    view.message = await interaction.original_response()


@bot.tree.command(name="invite", description="Generates a Discord server invite link.")
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@discord.app_commands.describe(
    max_uses="Maximum number of times the invite can be used (default: 0 for unlimited).",
    max_age="Duration after which the invite expires in seconds (default: 0 for never).",
    temporary="Whether this invite only grants temporary membership (default: False).",
    unique="Whether to create a unique invite, even if a similar one already exists (default: False)."
)
async def invite(
    interaction: discord.Interaction,
    max_uses: Optional[int] = 0,
    max_age: Optional[int] = 0,
    temporary: Optional[bool] = False,
    unique: Optional[bool] = False
):
    if not interaction.user.guild_permissions.create_instant_invite:
        await interaction.response.send_message("You don't have permission to create invite links.", ephemeral=True)
        return

    try:
        invite_link = await interaction.channel.create_invite(
            max_uses=max_uses,
            max_age=max_age,
            temporary=temporary,
            unique=unique
        )
        await interaction.response.send_message(f"Here is your invite link: {invite_link.url}")
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to create invite links in this channel.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred while creating the invite: {e}", ephemeral=True)

@bot.tree.command(name="fact", description="Generates a random interesting fact.")
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def fact(interaction: discord.Interaction):
    try:
        response = requests.get("https://uselessfacts.jsph.pl/random.json?language=en")
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        await interaction.response.send_message(f"**Random Fact:** {data['text']}")
    except requests.exceptions.RequestException as e:
        await interaction.response.send_message(f"Failed to fetch a fact: {e}", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An unexpected error occurred: {e}", ephemeral=True)

# --- API ENDPOINTS for animal commands ---
DOG_API_URL = "https://dog.ceo/api/breeds/image/random"
CAT_API_URL = "https://api.thecatapi.com/v1/images/search"

# --- HELPER FUNCTION for animal commands ---
async def fetch_and_send_animal(interaction: discord.Interaction, animal_type: str):
    """A helper function to fetch and send an animal picture."""
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

        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()

        if animal_type == 'dog':
            image_url = data.get('message')
        elif animal_type == 'cat':
            image_url = data[0].get('url')

        if image_url:
            embed = discord.Embed(title=title, color=color)
            embed.set_image(url=image_url)
            embed.set_footer(text=f"Powered by {animal_type} APIs")
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("Sorry, the API didn't provide an image URL.")

    except requests.RequestException as e:
        print(f"Error fetching {animal_type} image: {e}")
        await interaction.followup.send(f"Sorry, I couldn't fetch a {animal_type} picture right now.")

@bot.tree.command(name="dog", description="Fetches a random picture of a dog.")
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def dog_command(interaction: discord.Interaction):
    """Calls the helper function to get a dog picture."""
    await fetch_and_send_animal(interaction, 'dog')

@bot.tree.command(name="cat", description="Fetches a random picture of a cat.")
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def cat_command(interaction: discord.Interaction):
    """Calls the helper function to get a cat picture."""
    await fetch_and_send_animal(interaction, 'cat')

@bot.tree.command(name="random", description="Fetches a random picture of a cat OR a dog.")
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def random_command(interaction: discord.Interaction):
    """Randomly chooses between a cat or a dog and sends a picture."""
    chosen_animal = random.choice(['dog', 'cat'])
    await fetch_and_send_animal(interaction, chosen_animal)


@bot.tree.command(name="help", description="Displays this command list.")
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def help_command(interaction: discord.Interaction):
    help_message = """
**Pybot Commands:**

**Slash Commands (`/`):**
`/ping` - Checks if the bot is alive.
`/tictactoe [opponent|difficulty]` - Starts a Tic-Tac-Toe game against AI or another player.
`/invite` - Generates a Discord server invite link.
`/fact` - Generates a random interesting fact.
`/dog` - Fetches a random picture of a dog.
`/cat` - Fetches a random picture of a cat.
`/random` - Fetches a random picture of a cat OR a dog.
`/spoof <message>` - Sends a message as the bot (Wokabi 758961658634043412 only).
`/roll <dice_string>` - Rolls dice (example: `/roll 2d6+3`).
`/base64encode <text>` - Encodes text to Base64.
`/base64decode <text>` - Decodes text from Base64.
`/calc <expression>` - Evaluates a mathematical expression (example: `/calc 10*5+2`).
`/encrypt <passphrase> <text>` - Encrypts text using a passphrase.
`/decrypt <passphrase> <encrypted_text>` - Decrypts text using a passphrase.
`/search <query>` - Searches on DuckDuckGo.
`/chat <message>` - Interacts with the AI.
`/clear [amount]` - Clears messages in the channel (default 100, max 1000).
`/setprefix <new_prefix>` - Sets a custom prefix for this server.
`/kick <member> [reason]` - Kicks a member from the server.
`/ban <member> [reason]` - Bans a member from the server.
`/help` - Displays this command list.
    """
    await interaction.response.send_message(help_message)

@bot.tree.command(name="spoof", description="Sends a message as the bot (Wokabi 758961658634043412 only).")
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def spoof(interaction: discord.Interaction, message: str):
    # Replace 108 with the actual user ID of Wokabi 108
    if interaction.user.id == 758961658634043412:
        await interaction.response.send_message(message)
    else:
        await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)

@bot.tree.command(name="roll", description="Rolls dice (example: /roll 2d6+3).")
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def roll(interaction: discord.Interaction, dice_string: str):
    try:
        parts = dice_string.lower().split('d')
        num_dice = int(parts[0])
        
        if '+' in parts[1]:
            die_type, modifier = map(int, parts[1].split('+'))
        elif '-' in parts[1]:
            die_type, modifier = map(int, parts[1].split('-'))
            modifier = -modifier
        else:
            die_type = int(parts[1])
            modifier = 0

        if num_dice <= 0 or die_type <= 0:
            await interaction.response.send_message("Number of dice and die type must be greater than 0.", ephemeral=True)
            return

        rolls = [random.randint(1, die_type) for _ in range(num_dice)]
        total = sum(rolls) + modifier

        await interaction.response.send_message(f"Roll: {rolls}, Total: {total}")
    except ValueError:
        await interaction.response.send_message("Invalid dice format. Example: `/roll 2d6` or `/roll 1d20+5`.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)

@bot.tree.command(name="base64encode", description="Encodes text to Base64.")
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def base64encode(interaction: discord.Interaction, text: str):
    encoded_bytes = base64.b64encode(text.encode('utf-8'))
    encoded_text = encoded_bytes.decode('utf-8')
    await interaction.response.send_message(f"Encoded: ```{encoded_text}```")

@bot.tree.command(name="base64decode", description="Decodes text from Base64.")
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def base64decode(interaction: discord.Interaction, text: str):
    try:
        decoded_bytes = base64.b64decode(text.encode('utf-8'))
        decoded_text = decoded_bytes.decode('utf-8')
        await interaction.response.send_message(f"Decoded: ```{decoded_text}```")
    except Exception:
        await interaction.response.send_message("Invalid text for Base64 decode.", ephemeral=True)

@bot.tree.command(name="calc", description="Evaluates a mathematical expression (example: /calc 10*5+2).")
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def calc(interaction: discord.Interaction, expression: str):
    try:
        # Only allow basic mathematical operations for security
        allowed_chars = "0123456789+-*/(). "
        if not all(c in allowed_chars for c in expression):
            await interaction.response.send_message("Invalid expression. Only numbers and basic operators (+-*/()) are allowed.", ephemeral=True)
            return
        result = eval(expression)
        await interaction.response.send_message(f"Result: {result}")
    except Exception:
        await interaction.response.send_message("Invalid mathematical expression.", ephemeral=True)

@bot.tree.command(name="encrypt", description="Encrypts text using a passphrase.")
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def encrypt(interaction: discord.Interaction, passphrase: str, text: str):
    try:
        key = base64.urlsafe_b64encode(hashlib.sha256(passphrase.encode()).digest())
        f = Fernet(key)
        encrypted_text = f.encrypt(text.encode()).decode()
        await interaction.response.send_message(f"Encrypted: ```{encrypted_text}```")
    except Exception as e:
        await interaction.response.send_message(f"Failed to encrypt: {e}", ephemeral=True)

@bot.tree.command(name="decrypt", description="Decrypts text using a passphrase.")
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def decrypt(interaction: discord.Interaction, passphrase: str, encrypted_text: str):
    try:
        key = base64.urlsafe_b64encode(hashlib.sha256(passphrase.encode()).digest())
        f = Fernet(key)
        decrypted_text = f.decrypt(encrypted_text.encode()).decode()
        await interaction.response.send_message(f"Decrypted: ```{decrypted_text}```")
    except Exception as e:
        await interaction.response.send_message(f"Failed to decrypt: {e}", ephemeral=True)

@bot.tree.command(name="search", description="Searches on DuckDuckGo.")
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def search(interaction: discord.Interaction, query: str):
    await interaction.response.defer()
    try:
        results = DDGS().text(query=query, max_results=3)
        if results:
            response_message = "**Search Results:**\n"
            for i, result in enumerate(results):
                response_message += f"{i+1}. [{result['title']}]({result['href']})\n{result['body']}\n\n"
            await interaction.followup.send(response_message)
        else:
            await interaction.followup.send("No results found.")
    except Exception as e:
        await interaction.followup.send(f"An error occurred during search: {e}", ephemeral=True)

@bot.tree.command(name="chat", description="Interacts with the AI.")
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def chat(interaction: discord.Interaction, message: str):
    await interaction.response.defer()
    response = chat_with_together(message)
    await interaction.followup.send(response)

@bot.tree.command(name="clear", description="Clears messages in the channel.")
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@discord.app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: Optional[int] = None):
    if amount is None:
        limit = 100  # Default to 100 if not specified
        await interaction.response.defer(ephemeral=True)
    elif amount <= 0:
        await interaction.response.send_message("Amount must be a positive number.", ephemeral=True)
        return
    elif amount > 1000: # Limit to prevent accidental mass deletion
        await interaction.response.send_message("Cannot clear more than 1000 messages at once.", ephemeral=True)
        return
    else:
        limit = amount + 1 # +1 to delete the command message itself
        await interaction.response.defer(ephemeral=True)

    try:
        deleted = await interaction.channel.purge(limit=limit)
        if amount is None:
            await interaction.followup.send(f"Cleared {len(deleted) - 1} messages.", ephemeral=True)
        else:
            await interaction.followup.send(f"Cleared {len(deleted) - 1} messages.", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send("I don't have permissions to delete messages.", ephemeral=True)
    except discord.HTTPException as e:
        await interaction.followup.send(f"An error occurred while clearing messages: {e}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"An unexpected error occurred: {e}", ephemeral=True)

@bot.tree.command(name="setprefix", description="Sets a custom prefix for this server.")
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@discord.app_commands.checks.has_permissions(manage_guild=True)
async def setprefix(interaction: discord.Interaction, new_prefix: str):
    if interaction.guild_id is None:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return
    if len(new_prefix) > 10:
        await interaction.response.send_message("Prefix cannot be longer than 10 characters.", ephemeral=True)
        return
    await database.set_prefix(interaction.guild_id, new_prefix)
    await interaction.response.send_message(f"Prefix for this server has been set to `{new_prefix}`")

@bot.tree.command(name="kick", description="Kicks a member from the server.")
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@discord.app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: Optional[str] = "No reason provided."):
    if interaction.guild_id is None:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return
    try:
        await interaction.response.defer(ephemeral=True)
        await member.kick(reason=reason)
        await interaction.followup.send(f"Successfully kicked {member.display_name} for: {reason}")
    except discord.Forbidden:
        await interaction.followup.send("I don't have permissions to kick members.", ephemeral=True)
    except discord.HTTPException as e:
        await interaction.followup.send(f"An error occurred while kicking: {e}", ephemeral=True)

@bot.tree.command(name="ban", description="Bans a member from the server.")
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@discord.app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: Optional[str] = "No reason provided."):
    if interaction.guild_id is None:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return
    try:
        await interaction.response.defer(ephemeral=True)
        await member.ban(reason=reason)
        await interaction.followup.send(f"Successfully banned {member.display_name} for: {reason}")
    except discord.Forbidden:
        await interaction.followup.send("I don't have permissions to ban members.", ephemeral=True)
    except discord.HTTPException as e:
        await interaction.followup.send(f"An error occurred while banning: {e}", ephemeral=True)

# Run the bot
if DISCORD_TOKEN:
    bot.run(DISCORD_TOKEN)
else:
    print("DISCORD_TOKEN not found in .env file. Please set it.")
