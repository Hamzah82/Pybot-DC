import os
import json
import base64
import requests
import discord
from discord.ext import commands
from dotenv import load_dotenv
from cryptography.fernet import Fernet
from ddgs import DDGS
from typing import Optional

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

# Bot setup
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent

bot = commands.Bot(command_prefix="py ", intents=intents, help_command=None)

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
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

class TicTacToeGame:
    def __init__(self, difficulty="easy"):
        self.board = [" " for _ in range(9)]
        self.current_player = "X"
        self.difficulty = difficulty
        self.game_over = False

    def make_move(self, index):
        if self.board[index] == " " and not self.game_over:
            self.board[index] = self.current_player
            if self.check_winner(self.board):
                self.game_over = True
                return True
            if self.check_draw(self.board):
                self.game_over = True
                return True
            self.current_player = "O" if self.current_player == "X" else "X"
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
        empty_cells = self.get_empty_cells()
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
    def __init__(self, game: TicTacToeGame, player_id: int):
        super().__init__(timeout=180)
        self.game = game
        self.player_id = player_id
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
        if interaction.user.id != self.player_id:
            await interaction.response.send_message("This is not your game!", ephemeral=True)
            return

        if self.game.current_player == "O": # AI's turn
            await interaction.response.send_message("Wait for AI's turn!", ephemeral=True)
            return

        index = int(interaction.data["custom_id"].split("_")[1])
        if self.game.make_move(index):
            self.update_buttons()
            if self.game.check_winner():
                await interaction.response.edit_message(content=f"Player {self.game.current_player} wins!", view=self)
                self.stop()
            elif self.game.check_draw():
                await interaction.response.edit_message(content="It's a draw!", view=self)
                self.stop()
            else:
                await interaction.response.edit_message(content=f"It's {self.game.current_player}'s turn.", view=self)
                if self.game.current_player == "O": # AI's turn
                    await self.message.edit(content="AI's turn...")
                    ai_move_index = self.game.ai_move()
                    if ai_move_index is not None:
                        self.game.make_move(ai_move_index)
                        self.update_buttons()
                        if self.game.check_winner():
                            await self.message.edit(content=f"AI wins!", view=self)
                            self.stop()
                        elif self.game.check_draw():
                            await self.message.edit(content="It's a draw!", view=self)
                            self.stop()
                        else:
                            await self.message.edit(content=f"It's {self.game.current_player}'s turn.", view=self)
        else:
            await interaction.response.send_message("This cell is already taken or the game is over.", ephemeral=True)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        await self.message.edit(content="Game ended due to timeout.", view=self)

@bot.tree.command(name="tictactoe", description="Starts a Tic-Tac-Toe game.")
@discord.app_commands.choices(difficulty=[
    discord.app_commands.Choice(name="Easy", value="easy"),
    discord.app_commands.Choice(name="Medium", value="medium"),
    discord.app_commands.Choice(name="Hard", value="hard"),
])
async def tictactoe(interaction: discord.Interaction, difficulty: discord.app_commands.Choice[str]):
    game = TicTacToeGame(difficulty.value)
    view = TicTacToeView(game, interaction.user.id)
    await interaction.response.send_message(f"Tic-Tac-Toe started! It's {game.current_player}'s turn.", view=view)
    view.message = await interaction.original_response()


@bot.tree.command(name="invite", description="Generates a Discord server invite link.")
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


@bot.command(name="help", description="Displays this command list.")
async def help_command(ctx):
    help_message = """
**Pybot Commands:**

**Message Commands (Prefix `py `):**
`py spoof <message>` - Sends a message as the bot (Wokabi 758961658634043412 only).
`py roll XdY[+Z]` - Rolls dice (example: `py roll 2d6+3`).
`py base64encode <text>` - Encodes text to Base64.
`py base64decode <text>` - Decodes text from Base64.
`py calc <expression>` - Evaluates a mathematical expression (example: `py calc 10*5+2`).
`py encrypt <passphrase> <text>` - Encrypts text using a passphrase.
`py decrypt <passphrase> <encrypted_text>` - Decrypts text using a passphrase.
`py search <query>` - Searches on DuckDuckGo.
`py chat <message>` - Interacts with the AI.
`py clear [amount|all]` - Clears messages in the channel (default 100, max 1000, or all).
`py kick <member> [reason]` - Kicks a member from the server.
`py ban <member> [reason]` - Bans a member from the server.
`py help` - Displays this command list.

**Slash Commands (`/`):**
`/ping` - Checks if the bot is alive.
`/tictactoe` - Starts a Tic-Tac-Toe game.
`/invite` - Generates a Discord server invite link.
    """
    await ctx.send(help_message)

@bot.command(name="spoof", description="Sends a message as the bot (Wokabi 108 only).")
async def spoof(ctx, *, message: str):
    # Replace 108 with the actual user ID of Wokabi 108
    if ctx.author.id == 758961658634043412:
        await ctx.send(message)
        await ctx.message.delete()
    else:
        await ctx.send("You are not authorized to use this command.")

