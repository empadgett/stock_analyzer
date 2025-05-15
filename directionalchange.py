import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mplfinance as mpf
import yfinance as yf

def directional_change(close: np.array, high: np.array, low: np.array, sigma: float):
    up_zig = True
    tmp_max = high[0]
    tmp_min = low[0]
    tmp_max_i = 0
    tmp_min_i = 0

    tops = []
    bottoms = []

    for i in range(len(close)):
        if up_zig:
            if high[i] > tmp_max:
                tmp_max = high[i]
                tmp_max_i = i
            elif close[i] < tmp_max - tmp_max * sigma:
                top = [i, tmp_max_i, tmp_max]
                tops.append(top)
                up_zig = False
                tmp_min = low[i]
                tmp_min_i = i
        else:
            if low[i] < tmp_min:
                tmp_min = low[i]
                tmp_min_i = i
            elif close[i] > tmp_min + tmp_min * sigma:
                bottom = [i, tmp_min_i, tmp_min]
                bottoms.append(bottom)
                up_zig = True
                tmp_max = high[i]
                tmp_max_i = i

    return tops, bottoms

def get_extremes(ohlc: pd.DataFrame, sigma: float):
    tops, bottoms = directional_change(ohlc['Close'].values, ohlc['High'].values, ohlc['Low'].values, sigma)
    tops = pd.DataFrame(tops, columns=['conf_i', 'ext_i', 'ext_p'])
    bottoms = pd.DataFrame(bottoms, columns=['conf_i', 'ext_i', 'ext_p'])
    tops['type'] = 1
    bottoms['type'] = -1
    extremes = pd.concat([tops, bottoms])
    extremes = extremes.set_index('conf_i')
    extremes = extremes.sort_index()
    return extremes

# Fetch Apple stock data
ticker = 'TSLA'
data = yf.download(ticker, start='2024-01-01', end='2024-10-12')

# Calculate extremes
sigma = 0.02  # 2% retracement
extremes = get_extremes(data, sigma)

# Visualization
apds = []

# Create empty Series for tops and bottoms
high_series = pd.Series(index=data.index, dtype=float)
low_series = pd.Series(index=data.index, dtype=float)

# Plot tops and bottoms
for _, row in extremes.iterrows():
    ext_index = int(row['ext_i'])  # Ensure ext_i is an integer
    if row['type'] == 1:  # Top
        high_series.iloc[ext_index] = data['High'].iloc[ext_index]
    elif row['type'] == -1:  # Bottom
        low_series.iloc[ext_index] = data['Low'].iloc[ext_index]

# Now add the plots
apds.append(mpf.make_addplot(high_series, type='scatter', markersize=100, marker='^', color='red'))
apds.append(mpf.make_addplot(low_series, type='scatter', markersize=100, marker='v', color='green'))

# Plot the candlestick chart with extremes
mpf.plot(data, type='candle', addplot=apds, title=f"{ticker} with Directional Changes", ylabel='Price', volume=True)

