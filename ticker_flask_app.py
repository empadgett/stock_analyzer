import subprocess
import sqlite3
import os

def initialize_database():
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create a 'data' directory if it doesn't exist
    data_dir = os.path.join(current_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Set the database path
    db_path = os.path.join(data_dir, 'sp500_data.db')
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS script_results
                 (script_name TEXT, result TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()
    
    return db_path

def run_script(script_name, db_path):
    print(f"Running {script_name}...")
    result = subprocess.run(["python", script_name], capture_output=True, text=True, check=True)
    print(f"{script_name} completed.\n")
    
    # Store the result in the database
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("INSERT INTO script_results (script_name, result) VALUES (?, ?)", (script_name, result.stdout))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    db_path = initialize_database()
    
    scripts = [
        "get_sp500tickers.py",
        "get_sp500pricedata.py",
        "get_consolidations.py",
        # "analyze_hma_crossovers.py",
        # "analyze_channels_breakouts.py",
        # "analyze_gaps_fvgs.py"
    ]

    for script in scripts:
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script)
        if not os.path.exists(script_path):
            print(f"Warning: {script} does not exist. Skipping.")
            continue
        try:
            run_script(script_path, db_path)
        except subprocess.CalledProcessError as e:
            print(f"Error running {script}: {e}")
            print(f"Script output: {e.output}")
        except Exception as e:
            print(f"Unexpected error running {script}: {e}")

    print("All scripts executed.")
