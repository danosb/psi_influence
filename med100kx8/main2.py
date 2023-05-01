# Pulls number from a random number generator, analyzes, stores to database
# Uses Scott Wilber's Random Walk Bias Amplification algorithm:
# ..https://drive.google.com/file/d/1ASvbdI-uQs_4HNL3fh85g72mIRndkjdn/view

import queue
import random
import time
import threading
import pymysql
import sys
from pyftdi.ftdi import Ftdi
import json
from datetime import datetime
import math
import os
from final_output import final_output
from dbutils.pooled_db import PooledDB


n = 31 # Defined number of steps required to complete a random walk
trial_count = 20000 # Number of trials we'll perform
count_subtrial_per_trial = 21 # Number of subtrials per trial
serial_number = "QWR4E010"  # Replace with your serial number

# Device communication parameters
FTDI_DEVICE_LATENCY_MS = 2
FTDI_DEVICE_PACKET_USB_SIZE = 8
FTDI_DEVICE_TX_TIMEOUT = 5000
ftdi = Ftdi()
ftdi.open_from_url(f"ftdi://ftdi:232:{serial_number}/1")
ftdi.set_latency_timer(FTDI_DEVICE_LATENCY_MS)
ftdi.write_data_get_chunksize = lambda x: FTDI_DEVICE_PACKET_USB_SIZE
ftdi.read_data_get_chunksize = lambda x: FTDI_DEVICE_PACKET_USB_SIZE

# Get MySQL creds from environment variables
username = os.getenv('MYSQL_USER')
password = os.getenv('MYSQL_PASSWORD')
host = os.getenv('MYSQL_HOST')
database = os.getenv('MYSQL_DB')

# Global variables to store total time taken by functions
total_extract_numbers_time = 0
total_analyze_subtrial_time = 0
total_write_to_database_time = 0


# Initialize connection pool for MySQL
mysql_pool = PooledDB(
    creator=pymysql,
    mincached=5,
    maxcached=10,
    host=host,
    user=username,
    password=password,
    database=database,
    autocommit=True,
)


# Looks up the max supertrial number so we can properly assign supertrial for our run
def get_supertrial():
    try:
        # Get connection from the connection pool
        cnx1 = mysql_pool.connection()
        cursor = cnx1.cursor()

        # Get the current max supertrial
        cursor.execute("SELECT MAX(supertrial) FROM trial_data")
        result = cursor.fetchone()

        # Store supertrial number
        if result is not None and result[0] is not None and isinstance(result[0], int):
            supertrial = result[0] + 1
        else:
            supertrial = 1

        print(f"supertrial:", (supertrial))

        return supertrial

        # Close the cursor and connection
        cursor.close()
        cnx1.close()

    except pymysql.Error as err:
        print("Error accessing MySQL database: {}".format(err))
        return None


# Function to extract numbers from the RNG. This happens indefinitely until a stop signal is received (analysis for the trial completes)
def extract_numbers(number_queue, stop_event):
    global total_extract_numbers_time

    number_buffer = bytearray()  # buffer for constructing random numbers
    number_buffer.clear()  # Clear the number_buffer when the function is called

    start_time = time.time()

    while not stop_event.is_set():  # while stop event is not triggered
        # Request a new random number
        init_comm = b'\x96'
        bytes_txd = ftdi.write_data(init_comm)

        # Read bytes from the buffer first if possible
        bytes_to_read = 64
        dx_data = ftdi.read_data(bytes_to_read)
        if dx_data:
            number_buffer.extend(dx_data)  # Add the received data to the number buffer

            # If we have at least 8 bytes in the number buffer, construct random numbers
            while len(number_buffer) >= 8:
                number = int.from_bytes(number_buffer[:8], "big")  # Construct the random number
                number_queue.put(number)  # Put the number into the queue
                number_buffer = number_buffer[8:]  # Remove the used bytes from the number buffer

        time.sleep(0.001)  # Sleep for a short time to avoid busy waiting

    end_time = time.time()
    elapsed_time = end_time - start_time
    total_extract_numbers_time += elapsed_time  # Update the global variable


