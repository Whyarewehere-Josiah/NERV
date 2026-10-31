# This file generates folders corresponding to the date
import json
import os
import time
from datetime import date, timedelta, datetime, timezone, time as dt_time
from pathlib import Path
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

from alpaca.data.historical import (
    StockHistoricalDataClient,
    OptionHistoricalDataClient,
)
from alpaca.data.requests import (
    StockLatestTradeRequest,
    OptionChainRequest,
)
from alpaca.data.enums import DataFeed, OptionsFeed
from requests.packages import target

load_dotenv("keys.env")

SYMBOLS = [
    "SPY", "QQQ", "IWM", "DIA",          # Major Index ETFs
    "AAPL", "MSFT", "NVDA", "AMZN",      # Mega-Cap Tech
    "META", "GOOGL", "TSLA",             # Mega-Cap Tech / EV
    "AMD", "NFLX", "JPM", "BA"           # High-volume wildcards (Chips, Streaming, Finance, Industrial)
]
DATA_ROOT = Path("data_gathering") / "src_asuka" / "data"
MAX_DTE = 40
STRIKE_RANGE = 20
POLL_SECONDS = 5


def generate_folders() -> Path:
    day_folder = DATA_ROOT / date.today().isoformat()
    day_folder.mkdir(parents=True, exist_ok=True)
    for symbol in SYMBOLS:
        (day_folder / symbol).mkdir(exist_ok=True)
    return day_folder


API_KEY = os.getenv("API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

ENFORCE_MARKET_HOURS = False
MARKET_TZ = ZoneInfo("America/New_York")
MARKET_OPEN = dt_time(9, 30)
MARKET_CLOSE = dt_time(16, 0)

stock_client = StockHistoricalDataClient(API_KEY,SECRET_KEY,)

option_client = OptionHistoricalDataClient(API_KEY,SECRET_KEY,)


def get_stock_price(symbol: str) -> float:

    request = StockLatestTradeRequest(
        symbol_or_symbols=symbol,
        feed=DataFeed.SIP,
    )

    trade = stock_client.get_stock_latest_trade(request)

    return float(trade[symbol].price)


# ============================================================
# GET OPTION CHAIN
# ============================================================

def get_option_chain(symbol: str, underlying_price: float):

    today = date.today()
    max_expiration = today + timedelta(days=MAX_DTE)

    request = OptionChainRequest(
        underlying_symbol=symbol,

        # Paid OPRA options feed
        feed=OptionsFeed.OPRA,

        # +/- $20 around stock price
        strike_price_gte=underlying_price - STRIKE_RANGE,
        strike_price_lte=underlying_price + STRIKE_RANGE,

        # 0-20 DTE
        expiration_date_gte=today,
        expiration_date_lte=max_expiration,
    )

    return option_client.get_option_chain(request)


# ============================================================
# CONVERT ALPACA MODELS TO JSON
# ============================================================

def serialize_chain(chain):

    data = {}

    for option_symbol, snapshot in chain.items():

        if hasattr(snapshot, "model_dump"):
            data[option_symbol] = snapshot.model_dump(
                mode="json",
                exclude_none=False,
            )
        else:
            data[option_symbol] = snapshot

    return data


def is_market_open() -> bool:
    now = datetime.now(MARKET_TZ)
    return now.weekday() < 5 and MARKET_OPEN <= now.time() < MARKET_CLOSE


# ============================================================
# SAVE SNAPSHOT
# ============================================================

def save_chain(day_folder: Path, symbol: str, underlying_price: float, chain):

    now = datetime.now(timezone.utc)

    timestamp = now.strftime("%Y%m%d_%H%M%S_%f")

    folder = day_folder / symbol
    folder.mkdir(parents=True, exist_ok=True)

    file_path = folder / f"{timestamp}.json"

    payload = {
        "timestamp_utc": now.isoformat(),
        "underlying": symbol,
        "underlying_price": underlying_price,

        "filters": {
            "strike_min": underlying_price - STRIKE_RANGE,
            "strike_max": underlying_price + STRIKE_RANGE,
            "expiration_min": date.today().isoformat(),
            "expiration_max": (
                date.today() + timedelta(days=MAX_DTE)
            ).isoformat(),
        },

        "contract_count": len(chain),

        "chain": serialize_chain(chain),
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"))
    return file_path




def main():
    day_folder = generate_folders()

    while True:
        now = datetime.now(MARKET_TZ)

        if ENFORCE_MARKET_HOURS and not is_market_open(now):
            print(f"{now} | Market closed. Waiting for next session...")
            time.sleep(60)
            continue

        try:

            for symbol in SYMBOLS:
                underlying_price = get_stock_price(symbol)

                chain = get_option_chain(
                    symbol,
                    underlying_price,
                )

                file_path = save_chain(
                    day_folder,
                    symbol,
                    underlying_price,
                    chain,
                )

                print(
                    f"{datetime.now()} | "
                    f"{symbol} ${underlying_price:.2f} | "
                    f"{len(chain)} contracts | "
                    f"{file_path}"
                )

        except KeyboardInterrupt:
            print("\nCollector stopped.")
            break

        except Exception as error:
            print(f"ERROR: {error}")

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    if ENFORCE_MARKET_HOURS:
        print("Waiting for market open (9:30 AM ET)...")

        while not is_market_open():
            now = datetime.now(MARKET_TZ)

            if now.weekday() >= 5:
                print(f"{now} | Weekend. Waiting until Monday market open...")
                generate_folders()
            else:
                print(f"{now} | Outside market hours. Waiting for 9:30 AM ET...")

            time.sleep(60)
    else:
        print("Market-hours check is disabled for testing.")

    print(f"Starting collector at {datetime.now(MARKET_TZ)}")
    main()