import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mplfinance as mpf
from perceptually_important import find_pips
from trendline_automation import fit_trendlines_high_low
from dataclasses import dataclass




@dataclass
class FlagPattern:
    base_x: int         # Start of the trend index, base of pole
    base_y: float       # Start of trend price

    tip_x: int   = -1       # Tip of pole, start of flag
    tip_y: float = -1.

    conf_x: int   = -1      # Index where pattern is confirmed
    conf_y: float = -1.      # Price where pattern is confirmed

    pennant: bool = False      # True if pennant, false if flag

    flag_width: int    = -1
    flag_height: float = -1.

    pole_width: int    = -1
    pole_height: float = -1.

    # Upper and lower lines for flag, intercept is tip_x
    support_intercept: float = -1.
    support_slope: float = -1.
    resist_intercept: float = -1.
    resist_slope: float = -1.

def find_local_extrema(data: pd.Series, order: int):
    """Finds local maxima and minima."""
    max_indices = data[(data.shift(1) < data) & (data.shift(-1) < data)].index
    min_indices = data[(data.shift(1) > data) & (data.shift(-1) > data)].index
    return max_indices, min_indices

def check_bear_pattern_pips(pending: FlagPattern, data: pd.Series, i: int, order: int):
    data_slice = data[pending.base_x: i + 1]
    min_i = data_slice.idxmin()  # Get index of local minimum

    if i - min_i < max(5, order * 0.5):
        return False

    # Test flag width / height 
    pole_width = min_i - pending.base_x
    flag_width = i - min_i
    if flag_width > pole_width * 0.5:
        return False

    pole_height = pending.base_y - data[min_i]
    flag_height = data[min_i:i + 1].max() - data[min_i]
    if flag_height > pole_height * 0.5:
        return False

    # Find perceptually important points from pole to current time
    pips_x, pips_y = find_pips(data[min_i:i + 1], 5, 3)

    # Check center pip is less than two adjacent.
    if not (pips_y[2] < pips_y[1] and pips_y[2] < pips_y[3]):
        return False

    # Find slope and intercept of flag lines
    support_rise = pips_y[2] - pips_y[0]
    support_run = pips_x[2] - pips_x[0]
    support_slope = support_rise / support_run
    support_intercept = pips_y[0]

    resist_rise = pips_y[3] - pips_y[1]
    resist_run = pips_x[3] - pips_x[1]
    resist_slope = resist_rise / resist_run
    resist_intercept = pips_y[1] + (pips_x[0] - pips_x[1]) * resist_slope

    # Find intersection
    if resist_slope != support_slope:
        intersection = (support_intercept - resist_intercept) / (resist_slope - support_slope)
    else:
        intersection = -flag_width * 100

    if intersection <= pips_x[4] and intersection >= 0:
        return False

    # Check breakout
    support_endpoint = pips_y[0] + support_slope * pips_x[4]
    if pips_y[4] > support_endpoint:
        return False

    pending.pennant = resist_slope < 0

    # Filter harshly diverging lines
    if intersection < 0 and intersection > -flag_width:
        return False

    pending.tip_x = min_i
    pending.tip_y = data[min_i]
    pending.conf_x = i
    pending.conf_y = data[i]
    pending.flag_width = flag_width
    pending.flag_height = flag_height
    pending.pole_width = pole_width
    pending.pole_height = pole_height
    pending.support_slope = support_slope
    pending.support_intercept = support_intercept
    pending.resist_slope = resist_slope
    pending.resist_intercept = resist_intercept

    return True

