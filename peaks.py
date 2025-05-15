import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import os
from datetime import datetime

PARAMS = {
    'max_lookback': 360,  # Longer lookback for several months
    'min_lookback': 60,   # Minimum 2 months
    'offset_days': 15,    # Offset from present
    'deviation_threshold': 0.1,
    'min_channel_length': 30,
    'min_touches': 3,     # Increased for more significant patterns
    'r2_threshold': 0.6
}

def calculate_touches(prices, line, threshold=0.03):
    touches = sum(1 for price, line_price in zip(prices, line) 
                 if abs(price - line_price) / line_price < threshold)
    return touches

def find_dynamic_channel(df, params=PARAMS):
    # Create offset window
    offset_end = -params['offset_days'] if params['offset_days'] > 0 else None
    prices = df['Close'].values[:offset_end]
    
    for lookback in range(params['min_lookback'], params['max_lookback']):
        window = prices[-lookback:]
        indices = np.arange(len(window))
        
        # Find local maxima and minima
        highs = []
        lows = []
        for i in range(1, len(window)-1):
            # Use wider window for peak detection
            left_window = window[max(0, i-10):i]
            right_window = window[i+1:min(len(window), i+11)]
            
            # Check if point is higher/lower than surrounding points
            if (window[i] > np.max(left_window) and 
                window[i] > np.max(right_window)):
                highs.append((i, window[i]))
            if (window[i] < np.min(left_window) and 
                window[i] < np.min(right_window)):
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
                x = np.arange(len(df) - channel_start - PARAMS['offset_days'])
                upper_channel = high_slope * x + high_intercept
                lower_channel = low_slope * x + low_intercept
                
                # Calculate duration excluding offset period
                channel_duration = (df.index[-PARAMS['offset_days']] - df.index[channel_start]).days
                channel_width = ((upper_channel[-1] - lower_channel[-1])/lower_channel[-1])*100
                
                # Plot only if channel width is reasonable
                if channel_width < 50:
                    plt.figure(figsize=(15, 7))
                    
                    # Plot full price history
                    plt.plot(df.index, df['Close'], label='Close Price')
                    
                    # Plot channel lines up to offset
                    channel_end = -PARAMS['offset_days'] if PARAMS['offset_days'] > 0 else len(df)
                    plt.plot(df.index[channel_start:channel_end], upper_channel, 'r--', label='Upper Channel')
                    plt.plot(df.index[channel_start:channel_end], lower_channel, 'g--', label='Lower Channel')
                    
                    # Add vertical line to show offset
                    plt.axvline(x=df.index[-PARAMS['offset_days']], color='gray', linestyle=':', label='Offset Point')
                    
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
