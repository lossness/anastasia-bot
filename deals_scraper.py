import json
import config
import os
import time
import sqlite3
import pandas as pd

from json import JSONDecodeError
from pathlib import Path
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup


# LAST 24HR PRICE DROPS AND LAST 7 DAYS PRICE DROPS URLS
DAY_URL = "https://pcpartpicker.com/products/pricedrop/day/"
WEEK_URL = "https://pcpartpicker.com/products/pricedrop/week/"

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
    counter = 0
    soup = BeautifulSoup(DRIVER.page_source, 'lxml')
    for category in PRODUCT_CATEGORIES:
        try:
            table = soup.find_all('div', attrs={'id': f'{category}'})[0]
            for df in pd.read_html(str(table)):
                if url == DAY_URL:
                    # opens file if exists, else creates file
                    connex = sqlite3.connect("daily_deals.db")
                    # this object lets us send msgs to our DB and receive results
                    cur = connex.cursor()
                    df.to_sql(name=f"{category}", con=connex, if_exists="replace")
                elif url == WEEK_URL:
                    connex = sqlite3.connect("weekly_deals.db")
                    cur = connex.cursor()
                    df.to_sql(name=f"{category}", con=connex, if_exists="replace")
                counter += 1
        except IndexError:
            continue
        finally:
            print("done")
            connex.close()


collect_data(DAY_URL)
collect_data(WEEK_URL)


def cleanText(directory, file_name):
    try:
        with open(f"{directory}/{file_name}") as f:
            json_file = json.load(f)
            for element in json_file:
                # Remove keys that we do not want in the sqlite database
                element.pop('Unnamed: 7', None)
                element.pop('Promo', None)
                # Clean up the values of each special
                element['Current'] = element['Current'].replace('Current', '')
                element['Drop'] = element['Drop'].replace('Drop', '')
                element['Item'] = element['Item'].replace('Item ', '')
                element['Previous'] = element['Previous'].replace('Previous', '')
                element['Save'] = element['Save'].replace('Save', '')
                element['Where'] = element['Where'].replace('Where', '')
            with open(f"{directory}/{file_name}", 'w') as outfile:
                json.dump(json_file, outfile)

    except FileNotFoundError as error:
        print(f"File not found. {error}")
    except JSONDecodeError as jsonerror:
        print(f"{jsonerror} has occured. This typically means the file contains no data.")

# applies the function cleanText to every file in the price_data directory. 
for price_file in tqdm(os.listdir(config.PRICE_DATA_DIR)):
    cleanText(config.PRICE_DATA_DIR, price_file)
