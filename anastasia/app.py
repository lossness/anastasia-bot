import logging
import os
import discord
import importlib
import json
import asyncio

from cmc_price import cmc_quote
from discord.ext import commands
from dotenv import load_dotenv
from data import sms_info
from sms_on_mention import send_text

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

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
    channel = message.channel
    with open("anastasia\\data\\user_info.json") as users_info_json:
        profiles = json.load(users_info_json)
    mentioned_users_int = message.raw_mentions
    mentioned_users_str = str(message.raw_mentions)
    await bot.process_commands(message)
    if message.author == bot.user:
        return
    elif bool(any(t in mentioned_users_str for t in profiles.keys())) == True:
        try:
            await channel.send("Would you also like to text this person(s)? Type yes if so.")

            def check_for_yes(m):
                return m.content == 'yes' and m.channel == channel

            msg = await bot.wait_for('message', check=check_for_yes, timeout=15)
            if msg is not None:
                for user in mentioned_users_int:
                    if profiles[str(user)]['carrier_gateway'] is not "":
                        send_text(profiles[str(user)]['phone'], profiles[str(user)]['carrier_gateway'], message.clean_content)
                        await channel.send('Sent text!')
                        return
                    else:
                        await channel.send('This user does not have a complete sms profile on file. Users can add a carrier to their profiles with the $carrier command.')
                        return
        except asyncio.TimeoutError:
            await channel.send("You took too long to reply.")  
    elif bool(any(t in mentioned_users_str for t in profiles.keys())) != False and len(mentioned_users_str) >= 18:
        await channel.send("Mentioned user(s) do not have text notifications setup. Encourage them to setup a profile with the $carrier command!")
    elif message.content.startswith('$carrier'):
        with open("anastasia\\data\\carrier_info.json") as carrier_info_json:
            carriers = json.load(carrier_info_json)
        command_user = str(message.author.id)
        if command_user not in profiles.keys():
            try:
                await channel.send('I dont know who the fuck you are.. you will need to add a sms profile.  Is this something you wanna do right now? Type yes if so.')
                def check_for_yes_user_profile(m):
                    return m.content == 'yes' and m.channel == channel and command_user == str(message.author.id)

                user_profile_answer = await bot.wait_for('message', check=check_for_yes_user_profile, timeout=30)
                
                if user_profile_answer.content is not None and len(user_profile_answer.content) <= 3:
                    await channel.send('Whats your phone number? Please reply with just the numbers, no dots or dashes and include the area code.')
                    def check_for_phone_number(m):
                        return bool(len(m.content) == 10) and m.channel == channel and command_user == str(message.author.id)

                    phone_answer = await bot.wait_for('message', check=check_for_phone_number, timeout=30)
                    
                    if phone_answer.content is not None and len(phone_answer.content) == 10:
                        profiles[command_user] = {'phone': phone_answer.content, 'carrier_gateway': ''}
                        with open("anastasia\\data\\user_info.json", "w") as new_user_json:
                            json.dump(profiles, new_user_json, indent=2)
                        await channel.send('Phone number added!')
                        return
                    else:
                        return
                else:
                    return        
            except asyncio.TimeoutError: # add more exceptions fucker
                await channel.send("You took too long to reply!")
            finally:
                return
        else:
            try:
                number = 0
                carrier_list = ""
                embed = discord.Embed()
                for key in carriers.keys():
                    number += 1
                    carrier_list += "{}.{}\n".format(number,key)
                embed.add_field(name="Pick a carrier below. Simply type the number!",value=carrier_list,inline=True)
                await channel.send(embed=embed)
                c_list = list(carriers)
                max_range_list = len(c_list)
                range_list = [i for i in range(1, max_range_list)]
                def check_for_carrier(m):
                    return m.content in str(range_list) and m.channel == channel

                carrier_answer = await bot.wait_for('message', check=check_for_carrier, timeout=30)
                if carrier_answer.content is not None and len(carrier_answer.content) <= 3:
                    profiles[command_user]['carrier_gateway'] += carriers["{}".format(c_list[int(carrier_answer.content)-1])]
                    with open("anastasia\\data\\user_info.json", "w") as user_json_file:
                        json.dump(profiles, user_json_file, indent=2)
                    await channel.send('Carrier added to your profile!')
                    return 
            except asyncio.TimeoutError:
                await channel.send("You took too long!")
            finally:
                return
    else:
        return
        



bot.run(token)
