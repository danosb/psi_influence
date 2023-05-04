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
from dbutils.pooled_db import PooledDB
from concurrent.futures import ThreadPoolExecutor


n = 31 # Defined number of steps required to complete a random walk
trial_count = 1000 # Number of trials we'll perform
count_subtrial_per_trial = 21 # Number of subtrials per trial
serial_number = "QWR4E010"  # Replace with your serial number
window_size = 5 # Numbers of trials to include in a window
significance_threshold = 0.05 # p-value significance
moving_avg_window_count = 21 # Number of windows we'll use to calculate moving average

# Initialize variables that track main function times
total_write_to_database_time = 0
total_analyze_subtrial_time = 0
total_extract_numbers_time = 0

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

    number_buffer = bytearray()  # buffer for constructing random numbers, ensures we drop no contiguous bytes
    number_buffer.clear()  # Clear the number_buffer when the function is called

    start_time = time.time()

    while not stop_event.is_set():  # while stop event is not triggered
        # Request a new random number
        init_comm = b'\x96'
        bytes_txd = ftdi.write_data(init_comm)

        # Read bytes from the buffer first if possible
        bytes_to_read = 32
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

    return ()


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

    stop_event.set() # We processed all subtrials, set the stop event to end extraction

    end_time = time.time()
    elapsed_time = end_time - start_time
    total_analyze_subtrial_time += elapsed_time  # Update the global variable
    
    return (trial_cum_sv, trial_weighted_sv, trial_norm_weighted_sv)


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


# Returns the trial_p value from the normalized weighted surprival value (nwsv) from 21 sub-trials with n = 31; The input range is -1 to +1 and the default output range is approximately: 0.0001 < p < 0.9999.
# Note, this is a two-tailed test, meaning if the nwsv is negative, take the p returned by the function above. If the nwsv is positive, the actual p value is 1-p returned by the function. If you were using the trial by itself, each of the p values would be doubled for the two-tailed statistic. For combining into a windowp, take the p values returned by the function without subtracting from 1 or doubling them.
def trialp_from_nwsv(nwsv):
    if nwsv < -0.916:
        x = -0.916
    elif nwsv > 0.916:
        x = 0.916
    else:
        x = nwsv

    trial_p = (
        0.4999447235559293
        + 1.2528465672038636 * x
        + 0.0023748498254079604 * x ** 2
        - 1.8238870199248776 * x ** 3
        - 0.01775000187777237 * x ** 4
        + 1.9836743245635038 * x ** 5
        + 0.05445147471824477 * x ** 6
        - 1.3540283379808826 * x ** 7
        - 0.08206132973167951 * x ** 8
        + 0.5389043846181366 * x ** 9
        + 0.060502652558113074 * x ** 10
        - 0.09752931591747523 * x ** 11
        - 0.01746939645456147 * x ** 12
    )

    return trial_p


# Accepts trial_p (the cumulative uniform distribution value) and returns the corresponding z-score
def invnorm(trial_p):
    trial_z = 0

    p0 = -0.322232431088
    p1 = -1.0
    p2 = -0.342242088547
    p3 = -0.0204231210245
    p4 = -0.453642210148e-4
    q0 = 0.099348462606
    q1 = 0.588581570495
    q2 = 0.531103462366
    q3 = 0.10353775285
    q4 = 0.38560700634e-2

    if trial_p < 0.5:
        pp = trial_p
    else:
        pp = 1.0 - trial_p

    y = math.sqrt(math.log(1 / (pp ** 2)))
 
    trial_z = y + ((((y * p4 + p3) * y + p2) * y + p1) * y + p0) / ((((y * q4 + q3) * y + q2) * y + q1) * y + q0)

    if trial_p < 0.5:
        trial_z = -trial_z
    
    return trial_z


# Accepts window_z, returns cumulative normal distribution p value for window (window_p). Accuracy better than 1% to z=±7.5; .05% to z=±4.
def cdf(window_z):
    c1 = 2.506628275
    c2 = 0.31938153
    c3 = -0.356563782
    c4 = 1.781477937
    c5 = -1.821255978
    c6 = 1.330274429
    c7 = 0.2316419

    if window_z >= 0:
        w = 1
    else:
        w = -1

    t = 1.0 + c7 * w * window_z
    y = 1.0 / t
    window_p = 0.5 + w * (0.5 - (c2 + (c6 + c5 * t + c4 * t ** 2 + c3 * t ** 3) / t ** 4) / (c1 * math.exp(0.5 * window_z ** 2) * t))
    
    # If the window_p value is less than 0.5, double the p value and that is the windowp value for a result of -1
    # If the window_p value is greater than (or =) 0.5, the windowp value is 2(1-p) for a result of +1.
    if window_p < 0.5:
        window_p = window_p * 2
    else:
        window_p = 2 * (1 - window_p)

    return window_p


