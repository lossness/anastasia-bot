import logging
import os
import discord
import json
import asyncio
import datetime
import io

from pathlib import Path
from cmc_price import cmc_quote
from discord.ext import commands
from dotenv import load_dotenv
from sms_on_mention import send_text


# load discord token from env file
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# bot commands must start with this character
bot = commands.Bot(command_prefix='$')
THE_TIME = datetime.datetime.now()

# load cogs
bot.load_extension("cogs.ProfileSetup")

# prints that the bot has connected to discord and is ready to accept commands
@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord at {THE_TIME}!')

# prints the bot has been disconnected from the server and at what time
@bot.event
async def on_disconnect():
    print(f'{bot.user.name} has disconnected from Discord at {THE_TIME}.')


@bot.command(name='price', help='responds with current value of a given cryptocurrency')
async def get_price(ctx, arg):
    response = cmc_quote(arg)
    await ctx.send(response)



@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    raise error

bot.run(TOKEN)