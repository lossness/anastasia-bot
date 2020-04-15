import datetime
import time
import os
import re

import pandas as pd
import numpy as np
import discord as Discord
from discord.ext import commands, menus
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from progressbar import progressbar

import config


# LAST 24HR PRICE DROPS AND LAST 7 DAYS PRICE DROPS URLS
DAY_URL = "http://pcpartpicker.com/products/pricedrop/day/"
WEEK_URL = "http://pcpartpicker.com/products/pricedrop/week/"

# function to pass csv file paths to the functions below
def csv_path(timescale):
    return config.PATH.joinpath("data", "price_data", f"{timescale}_deals.csv")

# all the HTML id's used on pcpartpicker for each category
PRODUCT_CATEGORIES = [
    "dg_case",
    "dg_case-fan",
    "dg_cpu",
    "dg_cpu-cooler",
    "dg_external-hard-drive",
    "dg_headphones",
    "dg_keyboard",
    "dg_laptop",
    "dg_memory",
    "dg_monitor",
    "dg_motherboard",
    "dg_mouse",
    "dg_optical-drive",
    "dg_power-supply",
    "dg_software",
    "dg_internal-hard-drive",
    "dg_ups",
    "dg_video-card",
    "dg_wired-network-card",
    "dg_wireless-network-card",
]

# global dataframes to append price data to in collect_data function
RESULTS_DAILY_DF_DATE = pd.DataFrame()
RESULTS_WEEKLY_DF_DATE = pd.DataFrame()

class DealsMenu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def deals(self, ctx):
        message = ctx.message
        channel = message.channel

        def collect_data(url):
            driver.get(url)
            time.sleep(5)
            soup = BeautifulSoup(driver.page_source, "lxml")

            for category in progressbar(PRODUCT_CATEGORIES):
                try:
                    table = soup.find_all("div", attrs={"id": f"{category}"})[0]
                    df = pd.read_html(str(table))

                    if url == DAY_URL:
                        global RESULTS_DAILY_DF_DATE
                        daily_list = df[0].to_dict(orient="records")
                        clean_DAILY_DF_DATE = pd.DataFrame(
                            data=clean_text(daily_list, category.replace("dg_", ""))
                        )
                        RESULTS_DAILY_DF_DATE = RESULTS_DAILY_DF_DATE.append(clean_DAILY_DF_DATE)

                    if url == WEEK_URL:
                        global RESULTS_WEEKLY_DF_DATE
                        weekly_list = df[0].to_dict(orient="records")
                        clean_WEEKLY_DF_DATE = pd.DataFrame(
                            data=clean_text(weekly_list, category.replace("dg_", ""))
                        )
                        RESULTS_WEEKLY_DF_DATE = RESULTS_WEEKLY_DF_DATE.append(clean_WEEKLY_DF_DATE)

                except IndexError:
                    continue

            if url == DAY_URL:
                RESULTS_DAILY_DF_DATE.to_csv(csv_path("daily"))
                print(f"\nDaily discounts updated at {datetime.datetime.now()}")

            if url == WEEK_URL:
                RESULTS_WEEKLY_DF_DATE.to_csv(csv_path("weekly"))
                print(f"\nWeekly discounts updated at {datetime.datetime.now()}")


        def clean_text(list_object, cat) -> list:
            for part_info in list_object:
                # Remove keys that we do not want in the sqlite database
                part_info.pop("Unnamed: 7", None)
                part_info.pop("Promo", None)
                # Clean up the values of each special
                part_info["Current"] = part_info["Current"].replace("Current", "")
                part_info["Drop"] = part_info["Drop"].replace("Drop", "")
                part_info["Item"] = part_info["Item"].replace("Item ", "")
                part_info["Previous"] = part_info["Previous"].replace("Previous", "")
                part_info["Save"] = part_info["Save"].replace("Save", "")
                part_info["Where"] = part_info["Where"].replace("Where", "")
                part_info["Date"] = datetime.datetime.now()
                part_info["Category"] = cat
            return list_object


        DAILY_DF_DATE = pd.read_csv(csv_path("daily"), usecols=["Date"])
        WEEKLY_DF_DATE = pd.read_csv(csv_path("weekly"), usecols=["Date"])
        NOW = datetime.datetime.now()

        class Scraper():

            @staticmethod
            async def check_date(collect_function, dataframe, url):
                dataframe_dict = dataframe.to_dict()
                print("\nChecking if the data has been updated since yesterday")
                await channel.send("Checking if the data has been updated since yesterday.")
                status = ""
                for values in progressbar(dataframe_dict.values()):
                    for value in values.values():
                        if value.startswith(str(NOW)[:10]):
                            status = "ok"
                            print("\nData up to date!")
                            await channel.send("Data up to date!")
                            break
                if status != "ok":
                    try:
                        # Opens a chrome window with debugging enabled to use selenium without chromedriver
                        print("\nData out of date, intilizing fresh data scraper..")
                        await channel.send("Data out of date, scraping fresh data..")
                        os.startfile(r"C:\Projects\weedmaps_review_bot\data\chrome_shortcut.lnk")
                        time.sleep(10)
                        chrome_options = Options()
                        chrome_options.debugger_address = "127.0.0.1:9222"
                        global driver
                        driver = webdriver.Chrome(
                            options=chrome_options,
                            executable_path=r"C:\Utility\Browserdrivers\chromedriver.exe",
                        )
                        collect_function(url)
                        return

                    finally:
                        await channel.send("Price data has been updated.")
                        print("\nPrice data has been updated")
                        driver.close()
                        driver.quit()

                else:
                    return

        await Scraper.check_date(collect_data, WEEKLY_DF_DATE, WEEK_URL)
        await Scraper.check_date(collect_data, DAILY_DF_DATE, DAY_URL)

        df_csv = pd.read_csv(csv_path("daily"))
        df_csv_weekly = pd.read_csv(csv_path("weekly"))

        daily_price_dict = df_csv.to_dict(orient='records')
        daily_price_categories = np.array([sub['Category'] for sub in daily_price_dict])
        unique_daily_categories = list(np.unique(daily_price_categories))

        weekly_price_dict = df_csv_weekly.to_dict(orient='records')
        weekly_price_categories = np.array([sub['Category'] for sub in weekly_price_dict])
        unique_weekly_categories = list(np.unique(weekly_price_categories))
        price_dicts = [daily_price_dict, weekly_price_dict]
        filtered_keys_list = ['Item', 'Previous', 'Drop', 'Current', 'Save', 'Where']

        print("penis")
        def filter_text(dict_list, categories_list):
            cat_deals = list(filter(lambda d: d['Category'] in categories_list, dict_list))
            ordered_deals = list()
            for deal in progressbar(cat_deals):
                # creates an ordered list by filtered_keys_list of all dict keys and values in string format
                ordered_deals.append(str(dict((k, deal[k]) for k in filtered_keys_list if k in deal)))
                for deal_str in ordered_deals:
                    # strips our list of strings of all unnessary characters (' { } :) and
                    # words. patt is created as an object to pass to sub
                    word_pattern = re.compile('(Item|Previous|Drop|Current|Where)')
                    # substitutes the above words with blank
                    deal_str = word_pattern.sub('', deal_str)
                    character_pattern = re.compile(r"['{}:]")
                    deal_str = character_pattern.sub('', deal_str)
            return ordered_deals

        
        test_text = filter_text(daily_price_dict, unique_daily_categories)
        print(test_text)
        # class Test:
        #     def __init__(self, key, value):
        #         self.key = key
        #         self.value = value

        # for price_dict in price_dicts:
        #     for price_data in price_dict:
        #         data = []
        #         data += [
        #             Test(key=key, value=value)
                    
        #             for value in range(20)
        # #         ]
 
        # def filterCategories(dicts_list, categories_list):
        #     # returns list of dicts with values in the category key matching values 
        #     # provided in the key_val_list
        #     for deal_category in categories_list:
        #         catorgized_list = list(filter(lambda d: d['Category'] in [deal_category], dicts_list))
        #         filtered_list = list(filter(lambda d: ))

        class Source(menus.GroupByPageSource):
            async def format_page(self, menu, entry) -> Discord.Embed:
                for price_dict in entry:
                    for price_data in price_dict:
                        joined = '\n'.join(f"{i}. {v.value}" for i, v in enumerate(price_data.items, start=1))
                        body = Discord.Embed(title=f'**Daily Deals**\n{joined}\nPage', description=f'{menu.current_page + 1}/{self.get_max_pages()}')
                return body

        #  start cog after all the above code has finished
        pages = menus.MenuPages(source=Source(price_dicts, key=lambda t: t.key, per_page=12), clear_reactions_after=True)
        await pages.start(ctx)
     

