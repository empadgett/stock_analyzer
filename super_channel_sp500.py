import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import os
from datetime import datetime

PARAMS = {
    'max_lookback': 240,  # One year
    'min_lookback': 30,
    'deviation_threshold': 0.1,
    'min_channel_length': 10,
    'parallel_tolerance': 0.2,
    'min_touches': 2,
    'r2_threshold': 0.6
}

def are_parallel(slope1, slope2, tolerance=PARAMS['parallel_tolerance']):
    return abs(slope1 - slope2) < tolerance

def calculate_touches(prices, line, threshold=0.03):
    touches = sum(1 for price, line_price in zip(prices, line) 
                 if abs(price - line_price) / line_price < threshold)
    return touches

def find_dynamic_channel(df, params=PARAMS):
    prices = df['Close'].values
    
    for lookback in range(params['min_lookback'], params['max_lookback']):
        window = prices[-lookback:]
        indices = np.arange(len(window))
        
        # Find local maxima and minima
        highs = []
        lows = []
        for i in range(1, len(window)-1):
            if window[i] > window[i-1] and window[i] > window[i+1]:
                highs.append((i, window[i]))
            if window[i] < window[i-1] and window[i] < window[i+1]:
                lows.append((i, window[i]))
        
        if len(highs) < params['min_touches'] or len(lows) < params['min_touches']:
            continue
            
        try:
            # Sort highs and lows by price
            highs.sort(key=lambda x: x[1], reverse=True)
            lows.sort(key=lambda x: x[1])
            
            # Take the top n highest peaks and lowest troughs
            top_n = min(len(highs), len(lows), params['min_touches'])
            high_x = np.array([x[0] for x in highs[:top_n]])
            high_y = np.array([x[1] for x in highs[:top_n]])
            low_x = np.array([x[0] for x in lows[:top_n]])
            low_y = np.array([x[1] for x in lows[:top_n]])
            
            # Perform linear regression
            high_slope, high_intercept, high_r, _, _ = stats.linregress(high_x, high_y)
            low_slope, low_intercept, low_r, _, _ = stats.linregress(low_x, low_y)
            
            if high_r**2 < params['r2_threshold'] or low_r**2 < params['r2_threshold']:
                continue
                
            if not are_parallel(high_slope, low_slope, params['parallel_tolerance']):
                continue
            
            # Generate channel lines
            x = np.arange(len(window))
            upper_line = high_slope * x + high_intercept
            lower_line = low_slope * x + low_intercept
            
            # Check if price stays within channel
            if not (all(window <= upper_line * (1 + params['deviation_threshold'])) and 
                    all(window >= lower_line * (1 - params['deviation_threshold']))):
                continue
            
            upper_touches = calculate_touches(window, upper_line)
            lower_touches = calculate_touches(window, lower_line)
            
            if upper_touches >= params['min_touches'] and lower_touches >= params['min_touches']:
                return high_slope, high_intercept, low_slope, low_intercept, len(prices) - lookback
                
        except ValueError:
            continue
    
    return None, None, None, None, None

def main():
    directory = 'sp500pricedata'
    channels_found = 0
    
    for filename in os.listdir(directory):
        if filename.endswith('.csv'):
            file_path = os.path.join(directory, filename)
            
            df = pd.read_csv(file_path)
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
            
            high_slope, high_intercept, low_slope, low_intercept, channel_start = find_dynamic_channel(df, PARAMS)

            if high_slope is not None:
                channels_found += 1
                
                # Generate channel lines
                x = np.arange(len(df) - channel_start)
                upper_channel = high_slope * x + high_intercept
                lower_channel = low_slope * x + low_intercept
                
                channel_duration = (df.index[-1] - df.index[channel_start]).days
                channel_width = ((upper_channel[-1] - lower_channel[-1])/lower_channel[-1])*100
                
                # Plot only if channel width is reasonable
                if channel_width < 50:  # Add reasonable threshold
                    plt.figure(figsize=(15, 7))
                    plt.plot(df.index, df['Close'], label='Close Price')
                    plt.plot(df.index[channel_start:], upper_channel, 'r--', label='Upper Channel')
                    plt.plot(df.index[channel_start:], lower_channel, 'g--', label='Lower Channel')
                    
                    plt.legend()
                    plt.title(f'Price Channel Detection: {filename}\nChannel Duration: {channel_duration} days')
                    plt.xlabel('Date')
                    plt.ylabel('Price')
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    plt.show()
                    
                    print(f"Channel found for {filename}")
                    print(f"Duration: {channel_duration} days")
                    print(f"Channel width: {channel_width:.2f}%")
                    print("------------------------")

    print(f"Total channels found: {channels_found}")

if __name__ == "__main__":
    main()


