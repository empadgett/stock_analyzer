##%%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import yfinance as yf
import matplotlib
import os
from datetime import datetime, timedelta
from pathlib import Path


def calculate_pivot_points(df, high_col='High', low_col='Low', close_col='Close'):
    """Calculate pivot points for the DataFrame."""
    df['PP'] = (df[high_col] + df[low_col] + df[close_col]) / 3
    return df

def find_price_channel(df, lookback_days, channel_width_factor=2):
    """Finds a price channel centered around the trend line."""
    if len(df) < lookback_days:
        return None, None, None

    recent_df = df.iloc[-lookback_days:]
    X = np.arange(len(recent_df)).reshape(-1, 1)
    y = recent_df['PP'].values

    # Fit linear regression to find the central trend line
    model = LinearRegression()
    model.fit(X, y)
    trend_line = model.predict(X)

    # Calculate standard deviation of the residuals for channel width
    residuals = y - trend_line
    std_dev = np.std(residuals)

    # Define channel width based on standard deviation
    upper_channel = trend_line + channel_width_factor * std_dev
    lower_channel = trend_line - channel_width_factor * std_dev

    return trend_line, upper_channel, lower_channel

def detect_breach(df, upper_channel, lower_channel, breach_lookback_days=5):
    """Detect if there's a breach in the last few days."""
    recent_close = df['Close'].iloc[-breach_lookback_days:]
    recent_upper = upper_channel[-breach_lookback_days:]
    recent_lower = lower_channel[-breach_lookback_days:]

    breach_upper = recent_close > recent_upper
    breach_lower = recent_close < recent_lower

    upper_breach_date = recent_close.index[breach_upper].max() if breach_upper.any() else None
    lower_breach_date = recent_close.index[breach_lower].max() if breach_lower.any() else None

    return breach_upper.any(), breach_lower.any(), upper_breach_date, lower_breach_date

def detect_channels(df, channel_lengths=[7, 14, 30], channel_width_factor=2, breach_lookback_days=5):
    """Detects price channels of specified lengths and checks for breaches."""
    detected_channels = []
    breach_occurred = False
    breach_dates = []
    
    for length in channel_lengths:
        trend_line, upper_channel, lower_channel = find_price_channel(df, length, channel_width_factor)
        if trend_line is not None:
            detected_channels.append((length, trend_line, upper_channel, lower_channel))
            breach_upper, breach_lower, upper_date, lower_date = detect_breach(df, upper_channel, lower_channel, breach_lookback_days)
            
            # Print only when a breach occurs
            if breach_upper or breach_lower:
                breach_occurred = True
                print(f"Breach detected:", filename)
                print(f"Channel Length: {length} days")
                if breach_upper:
                    print(f"Upper Channel Breached on {upper_date}")
                    breach_dates.append(upper_date)
                if breach_lower:
                    print(f"Lower Channel Breached on {lower_date}")
                    breach_dates.append(lower_date)
                #print(f"Last price: {df['Close'].iloc[-1]:.2f}")
                #print(f"Upper channel: {upper_channel[-1]:.2f}")
                #print(f"Lower channel: {lower_channel[-1]:.2f}")
                print()  # Add a blank line for readability

    return detected_channels, breach_occurred, breach_dates





def plot_channels(df, channels, title):
    """Plot the price data and detected channels for the last 3 months."""
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df.index, df['Close'], label='Close Price', color='blue')
    for length, trend_line, upper_channel, lower_channel in channels:
        plot_length = min(len(trend_line), len(df))
        ax.plot(df.index[-plot_length:], trend_line[-plot_length:], label=f'Trend Line ({length} days)', linestyle='--')
        ax.plot(df.index[-plot_length:], upper_channel[-plot_length:], label=f'Upper Channel ({length} days)', linestyle='--')
        ax.plot(df.index[-plot_length:], lower_channel[-plot_length:], label=f'Lower Channel ({length} days)', linestyle='--')

    ax.set_title(f"{title} - Last 3 Months")
    ax.set_xlabel('Date')
    ax.set_ylabel('Price')
    ax.legend(loc='upper left')
    ax.grid(True)
    return fig

# Define the directory path
dir_path = Path.home() / "dashboard" / "stock_data"

breach_count = 0
processed = 0
# Iterate over all CSV files in the directory
for file_path in dir_path.glob("*.csv"):
    # Read the CSV file
    df = pd.read_csv(file_path)
    processed += 1
    # Get the filename (without path and extension)
    ticker = file_path.stem  # This gets the filename without the .csv extension
    # Get the filename (without path)
    filename = file_path.name
    # Process the dataframe
    
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
    else:
        print(f"Warning: 'Date' column not found in {filename}")
        continue  # Skip to the next file if 'Date' column is not present

    # Calculate pivot points
    df = calculate_pivot_points(df)

    # Get the date 3 months ago from the last date in the dataframe
    three_months_ago = df.index[-1] - timedelta(days=90)

    # Trim the dataframe to only include the last 3 months
    df = df[df.index >= three_months_ago]

    # Detect channels and breaches
    detected_channels, file_breached, breach_dates = detect_channels(df)
    if file_breached:
        breach_count += 1
        #print(f"File: {filename}")
        #print(f"Breach dates: {breach_dates}")
        #print()  # Add a blank line for readability
    
    # Plot the results
    fig = plot_channels(df, detected_channels, ticker)
    plt.show()
    plt.close(fig)  # Close the figure to free up memory

print(f"Processed {processed} files.")
print(f"Total breaches: {breach_count}")




