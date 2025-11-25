# local imports
import scraper
import globals
import yfinance as yf



from classes import NASDAQ

def main():

    print("Initializing global variables . . .")
    globals.initialize_global_variables()
    print(len(globals.NASDAQ.ticker_data))

    return

    # grabs threads from /u/wsbapp
    # Grabs top 20 threads, ignores latest thread
    # Do this via checking the history of wsbapp
    scraper.get_wsb_thread()




if __name__ == "__main__":
    main()

