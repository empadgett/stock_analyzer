# get_sp500tickers.py

import pandas as pd
import sqlite3
import re
from datetime import datetime
import os
import sys

def get_sp500_tickers():
    try:
        # URL of the Wikipedia page containing the S&P 500 list
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'

        # Read the HTML tables from the page
        tables = pd.read_html(url)

        # The first table contains the S&P 500 companies
        sp500_table = tables[0]

        # Extract the tickers
        tickers = sp500_table['Symbol'].tolist()

        # Check for 'xxxx.x' tickers and add 'xxxx-x' versions
        additional_tickers = []
        for ticker in tickers:
            if re.match(r'^.+\.[A-Z]$', ticker):
                additional_tickers.append(ticker[:-2] + '-' + ticker[-1])

        # Add the additional tickers to the list
        tickers.extend(additional_tickers)

        # Create a DataFrame from the list
        df = pd.DataFrame(tickers, columns=['Ticker'])

        # Get the user's home directory
        home_dir = os.path.expanduser("~")
        
        # Create a 'myproject_data' directory in the home directory if it doesn't exist
        data_dir = os.path.join(home_dir, 'myproject_data')
        os.makedirs(data_dir, exist_ok=True)
        
        # Set the database path
        db_path = os.path.join(data_dir, 'sp500_data.db')

        print(f"Attempting to connect to database at: {db_path}")

        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # Create the table with Ticker as primary key
        cur.execute('''
            CREATE TABLE IF NOT EXISTS tickers (
                Ticker TEXT PRIMARY KEY,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending'
            )
        ''')

        # Insert or replace the data
        df['timestamp'] = datetime.now().isoformat()
        df['status'] = 'pending'
        df.to_sql('tickers', conn, if_exists='replace', index=False)

        # Verify the data
        cur.execute('SELECT COUNT(*) FROM tickers')
        count = cur.fetchone()[0]
        print(f'Number of tickers in database: {count}')

        # Commit changes and close connection
        conn.commit()
        conn.close()

        print('Tickers have been saved to the database with Ticker as primary key')

        return tickers

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    get_sp500_tickers()

