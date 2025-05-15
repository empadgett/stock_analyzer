import pandas as pd
import yfinance as yf
import mplfinance as mpf
from backtesting import Backtest, Strategy
import time

def download_data(ticker, retries=3):
    for attempt in range(retries):
        try:
            df = yf.download(ticker, period='1y', interval='1d')
            if df.empty:
                raise ValueError("Downloaded DataFrame is empty.")
            return df
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(2)  # Wait before retrying
    return None  # Return None if all attempts fail

ticker='amd'
df = download_data(ticker)

df = df.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close'})
# Ensure the index is a DateTimeIndex
df.index = pd.to_datetime(df.index)



# Define input parameters
temaLength = 60
emaLength = 55
candleSizeFactor = 1.1

# Calculate OHLC4 for each row
df['ohlc4'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4

# Calculate Heikin-Ashi open
df['haOpen'] = 0.0
original_index=df.index
df.reset_index(drop=True, inplace=True)

df.at[0, 'haOpen'] = df.at[0, 'ohlc4']
for index in range(1, len(df)):
    if index == 1:
        df.at[index, 'haOpen'] = (df.at[index - 1, 'haOpen'] + df.at[index, 'ohlc4']) / 2
    else:
        df.at[index, 'haOpen'] = (df.at[index - 1, 'haOpen'] + df.at[index - 1, 'ohlc4']) / 2

# Calculate Heikin-Ashi close
df['haClose'] = (df['haOpen'] + 
                  df[['high', 'haOpen']].max(axis=1) + 
                  df[['low', 'haOpen']].min(axis=1) + 
                  df['ohlc4']) / 4

def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

# Calculate TEMA
ema1 = ema(df['haClose'], temaLength)
ema2 = ema(ema1, temaLength)
ema3 = ema(ema2, temaLength)

df['temp'] = 3 * (ema1 - ema2) + ema3
df['temaHaClose'] = 3 * (ema1 - ema2) + ema3

# Calculate zero lag
ema1 = ema(df['temaHaClose'], temaLength)
ema2 = ema(ema1, temaLength)
ema3 = ema(ema2, temaLength)
df['zeroLagHaClose'] = 2 * df['temaHaClose'] - (3 * (ema1 - ema2) + ema3)

# Calculate TEMA for typical price
df['hl2'] = (df['high'] + df['low']) / 2
ema1 = ema(df['hl2'], temaLength)
ema2 = ema(ema1, temaLength)
ema3 = ema(ema2, temaLength)
df['temaTypPrice'] = 3 * (ema1 - ema2) + ema3
df['zeroLagTypPrice'] = 2 * df['temaTypPrice'] - df['temp']

# Define conditions
df['shortCandle'] = (df['close'] - df['open']).abs() < (df['high'] - df['low']) * candleSizeFactor
df['keepGreen'] = (df['haClose'] >= df['haOpen']) | (df['haClose'].shift(1) >= df['haOpen'].shift(1)) | \
                  (df['close'] >= df['haClose']) | (df['high'] > df['high'].shift(1)) | \
                  (df['low'] > df['low'].shift(1)) | (df['zeroLagTypPrice'] >= df['zeroLagHaClose'])

# More conditions
df['keepGreenAll'] = df['keepGreen'] | (df['keepGreen'].shift(1) & ((df['close'] >= df['open']) | (df['close'] >= df['close'].shift(1))))
df['holdLong'] = df['shortCandle'] & (df['high'] >= df['low'].shift(1))
df['utr'] = df['keepGreenAll'] | (df['keepGreenAll'].shift(1) & df['holdLong'])

df['keepRed'] = (df['haClose'] < df['haOpen']) | (df['haClose'].shift(1) < df['haOpen'].shift(1)) | \
                (df['zeroLagTypPrice'] < df['zeroLagHaClose'])

df['keepRedAll'] = df['keepRed'] | (df['keepRed'].shift(1) & ((df['close'] < df['open']) | (df['close'] < df['close'].shift(1))))
df['holdShort'] = df['shortCandle'] & (df['low'] <= df['high'].shift(1))
df['dtr'] = df['keepRedAll'] | (df['keepRedAll'].shift(1) & df['holdShort'])

df['upw'] = ~df['dtr'] & df['dtr'].shift(1) & df['utr']
df['dnw'] = ~df['utr'] & df['utr'].shift(1) & df['dtr']

# Calculate upwSave
df['upwSave'] = False
previous_upwSave = False
for date, row in df.iterrows():
    if date == df.index[0]:
        df.at[date, 'upwSave'] = row['upw']
    else:
        if row['upw'] or row['dnw']:
            df.at[date, 'upwSave'] = row['upw']
        else:
            df.at[date, 'upwSave'] = previous_upwSave
    previous_upwSave = df.at[date, 'upwSave']

df['buy'] = df['upw'] | (~df['dnw'] & df['upwSave'])
df['longTermSell'] = df['close'] < df['close'].ewm(span=emaLength, adjust=False).mean()
df['neutral'] = False
previous_neutral = False

for date, row in df.iterrows():
    if row['buy']:
        df.at[date, 'neutral'] = True
    elif row['longTermSell']:
        df.at[date, 'neutral'] = False
    else:
        df.at[date, 'neutral'] = previous_neutral
    previous_neutral = df.at[date, 'neutral']

# Define HACOLT
def calculate_hacolt(row):
    if row['buy']:
        return 100
    elif row['neutral']:
        return 50
    else:
        return 0

df['HACOLT'] = df.apply(calculate_hacolt, axis=1)

df.rename(columns={'open':'Open', 'high': 'High', 'low':'Low', 'close':'Close'}, inplace=True)

df.index=original_index


# Define the strategy class
class Strat(Strategy):
    temaLength = 55  # Default value, will be optimized
    emaLength = 23   # Default value, will be optimized

    def init(self):
        self.hacol = self.I(self.hacol_indicator)
        self.iteration_count = 0
        self.pc = 0

    def hacol_indicator(self):
        return self.data.HACOLT

    def next(self):
        self.iteration_count += 1
        self.pc = self.position.size
        if self.data.HACOLT[-2] <= 50 and self.data.HACOLT[-1] == 100:
            if self.position.size == 0:
                self.buy(size=100)
               
            # elif self.position.size < 0:
            #     self.position.close()
            

        if self.data.HACOLT[-2] == 100 and self.data.HACOLT[-1] <= 50:
            if self.position:
                self.position.close()
               

        # if self.data.HACOLT[-2] >= 50 and self.data.HACOLT[-1] == 0:
        #     if self.position.size == 0:
        #         self.sell(size=100)
              
        #     elif self.position.size > 0:
        #         self.position.close()
              

# Optimization function
def run_backtest(temaLength, emaLength):
    Strat.temaLength = temaLength
    Strat.emaLength = emaLength
    bt = Backtest(df, Strat, cash=100000)
    stats = bt.run()
    return stats['Return [%]']

# Optimize parameters
best_return = -float('inf')
best_params = None

for tema in range(20, 200, 5):  # Range for TEMA length
    for ema in range(5, 100, 5):   # Range for EMA length
        current_return = run_backtest(tema, ema)
        if current_return > best_return and tema>ema:
            best_return = current_return
            best_params = (tema, ema)


         

print(f'Best Return: {best_return:.2f}% with TEMA Length: {best_params[0]} and EMA Length: {best_params[1]}')

# Final backtest with best parameters
Strat.temaLength, Strat.emaLength = best_params
bt = Backtest(df, Strat, cash=100000)

stats = bt.run()
print(stats)

# Plotting equity curve using mplfinance
equity_df = pd.DataFrame(stats._equity_curve['Equity'])
equity_df.columns = ['Close']  # Rename column to 'Close'
equity_df['Open'] = equity_df['High'] = equity_df['Low'] = equity_df['Close']  # Add required columns

df.index = pd.to_datetime(df.index)

df = df.sort_index()

# Prepare data for mplfinance
df_mpf = df[['Open', 'High', 'Low', 'Close']]

# Get equity data from stats and align it with df_mpf
equity_series = pd.Series(stats._equity_curve['Equity'])
equity_series.index = df_mpf.index[:len(equity_series)]  # Align indices

# Ensure HACOLT is aligned with df_mpf
hacolt_series = df['HACOLT']

# Create HACOLT plot
hacolt_plot = mpf.make_addplot(hacolt_series, panel=2, color='b', ylabel='HACOLT')

# Create equity plot
equity_plot = mpf.make_addplot(equity_series, panel=1, color='g', ylabel='Equity')



# Create candlestick chart with HACOLT and Equity
mpf.plot(df_mpf, type='candle', style='charles',
         title=f'{ticker} - Candlestick Chart with Equity and HACOLT',
         ylabel='Price',
         volume=False,
         addplot=[equity_plot, hacolt_plot],
         figsize=(12, 10),
         panel_ratios=(2,1,1),
         datetime_format='%Y-%m-%d')