def check_bull_pattern_pips(pending: FlagPattern, data: pd.Series, i: int, order: int):
    data_slice = data[pending.base_x: i + 1]
    max_i = data_slice.idxmax()  # Get index of local maximum
    pole_width = max_i - pending.base_x

    if i - max_i < max(5, order * 0.5):
        return False

    flag_width = i - max_i
    if flag_width > pole_width * 0.5:
        return False

    pole_height = data[max_i] - pending.base_y
    flag_height = data[max_i] - data[max_i:i + 1].min()
    if flag_height > pole_height * 0.5:
        return False

    pips_x, pips_y = find_pips(data[max_i:i + 1], 5, 3)

    if not (pips_y[2] > pips_y[1] and pips_y[2] > pips_y[3]):
        return False

    # Find slope and intercept of flag lines
    resist_rise = pips_y[2] - pips_y[0]
    resist_run = pips_x[2] - pips_x[0]
    resist_slope = resist_rise / resist_run
    resist_intercept = pips_y[0]

    support_rise = pips_y[3] - pips_y[1]
    support_run = pips_x[3] - pips_x[1]
    support_slope = support_rise / support_run
    support_intercept = pips_y[1] + (pips_x[0] - pips_x[1]) * support_slope

    # Find intersection
    if resist_slope != support_slope:
        intersection = (support_intercept - resist_intercept) / (resist_slope - support_slope)
    else:
        intersection = -flag_width * 100

    if intersection <= pips_x[4] and intersection >= 0:
        return False

    if intersection < 0 and intersection > -1.0 * flag_width:
        return False

    resist_endpoint = pips_y[0] + resist_slope * pips_x[4]
    if pips_y[4] < resist_endpoint:
        return False

    pending.pennant = support_slope > 0

    pending.tip_x = max_i
    pending.tip_y = data[max_i]
    pending.conf_x = i
    pending.conf_y = data[i]
    pending.flag_width = flag_width
    pending.flag_height = flag_height
    pending.pole_width = pole_width
    pending.pole_height = pole_height

    pending.support_slope = support_slope
    pending.support_intercept = support_intercept
    pending.resist_slope = resist_slope
    pending.resist_intercept = resist_intercept

    return True

def find_flags_pennants_pips(data: pd.Series, order: int):
    assert(order >= 3)
    pending_bull = None
    pending_bear = None

    bull_pennants = []
    bear_pennants = []
    bull_flags = []
    bear_flags = []

    # Find local extrema
    max_indices, min_indices = find_local_extrema(data, order)

    for i in range(len(data)):
        # Check for bear patterns
        if i in max_indices:
            pending_bear = FlagPattern(i - order, data[i - order])

        # Check for bull patterns
        if i in min_indices:
            pending_bull = FlagPattern(i - order, data[i - order])

        if pending_bear is not None:
            if check_bear_pattern_pips(pending_bear, data, i, order):
                if pending_bear.pennant:
                    bear_pennants.append(pending_bear)
                else:
                    bear_flags.append(pending_bear)
                pending_bear = None

        if pending_bull is not None:
            if check_bull_pattern_pips(pending_bull, data, i, order):
                if pending_bull.pennant:
                    bull_pennants.append(pending_bull)
                else:
                    bull_flags.append(pending_bull)
                pending_bull = None

    return bull_flags, bear_flags, bull_pennants, bear_pennants


def plot_flag(candle_data: pd.DataFrame, pattern: FlagPattern, pad=2):
    if pad < 0:
        pad = 0

    start_i = pattern.base_x - pad
    end_i = pattern.conf_x + 1 + pad
    dat = candle_data.iloc[start_i:end_i]
    idx = dat.index
    
    plt.style.use('dark_background')
    fig = plt.gcf()
    ax = fig.gca()

    tip_idx = idx[pattern.tip_x - start_i]
    conf_idx = idx[pattern.conf_x - start_i]

    pole_line = [(idx[pattern.base_x - start_i], pattern.base_y), (tip_idx, pattern.tip_y)]
    upper_line = [(tip_idx, pattern.resist_intercept), (conf_idx, pattern.resist_intercept + pattern.resist_slope * pattern.flag_width)]
    lower_line = [(tip_idx, pattern.support_intercept), (conf_idx, pattern.support_intercept + pattern.support_slope * pattern.flag_width)]

    mpf.plot(dat, alines=dict(alines=[pole_line, upper_line, lower_line], colors=['w', 'b', 'b']), type='candle', style='charles', ax=ax)
    plt.show()

