import os

# Define the file path
file_path = r'C:\tmp\test.txt'

# Write "Hello, World!" to the file
with open(file_path, 'w') as file:
    file.write("Hello, World!")

# Check if the file exists
if os.path.exists(file_path):
    print(f"File successfully saved to: {file_path}")
else:
    print("File does not exist.")
