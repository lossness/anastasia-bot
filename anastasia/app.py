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

# path variables
# USER_INFO = "/home/pi/anastasia-bot/anastasia/data/user_info.json"
# CARRIER_INFO_FILE = "/home/pi/anastasia-bot/anastasia/data/carrier_info.json"
# USER_INFO = r"C:\Projects\Anastasia-bot-master\anastasia\data\user_info.json"

# define paths to config files
BASE_PATH = Path(__file__).parent
USER_INFO_PATH = os.path.abspath((BASE_PATH / "../anastasia/data/").resolve())
CARRIER_INFO_FILE = r"C:\Projects\Anastasia-bot-master\anastasia\data\carrier_info.json"
YES_FILE = r"C:\Projects\Anastasia-bot-master\anastasia\data\yes_word.txt"

def startup_check(path: str):
    """ this checks if user_info.json exists
    if not, creates one. """
    if os.path.isfile(f"{path}\\user_info.json") and os.access(path, os.R_OK):
        print("User file found, loading..")
        return
    else:
        print("User data file missing, creating one..")
        with io.open(os.path.join(path, 'user_info.json'), 'w') as db_file:
            db_file.write(json.dumps({}))

startup_check(USER_INFO_PATH)  
# this is the user_info.json path.  We will use this to load into the program
# as a dict.          
USER_INFO = f"{USER_INFO_PATH}\\user_info.json"


# record logging info to a file
LOGGER = logging.getLogger('discord')
LOGGER.setLevel(logging.DEBUG)
HANDLER = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
HANDLER.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
LOGGER.addHandler(HANDLER)

# open all our config files
with open(USER_INFO) as user_info_json:
    PROFILES = json.load(user_info_json)

with open(YES_FILE) as f:
    YES_LIST = json.load(f)

with open(CARRIER_INFO_FILE) as f:
    CARRIERS = json.load(f)

# define the following variables for better understanding of 
# what they are used for in the functions that follow
CARRIER_LIST = list(CARRIERS)
MAX_RANGE_LIST = len(CARRIER_LIST)
RANGE_LIST = [i for i in range(1, MAX_RANGE_LIST)]

# bot commands must start with this character
bot = commands.Bot(command_prefix='$')
THE_TIME = datetime.datetime.now()

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
async def on_message(message):
    # required commands for on message
    channel = message.channel
    await bot.process_commands(message)
    if message.author == bot.user:
        return
    # Multiple checks that are run agaisnt user replies
    def check_is_author(msg):
        return msg.channel == channel and str(msg.author.id) == str(message.author.id) 

    def check_for_profile(msg):
        return bool(any(t in str(msg.raw_mentions) for t in PROFILES.keys()))

    def check_for_yes(user_reply):
        yes_options = YES_LIST
        return (bool(any(t in user_reply.content.lower() for t in yes_options and
                         str(user_reply.author.id == str(message.author.id)))))

    def check_for_no(user_reply):
        return bool(user_reply.content.lower() == 'no')

    # cant remember why I did this.  Come back and edit when known
    mentioned_users_int = message.raw_mentions

    # checks chat if a @mentioned user has a profile setup for the bot to text
    if mentioned_users_int:
        await channel.send("Would you also like to text this person(s)? Type yes or no.")
        try:
            msg_reply = await bot.wait_for("message", timeout=15)

            if check_for_no(msg_reply):
                await channel.send("Fine")

            elif (check_for_profile(message) is False and check_is_author(message) is True and
                  check_for_yes(msg_reply) is True):

                await channel.send("This user does not have a texting profile setup."
                                   "  They can setup with the $carrier command.")
                return

            elif check_for_profile(message) and check_is_author(message) and msg_reply is not None:
                if check_for_yes(msg_reply):
                    for user in mentioned_users_int:
                        if PROFILES[str(user)]['carrier_gateway'] is not "":
                            (send_text(PROFILES[str(user)]['phone'], 
                                       PROFILES[str(user)]['carrier_gateway'],
                                       message.clean_content))
                            await channel.send('Sent text!')
                            return
                        else:
                            await channel.send("This user does not have a "
                                               "complete texting profile setup. Setup "
                                               "can be access with the $carrier command.")
                            return
        except asyncio.TimeoutError:
            await channel.send("...")
    else:
        return


