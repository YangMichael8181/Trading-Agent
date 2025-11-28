import sys
import yfinance as yf

# local imports
import scraper
import globals
from classes import NASDAQ

import yfinance as yf

from repo import Repository
from api import API

def main():


    api = API()
    return


    # data = yf.download(tickers="NVDA", period="5y",interval="1d", auto_adjust=True)
    # repo = Repository()
    # repo.write(ticker="NVDA", data=data)
    # return


    config_file_name = "test.json"
    if len(sys.argv) > 1:
        config_file_name = sys.argv[1]
        print("Detected command line argument . . .")
        print(f"Loading in {config_file_name} . . .")

    print(f"Using config file {config_file_name} . . .")

    print("Initializing global variables . . .")
    globals.initialize_global_variables(config_file_name=config_file_name)

    return

    # grabs threads from /u/wsbapp
    # Grabs top 20 threads, ignores latest thread
    # Do this via checking the history of wsbapp
    scraper.get_wsb_thread()




if __name__ == "__main__":
    main()

