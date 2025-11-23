import requests
import yfinance as yf
import threading
import time
import sys

class Comment:
    ticker = ""
    author = ""
    text = ""
    link = ""
    score = 0

    def __init__(self, _author, _body, _link, _score):
        self.author = _author
        self.body = _body
        self.link = _link
        self.score = _score


class NASDAQ:

    """
    NASDAQ Object. Contains the data for the past 3 months
    """

    ticker_data = {}
    interval = ""
    period = ""
    lock = threading.Lock()

    def __init__(self, period:str="3mo",interval:str="1d"):

        # Keep track of variables
        self.period = period
        self.interval = interval
        

        # Send HTTP request to gather required file
        response = requests.get("https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt")
        if response.status_code == 200:
            data = response.text

        # Parse data
        # skip first line: provides headers for each column
        # skip second-last line: not a company, some "File creation time"
        # skip last line: last line is newline, creates empty array and breaks
        data = data.split('\n')
        tickers_list = []
        threads_list = []
        for i in range(1, len(data) - 2):
            ticker, _, _, _, _, _, _, _     = data[i].split('|')
            tickers_list.append(ticker)
        
        print("Starting test")
        start_time = time.time()
        for t in tickers_list:
            thread = threading.Thread(target=self.gather_ticker_data, args=(t,))
            threads_list.append(thread)
        for t in threads_list:
            t.start()
        for t in threads_list:
            t.join()

        print(f"Total time to gather all ticker data: {time.time() - start_time}")
        print(f"ticker_data len: {len(self.ticker_data)}")
    
    def gather_ticker_data(self, ticker:str):
        # Somewhat jank, but worried about getting timed out, thus this
        data = None
        while data is None:
            data = yf.Ticker(ticker)

        price_history = None
        print(f"grabbing price history for {ticker}. . .")
        while price_history is None:
            try:
                price_history = data.history(period="3mo",interval="1d")
                time.sleep(5)
            except Exception as e:
                print(f"Failed to grab price for {ticker}. Trying again . . .")
                continue

        print(f"finished grabbing price history for {ticker}. . .")
        sma_50 = round(price_history["Close"].tail(50).mean(), 2)

        # Grab latest close price, round it to 2 decimal places
        # For some reason it might return an array and raise an exception
        # So catch exception and calculate average of array
        try:
            latest_close = round(price_history["Close"].tail(1).item(), 2)
        except Exception as e:
            latest_close = round(price_history["Close"].tail(1).mean(), 2)

        if latest_close < sma_50:
            return

        with self.lock:
            self.ticker_data[ticker] = data
        return