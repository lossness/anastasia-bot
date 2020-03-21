import os
import json
import io



# define paths to config files
USER_INFO_PATH = os.path.abspath("./anastasia/data/")
CARRIER_INFO_FILE = "./anastasia/data/carrier_info.json"
YES_FILE = "./anastasia/data/yes_word.txt"
PRICE_DATA = "./anastasia/data/price_data/"


def startup_check(path: str):
""" this checks if user_info.json exists
if not, creates one. """
if os.path.isfile(f"{settings['files']['user_info']}") and os.access(path, os.R_OK):
    print("User file found, loading..")
    return
else:
    print("User data file missing, creating one..")
    with open("./anastasia/data/user_info.json", 'w') as db_file:
        db_file.write(json.dumps({}))

startup_check(USER_INFO_PATH)  
# this is the user_info.json path.  We will use this to load into the program
# as a dict.          
USER_INFO = f"{USER_INFO_PATH}/user_info.json"


# open all our config files
with open(USER_INFO) as user_info_json:
    PROFILES = json.load(user_info_json)

with open(YES_FILE) as f:
    YES_LIST = json.load(f)

with open(CARRIER_INFO_FILE) as f:
    CARRIERS = json.load(f)

# define the following variables for better understanding of 
# what they are used for in the functions that follow
CARRIER_LIST = list(CARRIERS)
MAX_RANGE_LIST = len(CARRIER_LIST)
RANGE_LIST = [i for i in range(1, MAX_RANGE_LIST)]