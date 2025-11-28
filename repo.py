import h5py
import pandas as pd
import numpy as np
import datetime

import globals

class Repository:

    repo_name = "repo.h5"
    curr_date = datetime.date.today()


    def __init__(self, data):
        return

    def write(self, ticker:str ,data):
    
        """
        Writes data to key in hdf5 file

        Parameters:
            key: string. Used to access HDF5 Group. Should be a string in the format: "ticker Close High Low Open Volume"
            data: Pandas Dataframe. Should be the frame returned by yf.download()
        """

        # Open file
        # Find latest stored_date, extract all data from frame from stored_date onward
        with h5py.File(self.repo_name, "w") as file:

            # Retrieve stored_date
            # Splice data to retrieve data from stored_date onward
            d = file.require_group("Date")

            if "Year" not in d.keys():
                d.create_dataset("Year", data=self.curr_date.year)
                stored_year = datetime.date.today().year
            else:
                stored_year = d["Year"]

            if "Month" not in d.keys():
                d.create_dataset("Month", data=self.curr_date.month)
                stored_month = datetime.date.today().month
            else:
                stored_month = d["Month"]

            if "Day" not in d.keys():
                d.create_dataset("Day", data=self.curr_date.day)
                stored_day = datetime.date.today().day
            else:
                stored_day = d["Day"]
            stored_date = datetime.date(year=stored_year, month=stored_month, day=stored_day)

            # Only concatenate data if more than 30 days of data difference
            if (self.curr_date - stored_date).days() > 30:
                data = data.loc[stored_date:]


            # Separate volume data from price data
            # Convert both price and volume data into numpy arrays
            vol_key = ('Volume', ticker)
            volume_frame = data[vol_key]
            price_frame = data.drop(columns=vol_key)
            vol_np_arr = volume_frame.to_numpy()
            price_np_arr = price_frame.to_numpy()

            print(volume_frame)
            print(price_frame)

            # Traverse hdf5 to proper location
            # Store data
            group = file.require_group("Tickers")
            group = group.require_group(ticker)
            
            if "Price" not in group.keys():
                group.create_dataset("Price", data=price_np_arr)
            else:
                group["Price"] = np.concatenate((group["Price"], price_np_arr), axis=0)

            if "Volume" not in group.keys():
                group.create_dataset("Volume", data=vol_np_arr)
            else:
                group["Volume"] = np.concatenate((group["Price"], price_np_arr), axis=0)



    def read(self, ticker):
        """
        Docstring for read
        """

        return

        with h5py.File(self.repo_name, "r") as file:
            group = file.require_group("Tickers")
            dset = group[ticker]
            # print(dset.)
