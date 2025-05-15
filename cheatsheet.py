import yfinance as yf
import mplfinance as mpf
from datetime import datetime, timedelta
import numpy as np

# Define the ticker and time period
ticker = 'goog'
end_date = datetime.now()
start_date = end_date - timedelta(days=180)  # 6 months of data

# Fetch the daily data
data = yf.download(ticker, start=start_date, end=end_date)

# Calculate the price levels
last_price = data['Close'].iloc[-1]
levels = [
176.36, #Price 3 Standard Deviations Resistance
175.91, #38.2% Retracement From 4 Week High
174.57, #Price 2 Standard Deviations Resistance
173.40, #50% Retracement From 4 Week High/Low
172.22, #Price 1 Standard Deviation Resistance
170.89, #38.2% Retracement From 4 Week Low
170.53, #Pivot Point 3rd Level Resistance
170.34, #38.2% Retracement From 13 Week High
169.40, #Pivot Point 2nd Level Resistance
168.90, #61.8% Retracement from the 52 Week Low
167.98, #Pivot Point 1st Resistance Point
166.85, #Pivot Point
166.11, #50% Retracement From 13 Week High/Low
165.43, #Pivot Point 1st Support Point
164.30, #Pivot Point 2nd Support Point
162.88, #Pivot Point 3rd Support Point
161.89, #38.2% Retracement From 13 Week Low
161.35, #50% Retracement From 52 Week High/Low
160.92, #Price 1 Standard Deviation Support
158.57, #Price 2 Standard Deviations Support
156.78, #Price 3 Standard Deviations Support

]
# Create a DataFrame for levels to match the dates
level_lines = {level: [level] * len(data) for level in levels}

# Create a list of plots for each level
addplots = [mpf.make_addplot(level_lines[level], type='line', color='red', linestyle='--') for level in levels]

# Create a candlestick chart
mpf.plot(data, type='candle', style='charles', title=f'{ticker} Candlestick Chart',
         ylabel='Price', volume=False, addplot=addplots,
         ylim=(min(levels) - 10, max(levels) + 10),  # Set y-limits for better visibility
         returnfig=True)

# Adjust y-ticks for the plot
fig, axlist = mpf.plot(data, type='candle', style='charles', title=f'{ticker} Candlestick Chart',
                        ylabel='Price', volume=False, addplot=addplots, returnfig=True)

# Set y-ticks with step of 1
y_ticks = np.arange(np.floor(min(levels)), np.ceil(max(levels)) + 1, 1)
axlist[0].set_yticks(y_ticks)

# Show the plot
mpf.show()