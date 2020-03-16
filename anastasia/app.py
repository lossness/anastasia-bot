import os
import datetime
import yaml

from discord.ext import commands, menus
from dotenv import load_dotenv
from cogs.utils.nmtchatbot.inference import inference


# load discord token from env file
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# load yaml config file
try:
    with open("./config.yaml", "r") as file:
        config = yaml.safe_load(file)
except Exception as e:
    print("Error reading the config file")


# bot commands must start with this character
bot = commands.Bot(command_prefix='$')

for filename in os.listdir('./anastasia/cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')

@bot.event
async def on_ready():
    print(f'{bot.user.name} has come online at {datetime.datetime.now()}')

@bot.event
async def on_disconnect():
    print(f'{bot.user.name} has disconnected at {datetime.datetime.now()}')

# @bot.event
# async def on_message(message):
#     channel = message.channel
#     await bot.process_commands(message)
#     if message.author == bot.user or message.author.bot is True:
#         return


#     response = inference("{}".format(message.clean_content))
#     await channel.send("{}".format(response['answers'][0]))



@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    raise error

bot.run(TOKEN)
