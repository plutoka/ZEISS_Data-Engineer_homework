import argparse
import csv
import logging
import os

from datetime import datetime, timedelta

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the argument parser
parser = argparse.ArgumentParser(description='Calculates using trip data for a specific month.')

# Add an argument for the input file path
parser.add_argument('input_file_path', type=str, help='Input path of data, which is stored in csv')

# Add an argument for outputh folder path
parser.add_argument('output_folder_path', type=str, help='Path of folder where the files will be saved')

# Parse the arguments
args = parser.parse_args()


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


def is_valid_trip(trip_distance, pickup_time, dropoff_time):
    """
    Validate trip data based on specified conditions.

    Parameters:
    trip_distance (float): The distance of the trip.
    pickup_time (datetime): The pickup time of the trip.
    dropoff_time (datetime): The dropoff time of the trip.

    Returns:
    bool: True if the trip data is valid, False otherwise.
    """
    # Calculate trip duration
    trip_duration = dropoff_time - pickup_time

    # Check for invalid conditions
    if dropoff_time < pickup_time or trip_distance == 0 or trip_distance > 300:
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

#Calculate the amounts paid (tipAmount, tollsAmount, totalAmount) by airports (rateCodeId)
def calculate_trip_distance(csv_data):
    """
    Task: Calculate the shortest and longest (tripDistance) trips by time of day
    """
    
    # Initialize dictionaries to store shortest and longest trips
    shortest_trips = {}
    longest_trips = {}

    # Iterate over the CSV rows with enumerate, starting at 1, useful for testing
    for row_num, row in enumerate(csv_data, start=1):
        try:
            trip_distance = float(row['trip_distance'])
            pickup_time = datetime.strptime(row['tpep_pickup_datetime'], '%Y-%m-%d %H:%M:%S')
            dropoff_time = datetime.strptime(row['tpep_dropoff_datetime'], '%Y-%m-%d %H:%M:%S')
                    
            # Use the validation function
            if not is_valid_trip(trip_distance, pickup_time, dropoff_time):
                continue  # Skip invalid trips
                
            trip_date = pickup_time.date()
            trip_time_of_day = get_time_of_day(pickup_time.hour)
                            
            # Initialize dictionaries for each date if not already present
            if trip_date not in shortest_trips:
                shortest_trips[trip_date] = {}
                longest_trips[trip_date] = {}
            
            # Update shortest trip for the specific time of day
            if trip_time_of_day not in shortest_trips[trip_date] or trip_distance < shortest_trips[trip_date][trip_time_of_day]:
                shortest_trips[trip_date][trip_time_of_day] = trip_distance
            
            # Update longest trip for the specific time of day
            if trip_time_of_day not in longest_trips[trip_date] or trip_distance > longest_trips[trip_date][trip_time_of_day]:
                longest_trips[trip_date][trip_time_of_day] = trip_distance 
                
        except ValueError as e:
            logging.error(f'Row {row_num}: Invalid value - {e}')

    # Transform the data into a list of dictionaries
    data = []
    for trip_date in shortest_trips:
        for trip_time_of_day in shortest_trips[trip_date]:
            data.append({
                'date': trip_date,
                'time_of_day': trip_time_of_day,
                'shortest_distance': shortest_trips[trip_date][trip_time_of_day],
                'longest_distance': longest_trips[trip_date][trip_time_of_day]
            })
            
    return data


trip_distance_entity = 'trip_distance_summary.csv'


# Read the CSV file
csv_data = read_csv(args.input_file_path)

# Calculate shortest and longest trip by time of day
trip_distance_data = calculate_trip_distance(csv_data)

# Write the results to a new CSV file
write_csv(trip_distance_data, args.output_folder_path, trip_distance_entity)

        
