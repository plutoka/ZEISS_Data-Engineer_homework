import argparse
import csv
import logging
import os

from collections import defaultdict
from datetime import datetime, timedelta


# ----------- Section 1: Constants and Configuration -----------

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

RATE_CODE_MAPPING = {
    2: 'JFK',
    3: 'Newark',
    4: 'Nassau/WC',
}

# ----------- Section 2: Function Definitions -----------

def parse_args():
    parser = argparse.ArgumentParser(description='Calculate trip data for a specific month.')
    parser.add_argument('input_file_path', type=str, help='Input path of data, which is stored in csv')
    parser.add_argument('output_folder_path', type=str, help='Path of folder where the files will be saved')
    args = parser.parse_args()
    
    # Validate the path, folder need exists
    if not os.path.isdir(args.output_folder_path):
        logging.error(f'Invalid path: {args.output_folder_path}')
        exit(1)
    
    
    return args


""" 
Function to categorize time of day
Categories: 
    MORNING 06:00 hours to 12:00 hours
    AFTERNOON 12:00 hours to 18:00 hours
    EVENING 18:00 hours to 22:00 hours
    NIGHT 22:00 hours to 06:00 hours
"""
def get_time_of_day(hour):
    if 6 <= hour < 12:
        return 'MORNING'
    elif 12 <= hour < 18:
        return 'AFTERNOON'
    elif 18 <= hour < 22:
        return 'EVENING'
    else:
        return 'NIGHT'


def is_valid_trip(trip_distance, pickup_datetime, dropoff_datetime):
    """
    Validate trip data based on specified conditions.

    Parameters:
    trip_distance (float): The distance of the trip.
    pickup_datetime: The pickup time of the trip.
    dropoff_datetime: The dropoff time of the trip.

    Returns:
    bool: True if the trip data is valid, False otherwise.
    """
    # Calculate trip duration
    trip_duration = dropoff_datetime - pickup_datetime

    # Check for invalid conditions
    if dropoff_datetime < pickup_datetime or trip_distance == 0 or trip_distance > 300:
        return False  # Invalid trip data

    # Filter out trips that are less than 1 minute
    if trip_duration < timedelta(minutes=1):
        return False  # Invalid trip duration

    return True  # Valid trip data


def read_csv(file_path):
    with open(file_path, mode='r') as file:
        reader = csv.DictReader(file)
        data = [row for row in reader]
    return data


# Function to write data to a CSV file with exception handling
def write_csv(data, output_folder_path, file_name):
    if not data:
        logging.warning(f'No data to write for {file_name}')
        return
        
    # Ensure the folder exists
    os.makedirs(output_folder_path, exist_ok=True)  # Creates the folder if it does not exist
    
    # Combine folder and file name
    output_file_path = os.path.join(output_folder_path, file_name)  
    try:
        with open(output_file_path, mode='w', newline='') as file:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(data)
        logging.info(f'The results have been saved to {output_file_path}')
    except Exception as e:
        logging.error(f'An error occurred while writing to the file: {e}')


