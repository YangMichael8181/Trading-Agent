import io
from contextlib import redirect_stderr
import yfinance as yf
import requests
import time
import itertools

import parse


class API:
    ticker_set = set()

    def __init__(self):

        # Collect all tickers from datasets found online
        # First process NASDAQ, then process NYSE
        # Delete ticker set afterwards, was used to prevent duplicates from dataset
        # After everything processed, let producer and consumers know job is finished by putting None into the queue
        self.ticker_set.update(parse.gather_invalid_tickers())
        self._gather_nasdaq_tickers()
        self._gather_nyse_tickers()


    def _gather_nasdaq_tickers(self) -> list:
        """
        Sends HTTP request to gather all tickers listed on the NASDAQ
        Parameters:
            self: required to store tickers retrieved into tickers queue
            tickers_gathered: set. Since cannot iterate through queue, use set to keep track of tickers already obtained
        """
        
        # Send HTTP request to gather required file
        # Use while loop to re-send request if failed
        print("Gathering NASDAQ-listed tickers . . . ")
        response = None
        while response is None:
            response = requests.get("https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt")
            if response.status_code == 200:
                data = response.text
            time.sleep(1)

        # Parse data
        # skip first line: provides headers for each column
        # skip second-last line: not a company, some "File creation time"
        # skip last line: last line is newline, creates empty array and breaks

        # line[0]: ticker
        # line[1]: company name (irrelevant)
        # line[2]: market category (irrelevant)
        # line[3]: test issue (test issue == fake stock)
        # line[4]: financial status (financial_status == 'N' is only good option)
        # line[5]: round lot size (irrelevant)
        # line[6]: etf status (only want stocks)
        # line[7]: nextshares (irrelevant)
        data = [list(line.split('|')) for line in data.split('\n')]
        tickers_list = [
            line[0]
            for line
            in data[1:-2]
            if (line[3] != 'Y')
            and (line[4] == 'N')
            and (line[6] == 'N')
            ]
            
        self.ticker_set.update(tickers_list)


    def _gather_nyse_tickers(self) -> list:
        """
        Sends HTTP request to gather all tickers listed on the NYSE
        Requires another function because the data is listed in a different format
        Parameters:
            self: required to store tickers retrieved into tickers queue
            tickers_gathered: set. Since cannot iterate through queue, use set to keep track of tickers already obtained
        """
        # Send HTTP request to gather required file
        # Use while loop to re-send request if failed
        print("Gathering NYSE-listed tickers . . . ")
        response = None
        while response is None:
            response = requests.get("https://www.nasdaqtrader.com/dynamic/symdir/otherlisted.txt")
            if response.status_code == 200:
                data = response.text
            time.sleep(1)

        # Parse data
        # skip first line: provides headers for each column
        # skip second-last line: not a company, some "File creation time"
        # skip last line: last line is newline, creates empty array and breaks

        # line[0]: ticker
        # line[1]: company name (irrelevant)
        # line[2]: exchange (Z and V are NOT NYSE, P is NYSE ARCA, which mainly holds ETFs)
        # line[3]: cqs symbol (irrelevant)
        # line[4]: etf status (do not want etfs)
        # line[5]: round lot size (irrelevant)
        # line[6]: test issue (test issue == fake stock, therefore DO NOT WANT)
        # line[7]: nasdaq_ticker (Ignore any tickers with non-letter characters (any warrant stocks, dividend stock, etc.))
        # line[7]: nasdaq_ticker (Already grabbed all nasdaq tickers, don't want duplicates)
        data = [list(line.split('|')) for line in data.split('\n')]
        tickers_list = [
            line[0]
            for line
            in data[1:-2]
            if (line[0].isalpha())
            and (line[2] != 'P' and line[2] != 'Z' and line[2] != 'V')
            and (line[4] == 'N')
            and (line[6] != 'Y')
            and (line[7] not in self.ticker_set)
            ]
        
        self.ticker_set.update(tickers_list)
    

    def gather_all_ticker_data(self, period:str="3mo", interval:str="1d", batch_size:int=100) -> None:
        """
        Sends HTTP request to get price history for all tickers.
        Parameters:
            self
            ticker: string. Should be a string with batch_size number of  tickers in the string, split by whitespace
            period: string. Can be one of: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max. Default is 3mo
            interval: string. Can be one of: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo. NOTE: Intraday data cannot extend last 60 days
            batch_size: int. Number of tickers to process
        """

        # Send API request to API to gather data
        # Rate-limit raises exception, thus need except block
        # Unable to find tickers DO NOT raise an exception, prints to stderr
        # Save stderr to file, check file for invalid tickers, add to ignore list
        print(f"grabbing price history for {ticker}. . .")
        stderr_output = io.StringIO()
        try:
            with self.output_lock:
                    with redirect_stderr(stderr_output):
                        data = yf.download(tickers=ticker, period=period,interval=interval, auto_adjust=True)
        except Exception as e:
            print(f"\nEXCEPTION OCCURED: {e}")

        with open(globals.ERROR_MESSAGE_FILE, "a+") as file:
            file.write(stderr_output.getvalue())

        # Search through price frames
        split_tickers = ticker.split(" ")
        for ticker in split_tickers:
            for key in data.columns.tolist():
                price, ticker = key
                frame = data[key]
                with self.raw_data_lock:
                    if price not in self.raw_data.keys():
                        self.raw_data[price] = {}
                    if ticker not in self.raw_data[price].keys():
                        self.raw_data[price][ticker] = {}

                    self.raw_data[price][ticker] = frame