import logging
import os
import discord
import json
import asyncio
import datetime

from cmc_price import cmc_quote
from discord.ext import commands
from dotenv import load_dotenv
from sms_on_mention import send_text


# load discord token from env file
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# path variables
# USER_INFO = "/home/pi/anastasia-bot/anastasia/data/user_info.json"
# CARRIER_INFO_FILE = "/home/pi/anastasia-bot/anastasia/data/carrier_info.json"
USER_INFO = r"C:\Projects\Anastasia-bot-master\anastasia\data\user_info.json"
CARRIER_INFO_FILE = r"C:\Projects\Anastasia-bot-master\anastasia\data\carrier_info.json"
YES_FILE = r"C:\Projects\Anastasia-bot-master\anastasia\data\yes_word.txt"

# record logging info to a file
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# open json files
with open(USER_INFO) as users_info_json:
    PROFILES = json.load(users_info_json)

with open(YES_FILE) as f:
    YES_LIST = json.load(f)

with open(CARRIER_INFO_FILE) as f:
    CARRIERS = json.load(f)
CARRIER_LIST = list(CARRIERS)
MAX_RANGE_LIST = len(CARRIER_LIST)
RANGE_LIST = [i for i in range(1, MAX_RANGE_LIST)]

# bot commands must start with this character
bot = commands.Bot(command_prefix='$')
THE_TIME = datetime.datetime.now()

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord at {THE_TIME}!')

@bot.event
async def on_disconnect():
    print(f'{bot.user.name} has disconnected from Discord at {THE_TIME}.')

@bot.command(name='price', help='responds with current value of a given cryptocurrency')
async def get_price(ctx, arg):
    response = cmc_quote(arg)
    await ctx.send(response)

@bot.event
async def on_message(message):
    # required commands for on message
    channel = message.channel
    if message.author == bot.user:
        return
    # checks if the the reply came from the same person that invoked the bot
    def check_is_author(msg):
        return msg.channel == channel and str(msg.author.id) == str(message.author.id) and bool(any(t in str(msg.raw_mentions) for t in PROFILES.keys()))
  
    # cant remember why I did this.  Come back and edit when known
    mentioned_users_int = message.raw_mentions

    # checks chat if a @mentioned user has a profile setup for the bot to text
    if message.author == bot.user:
        return
    await channel.send("Would you also like to text this person(s)? Type yes if so.")
    try:
        msg_reply = await bot.wait_for("message", check=check_is_author, timeout=15)

        if msg_reply:
            if bool(any(t in msg_reply.content.lower() for t in YES_LIST)):
                for user in mentioned_users_int:
                    if PROFILES[str(user)]['carrier_gateway'] is not "":
                        send_text(PROFILES[str(user)]['phone'], PROFILES[str(user)]['carrier_gateway'], message.clean_content)
                        await channel.send('Sent text!')
                    else:
                        await channel.send('This user does not have a complete sms profile on file. Users can add a carrier to their PROFILES with the $carrier command, which allows them to receive texts when someone mentions them in the channel.')
            
            elif msg_reply.content.lower() == 'no':
                await channel.send("Fine.")
        else:
            await channel.send("This user does not have a texting profile setup.  They can set one up with the $carrier command.")
            return

    except asyncio.TimeoutError:
        await channel.send("...")
    await bot.process_commands(message)



@bot.command(name='carrier', help="This command starts the profile setup process to enable text messages on mention.")
async def create_profile(ctx):
    message = ctx.message
    channel = message.channel
    await bot.process_commands(message)
     # a check to see if the mentioned user has a phone number in their profile
    def check_for_phone_number(msg):
        return bool(len(msg.content) == 10) and msg.channel == channel and str(msg.author.id) == str(message.author.id)
    
    def check_is_author(msg):
        return msg.channel == channel and str(msg.author.id) == str(message.author.id)
  
    command_user = str(message.author.id)
    try:
        msg_reply = await bot.wait_for("message", check=check_is_author, timeout=15)
        if msg_reply:
            if bool(any(t in msg_reply.content.lower() for t in YES_LIST)):
                await channel.send('Whats your phone number? Please reply with just the numbers, no dots or dashes and include the area code.')
                phone_answer = await bot.wait_for('message', check=check_for_phone_number, timeout=30)
                
                if phone_answer.content is not None and len(phone_answer.content) == 10:
                    PROFILES[command_user] = {'phone': phone_answer.content, 'carrier_gateway': ''}
                    with open(USER_INFO, "w") as new_user_json:
                        json.dump(PROFILES, new_user_json, indent=2)
                    await channel.send('Phone number added!')
                    
                # has the user select their carrier from the list
                number = 0
                carrier_list = ""
                embed = discord.Embed()

                for key in CARRIERS.keys():
                    number += 1
                    carrier_list += "{}.{}\n".format(number, key)

                embed.add_field(name="Pick a carrier below. Simply type the number!", value=carrier_list, inline=True)
                await channel.send(embed=embed)

                def check_for_carrier(m):
                    return m.content in str(RANGE_LIST) and m.channel == channel

                carrier_answer = await bot.wait_for('message', check=check_for_carrier, timeout=30)

                if carrier_answer.content is not None and len(carrier_answer.content) <= 3:
                    PROFILES[command_user]['carrier_gateway'] += CARRIERS["{}".format(CARRIER_LIST[int(carrier_answer.content)-1])]
                    with open(USER_INFO, "w") as user_json_file:
                        json.dump(PROFILES, user_json_file, indent=2)
                    await channel.send('Carrier added to your profile!')

            elif msg_reply.content.lower() == 'no':
                await channel.send("Suit yourself.")

    except asyncio.TimeoutError:
        await channel.send("You took too long to reply!")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    raise error

bot.run(TOKEN)
