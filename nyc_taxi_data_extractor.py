import argparse
import os
import pandas as pd
import requests
import logging

from datetime import datetime
from io import BytesIO


# ----------- Section 1: Constants and Configuration -----------

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ----------- Section 2: Function Definitions -----------

def parse_args():
    parser = argparse.ArgumentParser(description='Download trip data for a specific month.')
    parser.add_argument('month_of_data', type=str, help='Month of data in YYYY-MM format')
    parser.add_argument('output_folder_path', type=str, help='Path of folder where the files will be saved')
    args = parser.parse_args()
    
    # Validate the month_of_data format
    if not validate_month_format(args.month_of_data):
        logging.error('Invalid month format. Please provide a valid date in YYYY-MM format.')
        exit(1)

    # Validate the path, folder need exists
    if not os.path.isdir(args.output_folder_path):
        logging.error(f'Invalid path: {args.output_folder_path}')
        exit(1)
    
    return args


# Function to validate the month format
def validate_month_format(month_str):
    try:
        datetime.strptime(month_str, '%Y-%m')
        return True
    except ValueError:
        return False

# Download parquet file from url
def fetch_data_from_url(url):
    try:
        with requests.get(url) as response:
            response.raise_for_status()
            return response.content
    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred: {e}")
        return None


# Convert Parquet file using panda lib, save as a CSV file
def convert_data_to_csv(data, csv_full_path):
    with BytesIO(data) as parquet_file:
        df = pd.read_parquet(parquet_file)
        df.to_csv(csv_full_path, index=False)


# ----------- Section 3: Main Execution (Calling Functions) -----------

if __name__ == '__main__':
    args = parse_args()
    
    source_file = f'yellow_tripdata_{args.month_of_data}.parquet'
    output_file = f'yellow_tripdata_{args.month_of_data}.csv'
    output_full_path = os.path.join(args.output_folder_path, output_file)

    # Construct the URL
    url = f'https://d37ci6vzurychx.cloudfront.net/trip-data/{source_file}'

    # Call the function to fetch the data
    data = fetch_data_from_url(url)

    if data:
        # Convert and save data to CSV
        convert_data_to_csv(data, output_full_path)
        logging.info(f'Data saved to {output_full_path}')