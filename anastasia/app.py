import os
import datetime

from discord.ext import commands
from dotenv import load_dotenv


# load discord token from env file
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# BOT commands must start with this character
BOT = commands.Bot(command_prefix='$')

@BOT.command()
async def load(ctx, extension):
    BOT.load_extension(f'cogs.{extension}')

@BOT.command()
async def unload(ctx, extension):
    BOT.load_extension(f'cogs.{extension}')

for filename in os.listdir('./anastasia/cogs'):
    if filename.endswith('.py'):
        BOT.load_extension(f'cogs.{filename[:-3]}')

@BOT.event
async def on_ready():
    print(f'{BOT.user.name} has come online at {datetime.datetime.now()}')

@BOT.event
async def on_disconnect():
    print(f'{BOT.user.name} has disconnected at {datetime.datetime.now()}')

@BOT.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    raise error

BOT.run(TOKEN)
