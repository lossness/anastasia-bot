import json
import os
import requests

from dotenv import load_dotenv
from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects


load_dotenv()
token = os.getenv("STEAM_TOKEN")



def get_player_stats(discord_id, game):
    with open("anastasia\\data\\user_info.json") as user_info_json:
        profiles = json.load(user_info_json)
        steamid = ""
        for k, v in profiles[discord_id].items():
            if k == 'steam_id':
                steamid += v

    with open("anastasia\\data\\steam_games.json") as steam_games_json:
        steam_games = json.load(steam_games_json)    

    appid = steam_games[game]
    session = Session()
    url = "https://api.steampowered.com/ISteamUserStats/GetUserStatsForGame/v0002/?appid={}&key={}&steamid={}".format(appid, token, steamid)
    
    try:
        response = session.get(url)
        data = json.loads(response.text)
        print(data)

    except (ConnectionError, Timeout, TooManyRedirects) as e:
        return(e)

    finally:
        return

""" finally:
        if response.status_code == 400:
            with open(os.path.join("anastasia", "data", "bad-words.csv"), 'rU') as csvFile:
                reader = csv.reader(csvFile)
                chosen_word = random.choice(list(reader))
                return "Thats not a cryptocurrency, you {}.".format(chosen_word[0]) """


get_player_stats("193957589308932097", "csgo")