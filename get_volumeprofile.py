import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# Download historical data
ticker = 'spy'
data = yf.download(ticker, start='2023-01-01', end='2024-10-15', interval='1d')

# Calculate volume profile
def calculate_volume_profile(data, bins=100):
    price_range = data['Close'].max() - data['Close'].min()
    bin_size = price_range / bins
    price_bins = pd.interval_range(start=data['Close'].min(), end=data['Close'].max(), freq=bin_size)
    volume_profile = data.groupby(pd.cut(data['Close'], bins=price_bins),observed=False)['Volume'].sum()
    return volume_profile

volume_profile = calculate_volume_profile(data)

# Create the figure
fig = go.Figure()

# Add candlestick chart
fig.add_trace(go.Candlestick(x=data.index,
                             open=data['Open'],
                             high=data['High'],
                             low=data['Low'],
                             close=data['Close'],
                             name='OHLC'))

# Add volume profile
max_volume = volume_profile.max()
fig.add_trace(go.Bar(y=[(i.left + i.right)/2 for i in volume_profile.index],
                     x=volume_profile.values / max_volume * (data.index[-1] - data.index[0]).days * 0.2,  # Reduced width
                     orientation='h',
                     name='Volume Profile',
                     marker=dict(color='rgba(128,128,128,0.5)'),
                     xaxis='x2'))

# Update layout
fig.update_layout(
    title=f'{ticker} Stock Price with Volume Profile',
    yaxis_title='Price',
    xaxis_title='Date',
    xaxis_rangeslider_visible=False,
    showlegend=False,
    height=1600,
    width=2400,
    xaxis2=dict(
        overlaying='x',
        side='top',
        showticklabels=False,
        range=[data.index[0], data.index[-1]],
        scaleanchor='x',
        scaleratio=1,
    ),
    margin=dict(l=50, r=100, t=100, b=50),  # Increased right margin
)

# Update font sizes
fig.update_layout(
    title_font_size=24,
    xaxis_title_font_size=18,
    yaxis_title_font_size=18,
    font_size=14
)

# Flip the volume profile to the right side
fig.update_traces(x=[-x for x in fig.data[1]['x']], selector=dict(name='Volume Profile'))
fig.update_layout(xaxis2_range=[data.index[-1], data.index[0]])

# Show the plot
fig.show()




