# Function to analyze subtrials and add to DB write-queue
def analyze_subtrial(number_queue, stop_event, db_queue, n, trial, supertrial):
    global total_analyze_subtrial_time
    start_time = time.time()
    subtrial_number = 0
    trial_cum_sv = 0
    trial_weighted_sv = 0
    trial_norm_weighted_sv = 0
    int_array = []
    bidirectional_count = 0
    bidirectional_is_pos = False
    number_steps = 0
    int_array = []

    # Hard-code the empirically-generated values, for now.
    N_CDF_vals = [(29, 0.0), (31, 4.6566e-10), (43, 2.5e-7), (55, 0.0000125), (65, 0.000099), (79, 0.00058575), (93, 0.00190025), (105, 0.0039455), (107, 0.0043945), (121, 0.008407), (141, 0.01659625), (149, 0.02066175), (165, 0.030027), (181, 0.04097325), (193, 0.050018), (205, 0.0596295), (217, 0.06968525), (229, 0.08007275), (241, 0.0908285), (251, 0.1000605), (263, 0.11127425), (273, 0.12071075), (283, 0.13028675), (293, 0.13996), (303, 0.14965975), (313, 0.159455), (323, 0.169184), (335, 0.1807995), (345, 0.19049125), (355, 0.20016375), (365, 0.2098285), (377, 0.2213085), (387, 0.230712), (397, 0.240088), (407, 0.2494425), (419, 0.26057975), (429, 0.26976425), (441, 0.280628), (451, 0.28950875), (463, 0.30000425), (475, 0.31068675), (487, 0.32107725), (497, 0.3295655), (509, 0.339624), (521, 0.34972), (533, 0.35958), (545, 0.36930075), (547, 0.37091775), (559, 0.38047775), (571, 0.38994775), (585, 0.40080525), (597, 0.4099845), (611, 0.4205175), (625, 0.43086725), (637, 0.43958075), (653, 0.45089025), (667, 0.46073875), (681, 0.470314), (695, 0.47976625), (711, 0.490367), (727, 0.50069425), (741, 0.50964775), (759, 0.52087975), (775, 0.53063475), (791, 0.54031025), (809, 0.55084375), (825, 0.55995425), (843, 0.57005225), (861, 0.57994375), (881, 0.59072425), (899, 0.6000415), (919, 0.61021475), (939, 0.620246), (959, 0.62984475), (981, 0.64021725), (1003, 0.6502895), (1025, 0.66007175), (1049, 0.670426), (1073, 0.68044825), (1097, 0.690253), (1123, 0.700487), (1149, 0.710324), (1175, 0.7198345), (1205, 0.73038025), (1233, 0.73999), (1263, 0.74984525), (1295, 0.7599175), (1329, 0.770246), (1363, 0.78015725), (1399, 0.79014875), (1437, 0.80026), (1475, 0.80978925), (1517, 0.8198905), (1563, 0.830206), (1609, 0.83999175), (1659, 0.85001525), (1713, 0.8600645), (1771, 0.870173), (1831, 0.87985925), (1899, 0.8899505), (1973, 0.89991075), (2055, 0.9100075), (2147, 0.92004975), (2251, 0.93005225), (2371, 0.9400265), (2513, 0.95003225), (2685, 0.95996375), (2909, 0.97001825), (3221, 0.9800235), (3757, 0.99000575), (4293, 0.99499475), (4691, 0.99700025), (5005, 0.998001), (5543, 0.99900225), (6081, 0.99950225), (6463, 0.9997005), (6789, 0.99980025), (7341, 0.9999), (7861, 0.99995), (8247, 0.99997), (9141, 0.99999), (9647, 0.999995), (10057, 0.999997), (10995, 0.999999), (11807, 0.9999995)]

    while subtrial_number < count_subtrial_per_trial:  # Loop for each subtrial

        number = number_queue.get()
        int_array.append(number) # Adds int value to an array
        binary_version = bin(number)[2:].zfill(64) # Converts to binary and left fills zeros that got stripped
         
        # Process the binary version of the random number. Goes through each digit from left to right and evaluates whether that digit is a 1 or a 0. 
        # If an analyzed digit is a 1, then we add 1 to the bidirectional_count. If it's a 0 then we subtract one.
        for digit in binary_version:
            if digit == '1' and bidirectional_count < n and bidirectional_count > -n:
                bidirectional_count += 1
                number_steps += 1
            elif digit == '0' and bidirectional_count < n and bidirectional_count > -n:
                bidirectional_count -= 1
                number_steps += 1

            # Stop when the absolute value of bidirectional_count reaches our defined "n" value.
            if abs(bidirectional_count) == n:
                subtrial_number += 1
                
                if(bidirectional_count) > 0:
                    bidirectional_is_pos = True

                # Find x1, y1, x2, y2, x3, and y3 by checking for the first x-value greater than or equal to number_steps
                for i, (x, _) in enumerate(N_CDF_vals):
                    if x >= number_steps:
                        x3, y3 = N_CDF_vals[i]
                        x2, y2 = N_CDF_vals[i - 1]
                        x1, y1 = N_CDF_vals[i - 2]
                        break

                # Compute a, b, c
                a = (x2 * (x2 - x3) * x3 * y1 + x1 * x3 * (x3 - x1) * y2 + x1 * (x1 - x2) * x2 * y3) / ((x1 - x2) * (x1 - x3) * (x2 - x3))
                b = (x3**2 * (y1 - y2) + x1**2 * (y2 - y3) + x2**2 * (y3 - y1)) / ((x1 - x2) * (x1 - x3) * (x2 - x3))
                c = (x3 * (y2 - y1) + x2 * (y1 - y3) + x1 * (y3 - y2)) / ((x1 - x2) * (x1 - x3) * (x2 - x3))

                # Calculate p_calculated
                p_calculated = a + b * number_steps + c * (number_steps**2)

                # Calculate SV
                SV = math.log2(1 / p_calculated)

                # Calculate trial-level data
                if bidirectional_is_pos:
                    trial_weighted_sv += SV
                    trial_cum_sv += SV
                    trial_norm_weighted_sv = trial_weighted_sv / trial_cum_sv
                else:
                    trial_weighted_sv -= SV
                    trial_cum_sv += SV
                    trial_norm_weighted_sv = trial_weighted_sv / trial_cum_sv

                # Prepare to add subtrial data to database queue
                data = {
                    'table': 'subtrial_data',
                    'supertrial': supertrial,
                    'trial': trial,
                    'subtrial_number': subtrial_number,
                    'int_array': json.dumps(int_array),
                    'bidirectional_count': bidirectional_count,
                    'bidirectional_is_pos': int(bidirectional_is_pos),
                    'number_steps': number_steps,
                    'x1': x1,
                    'x2': x2,
                    'x3': x3,
                    'y1': y1,
                    'y2': y2,
                    'y3': y3,
                    'a': a,
                    'b': b,
                    'c': c,
                    'p_calculated': p_calculated,
                    'SV': SV,
                    'created_datetime': datetime.now()
                }
                
                db_queue.put(data)

                print(f"--------------")
                print(f"Sub-trial number: ", subtrial_number)
                print(f"Supertrial: ", supertrial)
                print(f"Trial: ", trial)
                print("Numbers generated (int): ", int_array)
                print("Bidirectional count: ", bidirectional_count)
                print("Bidirectional positive?: ", bidirectional_is_pos)
                print("Number of steps: ", number_steps)
                print(f"x1,y1: ",{x1},",",{y1})
                print(f"x2,y2: ",{x2},",",{y2})
                print(f"x3,y3: ",{x3},",",{y3})
                print(f"a: ",{a})
                print(f"b: ",{b})
                print(f"c: ",{c})
                print(f"p calculated for subtrial: ",{p_calculated})
                print(f"Surprisal Value (SV) for subtrial: ",{SV})
                print(f"Cumulative SV for trial  {trial}: {trial_cum_sv}")
                print(f"Cumulative weighted SV for trial {trial}: {trial_weighted_sv}")
                print(f"Cumulative weighted normalized SV for trial {trial}: {trial_norm_weighted_sv}")

                bidirectional_count = 0
                bidirectional_is_pos = False
                number_steps = 0
                int_array = []


    # For trial data
    data = {
        'table': 'trial_data',
        'supertrial': supertrial,
        'trial': trial,
        'trial_cum_sv': trial_cum_sv,
        'trial_weighted_sv': trial_weighted_sv,
        'trial_norm_weighted_sv': trial_norm_weighted_sv,
        'created_datetime': datetime.now()
    }
    db_queue.put(data)

    stop_event.set() # We processed all subtrials, set the stop event to end extraction


    end_time = time.time()
    elapsed_time = end_time - start_time
    total_analyze_subtrial_time += elapsed_time  # Update the global variable
    
    return ()


