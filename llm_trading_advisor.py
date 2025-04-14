import pandas as pd
import numpy as np
import requests
import os
from datetime import datetime
import json
import ta
import time
from binance.client import Client

class TradingAdvisor:
    def __init__(self, symbol, hf_api_key=None, provider='huggingface'):
        """Initialize the trading advisor"""
        self.symbol = symbol
        self.hf_api_key = hf_api_key or os.getenv('HF_API_KEY')
        self.provider = provider
        
        if not self.hf_api_key:
            raise ValueError("Hugging Face API key is required")
        
        # Initialize Binance client
        self.binance_client = Client()
        
        # Load and prepare market data
        self.load_market_data()
    
    def get_realtime_price(self):
        """Get real-time price data from Binance"""
        try:
            ticker = self.binance_client.get_symbol_ticker(symbol=self.symbol)
            return float(ticker['price'])
        except Exception as e:
            print(f"Error fetching real-time price: {e}")
            return None
            
    def get_realtime_depth(self):
        """Get real-time order book data from Binance"""
        try:
            depth = self.binance_client.get_order_book(symbol=self.symbol, limit=20)
            
            # Calculate buy and sell walls
            buy_wall = sum(float(bid[1]) for bid in depth['bids'][:5])
            sell_wall = sum(float(ask[1]) for ask in depth['asks'][:5])
            
            # Calculate bid and ask quantities
            bid_qty = float(depth['bids'][0][1])
            ask_qty = float(depth['asks'][0][1])
            
            return {
                'Buy Wall': buy_wall,
                'Sell Wall': sell_wall,
                'Bid Quantity': bid_qty,
                'Ask Quantity': ask_qty
            }
        except Exception as e:
            print(f"Error fetching market depth: {e}")
            return None
    
    def format_price(self, price):
        """Format price with appropriate decimal places"""
        if price < 0.0001:
            return f"{price:.8f}"
        elif price < 0.01:
            return f"{price:.6f}"
        elif price < 1:
            return f"{price:.4f}"
        else:
            return f"{price:.2f}"

    def load_market_data(self):
        """Load and calculate necessary market indicators from multiple data sources"""
        # Check if required data files exist
        data_folder = f"tmp/{self.symbol}"
        required_files = [
            f'{data_folder}/{self.symbol}_ohlcv.csv',
            f'{data_folder}/{self.symbol}_technical_indicators.csv',
            f'{data_folder}/{self.symbol}_market_depth.csv'
        ]
        
        missing_files = [f for f in required_files if not os.path.exists(f)]
        if missing_files:
            raise FileNotFoundError(
                f"Required data files are missing: {', '.join(missing_files)}\n"
                "Please ensure all required CSV files are present in the data directory"
            )
        
        # Load OHLCV data
        ohlcv_df = pd.read_csv(f'{data_folder}/{self.symbol}_ohlcv.csv')
        
        # Load technical indicators
        tech_df = pd.read_csv(f'{data_folder}/{self.symbol}_technical_indicators.csv')
        
        # Load market depth
        depth_df = pd.read_csv(f'{data_folder}/{self.symbol}_market_depth.csv')
        
        # Get real-time data
        current_price = self.get_realtime_price()
        depth_data = self.get_realtime_depth()
        
        if current_price:
            print(f"\nReal-time {self.symbol} price: {self.format_price(current_price)}")
        
        # Store the latest data
        self.latest_ohlcv = ohlcv_df.iloc[-1].copy()
        self.prev_ohlcv = ohlcv_df.iloc[-2].copy()
        
        # Update with real-time price if available
        if current_price:
            self.latest_ohlcv['close'] = current_price
        
        self.latest_tech = tech_df.iloc[-1]
        self.prev_tech = tech_df.iloc[-2]
        
        # Store real-time market depth
        self.latest_depth = depth_data if depth_data else pd.Series({
            'Buy Wall': 0,
            'Sell Wall': 0,
            'Bid Quantity': 0,
            'Ask Quantity': 0
        })
        
        print(f"\n{self.symbol} Market Data Loaded:")
        print(f"Current Price: {self.format_price(self.latest_ohlcv['close'])}")
        print(f"RSI: {self.latest_tech['RSI']:.2f}")
        print(f"MACD: {self.latest_tech['MACD']:.8f}")
        print(f"MACD Signal: {self.latest_tech['MACD_Signal']:.8f}")
        if depth_data:
            print(f"Buy Wall: {self.latest_depth['Buy Wall']:.2f}")
            print(f"Sell Wall: {self.latest_depth['Sell Wall']:.2f}")

    def analyze_market_depth(self):
        """Analyze market depth and return pressure description"""
        bid_qty = self.latest_depth['Bid Quantity']
        ask_qty = self.latest_depth['Ask Quantity']
        buy_wall = self.latest_depth['Buy Wall']
        sell_wall = self.latest_depth['Sell Wall']
        
        # Calculate buy/sell pressure ratio
        wall_ratio = buy_wall / sell_wall if sell_wall != 0 else float('inf')
        qty_ratio = bid_qty / ask_qty if ask_qty != 0 else float('inf')
        
        if wall_ratio > 1.2 and qty_ratio > 1.2:
            return "strong buy pressure"
        elif wall_ratio < 0.8 and qty_ratio < 0.8:
            return "strong sell pressure"
        else:
            return "balanced"

    def analyze_rsi(self):
        """Analyze RSI and return condition"""
        rsi = self.latest_tech['RSI']
        if pd.isna(rsi):
            return "unavailable"
        
        if rsi <= 30:
            return f"oversold at {rsi:.1f}"
        elif rsi >= 70:
            return f"overbought at {rsi:.1f}"
        else:
            return f"neutral at {rsi:.1f}"

    def analyze_macd(self):
        """Analyze MACD and return crossing condition"""
        macd = self.latest_tech['MACD']
        signal = self.latest_tech['MACD_Signal']
        
        if pd.isna(macd) or pd.isna(signal):
            return "unavailable"
        
        prev_macd = self.prev_tech['MACD']
        prev_signal = self.prev_tech['MACD_Signal']
        
        # Check for crossovers
        if macd > signal and prev_macd <= prev_signal:
            return "bullish crossover"
        elif macd < signal and prev_macd >= prev_signal:
            return "bearish crossover"
        elif macd > signal:
            return "bullish trend"
        else:
            return "bearish trend"

    def analyze_price_pattern(self, lookback=300):
        """Analyze recent price patterns and convert to text description"""
        try:
            # Get last N periods of data
            ohlcv_df = pd.read_csv(f'tmp/{self.symbol}/{self.symbol}_ohlcv.csv')
            recent_data = ohlcv_df.tail(lookback)
            
            # Calculate key pattern indicators
            highs = recent_data['high'].values
            lows = recent_data['low'].values
            closes = recent_data['close'].values
            
            # Identify trend
            trend_close = closes[-1] - closes[0]
            trend = "upward" if trend_close > 0 else "downward"
            
            # Calculate swing points
            swing_highs = []
            swing_lows = []
            
            for i in range(1, len(highs)-1):
                if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
                    swing_highs.append(highs[i])
                if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
                    swing_lows.append(lows[i])
            
            # Support/Resistance levels
            support = min(lows[-5:])
            resistance = max(highs[-5:])
            
            # Analyze price structure
            pattern_desc = {
                'trend': trend,
                'support': support,
                'resistance': resistance,
                'volatility': np.std(closes[-5:]) / np.mean(closes[-5:]) * 100
            }
            
            return pattern_desc
            
        except Exception as e:
            print(f"Error in pattern analysis: {e}")
            return {
                'trend': 'unknown',
                'support': self.latest_ohlcv['low'],
                'resistance': self.latest_ohlcv['high'],
                'volatility': 0
            }

    def analyze_historical_data(self, lookback=120):  # 120 4-hour periods = 20 days
        """Analyze historical price and volume data"""
        try:
            # Load historical data
            ohlcv_df = pd.read_csv(f'tmp/{self.symbol}/{self.symbol}_ohlcv.csv')
            tech_df = pd.read_csv(f'tmp/{self.symbol}/{self.symbol}_technical_indicators.csv')
            
            # Get recent data
            recent_ohlcv = ohlcv_df.tail(lookback)
            recent_tech = tech_df.tail(lookback)
            
            # Calculate price metrics
            price_high = recent_ohlcv['high'].max()
            price_low = recent_ohlcv['low'].min()
            price_change_20d = ((recent_ohlcv.iloc[-1]['close'] / recent_ohlcv.iloc[0]['close'] - 1) * 100)
            
            # Calculate shorter timeframe changes
            price_change_5d = ((recent_ohlcv.iloc[-1]['close'] / recent_ohlcv.iloc[-30]['close'] - 1) * 100)
            price_change_24h = ((recent_ohlcv.iloc[-1]['close'] / recent_ohlcv.iloc[-6]['close'] - 1) * 100)
            
            # Volume analysis
            avg_volume = recent_ohlcv['volume'].mean()
            recent_avg_volume = recent_ohlcv['volume'].tail(6).mean()  # Last 24h
            volume_change = ((recent_avg_volume / avg_volume - 1) * 100)
            
            # Technical indicator trends
            rsi_values = recent_tech['RSI'].dropna().tolist()
            macd_values = recent_tech['MACD'].dropna().tolist()
            
            # Determine trends
            rsi_trend = "neutral"
            if len(rsi_values) >= 2:
                rsi_short_trend = "rising" if rsi_values[-1] > rsi_values[-2] else "falling"
                rsi_long_trend = "rising" if rsi_values[-1] > rsi_values[0] else "falling"
                rsi_trend = f"{rsi_short_trend} short-term, {rsi_long_trend} long-term"
            
            macd_trend = "neutral"
            if len(macd_values) >= 2:
                macd_short_trend = "rising" if macd_values[-1] > macd_values[-2] else "falling"
                macd_long_trend = "rising" if macd_values[-1] > macd_values[0] else "falling"
                macd_trend = f"{macd_short_trend} short-term, {macd_long_trend} long-term"
            
            return {
                'period_days': lookback * 4/24,
                'price_high': price_high,
                'price_low': price_low,
                'price_change_20d': price_change_20d,
                'price_change_5d': price_change_5d,
                'price_change_24h': price_change_24h,
                'avg_volume': avg_volume,
                'volume_change': volume_change,
                'rsi_trend': rsi_trend,
                'macd_trend': macd_trend
            }
        except Exception as e:
            print(f"Error analyzing historical data: {e}")
            return None

    def calculate_fibonacci_levels(self, lookback=100):
        """Calculate Fibonacci retracement levels for recent price action"""
        try:
            # Load recent OHLCV data
            ohlcv_df = pd.read_csv(f'tmp/{self.symbol}/{self.symbol}_ohlcv.csv')
            recent_data = ohlcv_df.tail(lookback)
            
            # Find swing high and low
            high = recent_data['high'].max()
            low = recent_data['low'].min()
            price_range = high - low
            
            # Calculate Fibonacci levels (common ratios: 0.236, 0.382, 0.5, 0.618, 0.786)
            fib_levels = {
                '0.236': high - (price_range * 0.236),
                '0.382': high - (price_range * 0.382),
                '0.5': high - (price_range * 0.5),
                '0.618': high - (price_range * 0.618),
                '0.786': high - (price_range * 0.786)
            }
            
            # Get current price
            current_price = self.latest_ohlcv['close']
            
            # Analyze price position relative to Fibonacci levels
            price_position = "above all levels"
            support_level = None
            resistance_level = None
            
            for level, price in fib_levels.items():
                if current_price < price:
                    resistance_level = f"{level} ({self.format_price(price)})"
                    continue
                if current_price > price:
                    support_level = f"{level} ({self.format_price(price)})"
                    break
            
            return {
                'levels': fib_levels,
                'current_price': current_price,
                'nearest_support': support_level,
                'nearest_resistance': resistance_level,
                'is_buy_zone': current_price <= fib_levels['0.618']  # Consider it a buy zone if price is below 0.618
            }
            
        except Exception as e:
            print(f"Error calculating Fibonacci levels: {e}")
            return None

    def generate_prompt(self):
        """Generate a prompt for the LLM based on market conditions"""
        price_change = ((self.latest_ohlcv['close'] / self.prev_ohlcv['close'] - 1) * 100)
        pattern_analysis = self.analyze_price_pattern()
        historical_data = self.analyze_historical_data()
        
        # Build sections separately
        header = f"Analyze {self.symbol} market conditions:"
        
        historical_section = [
            "HISTORICAL DATA (20-day analysis):",
            f"- Price Range: {self.format_price(historical_data['price_low'])} - {self.format_price(historical_data['price_high'])}",
            f"- 20-day Change: {historical_data['price_change_20d']:.2f}%",
            f"- 5-day Change: {historical_data['price_change_5d']:.2f}%",
            f"- 24h Change: {historical_data['price_change_24h']:.2f}%",
            f"- Volume Trend: {historical_data['volume_change']:.2f}% vs 20-day average",
            f"- RSI Trend: {historical_data['rsi_trend']}",
            f"- MACD Trend: {historical_data['macd_trend']}"
        ] if historical_data else ["HISTORICAL DATA: Not available"]
        
        price_section = [
            "CURRENT MARKET:",
            f"- Price: {self.format_price(self.latest_ohlcv['close'])} ({price_change:.2f}% 4h change)",
            f"- Support: {self.format_price(pattern_analysis['support'])}",
            f"- Resistance: {self.format_price(pattern_analysis['resistance'])}",
            f"- Trend: {pattern_analysis['trend']}"
        ]
        
        technical_section = [
            "TECHNICAL INDICATORS:",
            f"- RSI: {self.latest_tech['RSI']:.2f} (oversold < 30, overbought > 70)",
            f"- MACD: {self.latest_tech['MACD']:.8f}",
            f"- MACD Signal: {self.latest_tech['MACD_Signal']:.8f}",
            f"- MACD Trend: {self.analyze_macd()}"
        ]
        
        depth_section = [
            "MARKET DEPTH:",
            f"- Buy Wall: {self.latest_depth['Buy Wall']:.2f}",
            f"- Sell Wall: {self.latest_depth['Sell Wall']:.2f}",
            f"- Pressure: {self.analyze_market_depth()}"
        ]
        
        # Add Fibonacci analysis
        fib_analysis = self.calculate_fibonacci_levels()
        if fib_analysis:
            fibonacci_section = [
                "FIBONACCI ANALYSIS:",
                f"- Nearest Support: {fib_analysis['nearest_support'] or 'None'}",
                f"- Nearest Resistance: {fib_analysis['nearest_resistance'] or 'None'}",
                f"- Buy Zone: {'Yes' if fib_analysis['is_buy_zone'] else 'No'}"
            ]
        else:
            fibonacci_section = ["FIBONACCI ANALYSIS: Not available"]
        
        footer = "Provide a clear BUY, SELL, or HOLD recommendation. Give one-sentence reason."
        
        # Join sections with newlines
        sections = [
            header,
            " ".join(historical_section),
            " ".join(price_section),
            " ".join(technical_section),
            " ".join(depth_section),
            " ".join(fibonacci_section),
            footer
        ]
        
        prompt = " ".join(sections)
        return prompt

    def get_llm_response(self, prompt):
        """Get response from LLM API"""
        if self.provider == 'huggingface':
            API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
            headers = {"Authorization": f"Bearer {self.hf_api_key}"}
            
            formatted_prompt = f"<s>[INST] {prompt} [/INST]"
            
            try:
                response = requests.post(
                    API_URL,
                    headers=headers,
                    json={
                        "inputs": formatted_prompt,
                        "parameters": {
                            "max_length": 100,
                            "temperature": 0.3,  # Lower temperature for more focused responses
                            "top_p": 0.9
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        # Clean up response by removing instruction tokens and extra whitespace
                        text = result[0].get('generated_text', '').strip()
                        text = text.replace(formatted_prompt, '').strip()
                        return text
                    return str(result)
                else:
                    return f"Error: {response.status_code} - {response.text}"
                    
            except Exception as e:
                return f"API Error: {str(e)}"
        
        return "Provider not supported"

    def _extract_recommendation(self, response):
        """Extract the trading recommendation from the response"""
        response_lower = response.lower()
        if 'buy' in response_lower:
            return 'BUY'
        elif 'sell' in response_lower:
            return 'SELL'
        else:
            return 'HOLD'

def main():
    """Main execution function"""
    try:
        # Get symbol input from user
        symbol = input("Enter trading pair symbol (e.g., BTCUSDT): ").upper()
        
        # Import and run the data fetching scripts
        import importlib.util
        import sys
        
        # Function to import and run a script and get its output
        def run_script(script_name):
            spec = importlib.util.spec_from_file_location(script_name, f"scripts/{script_name}.py")
            module = importlib.util.module_from_spec(spec)
            sys.modules[script_name] = module
            spec.loader.exec_module(module)
            if hasattr(module, 'main'):
                return module.main()
            return None
        
        # Check if data files exist, if not, fetch them
        data_folder = f"tmp/{symbol}"
        required_files = [
            f'{data_folder}/{symbol}_ohlcv.csv',
            f'{data_folder}/{symbol}_technical_indicators.csv',
            f'{data_folder}/{symbol}_market_depth.csv'
        ]
        
        missing_files = [f for f in required_files if not os.path.exists(f)]
        if missing_files:
            print(f"\nFetching required data for {symbol}...")
            
            # Set the symbol as an environment variable for the scripts to use
            os.environ['TRADING_SYMBOL'] = symbol
            
            # Create the data directory if it doesn't exist
            os.makedirs(data_folder, exist_ok=True)
            
            # Run the scripts in order
            print("Fetching OHLCV data...")
            run_script("ohlcv_data_fetch")
            print("\nCalculating technical indicators...")
            run_script("technical_indicators_fetch")
            print("\nFetching market depth...")
            run_script("market_depth_fetch")
            print("\nData fetching complete!")
        
        advisor = TradingAdvisor(symbol)
        prompt = advisor.generate_prompt()
        print("\nGenerated Prompt:")
        print(prompt)
        
        response = advisor.get_llm_response(prompt)
        print("\nLLM Response:")
        print(response)
        recommendation = advisor._extract_recommendation(response)
        print(f"\nRecommendation: {recommendation}")
        
        # If recommendation is BUY, run the price calculator script
        if recommendation == "BUY":
            print("\nCalculating price targets...")
            os.environ['TRADING_SYMBOL'] = symbol  # Ensure symbol is set
            
            # Import PriceCalculator directly
            from scripts.risk_calculator import RiskCalculator
            calculator = RiskCalculator(symbol)
            targets = calculator.get_price_targets()
            
            print(f"\n📊 Entry/Exit Levels for {symbol}:")
            print(f"Current Price: {targets['current_price']}")
            print(f"Stop Loss: {targets['stop_loss']} ({targets['risk_percentage']:.2f}% risk)")
            print("\nTarget Prices:")
            print(f"🎯 Conservative: {targets['targets']['conservative']}")
            print(f"🎯 Moderate: {targets['targets']['moderate']}")
            print(f"🎯 Aggressive: {targets['targets']['aggressive']}")
            print(f"\nMarket Metrics:")
            print(f"ATR: {targets['atr']}")
            print(f"Volatility: {targets['volatility']}")
        
        # Purge CSV data after completion
        purge_csv_data()
        
    except Exception as e:
        print(f"❌ Error in main: {str(e)}")
        return 1
    return 0

def purge_csv_data():
    """Delete all CSV files and empty directories in the data directory"""
    try:
        data_dir = "tmp"
        
        if not os.path.exists(data_dir):
            return
            
        # First, delete all CSV files
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                if file.endswith('.csv'):
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass
        
        # Then remove empty directories (bottom-up to ensure parent directories are empty)
        for root, dirs, files in os.walk(data_dir, topdown=False):
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    # Only remove if directory is empty
                    if not os.listdir(dir_path):
                        os.rmdir(dir_path)
                except Exception:
                    pass
    except Exception:
        pass

if __name__ == "__main__":
    exit(main())