@bot.command(name="roll", description="Rolls dice (example: py roll 2d6+3).")
async def roll(ctx, dice_string: str):
    try:
        import random
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
            await ctx.send("Number of dice and die type must be greater than 0.")
            return

        rolls = [random.randint(1, die_type) for _ in range(num_dice)]
        total = sum(rolls) + modifier

        await ctx.send(f"Roll: {rolls}, Total: {total}")
    except ValueError:
        await ctx.send("Invalid dice format. Example: `2d6` or `1d20+5`.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@bot.command(name="base64encode", description="Encodes text to Base64.")
async def base64encode(ctx, *, text: str):
    encoded_bytes = base64.b64encode(text.encode('utf-8'))
    encoded_text = encoded_bytes.decode('utf-8')
    await ctx.send(f"Encoded: ```{encoded_text}```")

@bot.command(name="base64decode", description="Decodes text from Base64.")
async def base64decode(ctx, *, text: str):
    try:
        decoded_bytes = base64.b64decode(text.encode('utf-8'))
        decoded_text = decoded_bytes.decode('utf-8')
        await ctx.send(f"Decoded: ```{decoded_text}```")
    except Exception:
        await ctx.send("Invalid text for Base64 decode.")

@bot.command(name="calc", description="Evaluates a mathematical expression (example: py calc 10*5+2).")
async def calc(ctx, *, expression: str):
    try:
        # Only allow basic mathematical operations for security
        allowed_chars = "0123456789+-*/(). "
        if not all(c in allowed_chars for c in expression):
            await ctx.send("Invalid expression. Only numbers and basic operators (+-*/()) are allowed.")
            return
        result = eval(expression)
        await ctx.send(f"Result: {result}")
    except Exception:
        await ctx.send("Invalid mathematical expression.")

@bot.command(name="encrypt", description="Encrypts text using a passphrase.")
async def encrypt(ctx, passphrase: str, *, text: str):
    try:
        import hashlib
        key = base64.urlsafe_b64encode(hashlib.sha256(passphrase.encode()).digest())
        f = Fernet(key)
        encrypted_text = f.encrypt(text.encode()).decode()
        await ctx.send(f"Encrypted: ```{encrypted_text}```")
    except Exception as e:
        await ctx.send(f"Failed to encrypt: {e}")

@bot.command(name="decrypt", description="Decrypts text using a passphrase.")
async def decrypt(ctx, passphrase: str, *, encrypted_text: str):
    try:
        import hashlib
        key = base64.urlsafe_b64encode(hashlib.sha256(passphrase.encode()).digest())
        f = Fernet(key)
        decrypted_text = f.decrypt(encrypted_text.encode()).decode()
        await ctx.send(f"Decrypted: ```{decrypted_text}```")
    except Exception as e:
        await ctx.send(f"Failed to decrypt: {e}")

@bot.command(name="search", description="Searches on DuckDuckGo.")
async def search(ctx, *, query: str):
    try:
        results = DDGS().text(query=query, max_results=3)
        if results:
            response_message = "**Search Results:**\n"
            for i, result in enumerate(results):
                response_message += f"{i+1}. [{result['title']}]({result['href']})\n{result['body']}\n\n"
            await ctx.send(response_message)
        else:
            await ctx.send("No results found.")
    except Exception as e:
        await ctx.send(f"An error occurred during search: {e}")

@bot.command(name="chat", description="Interacts with the AI.")
async def chat(ctx, *, message: str):
    loading_message = await ctx.send("Loading...")
    response = chat_with_together(message)
    await loading_message.edit(content=response)

@bot.command(name="clear", description="Clears messages in the channel.")
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: Optional[str] = None):
    if amount is None or amount.lower() == "all":
        limit = None  # No limit, clear all
        await ctx.send("Clearing all messages... This might take a while.")
    else:
        try:
            amount = int(amount)
            if amount <= 0:
                await ctx.send("Amount must be a positive number.")
                return
            if amount > 1000: # Limit to prevent accidental mass deletion
                await ctx.send("Cannot clear more than 1000 messages at once.")
                return
            limit = amount + 1 # +1 to delete the command message itself
        except ValueError:
            await ctx.send("Invalid amount. Please provide a number or 'all'.")
            return

    try:
        deleted = await ctx.channel.purge(limit=limit)
        if limit is None:
            await ctx.send(f"Cleared all messages.", delete_after=5)
        else:
            await ctx.send(f"Cleared {len(deleted) - 1} messages.", delete_after=5)
    except discord.Forbidden:
        await ctx.send("I don't have permissions to delete messages.")
    except discord.HTTPException as e:
        await ctx.send(f"An error occurred while clearing messages: {e}")
    except Exception as e:
        await ctx.send(f"An unexpected error occurred: {e}")

@bot.command(name="setprefix", description="Sets a custom prefix for this server.")
@commands.has_permissions(manage_guild=True)
async def setprefix(ctx, new_prefix: str):
    if len(new_prefix) > 10:
        await ctx.send("Prefix cannot be longer than 10 characters.")
        return
    await database.set_prefix(ctx.guild.id, new_prefix)
    await ctx.send(f"Prefix for this server has been set to `{new_prefix}`")

@bot.command(name="kick", description="Kicks a member from the server.")
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason: Optional[str] = "No reason provided."):
    try:
        await member.kick(reason=reason)
        await ctx.send(f"Successfully kicked {member.display_name} for: {reason}")
    except discord.Forbidden:
        await ctx.send("I don't have permissions to kick members.")
    except discord.HTTPException as e:
        await ctx.send(f"An error occurred while kicking: {e}")

@bot.command(name="ban", description="Bans a member from the server.")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason: Optional[str] = "No reason provided."):
    try:
        await member.ban(reason=reason)
        await ctx.send(f"Successfully banned {member.display_name} for: {reason}")
    except discord.Forbidden:
        await ctx.send("I don't have permissions to ban members.")
    except discord.HTTPException as e:
        await ctx.send(f"An error occurred while banning: {e}")

# Run the bot
if DISCORD_TOKEN:
    bot.run(DISCORD_TOKEN)
else:
    print("DISCORD_TOKEN not found in .env file. Please set it.")
