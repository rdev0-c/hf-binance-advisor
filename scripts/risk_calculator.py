import pandas as pd
import numpy as np
from binance.client import Client
import os
import ta

class RiskCalculator:
    def __init__(self, symbol):
        self.symbol = symbol
        self.client = Client()
        self.load_data()
        
    def load_data(self):
        """Load OHLCV and technical data"""
        data_folder = f"tmp/{self.symbol}"
        self.df = pd.read_csv(f'{data_folder}/{self.symbol}_ohlcv.csv')
        self.current_price = float(self.client.get_symbol_ticker(symbol=self.symbol)['price'])
        
    def calculate_atr(self, period=14):
        """Calculate Average True Range"""
        high = self.df['high']
        low = self.df['low']
        close = self.df['close']
        
        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calculate ATR
        atr = tr.rolling(window=period).mean().iloc[-1]
        return atr
        
    def calculate_support_resistance(self, lookback=20):
        """Calculate support and resistance levels"""
        recent_data = self.df.tail(lookback)
        
        # Find local minima and maxima
        support_levels = []
        resistance_levels = []
        
        for i in range(1, len(recent_data)-1):
            if recent_data.iloc[i]['low'] < recent_data.iloc[i-1]['low'] and \
               recent_data.iloc[i]['low'] < recent_data.iloc[i+1]['low']:
                support_levels.append(recent_data.iloc[i]['low'])
                
            if recent_data.iloc[i]['high'] > recent_data.iloc[i-1]['high'] and \
               recent_data.iloc[i]['high'] > recent_data.iloc[i+1]['high']:
                resistance_levels.append(recent_data.iloc[i]['high'])
        
        # Get closest levels
        support_levels = sorted([x for x in support_levels if x < self.current_price])
        resistance_levels = sorted([x for x in resistance_levels if x > self.current_price])
        
        return {
            'closest_support': support_levels[-1] if support_levels else self.current_price * 0.95,
            'closest_resistance': resistance_levels[0] if resistance_levels else self.current_price * 1.05
        }
        
    def calculate_volatility(self, lookback=20):
        """Calculate price volatility"""
        recent_data = self.df.tail(lookback)
        return np.std(recent_data['close'].pct_change().dropna())
        
    def get_price_targets(self):
        """Calculate stop loss and target prices"""
        # Get ATR for volatility-based calculations
        atr = self.calculate_atr()
        
        # Get support/resistance levels
        levels = self.calculate_support_resistance()
        
        # Get volatility
        volatility = self.calculate_volatility()
        
        # Calculate stop loss (based on ATR and closest support)
        stop_loss_atr = self.current_price - (atr * 2)  # 2 ATR below current price
        stop_loss_support = levels['closest_support']
        stop_loss = max(stop_loss_atr, stop_loss_support)  # Use the higher of the two
        
        # Calculate risk (difference between current price and stop loss)
        risk = self.current_price - stop_loss
        
        # Calculate targets based on risk:reward ratios
        target_1 = self.current_price + (risk * 1.5)  # 1.5:1 risk:reward
        target_2 = self.current_price + (risk * 2)    # 2:1 risk:reward
        target_3 = self.current_price + (risk * 3)    # 3:1 risk:reward
        
        # Adjust targets based on resistance levels
        if target_1 > levels['closest_resistance']:
            target_1 = levels['closest_resistance']
        
        # Format prices based on current price magnitude
        def format_price(price):
            if price < 0.0001:
                return f"{price:.8f}"
            elif price < 0.01:
                return f"{price:.6f}"
            elif price < 1:
                return f"{price:.4f}"
            else:
                return f"{price:.2f}"
        
        return {
            'current_price': format_price(self.current_price),
            'stop_loss': format_price(stop_loss),
            'targets': {
                'conservative': format_price(target_1),
                'moderate': format_price(target_2),
                'aggressive': format_price(target_3)
            },
            'risk_percentage': abs((stop_loss - self.current_price) / self.current_price * 100),
            'atr': format_price(atr),
            'volatility': f"{volatility*100:.2f}%"
        }

def main():
    try:
        symbol = os.getenv('TRADING_SYMBOL')
        if not symbol:
            symbol = input("Enter trading pair symbol (e.g., BTCUSDT): ").upper()
        
        calculator = RiskCalculator(symbol)
        targets = calculator.get_price_targets()
        
        print(f"\n📊 Price Targets for {symbol}:")
        print(f"Current Price: {targets['current_price']}")
        print(f"Stop Loss: {targets['stop_loss']} ({targets['risk_percentage']:.2f}% risk)")
        print("\nTarget Prices:")
        print(f"🎯 Conservative: {targets['targets']['conservative']}")
        print(f"🎯 Moderate: {targets['targets']['moderate']}")
        print(f"🎯 Aggressive: {targets['targets']['aggressive']}")
        print(f"\nMarket Metrics:")
        print(f"ATR: {targets['atr']}")
        print(f"Volatility: {targets['volatility']}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main()) 