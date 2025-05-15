import yfinance as yf

def get_current_price(ticker):
    """Fetches the latest stock price for a given ticker symbol."""

    try:
        stock_data = yf.download(ticker, period="1d") 
        latest_price = stock_data['Close'][-1]  # Get the last closing price
        return latest_price 
    except Exception as e:
        return None  # Handle errors gracefully (e.g., invalid ticker)