# If DB writing is needed this function is called. It runs in its own thread, uses an async queue, and uses connection pooling
def write_to_database(data_queue):
    global total_write_to_database_time

    while True:
        start_time = time.time()

        data = data_queue.get()
        if data is None:  # We use None as a sentinel value to indicate that we're done
            break

        # Get connection from the connection pool
        cnx1 = mysql_pool.connection()
        cursor = cnx1.cursor()


        # Extract the table name and remove it from the data dictionary
        table = data.pop('table')
        
        # Prepare the SQL query
        fields = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        add_data = f"INSERT INTO {table} ({fields}) VALUES ({placeholders})"
        
        cursor = cnx1.cursor()

        # Execute the SQL command
        cursor.execute(add_data, list(data.values()))

        # Commit your changes in the database
        cnx1.commit()

        cursor.close()
        cnx1.close()

        end_time = time.time()
        elapsed_time = end_time - start_time
        total_write_to_database_time += elapsed_time  # Update the global variable

       
# Get numbers and process the trial. Uses unique threads for extraction, analyzing, and DB writing
def process_trial(trial, supertrial, db_queue):
    number_queue = queue.Queue()
    stop_event = threading.Event()
    extraction_thread = threading.Thread(target=extract_numbers, args=(number_queue, stop_event))
    analysis_thread = threading.Thread(target=analyze_subtrial, args=(number_queue, stop_event, db_queue, n, trial, supertrial))

    extraction_thread.start()
    analysis_thread.start()

    extraction_thread.join()
    analysis_thread.join()


# Main function, loops for trials
def main():

    db_queue = queue.Queue()  # Initialize the DB queue outside the loop
    db_writer_thread = threading.Thread(target=write_to_database, args=(db_queue,))
    db_writer_thread.start()  # Start the DB writer thread
    
    start_time = time.time()
    supertrial = get_supertrial()

    for trial in range(1, trial_count + 1):
        process_trial(trial, supertrial, db_queue)
    print('')
    print(f"Total extract_numbers time: {total_extract_numbers_time:.2f} seconds")
    print(f"Total analyze_subtrial time: {total_analyze_subtrial_time:.2f} seconds")
    print(f"Total write_to_database time: {total_write_to_database_time:.2f} seconds")

    db_queue.put(None)  # Signal db_writer to stop
    db_writer_thread.join()  # Wait for the DB writer thread to finish

    end_time = time.time()  # Capture the end time
    elapsed_time = end_time - start_time  # Calculate the elapsed time
    
    ftdi.close
    
    final_output(supertrial, elapsed_time, n, trial_count, count_subtrial_per_trial)

if __name__ == "__main__":
    main()
