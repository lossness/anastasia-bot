import discord
import json
import asyncio
import config

from discord.ext import commands



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
            return bool(any(t in msg.content.lower() for t in config.YES_LIST))

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
                    config.PROFILES[command_user] = {'phone': valid_num.content, 'carrier_gateway': ''}
                    with open(config.USER_INFO_PATH, "w") as new_user_json:
                        json.dump(config.PROFILES, new_user_json, indent=2)
                    await channel.send('Phone number added!')

                    # define an empty int and list to add our values to
                    number = 0
                    config.CARRIER_LIST = ""
                    # this embed object will show the carrier list in an embed message in the channel
                    embed = discord.Embed()

                    # attaches a number to each carrier from our list
                    for key in config.CARRIERS.keys():
                        number += 1
                        config.CARRIER_LIST += "{}.{}\n".format(number, key)
                    # adds our numbered list to the embed object.  Sends object to channel
                    embed.add_field(name="Pick a carrier below. Simply type the "
                                        "number!", value=config.CARRIER_LIST, inline=True)
                    await channel.send(embed=embed)

                    # this check will make sure to only create carrier_answer if the users response
                    # is a valid choice
                    def check_for_carrier(m):
                        return m.content in str(config.RANGE_LIST) and m.channel == channel

                    carrier_answer = await self.bot.wait_for('message', check=check_for_carrier, timeout=30)

                    # checks if carrier answer exists
                    if carrier_answer.content is not None and len(carrier_answer.content) <= 3:
                        config.PROFILES[command_user]['carrier_gateway'] += config.CARRIERS["{}".format(config.CARRIER_LIST[int(carrier_answer.content)-1])]

                        with open(config.USER_INFO_PATH, "w") as user_json_file:
                            json.dump(config.PROFILES, user_json_file, indent=2)

                        await channel.send('Carrier added to your profile! You are now ready '
                                        'to receive a text message when mentioned.')

                else:
                    await channel.send("Profile setup terminated.")

        except asyncio.TimeoutError:
            await channel.send("You took too long to reply!")

def setup(bot):
    bot.add_cog(Carrier(bot))
