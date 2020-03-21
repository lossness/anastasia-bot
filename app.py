import os
import sys
import datetime
import logging
import json
import config

from discord.ext import commands
from dotenv import load_dotenv

# from nmtchatbot.inference import inference


# this checks if user_info.json exists
# if not, creates one.
if os.path.isfile(config.USER_INFO_PATH) and os.access(config.USER_INFO_PATH, os.R_OK):
    print("User file found, loading..")
else:
    print("User data file missing, creating one..")
    with open(config.USER_INFO_PATH, 'w') as db_file:
        db_file.write(json.dumps({}))

# Logging saved to discord.log file
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# load discord token from env file
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# bot commands must start with this character
bot = commands.Bot(command_prefix='$')

# list of cogs
initial_extensions = (
    'cogs.cmc_price',
    'cogs.embeded_menus',
    'cogs.profile_setup',
    'cogs.sms_mention',
)

# load cogs
for extension in initial_extensions:
    try:
        bot.load_extension(extension)
    except Exception as e:
        print(f'Failed to load extension {extension}.', file=sys.stderr)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has come online at {datetime.datetime.now()}')

@bot.event
async def on_disconnect():
    print(f'{bot.user.name} has disconnected at {datetime.datetime.now()}')

@bot.event
async def on_message(message):
    await bot.process_commands(message)
#     response = inference("{}".format(message.clean_content))
#     await channel.send("{}".format(response['answers'][0]))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    raise error

bot.run(TOKEN)
