import requests
import yfinance as yf
import threading
import time
import numpy as np
import queue

class NASDAQ:

    """
    NASDAQ Object. Contains the data for the past period (default value for period is 3 months)
    in interval timeframes (default value for interval is 1d)

    Parameters:
        period: string. Can be one of: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max. Default is 3mo
        interval: string. Can be one of: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo. NOTE: Intraday data cannot extend last 60 days
    """

    ticker_data = {}
    interval = ""
    period = ""
    num_threads = 0
    TIMEOUT_DURATION = 0

    ticker_dict_lock = threading.Lock()
    tickers = queue.Queue()

    raw_data_lock = threading.Lock()
    raw_data = {}


    def __init__(self, period:str="3mo",interval:str="1d",num_threads:int = 5,timeout:int = 1):

        # Initialize state
        self.period = period
        self.interval = interval
        self.num_threads = num_threads
        self.TIMEOUT_DURATION = timeout
        tickers_gathered = set()

        self._gather_nasdaq_tickers(tickers_gathered)
        self._gather_nyse_tickers(tickers_gathered)

        # Gathered all tickers, no need for data structure any more
        del tickers_gathered

        # Initialize threads        
        # Start threads
        # Wait for threads to finish

        threading.Thread(target=self._producer_func).start()

        for _ in range(1, num_threads):
            threading.Thread(target=self._consumer_func).start()
        
        self.tickers.join()

        # Once finished, put None into the queue to let threads know job is finished
        self.tickers.put(None)
        
        # NOTE: for testing purposes
        with open("nasdaq_above_50sma.json", "w") as file:
            for key in self.ticker_data.keys():
                file.write(f"{key}\n")


#-----------------------------------------HELPERS-----------------------------------------------------------



    def _gather_nasdaq_tickers(self, tickers_gathered:set):
        """
        Sends HTTP request to gather all tickers listed on the NASDAQ
        Parameters:
            self: required to store tickers retrieved into tickers queue
            tickers_gathered: set. Since cannot iterate through queue, use set to keep track of tickers already obtained
        """
        print("Gathering NASDAQ-listed tickers . . . ")
        # Send HTTP request to gather required file
        # Use while loop to re-send request if failed
        response = None
        while response is None:
            response = requests.get("https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt")
            if response.status_code == 200:
                data = response.text

        # Parse data
        # skip first line: provides headers for each column
        # skip second-last line: not a company, some "File creation time"
        # skip last line: last line is newline, creates empty array and breaks

        # line[0]: ticker
        # line[3]: test issue (test issue == fake stock, therefore DO NOT WANT)
        # line[4]: financial status (financial_status != 'N' IS BAD DO NOT WANT)
        data = [list(line.split('|')) for line in data.split('\n')]
        tickers_list = [
            line[0]
            for line
            in data[1:-2]
            if (line[3] != 'Y')
            and (line[4] == 'N')
            ]
            
        split_tickers_list = [tickers_list[i:i + 100] for i in range(0, len(tickers_list), 100)]
        for t in split_tickers_list:
            self.tickers.put_nowait(" ".join(t))
        
        tickers_gathered.update(tickers_list)

    def _gather_nyse_tickers(self, tickers_gathered:set):
        """
        Sends HTTP request to gather all tickers listed on the NYSE
        Requires another function because the data is listed in a different format
        Parameters:
            self: required to store tickers retrieved into tickers queue
            tickers_gathered: set. Since cannot iterate through queue, use set to keep track of tickers already obtained
        """
        print("Gathering NYSE-listed tickers . . . ")
        # Send HTTP request to gather required file
        # Use while loop to re-send request if failed
        response = None
        while response is None:
            response = requests.get("https://www.nasdaqtrader.com/dynamic/symdir/otherlisted.txt")
            if response.status_code == 200:
                data = response.text

        # Parse data
        # skip first line: provides headers for each column
        # skip second-last line: not a company, some "File creation time"
        # skip last line: last line is newline, creates empty array and breaks

        # line[0]: ticker
        # line[2]: exchange (Z and V are NOT NYSE, therefore IGNORE)
        # line[5]: test issue (test issue == fake stock, therefore DO NOT WANT)
        # line[7]: nasdaq_ticker (Already grabbed all nasdaq tickers, don't want duplicates)
        data = [list(line.split('|')) for line in data.split('\n')]
        tickers_list = [
            line[0]
            for line
            in data[1:-2]
            if (line[2] != 'Z' and line[2] != 'V')
            and (line[5] != 'Y')
            and (line[7] not in tickers_gathered)
            ]
            
        split_tickers_list = [tickers_list[i:i + 100] for i in range(0, len(tickers_list), 100)]
        for t in split_tickers_list:
            self.tickers.put_nowait(" ".join(t))
        tickers_gathered.update(tickers_list)

    def _producer_func(self):
        while True:
            ticker = self.tickers.get()
            if ticker is None:
                self.tickers.task_done()
                break

            time.sleep(2)
            self._gather_ticker_data(ticker)
            self.tickers.task_done()
    
    def _consumer_func(self):
        while True:
            ticker_to_process = None
            frame_to_process = None
            with self.raw_data_lock:
                if len(self.raw_data) > 0:
                    ticker_to_process, frame_to_process = self.raw_data.popitem()
            
            if ticker_to_process is not None and frame_to_process is not None:
                self._process_ticker_data(ticker_to_process, frame_to_process)
            else:
                time.sleep(0.1)

    
    def _gather_ticker_data(self, ticker:str):

        print(f"grabbing price history for {ticker}. . .")

        try:
            data = yf.Tickers(ticker).history(period="3mo",interval="1d")

        except Exception as e:
            print(f"\nEXCEPTION OCCURED: {e}")

        split_tickers = ticker.split(" ")
        for ticker in split_tickers:
            key = ('Close', ticker)
            if key not in data.columns:
                continue
            frame = data[key]


            # Check to see if there are 50 days of information
            # Especially for new stocks, may not have 50 days worth of information
            if len(frame) < 50:
                return None
            
            with self.raw_data_lock:
                self.raw_data[ticker] = frame
        
        time.sleep(0.1)

    def _process_ticker_data(self, ticker:str, price_frame):

        print("Processing raw_data . . .")
        # Calculate 50 day simple moving average
        # Grab latest close price, round it to 2 decimal places
        # Sometimes yfinance API returns close price as an array, so try . . . except
        sma_50 = round(price_frame.tail(50).mean(), 2)
        try:
            latest_close = round(price_frame.tail(1).item(), 2)

        except Exception as e:
            latest_close = round(price_frame.tail(1).mean(), 2)
        
        # If faulty data, ignore
        # Only save tickers that are above 50 day simple moving average
        if np.isnan(sma_50) or np.isnan(latest_close):
            return
        if latest_close > sma_50:
            with self.ticker_dict_lock:
                self.ticker_data[ticker] = yf.Ticker(ticker)