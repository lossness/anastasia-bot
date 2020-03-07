import discord
import os
import io
import json
import asyncio

from discord.ext import commands


# define paths to config files
USER_INFO_PATH = os.path.abspath("./anastasia/data/")
CARRIER_INFO_FILE = "./anastasia/data/carrier_info.json"
YES_FILE = "./anastasia/data/yes_word.txt"


def startup_check(path: str):
    """ this checks if user_info.json exists
    if not, creates one. """
    if os.path.isfile(f"{path}/user_info.json") and os.access(path, os.R_OK):
        print("User file found, loading..")
        return
    else:
        print("User data file missing, creating one..")
        with io.open(os.path.join(path, 'user_info.json'), 'w') as db_file:
            db_file.write(json.dumps({}))

startup_check(USER_INFO_PATH)  
# this is the user_info.json path.  We will use this to load into the program
# as a dict.          
USER_INFO = f"{USER_INFO_PATH}/user_info.json"


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


class Carrier(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    async def carrier(self, ctx):
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
                    phone_number_answer = await (self.bot.wait_for('message', timeout=30.0))

                    if check_valid_phone(phone_number_answer) is False:
                        raise continue_counter

                    if check_valid_phone(phone_number_answer):
                        await channel.send("{}. Is this correct?".format(phone_number_answer.content))
                        confirm_correct = await self.bot.wait_for('message', timeout=10.0)
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
            msg_reply = await self.bot.wait_for("message", timeout=15)

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

                    carrier_answer = await self.bot.wait_for('message', check=check_for_carrier, timeout=30)

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

def setup(bot):
    bot.add_cog(Carrier(bot))
