import discord as Discord
import json
import os
import config
import datetime
import random
import pymysql
import re

from discord.ext import menus, commands

# Connect to MySQL server for price data
CONN = pymysql.connect(host='127.0.0.1', user='root', passwd=None, db='mysql',
                       charset='utf8')
CUR = CONN.cursor()
CUR.execute("USE scrap")
random.seed(datetime.datetime.now())
def store(title, content):
    CUR.execute('INSERT INTO Week_deals (title, content) VALUES '' ("%s", "%s")', (title, content))
    CUR.connection.commit()



class Test:
    def __init__(self, key, value):
        self.key = key
        self.value = value

PRICE_DATA = []
for price_file in os.listdir(config.PRICE_DATA_DIR):
    with open(f"{config.PRICE_DATA_DIR}/{price_file}", "r") as stream:
        PRICE_DATA += json.load(stream)

for price_dict in PRICE_DATA:
    DATA = []
    DATA += [
        Test(key=key, value=value)
        for key in price_dict
        for value in range(20)
    ]

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
        pages = menus.MenuPages(source=Source(DATA, key=lambda t: t.key, per_page=12), clear_reactions_after=True)
        await pages.start(ctx)



def setup(bot):
    bot.add_cog(DealsMenu(bot))
