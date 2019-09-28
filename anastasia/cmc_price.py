import csv
import json
import os
import random

from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects

"""
this function searches a dict (including all nested dicts)
for key / value pairs matching a list of keys you would like
to find.  This function recursively loops through the dict
and any nested dicts and lists it contains to build a list
of all possible dicts to be checked for matching keys
"""
def find_key_value_pairs(q, keys, dicts=None):
    if not dicts:
        dicts = [q]
        q = [q]

    data = q.pop(0)
    if isinstance(data, dict):
        data = data.values()

    for d in data:
        dtype = type(d)
        if dtype is dict or dtype is list:
            q.append(d)
            if dtype is dict:
                dicts.append(d)

    if q:
        return find_key_value_pairs(q, keys, dicts)

    return [(k, v) for d in dicts for k, v in d.items() if k in keys]



def cmc_quote(crypto_name):
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
    parameters = {
        'slug': crypto_name
    }
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': 'db92b1be-ab20-4767-8eed-6fbd38fe6d23',
    }

    session = Session()
    session.headers.update(headers)

    try:
        translationtable = str.maketrans("(", ",", ")")
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        for item in find_key_value_pairs(data, "price"):
            tuple_price = item[1:3]
            string_price = ''.join(str(n) for n in tuple_price)
            return "$" + string_price.translate(translationtable)[:5]

    except (ConnectionError, Timeout, TooManyRedirects) as e:
        return(e + 'on quote data')

    finally:
        if response.status_code == 400:
            with open(os.path.join("anastasia", "data", "bad-words.csv"), 'rU') as csvFile:
                reader = csv.reader(csvFile)
                chosen_word = random.choice(list(reader))
                return "Thats not a cryptocurrency, you {}.".format(chosen_word[0])

