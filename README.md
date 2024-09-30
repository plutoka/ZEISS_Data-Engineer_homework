# NYC Yellow Taxi Trip Data Processor

This script processes New York City (NYC) yellow taxi trip data, extracts meaningful insights, and saves the results into separate CSV files. 
The data includes:
	- trip distance summaries
	- amounts paid by airports (based on rate codes)
	- average passenger counts by date and location. 
	
The script is designed to handle errors in the data and ensure the output contains only valid and reliable information.

## Table of Contents

1. [Features](#features)
2. [Installation](#installation)
3. [Usage](#usage)
4. [Input File Format](#input-file-format)
5. [Output Files](#output-files)
6. [Script Workflow](#script-workflow)
7. [Error Handling](#error-handling)
8. [Logging](#logging)

## Features

- **Trip Distance Analysis**: Calculate the shortest and longest trips by time of day.
- **Airport-Specific Amounts**: Summarizes total fare, tip amount, and toll charges based on trip destinations (JFK, Newark, Nassau/Westchester).
- **Passenger Count Analysis**: Computes the average number of passengers by date and pickup location.
- **Data Validation**: Filters out invalid trips, including trips with incorrect distances, unreasonable durations, or negative fare values.
- **Logging**: Logs process steps and errors, providing clear insight into the script's operation.


## Installation

1. **Ensure Python 3.12 is installed**:  
   This script requires Python 3.12 or later. You can check your Python version by running:

   ```bash
   python --version
   ```

2. **Clone the Repository**:
   ```bash
   git clone https://github.com/plutoka/ZEISS_Data-Engineer_homework.git
   cd nyc-taxi-trip-processor
   ```

3. **Environment Setup**:
	The data extraction script requires the following Python libraries:

	- `pandas`
	- `pyarrow`
	- `requests`
	
	Install this libraries manualy or use requirements.txt:
	
	```bash
	pip install -r requirements.txt
	```

   The data processing script uses only Python's standard libraries:
   - `argparse`
   - `csv`
   - `logging`
   - `os`
   - `datetime`
   - `collections`

## Usage

To run the scripts, provide the arguments:

```bash
python nyc_taxi_data_extractor.py <YYYY-MM> <output_folder_path>
python nyc_taxi_trip_data_processor.py <input_file_path> <output_folder_path>
```

### Example:

```bash
python nyc_taxi_data_extractor.py 2024-02 C:\Work\NCY
python nyc_taxi_trip_data_processor.py C:\Work\NCY\yellow_tripdata_2024-02.csv C:\Work\NCY
```

### Arguments:
	nyc_taxi_data_extractor.py:
	- `month_of_data`: Path to the CSV file containing NYC yellow taxi trip data.
	- `output_folder_path`: Path to the folder where output file will be saved.
	
	nyc_taxi_trip_data_processor.py:
	- `input_file_path`: Chosen month of data analysis.
	- `output_folder_path`: Path to the folder where output files will be saved.
	
## Input File Format

The input file should be in CSV format and must contain the following columns:
- `trip_distance`: Distance of the trip.
- `tpep_pickup_datetime`: Pickup timestamp.
- `tpep_dropoff_datetime`: Dropoff timestamp.
- `RatecodeID`: Numeric code representing the destination of the trip (e.g., 2 for JFK, 3 for Newark).
- `total_amount`: The total amount charged for the trip.
- `tip_amount`: The tip amount given by the passenger.
- `tolls_amount`: The amount paid in tolls.
- `passenger_count`: The number of passengers in the taxi.
- `PULocationID`: Pickup location ID.

## Output Files

The script generates three CSV files in the output folder:

1. **Trip Distance Summary (`trip_distance_summary.csv`)**:  
   Contains the shortest and longest trip distances by date and time of day (morning, afternoon, evening, night).

   | Date       | Time of Day | Shortest Distance | Longest Distance |
   |------------|-------------|-------------------|------------------|
   | 2024-01-01 | MORNING     | 1.2               | 15.5             |

2. **Amounts by Airports (`amounts_by_airports.csv`)**:  
   Summarizes the total amount, tip amount, and tolls amount for trips to JFK, Newark, and Nassau/Westchester.

   | Category   | Total Amount | Tip Amount | Tolls Amount |
   |------------|--------------|------------|--------------|
   | JFK        | 1000.50      | 150.75     | 25.00        |

3. **Average Passenger Count (`avg_passenger_count.csv`)**:  
   Contains the average passenger count by date and pickup location.

   | Date       | Pickup Location ID | Average Passenger Count |
   |------------|--------------------|-------------------------|
   | 2024-01-01 | 101                | 1.75                    |

## Script Workflow

1. **Argument Parsing**:  
   The scripts accepts two arguments via the `argparse` library.

2. **Reading Data**:  
   The data processor script reads the input CSV file using Python’s `csv.DictReader`.

3. **Data Processing**:  
   The following tasks are performed:
   - **Trip Distance Calculation**: The shortest and longest trips are calculated for each day and time period.
   - **Amount Summarization**: Total amounts, tip amounts, and toll amounts are aggregated based on rate codes (JFK, Newark, Nassau/Westchester).
   - **Passenger Count Calculation**: The average number of passengers per pickup location and date is computed.

4. **Writing Output**:  
   The processed results are written to three separate CSV files.

## Error Handling

- **Invalid Data**:  
  The data processor script validates trips using the `is_valid_trip()` function while calculate trip distance.
  The function filters out entries with incorrect trip distances, invalid pickup and dropoff times, or extremely short trips (<1 minute).
  The `RatecodeID` and `passenger_count` columns is specified as 'int' in the specification, but the data may contain float and empty values.
  We replace empty values to a default and convert float values to int.
  
- **Row-Level Validation**:  
  Each row in the CSV file is processed in a `try-except` block to handle potential issues such as missing or malformed data. Errors are logged with the row number and error details.

## Logging

- Logging is configured at the `INFO` level, providing insight into the process flow.
- Errors encountered during data reading or processing are logged with details for troubleshooting.