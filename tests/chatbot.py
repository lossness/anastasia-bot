import sys

from discord.ext import commands

from utils.nmtchatbot import inference as nmt


sys.path.append("./utils/")

class Chatbot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        channel = message.channel

        if message.author == self.bot.user or message.author.bot is True:
            return

        await channel.send("Starting chatbot..")
        response = nmt.inference("Hello!")
        await channel.send("{}".format(response))

def setup(bot):
    bot.add_cog(Chatbot(bot))
