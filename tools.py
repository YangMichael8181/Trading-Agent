# from globals import ticker_company_dict
import yfinance as yf
import pandas as pd
from datetime import date, timedelta
import sys

# # checks to see if ticker exists
# def ticker_exists():
#     return

# # checks to see if company name exists
# def company_exists():
#     return

# # checks to see which ticker is associated with which company
# def ticker_to_company():
#     return

# # checks to which company is associated with which ticker
# def company_to_ticker():
#     return


def calc_sma(ticker: str, range:int = 50):
    """
    Function to calculate simple moving averages. Assuming 1D timeframe.
    Parameters:
        ticker: string. The stock ticker to calculate the moving average for
        range: int. The date range. Default is 50 (calculates 50 day sma)
    """

    price_data = yf.Ticker(ticker).history(period="3mo",interval="1d")
    return price_data["Close"].tail(range).mean()