import os
import shutil
import getpass
from datetime import datetime

# Get the Windows username
windows_username = getpass.getuser()

# Define the paths
windows_downloads = f'/mnt/c/Users/empad/Downloads/'
current_dir = os.getcwd()

# Find the most recent Portfolio_positions file
portfolio_files = [f for f in os.listdir(windows_downloads) if f.startswith("Portfolio_Positions_")]
if not portfolio_files:
    print("No Portfolio_positions files found in Downloads.")
    exit()

most_recent_file = max(portfolio_files, key=lambda f: os.path.getmtime(os.path.join(windows_downloads, f)))

# Source and destination paths
src_path = os.path.join(windows_downloads, most_recent_file)
dst_path = os.path.join(current_dir, most_recent_file)

# Copy the file
try:
    shutil.copy2(src_path, dst_path)
    print(f"File '{most_recent_file}' copied successfully to {dst_path}")
except FileNotFoundError:
    print(f"File not found: {src_path}")
except PermissionError:
    print(f"Permission denied: Unable to copy {src_path}")
except Exception as e:
    print(f"An error occurred: {str(e)}")

# Ask if user wants to delete the original file
if os.path.exists(dst_path):
    delete = input("Do you want to delete the original file from Downloads? (y/n): ")
    if delete.lower() == 'y':
        try:
            os.remove(src_path)
            print(f"Original file deleted from {src_path}")
        except PermissionError:
            print(f"Permission denied: Unable to delete {src_path}")
        except Exception as e:
            print(f"An error occurred while deleting: {str(e)}")

# Rename the file to a standard name if needed
standard_name = "Positions"
if os.path.exists(dst_path):
    standard_path = os.path.join(current_dir, standard_name)
    os.rename(dst_path, standard_path)
    print(f"File renamed to {standard_name}")
