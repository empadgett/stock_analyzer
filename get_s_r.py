import yfinance as yf
import numpy as np
import pandas as pd
import mplfinance as mpf
from datetime import datetime, timedelta

def calculate_pivot_points(high, low, close):
    """Calculate all pivot points levels"""
    pivot = (high + low + close) / 3
    
    # Standard pivot points
    r1 = 2 * pivot - low
    r2 = pivot + (high - low)
    r3 = high + 2 * (pivot - low)
    s1 = 2 * pivot - high
    s2 = pivot - (high - low)
    s3 = low - 2 * (high - pivot)
    
    # Fibonacci pivot points
    fib_r1 = pivot + 0.382 * (high - low)
    fib_r2 = pivot + 0.618 * (high - low)
    fib_r3 = pivot + 1.000 * (high - low)
    fib_s1 = pivot - 0.382 * (high - low)
    fib_s2 = pivot - 0.618 * (high - low)
    fib_s3 = pivot - 1.000 * (high - low)
    
    return {
        'P': pivot,
        'R1': r1, 'R2': r2, 'R3': r3,
        'S1': s1, 'S2': s2, 'S3': s3,
        'FibR1': fib_r1, 'FibR2': fib_r2, 'FibR3': fib_r3,
        'FibS1': fib_s1, 'FibS2': fib_s2, 'FibS3': fib_s3
    }

def calculate_all_pivot_points(data, window=120):
    """Calculate pivot points for the specified window"""
    recent_data = data.tail(window)
    pivots = calculate_pivot_points(
        recent_data['High'].max(),
        recent_data['Low'].min(),
        recent_data['Close'].iloc[-1]
    )
    
    # Sort levels from highest to lowest
    return sorted(list(pivots.values()), reverse=True)

def calculate_fibonacci_levels(data):
    """Calculate Fibonacci retracement and extension levels"""
    high = data['High'].max()
    low = data['Low'].min()
    price_range = high - low
    
    levels = {
        'Ext 161.8%': high + price_range * 0.618,
        'Ext 127.2%': high + price_range * 0.272,
        '100%': high,
        '78.6%': high - price_range * 0.214,
        '61.8%': high - price_range * 0.382,
        '50%': high - price_range * 0.5,
        '38.2%': high - price_range * 0.618,
        '23.6%': high - price_range * 0.764,
        '0%': low,
    }
    
    return sorted(list(levels.values()), reverse=True)

# Fetch NVDA data
ticker = 'tgt'
data = yf.download(ticker, period='1y')

# Calculate all levels
pivot_levels = calculate_all_pivot_points(data, window=90)
fib_levels = calculate_fibonacci_levels(data)

# Combine all levels and remove duplicates
all_levels = sorted(list(set(pivot_levels + fib_levels)), reverse=True)

# Create plot lines for all levels
plot_lines = []
current_price = data['Close'].iloc[-1]

# Create color-coded lines based on relation to current price
for level in all_levels:
    if level > current_price:
        color = 'red'  # Resistance
    elif level < current_price:
        color = 'green'  # Support
    else:
        color = 'blue'  # Current level
        
    plot_lines.append(
        mpf.make_addplot([level] * len(data), 
                        color=color, 
                        linestyle='--', 
                        width=0.75)
    )

# Print levels analysis
print(f"\nCurrent Price: ${current_price:.2f}")
print("\nAll Price Levels (from highest to lowest):")
for i, level in enumerate(all_levels, 1):
    distance = level - current_price
    percent = (distance / current_price) * 100
    level_type = "Resistance" if level > current_price else "Support"
    print(f"Level {i}: ${level:.2f} ({level_type}) - ${abs(distance):.2f} ({percent:.1f}%) {'above' if distance > 0 else 'below'} current price")




# Plot
mpf.plot(data, 
         type='candle',
         style='yahoo',
         title=f'{ticker} with Pivot Points and Fibonacci Levels',
         ylabel='Price ($)',
         volume=True,
         addplot=plot_lines,
         figratio=(16,8),
         figscale=1.2)


