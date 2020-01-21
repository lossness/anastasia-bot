import logging
import os
import discord
import json
import asyncio

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

# record logging info to a file
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# bot commands must start with this char
bot = commands.Bot(command_prefix='$')

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

@bot.command(name='price', help='responds with current value of a given cryptocurrency')
async def get_price(ctx, arg):
    response = cmc_quote(arg)
    await ctx.send(response)

@bot.event
async def on_message(message):
    # required commands for on message
    channel = message.channel
    await bot.process_commands(message)
    # defines a check to see if the person respond to the bots commands typed yes or no and if they are the caller of the command
    def check_for_yes_and_is_author(msg):
        return msg.content.lower() == 'yes' and msg.channel == channel and command_user == str(message.author.id)

    def check_for_no_and_is_author(msg):
        return msg.content.lower() == 'no' and msg.channel == channel and command_user == str(message.author.id)
    
    # a check to see if the mentioned user has a phone number in their profile
    def check_for_phone_number(msg):
        return bool(len(msg.content) == 10) and msg.channel == channel and command_user == str(message.author.id)

    # Opens the user profiles and defines listening*(?) variables set by messages in chat
    with open(USER_INFO) as users_info_json:
        profiles = json.load(users_info_json)
    
    # cant remember why I did this.  Come back and edit when known
    mentioned_users_int = message.raw_mentions
    mentioned_users_str = str(message.raw_mentions)
    # checks chat if a @mentioned user has a profile setup for the bot to text
    if bool(any(t in mentioned_users_str for t in profiles.keys())):
        try:
            await channel.send("Would you also like to text this person(s)? Type yes if so.")

            if await bot.wait_for('message', check=check_for_yes_and_is_author, timeout=15) is not None:
                for user in mentioned_users_int:
                    if profiles[str(user)]['carrier_gateway'] is not "":
                        send_text(profiles[str(user)]['phone'], profiles[str(user)]['carrier_gateway'], message.clean_content)
                        await channel.send('Sent text!')
                    else:
                        await channel.send('This user does not have a complete sms profile on file. Users can add a carrier to their profiles with the $carrier command, which allows them to receive texts when someone mentions them in the channel.')

            else:
                if await bot.wait_for('message', check=check_for_no_and_is_author, timeout=15) is not None:
                    await channel.send("Fine.")

        except asyncio.TimeoutError:
            await channel.send("...")

    # Reponse when the mentioned user doesn't have a user profile for the bot to text. 
    elif bool(any(t in mentioned_users_str for t in profiles.keys())) == False and len(mentioned_users_str) >= 18:
        await channel.send("Mentioned user(s) do not have text notifications setup. Encourage them to setup a profile with the $carrier command, which allows them to receive texts when someone mentions them in the channel.")

    # Begins the user profile setup
    elif message.content.startswith('$carrier'):
        with open(CARRIER_INFO_FILE) as carrier_info_json:
            carriers = json.load(carrier_info_json)
        command_user = str(message.author.id)
        if command_user not in profiles.keys():
            try:
                await channel.send('Seems youre new here.  Would you like to proceed with account creation? Type yes or no.')
                # this checks if the user answered yes to proceeding with user profile creation
                if await bot.wait_for('message', check=check_for_yes_and_is_author, timeout=15) is not None:
                    await channel.send('Whats your phone number? Please reply with just the numbers, no dots or dashes and include the area code.')
                    phone_answer = await bot.wait_for('message', check=check_for_phone_number, timeout=30)
                    
                    if phone_answer.content is not None and len(phone_answer.content) == 10:
                        profiles[command_user] = {'phone': phone_answer.content, 'carrier_gateway': ''}
                        with open(USER_INFO, "w") as new_user_json:
                            json.dump(profiles, new_user_json, indent=2)
                        await channel.send('Phone number added!')

                # the response from the bot if the user answers no to being asked if they would like to setup a user profile
                elif await bot.wait_for('message', check=check_for_no_and_is_author, timeout=15) is not None:
                    await channel.send("Suit yourself.")
                    return
            except asyncio.TimeoutError:
                await channel.send("You took too long to reply!")
        else:
            try:
                number = 0
                carrier_list = ""
                embed = discord.Embed()

                for key in carriers.keys():
                    number += 1
                    carrier_list += "{}.{}\n".format(number, key)

                embed.add_field(name="Pick a carrier below. Simply type the number!", value=carrier_list, inline=True)
                await channel.send(embed=embed)

                c_list = list(carriers)
                max_range_list = len(c_list)
                range_list = [i for i in range(1, max_range_list)]

                def check_for_carrier(m):
                    return m.content in str(range_list) and m.channel == channel

                carrier_answer = await bot.wait_for('message', check=check_for_carrier, timeout=30)

                if carrier_answer.content is not None and len(carrier_answer.content) <= 3:
                    profiles[command_user]['carrier_gateway'] += carriers["{}".format(c_list[int(carrier_answer.content)-1])]
                    with open(USER_INFO, "w") as user_json_file:
                        json.dump(profiles, user_json_file, indent=2)
                    await channel.send('Carrier added to your profile!')
            except asyncio.TimeoutError:
                await channel.send("You took too long!")
    else:
        return

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    raise error

bot.run(TOKEN)
