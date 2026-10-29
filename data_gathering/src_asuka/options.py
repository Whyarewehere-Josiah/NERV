# This file generates folders corresponding to the date
import os
import datetime
import time
import subprocess
import shutil

symbols = ['AAPL', 'SPY', 'MSFT', 'AMZN', 'QQQ']  # List of stock symbols


def generate_folders():
    date_str = datetime.date.today().isoformat()  # e.g. "2026-10-28"
    base = os.mkdir(f"{date_str}")
    for symbol in symbols:
        folder_name = f"{date_str}/{symbol}"
        os.mkdir(folder_name)

    try:
        subprocess.run(["scp", "-r", base, "Rei@rei:/home/Rei/MAGI/data_gathering"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to send to Rei: {e}")

generate_folders()