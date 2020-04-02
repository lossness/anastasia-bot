import os
import time
import datetime
import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from progressbar import progressbar

import config


# LAST 24HR PRICE DROPS AND LAST 7 DAYS PRICE DROPS URLS
DAY_URL = "http://pcpartpicker.com/products/pricedrop/day/"
WEEK_URL = "http://pcpartpicker.com/products/pricedrop/week/"

# Initialize selenium webdriver and attaches to chrome.exe using debugger port
CHROME_OPTIONS = Options()
CHROME_OPTIONS.debugger_address = "127.0.0.1:9222"
DRIVER = webdriver.Chrome(
    options=CHROME_OPTIONS,
    executable_path=r"C:\Utility\Browserdrivers\chromedriver.exe",
)


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
RESULTS_DAILY_DF = pd.DataFrame()
RESULTS_WEEKLY_DF = pd.DataFrame()


def collect_data(url):
    DRIVER.get(url)
    time.sleep(5)
    soup = BeautifulSoup(DRIVER.page_source, "lxml")

    for category in progressbar(PRODUCT_CATEGORIES):
        try:
            table = soup.find_all("div", attrs={"id": f"{category}"})[0]
            df = pd.read_html(str(table))

            if url == DAY_URL:
                global RESULTS_DAILY_DF
                daily_list = df[0].to_dict(orient="records")
                clean_daily_df = pd.DataFrame(
                    data=clean_text(daily_list, category.replace("dg_", ""))
                )
                RESULTS_DAILY_DF = RESULTS_DAILY_DF.append(clean_daily_df)

            if url == WEEK_URL:
                global RESULTS_WEEKLY_DF
                weekly_list = df[0].to_dict(orient="records")
                clean_weekly_df = pd.DataFrame(
                    data=clean_text(weekly_list, category.replace("dg_", ""))
                )
                RESULTS_WEEKLY_DF = RESULTS_WEEKLY_DF.append(clean_weekly_df)

        except IndexError:
            continue

    if url == DAY_URL:
        RESULTS_DAILY_DF.to_csv(csv_path("daily"))
        print(f"\nDaily discounts updated at {datetime.datetime.now()}")

    if url == WEEK_URL:
        RESULTS_WEEKLY_DF.to_csv(csv_path("weekly"))
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


DAILY_DF = pd.read_csv(csv_path("daily"), usecols=["Date"])
WEEKLY_DF = pd.read_csv(csv_path("weekly"), usecols=["Date"])
NOW = datetime.datetime.now()


def check_date(collect_function, dataframe, url):
    dataframe_dict = dataframe.to_dict()
    print("\nChecking if the data has been updated since yesterday")
    for values in progressbar(dataframe_dict.values()):
        for value in values.values():
            if value.startswith(str(NOW)[:10]):
                print("\nData up to date!")
                break

    # Opens a chrome window with debugging enabled to use selenium without chromedriver
    print("\nData out of date, intilizing fresh data scraper..")
    os.startfile(r"C:\Projects\weedmaps_review_bot\data\chrome_shortcut.lnk")
    time.sleep(10)
    collect_function(url)


check_date(collect_data, DAILY_DF, DAY_URL)
check_date(collect_data, WEEKLY_DF, WEEK_URL)
DRIVER.close()
DRIVER.quit()
