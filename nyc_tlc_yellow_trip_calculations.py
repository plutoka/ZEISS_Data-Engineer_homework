# Questions
# 1. Calculate the shortest and longest (tripDistance) trips by time of day
import csv
from datetime import datetime, timedelta

# Function to categorize time of day
# Categories: 
#   MORNING 06:00 hours to 12:00 hours
#   AFTERNOON 12:00 hours to 18:00 hours
#   EVENING 18:00 hours to 22:00 hours
#   NIGHT 22:00 hours to 06:00 hours

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



# Specify the path for the output CSV file
input_file = r'C:\_work\zeiss\yellow_tripdata_2024-01.csv'
output_file = r'C:\_work\zeiss\yellow_tripdata_summary.csv'


# Initialize dictionaries to store shortest and longest trips
shortest_trips = {}
longest_trips = {}


# Read the CSV file
with open(input_file, mode='r') as file:
    csv_reader = csv.DictReader(file)
    
    # Iterate over the CSV rows with enumerate, starting at 1, usefull for testing
    for row_num, row in enumerate(csv_reader, start=1):
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
                #print(trip_date, trip_time_of_day, row_num, pickup_time, trip_distance)
            
            
# Write the results to a new CSV file
with open(output_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['trip_date', 'trip_time_of_day', 'shortest_trip_distance', 'longest_trip_distance'])
    
    for trip_date in shortest_trips:
        for trip_time_of_day in shortest_trips[trip_date]:
            writer.writerow([trip_date, trip_time_of_day, shortest_trips[trip_date][trip_time_of_day], longest_trips[trip_date][trip_time_of_day]])

print("The results have been saved to trip_summary.csv")       

        
