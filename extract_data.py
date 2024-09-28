import argparse
import os
import pandas as pd
import requests
import logging

from datetime import datetime
from io import BytesIO

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the argument parser
parser = argparse.ArgumentParser(description='Download trip data for a specific month.')

# Add an argument for the month of data
parser.add_argument('month_of_data', type=str, help='Month of data in YYYY-MM format')

# Add an argument for the output path
parser.add_argument('output_file_path', type=str, help='Path where the file will be saved')

# Parse the arguments
args = parser.parse_args()

# Function to validate the month format
def validate_month_format(month_str):
    try:
        datetime.strptime(month_str, '%Y-%m')
        return True
    except ValueError:
        return False

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

# Validate the month_of_data format
if not validate_month_format(args.month_of_data):
    logging.error('Invalid month format. Please provide a valid date in YYYY-MM format.')
    exit(1)

# Validate the path
if not os.path.isdir(args.output_file_path):
    logging.error(f'Invalid path: {args.output_file_path}')
    exit(1)

# Construct the URL
url = f'https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{args.month_of_data}.parquet'

# Call the function to fetch the data
data = fetch_data_from_url(url)

if data:
    # Convert and save data to CSV
    csv_full_path = os.path.join(args.output_file_path, f"yellow_tripdata_{args.month_of_data}.csv")
    convert_data_to_csv(data, csv_full_path)
    logging.info(f'Data saved to {csv_full_path}')