@bot.command(name='carrier', help="This command starts the profile setup process to enable text messages on mention.")
async def create_profile(ctx):
    message = ctx.message
    channel = message.channel

    def check_valid_phone(msg):
        return check_is_author(msg) and len(msg.content) == 10

    def check_is_author(msg):
        return msg.channel == channel and str(msg.author.id) == str(message.author.id)

    def check_for_yes(msg):
        yes_options = YES_LIST
        return bool(any(t in msg.content.lower() for t in yes_options))

    def check_for_no(msg):
        return bool(msg.content.lower() == 'no')

    class ContinueCounter(Exception):
        pass

    continue_counter = ContinueCounter

    async def valid_phone(prompt):
        await prompt
        for i in range(6):
            try:
                phone_number_answer = await (bot.wait_for('message', timeout=30.0))

                if check_valid_phone(phone_number_answer) is False:
                    raise continue_counter

                if check_valid_phone(phone_number_answer):
                    await channel.send("{}. Is this correct?".format(phone_number_answer.content))
                    confirm_correct = await bot.wait_for('message', timeout=10.0)
                    if check_for_yes(confirm_correct) is False:
                        raise continue_counter
                    if check_for_yes(confirm_correct):
                        return phone_number_answer

            except ContinueCounter:
                await channel.send("Invalid entry. Type your phone number with "
                                   "no dashes or spaces. {}/6 Attempts.".format(i+1))
                continue
            except asyncio.TimeoutError:
                await channel.send("You took too long, Goodbye.DEBUG=VALID_PHONE")
                break
        else:
            await channel.send("Goodbye.")
            return False


    command_user = str(message.author.id)
    await channel.send("This will setup or edit your texting profile. "
                       "Would you like to continue? Type yes or no.")
    try:
        msg_reply = await bot.wait_for("message", timeout=15)

        if check_for_no(msg_reply):
            await channel.send("Suit yourself.")
            return

        elif check_is_author(msg_reply) and check_for_yes(msg_reply):
            valid_num = None
            valid_num = await valid_phone(channel.send("Whats your phone number? Please reply "
                                                       "with just the numbers, no dots or dashes"
                                                       " and include the area code."))

            if valid_num is not False:
                PROFILES[command_user] = {'phone': valid_num.content, 'carrier_gateway': ''}
                with open(USER_INFO, "w") as new_user_json:
                    json.dump(PROFILES, new_user_json, indent=2)
                await channel.send('Phone number added!')

                # define an empty int and list to add our values to
                number = 0
                carrier_list = ""
                # this embed object will show the carrier list in an embed message in the channel
                embed = discord.Embed()

                # attaches a number to each carrier from our list
                for key in CARRIERS.keys():
                    number += 1
                    carrier_list += "{}.{}\n".format(number, key)
                # adds our numbered list to the embed object.  Sends object to channel
                embed.add_field(name="Pick a carrier below. Simply type the "
                                     "number!", value=carrier_list, inline=True)
                await channel.send(embed=embed)

                # this check will make sure to only create carrier_answer if the users response
                # is a valid choice
                def check_for_carrier(m):
                    return m.content in str(RANGE_LIST) and m.channel == channel

                carrier_answer = await bot.wait_for('message', check=check_for_carrier, timeout=30)

                # checks if carrier answer exists
                if carrier_answer.content is not None and len(carrier_answer.content) <= 3:
                    PROFILES[command_user]['carrier_gateway'] += CARRIERS["{}".format(CARRIER_LIST[int(carrier_answer.content)-1])]

                    with open(USER_INFO, "w") as user_json_file:
                        json.dump(PROFILES, user_json_file, indent=2)

                    await channel.send('Carrier added to your profile! You are now ready '
                                       'to receive a text message when mentioned.')

            else:
                await channel.send("Profile setup terminated.")

    except asyncio.TimeoutError:
        await channel.send("You took too long to reply!")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    raise error

bot.run(TOKEN)