if __name__ == '__main__':
    data = pd.read_csv('/home/empadgett/myproject/stock_data/AAPL.csv')
    data.columns = data.columns.str.lower()
    data['date'] = data['date'].astype('datetime64[s]')
    
    data = data.set_index('date')
    numeric_data = data.select_dtypes(include=[np.number])
    data = np.log(numeric_data)

    dat_slice = data['close'].to_numpy()
    bull_flags, bear_flags, bull_pennants, bear_pennants  = find_flags_pennants_pips(dat_slice, 12)
    #bull_flags, bear_flags, bull_pennants, bear_pennants  = find_flags_pennants_trendline(dat_slice, 10)


    bull_flag_df = pd.DataFrame()
    bull_pennant_df = pd.DataFrame()
    bear_flag_df = pd.DataFrame()
    bear_pennant_df = pd.DataFrame()

    # Assemble data into dataframe
    hold_mult = 1.0 # Multipler of flag width to hold for after a pattern
    for i, flag in enumerate(bull_flags):
        bull_flag_df.loc[i, 'flag_width'] = flag.flag_width
        bull_flag_df.loc[i, 'flag_height'] = flag.flag_height
        bull_flag_df.loc[i, 'pole_width'] = flag.pole_width
        bull_flag_df.loc[i, 'pole_height'] = flag.pole_height
        bull_flag_df.loc[i, 'slope'] = flag.resist_slope

        hp = int(flag.flag_width * hold_mult)
        if flag.conf_x + hp >= len(data):
            bull_flag_df.loc[i, 'return'] = np.nan
        else:
            ret = dat_slice[flag.conf_x + hp] - dat_slice[flag.conf_x]
            bull_flag_df.loc[i, 'return'] = ret 

    for i, flag in enumerate(bear_flags):
        bear_flag_df.loc[i, 'flag_width'] = flag.flag_width
        bear_flag_df.loc[i, 'flag_height'] = flag.flag_height
        bear_flag_df.loc[i, 'pole_width'] = flag.pole_width
        bear_flag_df.loc[i, 'pole_height'] = flag.pole_height
        bear_flag_df.loc[i, 'slope'] = flag.support_slope

        hp = int(flag.flag_width * hold_mult)
        if flag.conf_x + hp >= len(data):
            bear_flag_df.loc[i, 'return'] = np.nan
        else:
            ret = -1 * (dat_slice[flag.conf_x + hp] - dat_slice[flag.conf_x])
            bear_flag_df.loc[i, 'return'] = ret 

    for i, pennant in enumerate(bull_pennants):
        bull_pennant_df.loc[i, 'pennant_width'] = pennant.flag_width
        bull_pennant_df.loc[i, 'pennant_height'] = pennant.flag_height
        bull_pennant_df.loc[i, 'pole_width'] = pennant.pole_width
        bull_pennant_df.loc[i, 'pole_height'] = pennant.pole_height

        hp = int(pennant.flag_width * hold_mult)
        if flag.conf_x + hp >= len(data):
            bull_pennant_df.loc[i, 'return'] = np.nan
        else:
            ret = dat_slice[pennant.conf_x + hp] - dat_slice[pennant.conf_x]
            bull_pennant_df.loc[i, 'return'] = ret 

    for i, pennant in enumerate(bear_pennants):
        bear_pennant_df.loc[i, 'pennant_width'] = pennant.flag_width
        bear_pennant_df.loc[i, 'pennant_height'] = pennant.flag_height
        bear_pennant_df.loc[i, 'pole_width'] = pennant.pole_width
        bear_pennant_df.loc[i, 'pole_height'] = pennant.pole_height

        hp = int(pennant.flag_width * hold_mult)
        if flag.conf_x + hp >= len(data):
            bear_pennant_df.loc[i, 'return'] = np.nan
        else:
            ret = -1 * (dat_slice[pennant.conf_x + hp] - dat_slice[pennant.conf_x])
            bear_pennant_df.loc[i, 'return'] = ret 
            
    print(bull_flags)
    print(bear_flags)
    print(bull_pennants)
    print(bear_pennants)