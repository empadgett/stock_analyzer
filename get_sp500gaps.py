import yfinance as yf
import pandas as pd
import numpy as np
import mplfinance as mpf
from datetime import datetime, timedelta
import os

def detect_gaps(data, min_gap_size=0.05):
    try:
               
        
        data.sort_index(inplace=True)
        data['PrevHigh'] = data['High'].shift(1)
        data['PrevLow'] = data['Low'].shift(1)
        
        data['BullishGap'] = (data['Low'] > data['PrevHigh']) & ((data['Low'] - data['PrevHigh']) / data['PrevHigh'] >= min_gap_size)
        data['BearishGap'] = (data['High'] < data['PrevLow']) & ((data['PrevLow'] - data['High']) / data['PrevLow'] >= min_gap_size)
        
        data['GapSize'] = 0.0

        # Calculate gap size for bullish gaps
        data.loc[data['BullishGap'], 'GapSize'] = (data['Low'] - data['PrevHigh']) / data['PrevHigh']
        # Calculate gap size for bearish gaps
        data.loc[data['BearishGap'], 'GapSize'] = (data['PrevLow'] - data['High']) / data['PrevLow']
        
            
        # Check for gaps in the past 5 days
        five_days_ago = datetime.now().date() - timedelta(days=5)
        last_5_days = data[data.index.date >= five_days_ago]
        gaps_in_last_5_days = last_5_days[last_5_days['BullishGap'] | last_5_days['BearishGap']]
        
        if not gaps_in_last_5_days.empty:
            # Get the gap sizes for the gaps in the last 5 days
            recent_gap_sizes = data.loc[gaps_in_last_5_days.index, 'GapSize']
    
            # Format the gap sizes for printing
            gap_sizes_str = ', '.join(f"{size:.2%}" for size in recent_gap_sizes)
            
            print(f"Gap(s) occurred in the past 5 days for {filename}. Gap size(s): {gap_sizes_str}")


        # Create the plot
        mc = mpf.make_marketcolors(up='g', down='r', inherit=True)
        s  = mpf.make_mpf_style(marketcolors=mc)
        
        additional_plots = [
            mpf.make_addplot((data['BullishGap'] * data['Low']).replace(0, np.nan), scatter=True, markersize=200, marker='^', color='g'),
            mpf.make_addplot((data['BearishGap'] * data['High']).replace(0, np.nan), scatter=True, markersize=200, marker='v', color='r')
        ]
        
        #mpf.plot(data, type='candle', style=s, addplot=additional_plots, 
        #        title=f'\n{filename} Price (Gaps ≥ {min_gap_size:.1%} Highlighted)',
        #         volume=True, figsize=(12, 8))
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")





#os.makedirs(directory, exist_ok=True)

# Loop through the list of tickers and fetch data
directory = 'sp500pricedata'
for filename in os.listdir(directory):
    if filename.endswith('.csv'):  # Exclude SPY file
        file_path = os.path.join(directory, filename)  # Get full file path
        data = pd.read_csv(file_path, parse_dates=['Date'], index_col='Date')  # Read the CSV file into a DataFrame
        detect_gaps(data, min_gap_size=0.001)  # Set minimum gap size to 0.1%