import sys
import yfinance as yf

# local imports
import scraper
import globals
from classes import NASDAQ


def main():

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

