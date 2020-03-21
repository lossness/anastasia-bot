import json
from pathlib import Path


# open all our config files

# Paths for files
PATH = Path.cwd()
CARRIER_INFO_PATH = PATH.joinpath('data', 'carrier_info.json')
YES_FILE_PATH = PATH.joinpath('data', 'yes_word.txt')
USER_INFO_PATH = PATH.joinpath('data', 'user_info.json')
PRICE_DATA_DIR = PATH.joinpath('data', 'price_data')
COGS_PATH = PATH.joinpath('cogs')

with open(USER_INFO_PATH) as user_info_json:
    PROFILES = json.load(user_info_json)

with open(YES_FILE_PATH) as f:
    YES_LIST = json.load(f)

with open(CARRIER_INFO_PATH) as f:
    CARRIERS = json.load(f)

# define the following variables for better understanding of
# what they are used for when imported into various modules
CARRIER_LIST = list(CARRIERS)
MAX_RANGE_LIST = len(CARRIER_LIST)
RANGE_LIST = [i for i in range(1, MAX_RANGE_LIST)]
