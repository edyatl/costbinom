#!/usr/bin/env python3
"""
    Developed by @edyatl <edyatl@yandex.ru> December 2022
    https://github.com/edyatl

"""
import os
from os import environ as env
from dotenv import load_dotenv


project_dotenv = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(project_dotenv):
    load_dotenv(project_dotenv)

class Configuration(object):
    DEBUG = True

    # Tokens
    ADSTERRA_TOKEN = env.get('ENV_ADSTERRA_TOKEN')
    PROPELLERADS_TOKEN = env.get('ENV_PROPELLERADS_TOKEN')
    BINOM_TOKEN = env.get('ENV_BINOM_TOKEN')

    # URLs
    ADSTERRA_BASE_URL = "https://api3.adsterratools.com/advertiser/"
    PROPELLERADS_BASE_URL = "https://ssp-api.propellerads.com/v5/"
    BINOM_BASE_URL = "https://trackhost.click/3k9b9.php"

    DB_FILE = os.path.join(os.path.dirname(__file__), "db/binom.db")
    LOG_FILE = os.path.join(os.path.dirname(__file__), "costbin.log")

