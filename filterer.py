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
    order = False

    # Holds all filtered stock data
    ticker_dict_lock = threading.Lock()
    ticker_data = {}

    # NOTE: Queue class has built-in synchronization
    tickers = queue.Queue()


#-------------------------------------------------STATE------------------------------------------------------------------------------

    def __init__(self, json_file):

        # Initialize state
        self.period = json_file.get("period", "3mo")
        self.interval = json_file.get("interval", "1d")
        self.requirements = json_file.get("requirements", {"sma": [50]})
        self.order = json_file.get("order", False)

        # Start producer/consumer threads
        threading.Thread(target=self._producer_func).start()
        for _ in range(1, self.num_threads):
            threading.Thread(target=self._consumer_func).start()

        # Start gathering data for all tickers



        self.tickers.join()
        self.tickers.put(None)
        # Cache results
        with open("nasdaq_above_50sma.txt", "w+") as file:
            for key in self.ticker_data.keys():
                file.write(f"{key}\n")


#---------------------------------------------GATHER-TICKERS-------------------------------------------------------------------------




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
        

        mas = self._validate_mas(ticker=ticker, frame=frame, ma_list=self.requirements["mas"])
        if mas == {}:
            return

        # If valid, add ticker and corresponding frame to memory
        with self.ticker_dict_lock:
            if self.ticker_data.get(ticker, None) is None:
                self.ticker_data[ticker] = {}
            self.ticker_data[ticker]["Frame"] = frame
            self.ticker_data[ticker]["MA"] = mas


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