import numpy as np
from scipy.stats import norm
import matplotlib.pyplot as plt

def black_scholes(S, K, days, r, sigma, option_type='call'):
    T = days / 365
    d1 = (np.log(S/K) + (r + sigma**2/2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    
    if option_type.lower() == 'call':
        option_price = S*norm.cdf(d1) - K*np.exp(-r*T)*norm.cdf(d2)
    else:
        option_price = K*np.exp(-r*T)*norm.cdf(-d2) - S*norm.cdf(-d1)
    return option_price

# Parameters
S = 793  # Stock price
K = 800  # Strike price
r = 0.05  # Risk-free rate
sigma = 0.36  # Volatility

# Create multiple DTE scenarios
dte_scenarios = [1, 7, 30, 86]
colors = ['red', 'orange', 'blue', 'green']

# Calculate price range
price_range = 0.20
min_price = S * (1 - price_range)
max_price = S * (1 + price_range)
stock_prices = np.linspace(min_price, max_price, 100)

# Create the plot
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12))

# Plot for calls
for days, color in zip(dte_scenarios, colors):
    call_prices = [black_scholes(s, K, days, r, sigma, 'call') for s in stock_prices]
    ax1.plot(stock_prices, call_prices, label=f'{days} DTE', color=color, linewidth=2)

ax1.axvline(x=K, color='gray', linestyle='--', alpha=0.5, label='Strike')
ax1.axvline(x=S, color='black', linestyle=':', alpha=0.5, label='Current Price')
ax1.grid(True, alpha=0.3)
ax1.set_title(f'Call Option Prices vs Days to Expiration\nStock=${S}, Strike=${K}, Vol={sigma*100:.0f}%')
ax1.set_xlabel('Stock Price')
ax1.set_ylabel('Call Option Price')
ax1.legend()

# Plot for puts
for days, color in zip(dte_scenarios, colors):
    put_prices = [black_scholes(s, K, days, r, sigma, 'put') for s in stock_prices]
    ax2.plot(stock_prices, put_prices, label=f'{days} DTE', color=color, linewidth=2)

ax2.axvline(x=K, color='gray', linestyle='--', alpha=0.5, label='Strike')
ax2.axvline(x=S, color='black', linestyle=':', alpha=0.5, label='Current Price')
ax2.grid(True, alpha=0.3)
ax2.set_title('Put Option Prices vs Days to Expiration')
ax2.set_xlabel('Stock Price')
ax2.set_ylabel('Put Option Price')
ax2.legend()

plt.tight_layout()

# Print some example values at current stock price
print(f"Option prices at current stock price (${S:.2f}):")
print("\nDays to Expiration  |  Call Price  |  Put Price")
print("-" * 50)
for days in dte_scenarios:
    call = black_scholes(S, K, days, r, sigma, 'call')
    put = black_scholes(S, K, days, r, sigma, 'put')
    print(f"{days:^16d} | ${call:^10.2f} | ${put:^9.2f}")

plt.show()