# Get numbers and process the trial. Uses unique threads for extraction, analyzing, and DB writing
def process_trial(trial, supertrial, db_queue):
    number_queue = queue.Queue()
    stop_event = threading.Event()
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        extraction_thread = executor.submit(extract_numbers, number_queue, stop_event)
        analysis_thread = executor.submit(analyze_subtrial, number_queue, stop_event, db_queue, n, trial, supertrial)

        extraction_thread.result()
        trial_cum_sv, trial_weighted_sv, trial_norm_weighted_sv = analysis_thread.result()
     
    trial_p = trialp_from_nwsv(trial_norm_weighted_sv)
    trial_z = invnorm(trial_p)

    # Add trial data to the DB write queue
    data = {
        'table': 'trial_data',
        'supertrial': supertrial,
        'trial': trial,
        'trial_cum_sv': trial_cum_sv,
        'p_value': trial_p,
        'z_value': trial_z,
        'trial_weighted_sv': trial_weighted_sv,
        'trial_norm_weighted_sv': trial_norm_weighted_sv,
        'created_datetime': datetime.now()
    }
    db_queue.put(data)

    return trial_p, trial_z


# Main function, loops for trials
def main():
    db_queue = queue.Queue()  # Initialize the DB queue outside the loop
    db_writer_thread = threading.Thread(target=write_to_database, args=(db_queue,))
    db_writer_thread.start()  # Start the DB writer thread
    trial_p = 0
    trial_z = 0
    total_trial_completed_count = 0

    window_data = []
    moving_avg_data = []
    min_supertrial_z = float("100")
    min_supertrial_p = float("100")

    start_time = time.time()
    supertrial = get_supertrial()

    for trial in range(1, trial_count + 1):
        trial_p, trial_z = process_trial(trial, supertrial, db_queue)
        
        # Update window_data
        if len(window_data) >= window_size:
            window_data.pop(0)
        window_data.append({"trial_p": trial_p, "trial_z": trial_z})
        
        # Calculate window_z, window_p, window_sv, and window_result_significant
        if len(window_data) == window_size:
            total_trial_completed_count = trial
            window_z = sum([data["trial_z"] for data in window_data]) / math.sqrt(window_size)
            window_p = cdf(window_z)
            window_sv = math.log2(1 / window_p)
            window_result_significant = window_p < significance_threshold

            # Update moving_avg_data
            if len(moving_avg_data) >= moving_avg_window_count:
                moving_avg_data.pop(0)
            moving_avg_data.append({"window_z": window_z, "window_p": window_p, "window_sv": window_sv})

            # Calculate moving averages and moving_avg_value_significant
            moving_avg_window_z = sum([data["window_z"] for data in moving_avg_data]) / len(moving_avg_data)
            moving_avg_window_p = sum([data["window_p"] for data in moving_avg_data]) / len(moving_avg_data)
            moving_avg_window_sv = sum([data["window_sv"] for data in moving_avg_data]) / len(moving_avg_data)
            moving_avg_value_significant = moving_avg_window_p < significance_threshold

            # Update min_supertrial_z and min_supertrial_p
            if window_z < min_supertrial_z:
                min_supertrial_z = window_z
            if window_p < min_supertrial_p:
                min_supertrial_p = window_p

            print(f"Trial p: {trial_p}")
            print(f"Trial z: {trial_z}")
            print(f"Window z: {window_z}")
            print(f"Window p: {window_p}")
            print(f"Window SV: {window_sv}")
            print(f"Window result significant: {window_result_significant}")
            print(f"Moving avg window z: {moving_avg_window_z}")
            print(f"Moving avg window p: {moving_avg_window_p}")
            print(f"Moving avg window SV: {moving_avg_window_sv}")
            print(f"Moving avg value significant: {moving_avg_value_significant}")

            # Add window data to DB write queue
            data = {
                'table': 'window_data',
                'supertrial': supertrial,
                'created_by_trial': trial,
                'window_z_value': window_z,
                'window_p_value': window_p,
                'window_SV': window_sv,
                'window_result_significant': window_result_significant,
                'moving_avg_z': moving_avg_window_z,
                'moving_avg_p': moving_avg_window_p,
                'moving_avg_sv': moving_avg_window_sv,
                'moving_avg_result_significant': moving_avg_value_significant,
                'created_datetime': datetime.now()
            }
            db_queue.put(data)

    print(f"Min z for supertrial: {min_supertrial_z}")
    print(f"Min p for supertrial: {min_supertrial_p}")
    print(f"Total trials executed: {total_trial_completed_count}")

    # Add supertrial data to DB write queue
    data = {
        'table': 'supertrial_data',
        'supertrial': supertrial,
        'count_trials_completed': total_trial_completed_count,
        'min_z_value': min_supertrial_z,
        'min_p_value': min_supertrial_p,
        'number_steps': n,
        'window_size': window_size,
        'significance_threshold': significance_threshold,
        'moving_avg_window_count': moving_avg_window_count,
        'created_datetime': datetime.now()
    }
    db_queue.put(data)

    print('')
    print(f"Total extract_numbers time: {total_extract_numbers_time:.2f} seconds")
    print(f"Total analyze_subtrial time: {total_analyze_subtrial_time:.2f} seconds")
    print(f"Total write_to_database time: {total_write_to_database_time:.2f} seconds")
    
    db_queue.put(None)  # Signal db_writer to stop
    db_writer_thread.join()  # Wait for the DB writer thread to finish

    end_time = time.time()  # Capture the end time
    elapsed_time = end_time - start_time  # Calculate the elapsed time
    print(f"Total time taken: {elapsed_time:.2f} seconds")
    print(f"Average time per trial: {elapsed_time / total_trial_completed_count * 1000:.2f} milliseconds")

    print(f"Complete.")

    ftdi.close


if __name__ == "__main__":
    main()
