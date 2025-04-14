import pandas as pd
from binance.client import Client
import os

# Connect to Binance
client = Client()

# Get symbol from environment variable
SYMBOL = os.getenv('TRADING_SYMBOL')
if not SYMBOL:
    raise ValueError("Trading symbol not set in environment variables")

INTERVAL = Client.KLINE_INTERVAL_4HOUR  # Options: 1HOUR, 4HOUR, 1DAY
LIMIT = 1000  # Number of data points to fetch

# Validate symbol
try:
    # Test if symbol exists by attempting to get ticker price
    client.get_symbol_ticker(symbol=SYMBOL)
except Exception as e:
    print(f"❌ Error: Invalid symbol '{SYMBOL}'. Please check the trading pair and try again.")
    exit(1)

# Fetch OHLCV Data from Binance
klines = client.get_klines(symbol=SYMBOL, interval=INTERVAL, limit=LIMIT)

# Convert to Pandas DataFrame
df = pd.DataFrame(klines, columns=[
    "timestamp", "open", "high", "low", "close", "volume",
    "close_time", "quote_asset_volume", "num_trades",
    "taker_buy_base", "taker_buy_quote", "ignore"
])

# Convert timestamps and select required columns
df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
df = df[["timestamp", "open", "high", "low", "close", "volume"]]
df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)

# Save as CSV File
folder_name = f"tmp/{SYMBOL}"
os.makedirs(folder_name, exist_ok=True)  # Create folder if it doesn't exist
csv_file = f"{folder_name}/{SYMBOL}_ohlcv.csv"
df.to_csv(csv_file, index=False)

# Display the result
print(f"✅ OHLCV Data saved successfully as {csv_file}")
