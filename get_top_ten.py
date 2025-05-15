import requests
from bs4 import BeautifulSoup

def get_spdr_holdings(ticker):
    # Convert ticker to uppercase
    ticker = ticker.upper()
    
    # SPDR ETFs often use this URL structure
    url = f"https://www.ssga.com/us/en/individual/etfs/funds/the-{ticker}-select-sector-spdr-fund-{ticker.lower()}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        holdings_table = soup.find('table', {'id': 'fund-top-holdings'})

        if holdings_table:
            holdings = []
            rows = holdings_table.find_all('tr')[1:]  # Skip header row
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    holding = cols[0].text.strip()
                    weight = cols[1].text.strip()
                    holdings.append(f"{holding}: {weight}")
            
            print(f"Top 10 Holdings for {ticker}:")
            for i, holding in enumerate(holdings[:10], 1):
                print(f"{i}. {holding}")
        else:
            print(f"Could not find holdings information for {ticker}")
            
    except requests.exceptions.RequestException as e:
        print(f"Error accessing the website: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage
ticker = "xlf"
get_spdr_holdings(ticker)
