import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import yfinance as yf

# Define parameters that might need optimization
PARAMS = {
    'max_lookback': 70,  # Approximately 4 weeks of trading days
    'deviation_threshold': 0.07,  # Increased for higher volatility
    'min_channel_length': 5,  # Reduced to capture shorter-term movements
    'parallel_tolerance': 0.1  # Increased for more flexibility in volatile conditions
}

def are_parallel(slope1, slope2, tolerance=PARAMS['parallel_tolerance']):
    return abs(slope1 - slope2) < tolerance

def find_dynamic_channel(df, params=PARAMS):
    prices = df['Close'].values
    highs, lows = [], []
    
    for i in range(2, min(len(prices), params['max_lookback'])):
        window = prices[-i:]
        
        # Find local extrema
        for j in range(1, len(window) - 1):
            if window[j] > window[j-1] and window[j] > window[j+1]:
                highs.append((len(prices) - i + j, window[j]))
            if window[j] < window[j-1] and window[j] < window[j+1]:
                lows.append((len(prices) - i + j, window[j]))
        
        # Need at least 2 points to form a line
        if len(highs) < 2 or len(lows) < 2:
            continue
        
        # Check if we have enough distinct x values
        if len(set([p[0] for p in highs])) < 2 or len(set([p[0] for p in lows])) < 2:
            continue
        
        # Fit lines to highs and lows
        try:
            high_slope, high_intercept, _, _, _ = stats.linregress([p[0] for p in highs], [p[1] for p in highs])
            low_slope, low_intercept, _, _, _ = stats.linregress([p[0] for p in lows], [p[1] for p in lows])
        except ValueError:
            # This can happen if all x values are identical
            continue
        
        # Check for parallelism
        if not are_parallel(high_slope, low_slope, tolerance=params['parallel_tolerance']):
            continue
        
        # Check if current price point fits within the channel
        x = len(prices) - i
        upper_bound = high_slope * x + high_intercept
        lower_bound = low_slope * x + low_intercept
        current_price = prices[-i]
        
        # Check for "wall" or "cliff"
        if current_price > upper_bound * (1 + params['deviation_threshold']) or current_price < lower_bound * (1 - params['deviation_threshold']):
            if i > params['min_channel_length']:
                return high_slope, high_intercept, low_slope, low_intercept, len(prices) - i
    
    return None, None, None, None, None


def main():
# Read portfolio symbols from .env.symbols
    with open('.env.symbols', 'r') as f:
        symbols = [symbol.strip() for symbol in f.read().strip().split('=')[1].split(',')]
    
    for ticker in symbols:
        df=yf.download(ticker,period='ytd')
    
    
        # You can modify parameters here if needed
        # PARAMS['max_lookback'] = 600
        # PARAMS['deviation_threshold'] = 0.06
    
        high_slope, high_intercept, low_slope, low_intercept, channel_start = find_dynamic_channel(df, PARAMS)

        if high_slope is not None:
            # Generate channel lines
            x = np.arange(channel_start, len(df))
            upper_channel = high_slope * x + high_intercept
            lower_channel = low_slope * x + low_intercept
            
            # Plot the results
            plt.figure(figsize=(15, 7))
            plt.plot(df.index, df['Close'], label='Close Price')
            plt.plot(df.index[channel_start:], upper_channel, 'r--', label='Upper Channel')
            plt.plot(df.index[channel_start:], lower_channel, 'g--', label='Lower Channel')
            plt.legend()
            plt.title(f'Price Channel Detection:{ticker}')
            plt.xlabel('Date')
            plt.ylabel('Price')
            plt.show()
        # else:
        #     print("No suitable channel found.")

if __name__ == "__main__":
    main()
