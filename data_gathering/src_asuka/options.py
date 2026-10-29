# This file generates folders corresponding to the date
import os
import datetime
import time
import subprocess
import shutil

symbols = ['AAPL', 'SPY', 'MSFT', 'AMZN', 'QQQ']  # List of stock symbols


def generate_folders():
    date_str = datetime.date.today().isoformat()  # e.g. "2026-10-28
    base = r"data_gathering\data"
    os.makedirs(base, exist_ok=True)
    day = r"data_gathering\data\{date_str}".format(date_str=date_str)
    os.makedirs(day, exist_ok=True)
    for symbol in symbols:
        folder_name = rf"data_gathering\data\{date_str}\{symbol}"
        os.makedirs(folder_name, exist_ok=True)


    try:
        subprocess.run(["scp", "-r", day, "Rei@rei:/home/Rei/NERV/data_gathering/data"], check=True)
    except subprocess.CalledProcessError as e:
       print(f"Failed to send to Rei: {e}")

