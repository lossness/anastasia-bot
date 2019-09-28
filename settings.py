import os
from os.path import join, dirname
from dotenv import load_dotenv

# Get the path to the directory this is in
BASEDIR = os.path.abspath(os.path.dirname(__file__))

# Connect the path with your '.env' file name
load_dotenv(os.path.join(BASEDIR, '.env'))

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")