def setup(bot):
    bot.add_cog(DealsMenu(bot))



        # class Source(menus.GroupByPageSource):
        #     async def format_page(self, menu, entry) -> Discord.Embed:
        #         joined = '\n'.join(f'{i}. <Test value={v.value}>' for i, v in enumerate(entry.items, start=1))
        #         body = Discord.Embed(title=f'**{entry.key}**\n{joined}\nPage', description=f'{menu.current_page + 1}/{self.get_max_pages()}')
        #         return body

        # start cog after all the above code has finished
        # pages = menus.MenuPages(source=Source(price_dicts,key=for price_dict in entry per_page=12), clear_reactions_after=True)
        # await pages.start(ctx)

                # class Test:
        #     def __init__(self, value):
        #         self.value = value

        #     def __repr__(self):
        #         for price_dict in price_dicts:
        #             for price_data in price_dict:
        #                 if item[0] in price_data.items() == 'Category':

        #                 return f'{item for item in price_data.items()}={self.value}'

        # async def generate(number):
        #     for i in range(number):
        #         yield Test(i)

        # class Source(menus.AsyncIteratorPageSource):
        #     def __init__(self):
        #         super().__init__(generate(9), per_page=4)

        #     async def format_page(self, menu, entries):
        #         start = menu.current_page * self.per_page
        #         joined = f'\n'.join(f'{i}. {v!r}' for i, v in enumerate(entries, start=start))
        #         body = Discord.Embed(title=f'**TEST**\n{joined}\nPage', description=f'{menu.current_page + 1}/{self.get_max_pages()}')
        #         return body

        # pages = menus.MenuPages(source=Source(), clear_reactions_after=True)
        # await pages.start(ctx)