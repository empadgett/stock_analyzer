import os
import yfinance as yf
import pandas as pd
import sqlite3
from datetime import datetime
import logging
import sys
from contextlib import contextmanager

@contextmanager
def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout

# Get the user's home directory
home_dir = os.path.expanduser("~")

# Set the database path
DB_PATH = os.path.join(home_dir, 'myproject_data', 'sp500_data.db')

# Ensure the directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Set up logging
log_dir = '/home/empadgett/myproject/logs'
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, 'stock_data_fetch.log')
logging.basicConfig(filename=log_file, level=logging.INFO,
                    format='%(asctime)s - %(message)s')

def create_table_if_not_exists(conn):
    try:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS tickers (
                Ticker TEXT PRIMARY KEY,
                status TEXT,
                timestamp TEXT
            )
        ''')
        conn.commit()
        logging.info("Tickers table created or already exists.")
    except sqlite3.Error as e:
        logging.error(f"Error creating tickers table: {e}")
        raise

def fetch_stock_data(ticker):
    try:
        with suppress_stdout():
            stock_data = yf.download(ticker, period='1y', interval='1d')
            logging.info(f"Fetched data for {ticker}: {stock_data.shape} rows.")  # Log data shape
            if stock_data.empty:
                logging.warning(f"No data returned for ticker: {ticker}")
                return None
            return stock_data
    except Exception as e:
        logging.error(f"Error fetching data for ticker {ticker}: {e}")
        return None

def update_db_status(conn, ticker, status):
    cur = conn.cursor()
    cur.execute("UPDATE tickers SET status = ?, timestamp = ? WHERE Ticker = ?", 
                (status, datetime.now().isoformat(), ticker))
    conn.commit()

def remove_ticker_from_db(conn, ticker):
    cur = conn.cursor()
    cur.execute("DELETE FROM tickers WHERE Ticker = ?", (ticker,))
    conn.commit()
    logging.info(f"Removed ticker {ticker} from database.")

# Connect to the database
try:
    with sqlite3.connect(DB_PATH) as conn:
        logging.info(f"Successfully connected to database at {DB_PATH}")
        create_table_if_not_exists(conn)

        cur = conn.cursor()

        # Check if the table exists and has data
        cur.execute("SELECT COUNT(*) FROM tickers")
        count = cur.fetchone()[0]
        if count == 0:
            logging.warning("The tickers table is empty. Please run get_sp500tickers.py first to populate the table.")
            sys.exit(1)

        # Fetch tickers from the database
        cur.execute("SELECT Ticker FROM tickers WHERE status = 'pending'")
        tickers = [row[0] for row in cur.fetchall()]

        # Log the count and the tickers retrieved
        logging.info(f"Number of pending tickers retrieved: {len(tickers)}")
        logging.info(f"Pending tickers: {tickers}")

        # Check if there are any tickers to process
        if not tickers:
            logging.warning("No pending tickers found. Exiting process.")
            sys.exit(1)

        # Directory to store CSV files
        directory = 'sp500pricedata'
        os.makedirs(directory, exist_ok=True)

        # Loop through the list of tickers and fetch data
        for ticker in tickers:
            original_ticker = ticker
            logging.info(f"Processing ticker: {ticker}")  # Log ticker being processed
            data = fetch_stock_data(ticker)
            
            if data is None:
                # Try alternative format
                alt_ticker = ticker.replace('.', '-') if '.' in ticker else ticker.replace('-', '.') if '-' in ticker else None
                
                if alt_ticker:
                    logging.info(f"Trying alternative ticker: {alt_ticker}")  # Log alternative attempt
                    data = fetch_stock_data(alt_ticker)
                    if data is not None:
                        ticker = alt_ticker
                        remove_ticker_from_db(conn, original_ticker)
                        logging.info(f"Switched from {original_ticker} to {ticker}")
            
            if data is not None:
                csv_file_name = os.path.join(directory, f"{ticker}.csv")
                try:
                    data.to_csv(csv_file_name, index=True)
                    update_db_status(conn, ticker, 'processed')
                    logging.info(f"Data for {ticker} has been saved to {csv_file_name}.")
                except Exception as e:
                    logging.error(f"Failed to write data for {ticker} to CSV: {e}")
            else:
                update_db_status(conn, original_ticker, 'failed')
                logging.warning(f"Failed to fetch data for {original_ticker}.")

        logging.info("Stock data fetch process completed.")

except sqlite3.Error as e:
    logging.error(f"Error connecting to database or creating table: {e}")
    logging.info(f"Current working directory: {os.getcwd()}")
    logging.info(f"Attempted database path: {DB_PATH}")
    raise


