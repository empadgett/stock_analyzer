import pandas as pd
import yfinance as yf
import mplfinance as mpf
from datetime import datetime, timedelta

def detect_fair_value_gaps(data):
    """
    Detect fair value gaps defined by 3 consecutive green candles in an uptrend.

    Parameters:
    - data: DataFrame containing 'Open', 'High', 'Low', 'Close' prices.

    Returns:
    - List of tuples containing (index of the 2nd candle, high of 1st candle, low of 3rd candle).
    """
    fvg_list = []

    for i in range(2, len(data)):
        # Check for three consecutive green candles
        if (data['Close'].iloc[i] > data['Open'].iloc[i] and
            data['Close'].iloc[i-1] > data['Open'].iloc[i-1] and
            data['Close'].iloc[i-2] > data['Open'].iloc[i-2]):
            
            # Check if it's an uptrend
            if ((data['Open'].iloc[i-2] < data['Close'].iloc[i-1]) and ( data['Open'].iloc[i-1] < data['Close'].iloc[i])):
                # Define FVG
                high_fvg = data['High'].iloc[i-2]  # High of the 1st candle
                low_fvg = data['Low'].iloc[i]       # Low of the 3rd candle
                fvg_list.append((i-1, high_fvg, low_fvg))  # Store index of 2nd candle

    return fvg_list

# Fetch AAPL data
if __name__ == "__main__":
    # Fetch historical data for AAPL
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)  # Get 1 year of data
    df = yf.download('tsla', start=start_date, end=end_date, progress=False)

    # Detect FVG
    fvg_results = detect_fair_value_gaps(df)

    # Check if any FVG was detected in the last 20 trading days
    last_20_days = df.index[-20:]
    recent_fvg = [fvg for fvg in fvg_results if df.index[fvg[0]] in last_20_days]
    
    if recent_fvg:
        print("FVG detected in the past 20 trading days")
        for fvg in recent_fvg:
            print(f"FVG on {df.index[fvg[0]].date()}: High = {fvg[1]:.2f}, Low = {fvg[2]:.2f}")
    else:
        print("No FVG detected in the past 20 trading days")

    # Prepare for plotting (last 30 days)
    df_plot = df.last('30D')
    high_lines = pd.Series(index=df_plot.index, dtype='float64')
    low_lines = pd.Series(index=df_plot.index, dtype='float64')

    for index, high, low in fvg_results:
        if df.index[index] in df_plot.index:
            # Create horizontal lines starting at the 2nd FVG candle and extending for 10 bars
            start_index = df_plot.index.get_loc(df.index[index])
            end_index = min(start_index + 10, len(df_plot) - 1)  # Ensure we don't go out of bounds

            # Set values for the FVG period
            high_lines.iloc[start_index:end_index+1] = high
            low_lines.iloc[start_index:end_index+1] = low

    # Create addplots
    apds = [
        mpf.make_addplot(high_lines, type='line', color='red', width=1),
        mpf.make_addplot(low_lines, type='line', color='blue', width=1)
    ]

    # Define the style
    mc = mpf.make_marketcolors(up='g', down='r', volume='in', wick={'up':'g', 'down':'r'})
    s = mpf.make_mpf_style(marketcolors=mc)

    # Plot the candlestick chart with volume
    mpf.plot(df_plot, 
             type='candle', 
             addplot=apds, 
             title='AAPL Fair Value Gap Detection (Last 30 Days)', 
             volume=True,  # Enable volume
             style=s,  # Use our custom style
             figsize=(12, 8),  # Increase figure size for better visibility
             panel_ratios=(2, 1),  # Ratio between price and volume panels
             )

