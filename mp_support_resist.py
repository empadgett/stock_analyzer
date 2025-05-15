import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy
import yfinance as yf
import pandas_ta as ta
import mplfinance as mpf
import scipy.stats
import scipy.signal
import matplotlib.ticker as mticker  # Changed alias to mticker

# Global parameters
MAX_LEVELS = 12
FIRST_W = 0.08
ATR_MULT = 2.0
PROM_THRESH = 0.0008
DISTANCE = 1
LOOKBACK = 75
CLUSTER_THRESHOLD = 1.5
PLOT_WINDOW = 400

def find_levels(
    price: np.array, atr: float,
    first_w: float = FIRST_W,
    atr_mult: float = ATR_MULT,
    prom_thresh: float = PROM_THRESH,
    distance: int = DISTANCE,
    max_levels: int = MAX_LEVELS
):
    # Setup weights
    last_w = 1.0
    w_step = (last_w - first_w) / len(price)
    weights = first_w + np.arange(len(price)) * w_step
    weights[weights < 0] = 0.0

    # Get kernel of price
    kernel = scipy.stats.gaussian_kde(price, bw_method=atr*atr_mult, weights=weights)

    # Construct market profile
    min_v, max_v = np.min(price), np.max(price)
    step = (max_v - min_v) / 200
    price_range = np.arange(min_v, max_v, step)
    pdf = kernel(price_range)  # Market profile

    # Find significant peaks in the market profile
    pdf_max = np.max(pdf)
    prom_min = pdf_max * prom_thresh

    peaks, props = scipy.signal.find_peaks(pdf, prominence=prom_min, distance=distance)
    
    # Sort peaks by prominence
    sorted_peaks = sorted(zip(peaks, props['prominences']), key=lambda x: x[1], reverse=True)
    
    # Select top peaks and convert to price levels
    levels = []
    for peak, _ in sorted_peaks[:max_levels]:
        levels.append(np.exp(price_range[peak]))
    
    # Cluster nearby levels
    clustered_levels = cluster_levels(levels, atr)
    
    return clustered_levels, peaks, props, price_range, pdf, weights

def cluster_levels(levels, atr, threshold=CLUSTER_THRESHOLD):
    if not levels:
        return []
    
    levels = sorted(levels)
    clustered = [levels[0]]
    
    for level in levels[1:]:
        if (level - clustered[-1]) / atr > threshold:
            clustered.append(level)
    
    return clustered

def support_resistance_levels(
    data: pd.DataFrame, lookback: int = LOOKBACK,
    first_w: float = FIRST_W,
    atr_mult: float = ATR_MULT,
    prom_thresh: float = PROM_THRESH,
    distance: int = DISTANCE,
    max_levels: int = MAX_LEVELS
):
    # Get log average true range
    atr = ta.atr(np.log(data['high']), np.log(data['low']), np.log(data['close']), lookback)

    all_levels = [None] * len(data)
    for i in range(lookback, len(data)):
        i_start = i - lookback
        vals = np.log(data.iloc[i_start+1: i+1]['close'].to_numpy())
        levels, peaks, props, price_range, pdf, weights = find_levels(
            vals, atr.iloc[i], first_w, atr_mult, prom_thresh, distance, max_levels
        )
        all_levels[i] = levels
        
    return all_levels

def sr_penetration_signal(data: pd.DataFrame, levels: list):
    signal = np.zeros(len(data))
    curr_sig = 0.0
    close_arr = data['close'].to_numpy()
    for i in range(1, len(data)):
        if levels[i] is None:
            continue

        last_c = close_arr[i - 1]
        curr_c = close_arr[i]

        for level in levels[i]:
            if curr_c > level and last_c <= level: # Close cross above line
                curr_sig = 1.0
            elif curr_c < level and last_c >= level: # Close cross below line
                curr_sig = -1.0

        signal[i] = curr_sig
    return signal

def get_trades_from_signal(data: pd.DataFrame, signal: np.array):
    long_trades = []
    short_trades = []

    close_arr = data['close'].to_numpy()
    last_sig = 0.0
    open_trade = None
    idx = data.index
    for i in range(len(data)):
        if signal[i] == 1.0 and last_sig != 1.0: # Long entry
            if open_trade is not None:
                open_trade[2] = idx[i] 
                open_trade[3] = close_arr[i]
                short_trades.append(open_trade)

            open_trade = [idx[i], close_arr[i], -1, np.nan]
        if signal[i] == -1.0  and last_sig != -1.0: # Short entry
            if open_trade is not None:
                open_trade[2] = idx[i] 
                open_trade[3] = close_arr[i]
                long_trades.append(open_trade)

            open_trade = [idx[i], close_arr[i], -1, np.nan]

        last_sig = signal[i]

    long_trades = pd.DataFrame(long_trades, columns=['entry_time', 'entry_price', 'exit_time', 'exit_price'])
    short_trades = pd.DataFrame(short_trades, columns=['entry_time', 'entry_price', 'exit_time', 'exit_price'])

    long_trades['percent'] = (long_trades['exit_price'] - long_trades['entry_price']) / long_trades['entry_price'] 
    short_trades['percent'] = -1 * (short_trades['exit_price'] - short_trades['entry_price']) / short_trades['entry_price']
    long_trades = long_trades.set_index('entry_time')
    short_trades = short_trades.set_index('entry_time')
    return long_trades, short_trades 

def plot_support_resistance(data, levels, window=PLOT_WINDOW, max_levels=MAX_LEVELS):
    recent_data = data.tail(window)
    fig, ax = plt.subplots(figsize=(20, 10))
    
    # Plot candlestick chart
    mpf.plot(recent_data, type='candle', ax=ax, style='charles', show_nontrading=False)
    
    # Get the most recent non-None level set
    recent_levels = next((level_set for level_set in reversed(levels) if level_set is not None), None)
    
    if recent_levels:
        current_price = recent_data.iloc[-1]['close']
        for level in recent_levels[:max_levels]:  # Limit the number of levels shown
            if level < current_price:
                color = 'green'  # Support
            else:
                color = 'red'    # Resistance
            ax.axhline(y=level, color=color, linestyle='--', alpha=0.7, linewidth=2)
    
    ax.set_title(f'{TICKER} Support and Resistance Levels', fontsize=16)  # Changed ticker to TICKER
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Price', fontsize=12)
    
    # Increase y-axis granularity
    y_range = recent_data['high'].max() - recent_data['low'].min()
    ax.yaxis.set_major_locator(mticker.MultipleLocator(y_range / 20))  # 20 major ticks
    ax.yaxis.set_minor_locator(mticker.MultipleLocator(y_range / 100))  # 5 minor ticks between each major tick
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.2f'))
    
    # Rotate and align the tick labels so they look better
    fig.autofmt_xdate()
    
    # Use a tight layout
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    TICKER = "meta" # Changed to uppercase to indicate it's a constant
    data = yf.download(TICKER, period="1y")

    # Rename columns to lowercase
    data.rename(columns={
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume'
    }, inplace=True)

    plt.style.use('dark_background')
    levels = support_resistance_levels(data, LOOKBACK, first_w=FIRST_W, atr_mult=ATR_MULT)
    data['sr_signal'] = sr_penetration_signal(data, levels)
    data['log_ret'] = np.log(data['close']).diff().shift(-1)
    data['sr_return'] = data['sr_signal'] * data['log_ret']

    long_trades, short_trades = get_trades_from_signal(data, data['sr_signal'].to_numpy())

    # Visualization of support and resistance levels
    plot_support_resistance(data, levels)
print(levels)