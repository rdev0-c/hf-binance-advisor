# LLM Binance Spot Trading Advisor

An LLM powered trading assistant that leverages Mistral-7B-Instruct-v0.2 model from Hugging Face to analyze cryptocurrency market data and provide trading recommendations.

## Features

- **Data Collection**: Automatically fetches OHLCV (Open, High, Low, Close, Volume) data, technical indicators, and market depth from Binance in CSV format
- **Risk Management**: Calculates optimal entry/exit points, stop losses, and multiple price targets based on market volatility
- **Clean Operation**: Automatically purges temporary data files after execution

## Requirements

- Python 3.11
- Hugging Face API Key

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/llm-trading-advisor.git
cd llm-trading-advisor
```

2. Create a virtual environment:

```bash
python3.11 -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up environment variables:

```bash
export HF_API_KEY=your_huggingface_api_key
```

5. Run the script:

```bash
python3.11 ./llm_trading_advisor.py
```

6. Enter trading pair symbol (e.g., BTCUSDT)

```bash
Enter trading pair symbol (e.g., BTCUSDT): [enter your trading pair symbol here]
```

The script will create a folder in the `tmp` directory with the name of the trading pair. After the script is finished, the folder will be purged.

```bash
tmp/
├── BTCUSDT_ohlcv.csv
├── BTCUSDT_technical_indicators.csv
└── BTCUSDT_market_depth.csv
```

## Disclaimer

**IMPORTANT**: This tool is provided for informational and educational purposes only. It is not intended to be, and should not be used as, a primary source of trading advice. Developer of this tool does not take any responsibility for any trading losses incurred from using this tool. Do your own research (DYOR) before making any trading decisions.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
