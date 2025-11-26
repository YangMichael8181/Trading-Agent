import requests
import yfinance as yf
import threading
import time
import numpy as np
import queue
from contextlib import redirect_stderr
import io
import parse
import json

import globals

class NASDAQ:

    """
    NASDAQ Object. Contains the data for the past period (default value for period is 3 months)
    in interval timeframes (default value for interval is 1d)

    Parameters:
        period: string. Can be one of: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max. Default is 3mo
        interval: string. Can be one of: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo. NOTE: Intraday data cannot extend last 60 days
    """
    # Collected stocks that match requirements

    # Requirements for stock
    # Check folder config/default.json for example options
    requirements = {}

    # Parameters used to find and filter stock
    # Interval: data interval (1m, 5m, 1w, 1d, etc.)
    # Period: data period (1d, 5d, 3mo, 1y, etc.)
    # Num_threads: 1 == # of producer_thread, (num_threads - 1) == # of consumer_threads
    # Order: if order matters or not
    # E.g. Some filter want EMA10 >= SMA20 >= SMA50 >= SMA100, while others want close_price > SMA20, SMA50, SMA100
    # Use order to remember if we need to compare SMA prices with eachother or not
    interval = ""
    period = ""
    num_threads = 0
    order = False

    # Holds all filtered stock data
    ticker_dict_lock = threading.Lock()
    ticker_data = {}

    # NOTE: Queue class has built-in synchronization
    tickers = queue.Queue()

    # Used to hold data retrieved from yfinance
    raw_data_lock = threading.Lock()
    raw_data = {}

    # Used to redirect stderr to a file
    output_lock = threading.Lock()

    # Cached MAs (for testing purposes)
    cached_mas = {}
    mas_lock = threading.Lock()

#-------------------------------------------------STATE------------------------------------------------------------------------------

    def __init__(self, json_file):

        # Initialize state
        self.period = json_file.get("period", "3mo")
        self.interval = json_file.get("interval", "1d")
        self.num_threads = json_file.get("num_threads", 5)
        self.requirements = json_file.get("requirements", {"sma": [50]})
        self.order = json_file.get("order", False)


        # Start producer/consumer threads
        threading.Thread(target=self._producer_func).start()
        for _ in range(1, self.num_threads):
            threading.Thread(target=self._consumer_func).start()

        # Collect all tickers from datasets found online
        # First process NASDAQ, then process NYSE
        # Delete ticker set afterwards, was used to prevent duplicates from dataset
        # After everything processed, let producer and consumers know job is finished by putting None into the queue
        tickers_gathered = set()
        tickers_gathered.update(parse.gather_invalid_tickers())
        self._gather_nasdaq_tickers(tickers_gathered)
        self._gather_nyse_tickers(tickers_gathered)
        self.tickers.join()
        del tickers_gathered
        self.tickers.put(None)

        # Cache results
        with open("nasdaq_above_50sma.txt", "w+") as file:
            for key in self.ticker_data.keys():
                file.write(f"{key}\n")


#---------------------------------------------GATHER-TICKERS-------------------------------------------------------------------------

    def _gather_nasdaq_tickers(self, tickers_gathered:set) -> None:
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
            
        split_tickers_list = [tickers_list[i:i + 100] for i in range(0, len(tickers_list), 100)]
        for t in split_tickers_list:
            self.tickers.put(" ".join(t))
        
        tickers_gathered.update(tickers_list)


    def _gather_nyse_tickers(self, tickers_gathered:set) -> None:
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
            and (line[7] not in tickers_gathered)
            ]
        
        split_tickers_list = [tickers_list[i:i + 100] for i in range(0, len(tickers_list), 100)]
        for t in split_tickers_list:
            self.tickers.put(" ".join(t))

        tickers_gathered.update(tickers_list)


