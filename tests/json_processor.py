import json
import config
import os
import time
import sqlite3
import pandas as pd
import datetime

from json import JSONDecodeError, JSONEncoder
from pathlib import Path
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from progress.bar import Bar



# LAST 24HR PRICE DROPS AND LAST 7 DAYS PRICE DROPS URLS
DAY_URL = "http://pcpartpicker.com/products/pricedrop/day/"
WEEK_URL = "http://pcpartpicker.com/products/pricedrop/week/"

def JsonPath(timescale):
    return config.PATH.joinpath('data', 'price_data', f"{timescale}_deals.json")

# Opens a chrome instance with debugging enabled to use selenium without chromedriver
os.startfile(r"C:\Projects\weedmaps_review_bot\data\chrome_shortcut.lnk")
time.sleep(10)

# Initialize selenium webdriver and attaches to chrome.exe using debugger port
CHROME_OPTIONS = Options()
CHROME_OPTIONS.debugger_address = "127.0.0.1:9222"
DRIVER = webdriver.Chrome(
    options=CHROME_OPTIONS,
    executable_path=r"C:\Utility\Browserdrivers\chromedriver.exe",
)

PRODUCT_CATEGORIES = [
    "dg_case", "dg_case-fan", "dg_cpu", "dg_cpu-cooler", "dg_external-hard-drive",
    "dg_headphones", "dg_keyboard", "dg_laptop", "dg_memory", "dg_monitor",
    "dg_motherboard", "dg_mouse", "dg_optical-drive", "dg_power-supply",
    "dg_software", "dg_internal-hard-drive", "dg_ups", "dg_video-card",
    "dg_wired-network-card", "dg_wireless-network-card"
]

def collect_data(url):
    DRIVER.get(url)
    time.sleep(5)
    soup = BeautifulSoup(DRIVER.page_source, 'lxml')
    for category in PRODUCT_CATEGORIES:
        try:
            table = soup.find_all('div', attrs={'id': f'{category}'})[0]
            df = pd.read_html(str(table))

            if url == DAY_URL:
                daily_list = df[0].to_dict(orient='records')
                cleanText(daily_list, "daily", category.replace("dg_", ""))

            elif url == WEEK_URL:
                weekly_list = df[0].to_dict(orient='records')
                cleanText(weekly_list, "weekly", category.replace("dg_", ""))

        except IndexError as index_error:
            print(f"An error has occured: {index_error}")
            print(f"No deals for {category}")
            continue

# subclass JSONEncoder
class DateTimeEncoder(JSONEncoder):
    # override the default method
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()

def cleanText(json_object, timescale, cat) -> list:
    try:
        with open(JsonPath(timescale), "a") as outfile:
            for json_dict in json_object:
                for part_info in json_dict.items():
                    # Remove keys that we do not want in the sqlite database
                    part_info.pop('Unnamed: 7', None)
                    part_info.pop('Promo', None)
                    # Clean up the values of each special
                    part_info['Current'] = part_info['Current'].replace('Current', '')
                    part_info['Drop'] = part_info['Drop'].replace('Drop', '')
                    part_info['Item'] = part_info['Item'].replace('Item ', '')
                    part_info['Previous'] = part_info['Previous'].replace('Previous', '')
                    part_info['Save'] = part_info['Save'].replace('Save', '')
                    part_info['Where'] = part_info['Where'].replace('Where', '')
                    part_info['Date'] = datetime.datetime.now()
                    part_info['Category'] = cat
            json.dump(json_object, outfile, indent=2, sort_keys=True, cls=DateTimeEncoder)
            print(f"    {cat} dumped.")

    except JSONDecodeError as jsonerror:
        print(jsonerror + f"{json_object} contains no data..")


# def checkDate(timescale):
#     with open(JsonPath(timescale), 'r') as fp:
#         json_file = json.load(fp)
#         for part_id, part_info in json_file.items():
#             for key in part_info:
#                 if part_info['Date'][:10] == str(datetime.datetime.now())



collect_data(DAY_URL)
collect_data(WEEK_URL)
DRIVER.quit()






# def collect_data(url):
#     DRIVER.get(url)
#     time.sleep(5)
#     counter = 0
#     soup = BeautifulSoup(DRIVER.page_source, 'lxml')
#     for category in tqdm(PRODUCT_CATEGORIES):
#         try:
#             table = soup.find_all('div', attrs={'id': f'{category}'})[0]
#             df = pd.read_html(str(table))

#             if url == DAY_URL:
#                 day_json = df[0].to_dict()
#                 cleanText(day_json, category, 'daily_deals.db')

#             elif url == WEEK_URL:
#                 week_json = df[0].to_dict()
#                 cleanText(week_json, category, 'weekly_deals.db')

#             counter += 1
#         except IndexError as index_error:
#             print(f"An error has occured: {index_error}")
#             continue
#         finally:
#             DRIVER.quit()


# def cleanText(json_object, cat, db_name):
#     try:
#         db_name_one = db_name
#         conn = sqlite3.connect(db_name_one)
#         c = conn.cursor()
#         print("Successfully connected to SQLite")
#         table_name = cat.replace("dg_", "")
#         create_table_query = f'''CREATE TABLE {table_name} (
#                                   Item TEXT PRIMARY KEY NOT NULL,
#                                   Previous TEXT NOT NULL,
#                                   Current TEXT NOT NULL,
#                                   Drop TEXT NOT NULL,
#                                   Save TEXT NOT NULL,
#                                   Where TEXT NOT NULL,
#                                   Date datetime);'''
#         c.execute(create_table_query)
#         print("SQLite table created")
#         for part in json_object:
#             # Remove keys that we do not want in the sqlite database
#             part.pop('Unnamed: 7', None)
#             part.pop('Promo', None)
#             # Clean up the values of each special
#             part['Current'] = part['Current'].replace('Current', '')
#             part['Drop'] = part['Drop'].replace('Drop', '')
#             part['Item'] = part['Item'].replace('Item ', '')
#             part['Previous'] = part['Previous'].replace('Previous', '')
#             part['Save'] = part['Save'].replace('Save', '')
#             part['Where'] = part['Where'].replace('Where', '')
#             table_name = cat.replace("dg_", "")
#             create_values = f"insert into {table_name} values (?,?,?,?,?,?)"
#             c.execute(create_values, json.dumps(json_object, sort_keys=True))
#     except JSONDecodeError as jsonerror:
#         print(jsonerror + f"{json_object} contains no data..")

#     finally:
#         conn.close()


# collect_data(DAY_URL)
# collect_data(WEEK_URL)

