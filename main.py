import json
import threading
from collections import defaultdict

# local imports
import scraper
import globals
import llm
import helper
import yfinance as yf

import requests
import tools

from classes import NASDAQ

def main():

    # helper.gather_nasdaq_listings()

    globals.GLOBAL_NASDAQ = NASDAQ()

    return
    # grabs threads from /u/wsbapp
    # Grabs top 20 threads, ignores latest thread
    # Do this via checking the history of wsbapp
    scraper.get_wsb_thread()

    nasdaq_thread = threading.Thread(target=helper.gather_nasdaq_listings)
    wsb_thread = threading.Thread(scraper.get_wsb_thread)
    threads = [nasdaq_thread, wsb_thread]

    for t in threads:
        t.start()
    
    for t in threads():
        t.join()





if __name__ == "__main__":
    main()

