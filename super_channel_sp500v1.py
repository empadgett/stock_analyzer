import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import yfinance as yf
import os


# Define parameters that might need optimization
PARAMS = {
    'max_lookback': 150,  # Approximately 4 weeks of trading days
    'deviation_threshold': 0.07,  # Increased for higher volatility
    'min_channel_length': 3,  # Reduced to capture shorter-term movements
    'parallel_tolerance': .99  # Increased for more flexibility in volatile conditions
}

def are_parallel(slope1, slope2, tolerance=PARAMS['parallel_tolerance']):
    return abs(slope1 - slope2) < tolerance

def find_dynamic_channel(df, params=PARAMS):
    prices = df['Close'].values
    highs, lows = [], []
    
    for i in range(2, min(len(prices), params['max_lookback'])):
        window = prices[-i:]
        window_indices = range(len(prices) - i, len(prices))
        
        # Reset highs and lows for each window
        highs, lows = [], []
        
        # Find local extrema
        for j in range(1, len(window) - 1):
            if window[j] > window[j-1] and window[j] > window[j+1]:
                highs.append((window_indices[j], window[j]))
            if window[j] < window[j-1] and window[j] < window[j+1]:
                lows.append((window_indices[j], window[j]))
        
        # Add endpoint if it's an extremum
        if len(window) > 1:
            if window[-1] > window[-2]:
                highs.append((window_indices[-1], window[-1]))
            if window[-1] < window[-2]:
                lows.append((window_indices[-1], window[-1]))
            if window[0] > window[1]:
                highs.append((window_indices[0], window[0]))
            if window[0] < window[1]:
                lows.append((window_indices[0], window[0]))
        
        # Need at least 2 points to form a line
        if len(highs) < 2 or len(lows) < 2:
            continue
            
        # Sort points by x-coordinate
        highs.sort(key=lambda x: x[0])
        lows.sort(key=lambda x: x[0])
        
        # Fit lines to highs and lows
        try:
            high_x = np.array([p[0] for p in highs])
            high_y = np.array([p[1] for p in highs])
            low_x = np.array([p[0] for p in lows])
            low_y = np.array([p[1] for p in lows])
            
            # Use numpy polyfit instead of linregress
            high_coeffs = np.polyfit(high_x, high_y, 1)
            low_coeffs = np.polyfit(low_x, low_y, 1)
            
            high_slope, high_intercept = high_coeffs[0], high_coeffs[1]
            low_slope, low_intercept = low_coeffs[0], low_coeffs[1]
            
        except (ValueError, np.linalg.LinAlgError):
            continue
        
        # Check for parallelism
        if not are_parallel(high_slope, low_slope, tolerance=params['parallel_tolerance']):
            continue
        
        # Verify channel width is reasonable
        channel_width = abs(high_intercept - low_intercept)
        avg_price = np.mean(prices[-i:])
        if channel_width > avg_price * params['deviation_threshold'] * 2:
            continue
        
        # Check if points are well-distributed
        time_span = max(high_x) - min(high_x)
        if time_span < params['min_channel_length']:
            continue
            
        return high_slope, high_intercept, low_slope, low_intercept, len(prices) - i
    
    return None, None, None, None, None



def main():
    directory = 'sp500pricedata'
    
    for filename in os.listdir(directory):
        if filename.endswith('.csv'):
            file_path = os.path.join(directory, filename)
            
            # Read CSV with dates
            df = pd.read_csv(file_path)
            
            # Convert the 'Date' column to datetime
            df['Date'] = pd.to_datetime(df['Date'])
            
            # Set Date as index
            df.set_index('Date', inplace=True)
            
            high_slope, high_intercept, low_slope, low_intercept, channel_start = find_dynamic_channel(df, PARAMS)

            if high_slope is not None:
                # Generate channel lines
                x = np.arange(channel_start, len(df))
                upper_channel = high_slope * x + high_intercept
                lower_channel = low_slope * x + low_intercept
                
                # Plot the results
                plt.figure(figsize=(15, 7))
                
                # Plot price data
                plt.plot(df.index, df['Close'], label='Close Price')
                
                # Plot channels using proper dates
                channel_dates = df.index[channel_start:]
                plt.plot(channel_dates, upper_channel, 'r--', label='Upper Channel')
                plt.plot(channel_dates, lower_channel, 'g--', label='Lower Channel')
                
                plt.legend()
                plt.title(f'Price Channel Detection: {filename}')
                plt.xlabel('Date')
                plt.ylabel('Price')
                
                # Rotate x-axis labels for better readability
                plt.xticks(rotation=45)
                
                # Adjust layout to prevent label cutoff
                plt.tight_layout()
                
                plt.show()
            else:
                print(f"No suitable channel found for {filename}")

if __name__ == "__main__":
    main()