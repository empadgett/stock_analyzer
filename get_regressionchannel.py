import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf

def calc_regression(source, length):
    if len(source) < length:
        return np.nan, np.nan, np.nan
    
    x = np.arange(length)
    y = source[-length:]
    
    slope, intercept = np.polyfit(x, y, 1)
    average = np.mean(y)
    
    return slope, average, intercept

def calc_channel(source, high, low, length, slope, intercept):
    y_line = np.arange(length) * slope + intercept
    deviations = source[-length:] - y_line
    std_dev = np.std(deviations)
    
    up_dev = np.max(high[-length:] - y_line)
    dn_dev = np.max(y_line - low[-length:])
    
    return std_dev, up_dev, dn_dev

def linear_regression_channel(data, length=200, upper_mult=2.0, lower_mult=2.0):
    close = data['Close'].values
    high = data['High'].values
    low = data['Low'].values
    
    slope, average, intercept = calc_regression(close, length)
    std_dev, up_dev, dn_dev = calc_channel(close, high, low, length, slope, intercept)
    
    x = np.arange(length)
    regression_line = x * slope + intercept
    upper_channel = regression_line + upper_mult * std_dev
    lower_channel = regression_line - lower_mult * std_dev
    
 
    print(f"{slope:.2f}")
    print("${:,.2f}".format(intercept))
    # Plotting
    plt.figure(figsize=(14, 7))
    plt.plot(data.index, close, label='Close Price', color='black')
    plt.plot(data.index[-length:], regression_line, label='Regression Line', color='red')
    plt.plot(data.index[-length:], upper_channel, label='Upper Channel', color='blue')
    plt.plot(data.index[-length:], lower_channel, label='Lower Channel', color='green')
    
    plt.fill_between(data.index[-length:], upper_channel, lower_channel, color='lightblue', alpha=0.3)
    plt.title(f'Linear Regression Channel for {ticker}')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.show()

# Fetch data from yfinance
ticker = 'tsla'
data = yf.download(ticker, start='2023-01-01', end='2024-10-04', progress=False)

# Call the function with the data
linear_regression_channel(data)