#-------------------------------------------PRODUCER-FUNCTIONS-----------------------------------------------------------------------


    def _producer_func(self):
        # Infinite loop so producer runs until job is finished
        # Check queue for work; if queue returns None, then means job is finished
        # Otherwise, get tickers, gather price data, put into consumer queue
        # Mark task as done, sleep
        while True:
            ticker = self.tickers.get()
            if ticker is None:
                with self.raw_data_lock:
                    self.raw_data["<Producer_Complete>"] = "<Producer_Complete>"
                self.tickers.task_done()
                break

            self._gather_ticker_data(ticker)
            self.tickers.task_done()
            time.sleep(4)


    def _gather_ticker_data(self, ticker:str) -> None:
        """
        Sends HTTP request to get price history for all tickers.
        Parameters:
            self
            ticker: string. Should be a string with 100 tickers in the string, split by whitespace
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
                        data = yf.download(tickers=ticker, period=self.period,interval=self.interval, auto_adjust=True)
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


#-------------------------------------------CONSUMER-FUNCTIONS-----------------------------------------------------------------------


    def _consumer_func(self):
        # Infinite loop so consumer runs until job is finished
        # Check dict for work; if "<Producer_Complete>" token exists in dict, means producer put it there, job is done
        # Otherwise, process tickers, put into ticker_data
        # Keep repeating process until queue is finished, gives more time between API calls
        while True:
            ticker = None
            frame = None
            with self.raw_data_lock:
                if self.raw_data.get("<Producer_Complete>", None) is not None:
                        break
                close_dict = self.raw_data.get("Close", None)
                if close_dict is not None and len(close_dict) > 0:
                    ticker, frame = close_dict.popitem()
            
            if ticker is not None and frame is not None:
                self._process_ticker_data(ticker, frame)
            else:
                time.sleep(0.1)


    def _process_ticker_data(self, ticker:str, frame) -> None:
        """
        Processes data from tickers to calculate 50 day simple-moving-average
        Parameters:
            self
            ticker: string. Singular ticker
            frame: Pandas Dataframe. Returned by the yfinance API, contains price data from the past 3 months
        """
        

        if not self._validate_mas(ticker=ticker, frame=frame, ma_list=self.requirements["mas"]):
            return

        # If valid, add ticker and corresponding frame to memory
        with self.ticker_dict_lock:
            self.ticker_data[ticker] = frame


#----------------------------------------------TECHNICALS----------------------------------------------------------------------------


    def _validate_mas(self, ticker:str, frame, ma_list:list) -> bool:
        """
        Calculates the SMA using the given frame for the given ticker. Assumes 1d timeframe
        If enough data exists, returns SMA rounded to 2 decimal points for given range.
        Otherwise, if lacking data, returns -1.0
        E.g. if calculating SMA 200 for stock that has 100 days of data, not possible. Return -1.0

        Parameters:
            self
            ticker: string. Singular ticker
            frame: Pandas Dataframe. Returned by the yfinance API, contains price data
        
        """
        # Grab latest close price from frame
        # Ensure price is valid

        write_dict = {}
        try:
            latest_close = round(frame.tail(1).item(), 2)
        except Exception as e:
            latest_close = round(frame.tail(1).mean(), 2)
        if np.isnan(latest_close):
            return False
        
        write_dict["latest_close"] = latest_close
        # Compare MA values
        prev_value = latest_close
        for ma in ma_list:
            ma = ma.upper()
            time_range = int(ma[3:])
            if "SMA" in ma:
                calc_val = self._calculate_sma(frame=frame, time_range=time_range)
            elif "EMA" in ma:
                calc_val = self._calculate_ema(frame=frame, time_range=time_range, smoothing=2)
            
            if np.isnan(calc_val):
                return False
            elif prev_value < calc_val:
                return False
            
            write_dict[ma] = calc_val
            if self.order:
                prev_value = calc_val

        with self.mas_lock:
            self.cached_mas[ticker] = write_dict
            with open("verify_mas.json", "w+") as file:
                json.dump(self.cached_mas, file, indent=4)
        return True


    def _calculate_ema(self, frame, time_range:int = 50, smoothing:int = 2) -> float:
        """
        Calculates the EMA using the given frame for the given ticker. Assumes 1d timeframe
        If enough data exists, returns EMA rounded to 2 decimal points for given range.
        Otherwise, if lacking data, returns -1.0
        E.g. if calculating EMA 200 for stock that has 100 days of data, not possible. Return -1.0

        Parameters:
            self
            ticker: string. Singular ticker
            frame: Pandas Dataframe. Returned by the yfinance API, contains price data
            time_range: int. the number of days to calculate the MA. e.g. EMA10, time_range == 10. Default is 50
            smoothing: int. Smoothing factor for algorithm. Default is 2
        """

        # Check if stock has enough data to calculate for provided range
        if len(frame) * 2 < time_range:
                return -1.0

        com_val = (time_range - 1) / 2
        ewm_series = frame.ewm(com=com_val, adjust=False).mean()
        ema_val = ewm_series.iloc[-1]
        return round(ema_val, 2)


    def _calculate_sma(self, frame, time_range:int = 50) -> float:
        """
        Calculates the EMA using the given frame for the given ticker. Assumes 1d timeframe
        If enough data exists, returns EMA rounded to 2 decimal points for given range.
        Otherwise, if lacking data, returns -1.0
        E.g. if calculating EMA 200 for stock that has 100 days of data, not possible. Return -1.0

        Parameters:
            self
            ticker: string. Singular ticker
            frame: Pandas Dataframe. Returned by the yfinance API, contains price data
            time_range: int. the number of days to calculate the MA. e.g. EMA10, time_range == 10. Default is 50
            smoothing: int. Smoothing factor for algorithm. Default is 2
        """
        # Check if stock has enough data to calculate for provided range
        if len(frame) < time_range:
                return -1.0
        
        return round(frame.tail(time_range).mean(), 2)


    def calculate_volume(self, ticker, frame, range) -> dict:
        """
        Calculates:
        latest volume: volume of latest day
        average volume: average volume of last range days
        relative volume: ratio of latest volume : average volume
        Returns in a dict {latest_volume: <value>, . . .}

        Parameters:
            self
            ticker: string. Singular ticker
            frame: Pandas Dataframe. Returned by the yfinance API, contains historical data

        
        """
        return