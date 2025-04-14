import pandas as pd
from binance.client import Client
import os

# 🚀 Binance API Credentials (Replace with your actual keys)
API_KEY = "zJRsVjkZItLKfC2tsHsSYGseyHeIgAUvFf1DbQPCfTPo6Bxg5SNFsNPGWgsktx6c"
API_SECRET = "s0JxS0EvCyUUN7YXAQo0EwqsGR15eyM8t8IXH4QWkMs6ETSIYtvrfMVn3ysiuiAD"

# Connect to Binance
client = Client(API_KEY, API_SECRET)

# Get symbol from environment variable
SYMBOL = os.getenv('TRADING_SYMBOL')
if not SYMBOL:
    raise ValueError("Trading symbol not set in environment variables")

# Validate symbol
try:
    # Test if symbol exists by attempting to get ticker price
    client.get_symbol_ticker(symbol=SYMBOL)
except Exception as e:
    print(f"❌ Error: Invalid symbol '{SYMBOL}'. Please check the trading pair and try again.")
    exit(1)

# 🔄 Fetch Market Depth Data from Binance
depth = client.get_order_book(symbol=SYMBOL)

# Extract bid and ask prices and quantities
bids = depth['bids']
asks = depth['asks']

# Create DataFrames for bids and asks
df_bids = pd.DataFrame(bids, columns=["Bid Price", "Bid Quantity"])
df_asks = pd.DataFrame(asks, columns=["Ask Price", "Ask Quantity"])

# Convert price and quantity columns to float
df_bids["Bid Price"] = df_bids["Bid Price"].astype(float)
df_bids["Bid Quantity"] = df_bids["Bid Quantity"].astype(float)
df_asks["Ask Price"] = df_asks["Ask Price"].astype(float)
df_asks["Ask Quantity"] = df_asks["Ask Quantity"].astype(float)

# Combine bids and asks into a single DataFrame
df_combined = pd.concat([df_bids, df_asks], axis=1)

# Calculate market sentiment via buy/sell walls
buy_wall = df_bids['Bid Quantity'].sum()  # Total liquidity for bids
sell_wall = df_asks['Ask Quantity'].sum()  # Total liquidity for asks

# Add market sentiment to the DataFrame
df_combined['Buy Wall'] = buy_wall
df_combined['Sell Wall'] = sell_wall

# 🌍 Save Market Depth Data as CSV
folder_name = f"tmp/{SYMBOL}"
os.makedirs(folder_name, exist_ok=True)  # Create folder if it doesn't exist
market_depth_file = f"{folder_name}/{SYMBOL}_market_depth.csv"
df_combined.to_csv(market_depth_file, index=False)

# Display the result
print(f"✅ Market Depth Data saved successfully as {market_depth_file}")
print(f"🔍 Market Sentiment:")
print(f"  Buy Wall (Total Bids): {buy_wall}")
print(f"  Sell Wall (Total Asks): {sell_wall}")
