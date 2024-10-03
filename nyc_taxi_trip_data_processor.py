import argparse
import csv
import logging
import os
from collections import defaultdict
from datetime import datetime, timedelta

# ----------- Section 1: Constants and Configuration -----------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

RATE_CODE_MAPPING = {
    2: 'JFK',
    3: 'Newark',
    4: 'Nassau/WC',
}

CHUNK_SIZE = 10000  # Define the size of chunks


# ----------- Section 2: Function Definitions -----------

def parse_args():
    parser = argparse.ArgumentParser(description='Calculate trip data for a specific month.')
    parser.add_argument('input_file_path', type=str, help='Input path of data, which is stored in csv') ### need check input file exists? 
    parser.add_argument('output_folder_path', type=str, help='Path of folder where the files will be saved')
    args = parser.parse_args()

    if not os.path.isdir(args.output_folder_path):
        logging.error(f'Invalid path: {args.output_folder_path}')
        exit(1)

    return args


def get_time_of_day(hour):
    """ 
    Function to categorize time of day
    Categories: 
        MORNING 06:00 hours to 12:00 hours
        AFTERNOON 12:00 hours to 18:00 hours
        EVENING 18:00 hours to 22:00 hours
        NIGHT 22:00 hours to 06:00 hours
    """
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
    trip_duration = dropoff_datetime - pickup_datetime
    if dropoff_datetime < pickup_datetime or trip_distance == 0 or trip_distance > 300:
        return False
    if trip_duration < timedelta(minutes=1):
        return False
    return True

### performance tuning, not read all csv data into memory, just little chunks 
def read_csv_in_chunks(file_path, chunk_size):
    """Generator function to read the CSV in chunks."""
    with open(file_path, mode='r') as file:
        reader = csv.DictReader(file)
        chunk = []
        for row in reader:
            chunk.append(row)
            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []
        # Yield the remaining rows if any
        if chunk:
            yield chunk


def write_csv(data, output_folder_path, file_name):
    if not data:
        logging.warning(f'No data to write for {file_name}')
        return

    os.makedirs(output_folder_path, exist_ok=True)
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

def process_chunk(chunk, totals, shortest_trips, longest_trips, passenger_data):
    """Process a single chunk of CSV data."""
    for row_num, row in enumerate(chunk, start=1):
        try:
            trip_distance = float(row['trip_distance'])
            ### Predict date format not changed between different months
            pickup_datetime = datetime.strptime(row['tpep_pickup_datetime'], '%Y-%m-%d %H:%M:%S')
            dropoff_datetime = datetime.strptime(row['tpep_dropoff_datetime'], '%Y-%m-%d %H:%M:%S')
            pickup_date = pickup_datetime.date()
            pickup_time_of_day = get_time_of_day(pickup_datetime.hour)

            """
            Assign a default value of 1 if RatecodeID is empty. 
            The RatecodeID column is specified as 'int' in the specification, but the data may contain float values.
            To handle this, convert the float to an int after checking for empty or invalid data.
            """
            rate_code_id = int(float(row['RatecodeID']) if row['RatecodeID'].strip() else 1)
            total_amount = float(row['total_amount'])
            tip_amount = float(row['tip_amount'])
            tolls_amount = float(row['tolls_amount'])
            
            """ 
            Assign a default value of 0 if passenger_count is empty. 
            The passenger_count column is specified as 'int' in the specification, but the data may contain float values.
            To handle this, convert the float to an int after checking for empty or invalid data.
            """
            passenger_count = int(float(row['passenger_count']) if row['passenger_count'].strip() else 0)
            pu_location_id = row['PULocationID'] # Keep PULocationID as string for consistency
            

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

            # Use the validation function
            if not is_valid_trip(trip_distance, pickup_datetime, dropoff_datetime):
                continue

            """
            Task: Calculate the shortest and longest (tripDistance) trips by time of day
            Issues: trip_distance and trip_time often contain incorrect or unreliable data, which can significantly affect calculations.
            is_valid_trip function filter the incorrect data
            Common errors include:
                - Unusually high or low trip distances (e.g., 0 or >300 miles).
                - Dropoff times earlier than pickup times.
                - Extremely short trips (< 1 minute) that may be due to taxi meter errors.
            """

            # Update shortest trip for the specific time of day
            if trip_distance < shortest_trips[pickup_date][pickup_time_of_day] or shortest_trips[pickup_date][pickup_time_of_day] == 0:
                shortest_trips[pickup_date][pickup_time_of_day] = trip_distance
            
            # Update longest trip for the specific time of day
            if trip_distance > longest_trips[pickup_date][pickup_time_of_day]:
                longest_trips[pickup_date][pickup_time_of_day] = trip_distance

        except ValueError as e:
            logging.error(f'Row {row_num}: Invalid value - {e}')


def process_trips_in_chunks(csv_file, chunk_size):
    """Process the entire CSV in chunks."""
    totals = defaultdict(lambda: {'total_amount': 0.0, 'tip_amount': 0.0, 'tolls_amount': 0.0}) ### need test this change
    shortest_trips = defaultdict(lambda: defaultdict(float))
    longest_trips = defaultdict(lambda: defaultdict(float))
    passenger_data = defaultdict(lambda: {'total_passengers': 0, 'trip_count': 0})

    for chunk in read_csv_in_chunks(csv_file, chunk_size):
        process_chunk(chunk, totals, shortest_trips, longest_trips, passenger_data)

    return shortest_trips, totals, passenger_data


# ----------- Section 3: Main Execution (Calling Functions) -----------

if __name__ == '__main__':
    args = parse_args()

    # Define output files
    trip_distance_entity = 'trip_distance_summary.csv'
    amounts_by_airports_entity = 'amounts_by_airports.csv'
    avg_passenger_count_entity = 'avg_passenger_count.csv'

    # Process the CSV in chunks
    trip_distance_data, amounts_data, avg_passenger_data = process_trips_in_chunks(args.input_file_path, CHUNK_SIZE)

    # Write the results to new CSV files
    write_csv(trip_distance_data, args.output_folder_path, trip_distance_entity)
    write_csv(amounts_data, args.output_folder_path, amounts_by_airports_entity)
    write_csv(avg_passenger_data, args.output_folder_path, avg_passenger_count_entity)

    logging.info('Processing complete!')
