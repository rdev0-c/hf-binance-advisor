import pandas as pd
import ta
import os

# Get symbol from environment variable
SYMBOL = os.getenv('TRADING_SYMBOL')
if not SYMBOL:
    raise ValueError("Trading symbol not set in environment variables")

# Load OHLCV data
folder_name = f"tmp/{SYMBOL}"
ohlcv_file = f"{folder_name}/{SYMBOL}_ohlcv.csv"

if not os.path.exists(ohlcv_file):
    raise FileNotFoundError(f"OHLCV data file not found: {ohlcv_file}")

df = pd.read_csv(ohlcv_file)

# Calculate Technical Indicators
# Moving Averages
df["SMA_20"] = ta.trend.sma_indicator(df["close"], window=20)
df["EMA_20"] = ta.trend.ema_indicator(df["close"], window=20)
df["SMA_50"] = ta.trend.sma_indicator(df["close"], window=50)
df["EMA_50"] = ta.trend.ema_indicator(df["close"], window=50)
df["SMA_200"] = ta.trend.sma_indicator(df["close"], window=200)
df["EMA_200"] = ta.trend.ema_indicator(df["close"], window=200)

# Relative Strength Index
df["RSI"] = ta.momentum.rsi(df["close"], window=14)

# MACD
df["MACD"] = ta.trend.macd(df["close"], window_slow=26, window_fast=12)
df["MACD_Signal"] = ta.trend.macd_signal(df["close"], window_slow=26, window_fast=12)
df["MACD_Diff"] = ta.trend.macd_diff(df["close"], window_slow=26, window_fast=12)

# Bollinger Bands
bb_indicator = ta.volatility.BollingerBands(df["close"], window=20, window_dev=2)
df["BB_Upper"] = bb_indicator.bollinger_hband()
df["BB_Lower"] = bb_indicator.bollinger_lband()
df["BB_Middle"] = bb_indicator.bollinger_mavg()

# Volume-weighted Average Price (VWAP)
df["VWAP"] = ta.volume.VolumeWeightedAveragePrice(
    high=df["high"],
    low=df["low"],
    close=df["close"],
    volume=df["volume"],
).volume_weighted_average_price()

# Save Technical Indicators Data
technical_indicators_file = f"{folder_name}/{SYMBOL}_technical_indicators.csv"
df.to_csv(technical_indicators_file, index=False)

# Display the result
print(f"✅ Technical Indicators Data saved successfully as {technical_indicators_file}")