def process_trips(csv_data):
    # Initialize dictionaries to store shortest and longest trips
    shortest_trips = {}
    longest_trips = {}
    
    # Initialize sums for each category
    totals = {
        'JFK': {'total_amount': 0.0, 'tip_amount': 0.0, 'tolls_amount': 0.0},
        'Newark': {'total_amount': 0.0, 'tip_amount': 0.0, 'tolls_amount': 0.0},
        'Nassau/WC': {'total_amount': 0.0, 'tip_amount': 0.0, 'tolls_amount': 0.0},
    }
    
    # Dictionary to hold the total passenger count and count of trips per day
    passenger_data = defaultdict(lambda: {'total_passengers': 0, 'trip_count': 0})

    for row_num, row in enumerate(csv_data, start=1):
        try:
            # Extract values for calculate shortest and longest distance
            trip_distance = float(row['trip_distance'])
            pickup_datetime = datetime.strptime(row['tpep_pickup_datetime'], '%Y-%m-%d %H:%M:%S')
            dropoff_datetime = datetime.strptime(row['tpep_dropoff_datetime'], '%Y-%m-%d %H:%M:%S')
            pickup_date = pickup_datetime.date()
            pickup_time_of_day = get_time_of_day(pickup_datetime.hour)
            
            # Extract values for calculate amounts by airports
            # Assign a default value of 1 if RatecodeID is empty. If value is float convert to int as specification declared
            rate_code_id = int(float(row['RatecodeID']) if row['RatecodeID'].strip() else 1)
            total_amount = float(row['total_amount'])
            tip_amount = float(row['tip_amount'])
            tolls_amount = float(row['tolls_amount'])
            
            # Assign a default value of 0 if passenger_count is empty. If value is float convert to int as specification declared
            passenger_count = int(float(row['passenger_count']) if row['passenger_count'].strip() else 0) 
            pu_location_id = row['PULocationID']  # Keep PULocationID as string for consistency
            
            """
            Task: Calculate the amounts paid (tipAmount, tollsAmount, totalAmount) by airports (rateCodeId)
            """
            # Use the mapping to determine the category
            category = RATE_CODE_MAPPING.get(rate_code_id)
            if category:
                totals[category]['total_amount'] += total_amount
                totals[category]['tip_amount'] += tip_amount
                totals[category]['tolls_amount'] += tolls_amount
                                
            """
            Optinal task: Calculate average passenger count by date and pickup location
            """
            # Update the totals for the respective (date, location)
            passenger_data[(pickup_date, pu_location_id)]['total_passengers'] += passenger_count
            passenger_data[(pickup_date, pu_location_id)]['trip_count'] += 1
            
            """
            Task: Calculate the shortest and longest (tripDistance) trips by time of day
            Issues: trip_distance and trip_time often contain incorrect or unreliable data, which can significantly affect calculations.
            is_valid_trip function filter the incorrect data
            Common errors include:
                - Unusually high or low trip distances (e.g., 0 or >300 miles).
                - Dropoff times earlier than pickup times.
                - Extremely short trips (< 1 minute) that may be due to taxi meter errors.
            """
            # Use the validation function
            if not is_valid_trip(trip_distance, pickup_datetime, dropoff_datetime):
                continue  # Skip invalid trips
                
                            
            # Initialize dictionaries for each date if not already present
            if pickup_date not in shortest_trips:
                shortest_trips[pickup_date] = {}
                longest_trips[pickup_date] = {}
            
            # Update shortest trip for the specific time of day
            if pickup_time_of_day not in shortest_trips[pickup_date] or trip_distance < shortest_trips[pickup_date][pickup_time_of_day]:
                shortest_trips[pickup_date][pickup_time_of_day] = trip_distance
            
            # Update longest trip for the specific time of day
            if pickup_time_of_day not in longest_trips[pickup_date] or trip_distance > longest_trips[pickup_date][pickup_time_of_day]:
                longest_trips[pickup_date][pickup_time_of_day] = trip_distance 

        except ValueError as e:
            logging.error(f'Row {row_num}: Invalid value - {e}')

    # Transform the totals into a list of dictionaries
    amounts_data = [{'category': key, **value} for key, value in totals.items()]
    
    # Transform the avg passenger_data into a list of dictionaries
    avg_passenger_data = []
    for (date, location), trip_data in passenger_data.items():
        if trip_data['trip_count'] > 0:
            average_passenger_count = round(trip_data['total_passengers'] / trip_data['trip_count'], 2)
            avg_passenger_data.append({
                'date': date,
                'pickup_loc_id': location,
                'avg_passenger_count': average_passenger_count
            })
            
    # Transform the trip_distance_data into a list of dictionaries
    trip_distance_data = []
    for trip_date in shortest_trips:
        for trip_time_of_day in shortest_trips[trip_date]:
            trip_distance_data.append({
                'date': trip_date,
                'time_of_day': trip_time_of_day,
                'shortest_distance': shortest_trips[trip_date][trip_time_of_day],
                'longest_distance': longest_trips[trip_date][trip_time_of_day]
            })
            
    return trip_distance_data, amounts_data, avg_passenger_data


# ----------- Section 3: Main Execution (Calling Functions) -----------

if __name__ == '__main__':
    args = parse_args()

    # Entities for define output files
    trip_distance_entity = 'trip_distance_summary.csv'
    amounts_by_airports_entity = 'amounts_by_airports.csv'
    avg_passenger_count_entity = 'avg_passenger_count.csv'

    # Read the CSV file
    csv_data = read_csv(args.input_file_path)

    # Calculate different task based on csv 
    trip_distance_data, amounts_data, avg_passenger_data = process_trips(csv_data)

    # Write the results to a new CSV files
    write_csv(trip_distance_data, args.output_folder_path, trip_distance_entity)
    write_csv(amounts_data, args.output_folder_path, amounts_by_airports_entity)
    write_csv(avg_passenger_data, args.output_folder_path, avg_passenger_count_entity)
    
    logging.info('Processing complete!')