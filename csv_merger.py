import os
import pandas as pd

# Define the directory where the CSV files are located
directory = 'csv\\GenderAPI'

# Define the prefix of the CSV file names
prefix = 'first_names_gapi_processed'

# Get the list of CSV files in the directory
csv_files = [file for file in os.listdir(directory) if file.startswith(prefix) and file.endswith('.csv')]

# Initialize an empty DataFrame to store the combined data
combined_data = pd.DataFrame()

# Iterate over the CSV files
for file in csv_files:
    # Read the CSV file into a DataFrame
    file_path = os.path.join(directory, file)
    data = pd.read_csv(file_path)
    
    # Append the data to the combined DataFrame
    combined_data = combined_data.append(data, ignore_index=True)

# Write the combined data to a new CSV file
combined_file_path = os.path.join(directory, f'{prefix}.csv')
combined_data.to_csv(combined_file_path, index=False)

print('CSV files combined successfully.')
