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


import parse


import io
from contextlib import redirect_stderr, redirect_stdout

from classes import NASDAQ

def main():


    # test = yf.Tickers("AACB AACBR AACBU AACG AADR AAL AALG AAME AAOI AAON").history(period="3mo",interval="1d")
    # print(test)

    # return

    print("Initializing NASDAQ() Object . . .")
    globals.GLOBAL_NASDAQ = NASDAQ()

    return

    # grabs threads from /u/wsbapp
    # Grabs top 20 threads, ignores latest thread
    # Do this via checking the history of wsbapp
    scraper.get_wsb_thread()




if __name__ == "__main__":
    main()

