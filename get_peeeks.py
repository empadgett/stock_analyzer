import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from scipy import stats
from datetime import datetime, timedelta

def get_stock_data(symbol, lookback=365):
    """Download stock data from Yahoo Finance"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback)
        df = yf.download(symbol, start=start_date, end=end_date)
        if df.empty:
            raise ValueError(f"No data found for symbol {symbol}")
        return df
    except Exception as e:
        print(f"Error downloading data for {symbol}: {str(e)}")
        return None

def calculate_atr(df, period=14):
    """Calculate Average True Range"""
    df = df.copy()
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df['ATR'] = df['TR'].rolling(period).mean()
    return df['ATR']

def find_trendline_points(df, direction='high', atr_multiplier=1.0, min_lookback=5, min_points=3):
    """
    Walk backwards from recent data to find trendline points
    
    Parameters:
    -----------
    df : pandas.DataFrame
        Price data
    direction : str
        'high' or 'low' for resistance or support lines
    atr_multiplier : float
        Multiplier for ATR bounds
    min_lookback : int
        Minimum days to look back from present
    min_points : int
        Minimum points required for valid trendline
    """
    df = df.copy()
    df['ATR'] = calculate_atr(df)
    
    # Start from x days before present
    current_idx = len(df) - min_lookback
    points = []
    
    price_col = 'High' if direction == 'high' else 'Low'
    
    # Function to check if point is a local extreme
    def is_extreme_point(idx):
        if direction == 'high':
            return (df[price_col].iloc[idx] > df[price_col].iloc[idx + 1] and 
                   df[price_col].iloc[idx] > df[price_col].iloc[idx - 1])
        else:
            return (df[price_col].iloc[idx] < df[price_col].iloc[idx + 1] and 
                   df[price_col].iloc[idx] < df[price_col].iloc[idx - 1])
    
    consecutive_deviations = 0
    max_deviations = 3  # Number of consecutive deviations before stopping
    
    while current_idx > 10:  # Keep some buffer at the start
        if len(points) < 2:
            # Need at least 2 points to start checking ATR bounds
            if is_extreme_point(current_idx):
                points.append((df.index[current_idx], df[price_col].iloc[current_idx]))
        else:
            # Calculate current trendline
            dates = [(pd.Timestamp(date) - pd.Timestamp(points[0][0])).days for date, _ in points]
            prices = [price for _, price in points]
            slope, intercept, r_value, _, _ = stats.linregress(dates, prices)
            
            # Project trendline to current point
            days_diff = (df.index[current_idx] - pd.Timestamp(points[0][0])).days
            projected_price = slope * days_diff + intercept
            
            # Check if point is within ATR bounds of trendline
            current_price = df[price_col].iloc[current_idx]
            current_atr = df['ATR'].iloc[current_idx]
            
            if is_extreme_point(current_idx):
                if abs(current_price - projected_price) <= atr_multiplier * current_atr:
                    points.append((df.index[current_idx], current_price))
                    consecutive_deviations = 0
                else:
                    consecutive_deviations += 1
                    if consecutive_deviations >= max_deviations and len(points) >= min_points:
                        break
        
        current_idx -= 1
    
    return list(reversed(points)) if len(points) >= min_points else []

def fit_trend_line(points):
    """Fit trend line through points"""
    if not points or len(points) < 2:
        return None
        
    dates = [(pd.Timestamp(date) - pd.Timestamp(points[0][0])).days for date, _ in points]
    prices = [price for _, price in points]
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(dates, prices)
    
    return {
        'slope': slope,
        'intercept': intercept,
        'r_value': r_value,
        'p_value': p_value,
        'std_err': std_err,
        'start_date': points[0][0],
        'end_date': points[-1][0],
        'points': points
    }

def plot_analysis(df, trend_lines_high, trend_lines_low):
    """Plot price with trend lines"""
    plt.style.use('default')
    
    fig, ax = plt.subplots(figsize=(15, 7))
    
    # Set the background color and grid
    ax.set_facecolor('#f0f0f0')
    fig.patch.set_facecolor('white')
    
    # Plot candlesticks
    width = np.timedelta64(12, 'h')
    up = df[df['Close'] >= df['Open']]
    down = df[df['Close'] < df['Open']]
    
    # Up candlesticks
    ax.bar(up.index, up['Close']-up['Open'], width, bottom=up['Open'], color='g', alpha=0.5)
    ax.bar(up.index, up['High']-up['Close'], width*0.2, bottom=up['Close'], color='g', alpha=0.5)
    ax.bar(up.index, up['Low']-up['Open'], width*0.2, bottom=up['Open'], color='g', alpha=0.5)
    
    # Down candlesticks
    ax.bar(down.index, down['Close']-down['Open'], width, bottom=down['Open'], color='r', alpha=0.5)
    ax.bar(down.index, down['High']-down['Open'], width*0.2, bottom=down['Open'], color='r', alpha=0.5)
    ax.bar(down.index, down['Low']-down['Close'], width*0.2, bottom=down['Close'], color='r', alpha=0.5)
    
    # Plot trend lines
    colors_high = ['#ff4444', '#cc0000', '#990000']  # Red variants
    for i, line in enumerate(trend_lines_high):
        points_x = [p[0] for p in line['points']]
        points_y = [p[1] for p in line['points']]
        ax.scatter(points_x, points_y, color=colors_high[i % len(colors_high)], alpha=0.6)
        
        # Plot trend line
        dates = pd.date_range(line['start_date'], line['end_date'])
        days = [(d - line['start_date']).days for d in dates]
        values = [line['slope'] * d + line['intercept'] for d in days]
        ax.plot(dates, values, '--', color=colors_high[i % len(colors_high)],
                label=f'High Trend (R={line["r_value"]:.2f})')
    
    colors_low = ['#44ff44', '#00cc00', '#009900']  # Green variants
    for i, line in enumerate(trend_lines_low):
        points_x = [p[0] for p in line['points']]
        points_y = [p[1] for p in line['points']]
        ax.scatter(points_x, points_y, color=colors_low[i % len(colors_low)], alpha=0.6)
        
        # Plot trend line
        dates = pd.date_range(line['start_date'], line['end_date'])
        days = [(d - line['start_date']).days for d in dates]
        values = [line['slope'] * d + line['intercept'] for d in days]
        ax.plot(dates, values, '--', color=colors_low[i % len(colors_low)],
                label=f'Low Trend (R={line["r_value"]:.2f})')
    
    ax.set_title(f'Trend Line Analysis - {df.index[-1].strftime("%Y-%m-%d")}',
                 pad=20, fontsize=12, fontweight='bold')
    ax.set_xlabel('Date', fontsize=10)
    ax.set_ylabel('Price', fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.7, color='#cccccc')
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def main(symbol='AAPL', lookback=365):
    """Main function to run the analysis"""
    # Get data
    df = get_stock_data(symbol, lookback)
    if df is None:
        return
    
    # Find trendline points
    high_points = find_trendline_points(df, direction='high', atr_multiplier=1.0)
    low_points = find_trendline_points(df, direction='low', atr_multiplier=1.0)
    
    # Fit trendlines
    high_trendline = fit_trend_line(high_points) if high_points else None
    low_trendline = fit_trend_line(low_points) if low_points else None
    
    # Plot results
    plot_analysis(df, 
                 [high_trendline] if high_trendline else [], 
                 [low_trendline] if low_trendline else [])
    
    # Print statistics
    if high_trendline:
        print("\nHigh Trendline Statistics:")
        print(f"Start Date: {high_trendline['start_date'].date()}")
        print(f"End Date: {high_trendline['end_date'].date()}")
        print(f"Slope: {high_trendline['slope']:.6f}")
        print(f"R-value: {high_trendline['r_value']:.4f}")
        print(f"Number of points: {len(high_trendline['points'])}")
    
    if low_trendline:
        print("\nLow Trendline Statistics:")
        print(f"Start Date: {low_trendline['start_date'].date()}")
        print(f"End Date: {low_trendline['end_date'].date()}")
        print(f"Slope: {low_trendline['slope']:.6f}")
        print(f"R-value: {low_trendline['r_value']:.4f}")
        print(f"Number of points: {len(low_trendline['points'])}")

if __name__ == "__main__":
    main('mo')
