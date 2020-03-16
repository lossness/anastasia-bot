from discord.ext import menus, commands
import discord as Discord

class Test:
    def __init__(self, key, value):
        self.key = key
        self.value = value

data = [Test(key=key, value=value) for key in ['test', 'other', 'okay'] for value in range(20)]

class Source(menus.GroupByPageSource):
    async def format_page(self, menu, entry) -> Discord.Embed:
        joined = '\n'.join(f'{i}. <Test value={v.value}>' for i, v in enumerate(entry.items, start=1))
        body = Discord.Embed(title=f'**{entry.key}**\n{joined}\nPage', description=f'{menu.current_page + 1}/{self.get_max_pages()}')
        return body

class DealsMenu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def deals(self, ctx):
        pages = menus.MenuPages(source=Source(data, key=lambda t: t.key, per_page=12), clear_reactions_after=True)
        await pages.start(ctx)



def setup(bot):
    bot.add_cog(DealsMenu(bot))
