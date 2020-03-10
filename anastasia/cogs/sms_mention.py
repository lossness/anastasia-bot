import asyncio

from discord.ext import commands

from .utils import file_paths, sms_config


class SmsOnMention(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # required commands for on message
        channel = message.channel
        await self.bot.process_commands(message)

        if message.author == self.bot.user or message.author.bot is True or message.clean_content.startswith("pls"):
            return


        # Multiple checks that are run agaisnt user replies
        def check_is_author(msg):
            return msg.channel == channel and str(msg.author.id) == str(message.author.id)

        def check_for_profile(msg):
            return bool(any(t in str(msg.raw_mentions) for t in file_paths.PROFILES.keys()))

        def check_for_yes(user_reply):
            yes_options = file_paths.YES_LIST
            return (bool(any(t in user_reply.content.lower() for t in yes_options and
                            str(user_reply.author.id == str(message.author.id)))))

        def check_for_no(user_reply):
            return bool(user_reply.content.lower() == 'no')

        # cant remember why I did this.  Come back and edit when known
        mentioned_users_int = message.raw_mentions

        # checks chat if a @mentioned user has a profile setup for the self.bot to text
        if mentioned_users_int:
            await channel.send("Would you also like to text this person(s)? Type yes or no.")
            try:
                msg_reply = await self.bot.wait_for("message", timeout=15)

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
                            if file_paths.PROFILES[str(user)]['carrier_gateway'] is not "":
                                (sms_config.send_text(file_paths.PROFILES[str(user)]['phone'],
                                        file_paths.PROFILES[str(user)]['carrier_gateway'],
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

def setup(bot):
    bot.add_cog(SmsOnMention(bot))
