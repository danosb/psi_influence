# Pulls number from a random number generator, analyzes, stores to database
# Provides real-time feedback about mental influence exerted
# Stores a variety of secondary data, all stored to database

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
from scipy.stats import binomtest
from multiprocessing import Process, Queue, Value
import multiprocessing
from dbutils.pooled_db import PooledDB
from concurrent.futures import ThreadPoolExecutor
from graphic import change_cube_properties,  draw_cube
from get_supertrial import get_supertrial
from write_to_database import write_to_database
from p_and_z_funcs import cdf
from process_trial import process_trial
from get_dst import get_dst
from get_kp import get_kp
from participant import participant_info    


n = 31 # Defined number of steps required to complete a random walk
count_subtrial_per_trial = 21 # Number of subtrials per trial
serial_number = "QWR4E010"  # Replace with your serial number
window_size = 5 # Numbers of trials to include in a window
significance_threshold = 0.05 # p-value significance


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

# Main function, loops for trials
def main():
    # Initialize stuff
    db_queue = queue.Queue()  # Initialize the DB queue outside the loop
    db_writer_thread = threading.Thread(target=write_to_database, args=(mysql_pool, db_queue,))
    db_writer_thread.start()  # Start the DB writer thread
    trial_p, trial_z = 0.0, 0.0
    total_trial_completed_count = 0
    count_window_hit = 0
    count_window_total = 0
    window_total_p = 0.0
    window_total_SV = 0.0
    window_total_reached_target = 0
    window_data = []
    influence_type = ''
    trial = 1

    supertrial = get_supertrial(mysql_pool)

    dst_index = get_dst() # Dst-index
    kp_index, BSR, ap_big, ap_small, SN, F10_7obs, F10_7adj = get_kp() # Other solar data

    # Add solar data to DB write queue
    data = {
        'table': 'solar_data',
        'supertrial': supertrial,
        'dst_index': dst_index,
        'kp_index': kp_index,
        'BSR': BSR,
        'ap_small': ap_small,
        'ap_big': ap_big,
        'SN': SN,
        'F10_7obs': F10_7obs,
        'F10_7adj': F10_7adj,
        'created_datetime': datetime.now()
    }
    db_queue.put(data)   

    # Prompt for info
    participant_name, age, gender, feeling, energy_level, focus_level, meditated, eaten_recently, technique_description, influence_type, duration_seconds, local_temp_fahrenheit, local_humidity_percent = participant_info()

    data = {
        'table': 'participant',
        'supertrial': supertrial,
        'participant_name': participant_name,
        'age': age,
        'gender': gender,
        'feeling': feeling,
        'energy_level': energy_level,
        'focus_level': focus_level,
        'meditated': meditated,
        'eaten_recently': eaten_recently,
        'technique_description': technique_description,
        'created_datetime': datetime.now()
    }
    db_queue.put(data)


    data = {
        'table': 'local_data',
        'supertrial': supertrial,
        'local_temp_fahrenheit': local_temp_fahrenheit,
        'local_humidity_percent': local_humidity_percent,
        'created_datetime': datetime.now()
    }
    db_queue.put(data)


    start_time = time.time()
    time_remaining = duration_seconds
    elapsed_time = 0 

    stop_flag = Value('b', False)  # Shared flag for stopping the cube process

    # Start the cube process
    cube_queue = Queue()
    cube_process = Process(target=draw_cube, args=(cube_queue, stop_flag))
    cube_process.start()
    cube_queue.put((1, 2, "Started", 0, False, False))

    cumulative_time = 0  # Initialize cumulative_time to 0
    state = {'cumulative_time_above_target': 0}  # Define state dictionary

    while (((time.time() - start_time) < duration_seconds) or duration_seconds == 0):
    
        trial_p, trial_z = process_trial(ftdi, trial, supertrial, db_queue, n, count_subtrial_per_trial, influence_type)

        # Update window_data
        if len(window_data) >= window_size:
            window_data.pop(0)
        window_data.append({"trial_p": trial_p, "trial_z": trial_z})
        total_trial_completed_count = trial
        trial += 1

        # Calculate window_z, window_p, window_sv, and window_result_significant
        if len(window_data) == window_size and (trial - 1) % window_size == 0:

            window_z = sum([data["trial_z"] for data in window_data]) / math.sqrt(window_size)
            window_p = cdf(window_z)
            window_sv = math.log2(1 / window_p)

            if influence_type != 'Alternate between producing more 0s and more 1s (continuous)' and window_p <= significance_threshold:
                window_result_significant = True

            elif influence_type == 'Alternate between producing more 0s and more 1s (continuous)' and ((window_p <= (significance_threshold/2)) or (window_p >= (1-(significance_threshold/2)))):
                window_result_significant = True
            
            else: 
                window_result_significant = False

            count_window_total += 1
            if window_result_significant:
                count_window_hit += 1
                
            # get p-value overall for all windows
            if influence_type != 'Alternate between producing more 0s and more 1s (continuous)':
                window_total_p = binomtest(count_window_hit, count_window_total, 0.5, alternative='greater').pvalue

            if influence_type == 'Alternate between producing more 0s and more 1s (continuous)':
                window_total_p = binomtest(count_window_hit, count_window_total, 0.5, alternative='two-sided').pvalue
            
            window_total_SV = math.log2(1 / window_total_p)

            if influence_type != 'Alternate between producing more 0s and more 1s (continuous)' and window_total_p <= significance_threshold:
                window_total_reached_target += 1

            if influence_type == 'Alternate between producing more 0s and more 1s (continuous)' and ((window_total_p <= significance_threshold) or (window_total_p >= (1-significance_threshold))):
                window_total_reached_target += 1

            print(f"...")
            print(f"Last window p-value: {window_p}")
            print(f"Last window surprisal value: {window_sv}")
            print(f"Window count hits: {count_window_hit} / {count_window_total} = {count_window_hit/count_window_total*100:.2f}%")
            print(f"Overall window p-value: {window_total_p}")
            print(f"Overall window surprisal value: {window_total_SV}")
            print(f"Window count overall p-value reached target: {window_total_reached_target} / {count_window_total} = {window_total_reached_target/count_window_total*100:.2f}%")

            # Add window data to DB write queue
            data = {
                'table': 'window_data',
                'supertrial': supertrial,
                'created_by_trial': trial-1,
                'window_z_value': window_z,
                'window_p_value': window_p,
                'window_SV': window_sv,
                'window_result_significant': window_result_significant,
                'count_window_total': count_window_total,
                'count_window_hit': count_window_hit,
                'window_total_p': window_total_p,
                'window_total_SV': window_total_SV,
                'window_total_reached_target': window_total_reached_target,
                'created_datetime': datetime.now()
            }
            db_queue.put(data)

            end_time = time.time()  # Capture the end time
            elapsed_time = end_time - start_time  # Calculate the elapsed time

            # Update cube window for one-tailed-1s
            if influence_type == 'Produce more 1s (time-bound)': 
                cube_queue.put(((1-window_total_p)*(-1), 1-window_total_p, f"Overall surprisal value (higher is better): {window_total_SV:.3f}", duration_seconds - elapsed_time, False))
            
            # Update cube window for one-tailed-0s
            if influence_type == 'Produce more 0s (time-bound)':
                cube_queue.put(((1-window_total_p), 1-window_total_p, f"Overall surprisal value (higher is better): {window_total_SV:.3f}", duration_seconds - elapsed_time, False))

            # Update cube window for two-tailed
            if influence_type == 'Alternate between producing more 0s and more 1s (continuous)': 
                cube_queue.put(((2*(.5-window_total_p)), window_total_p, f"Overall surprisal value (higher is better): {window_total_SV:.3f}", duration_seconds - elapsed_time, True))
            
        if stop_flag.value:  # Check the value of the stop_flag
            break  # Exit the while loop
    
    # Send stop signal to graphic window
    stop_flag.value = True  # Set the stop_flag to True to stop the cube process
    cube_process.join()  # Wait for the cube process to finish

    # Add supertrial data to DB write queue
    data = {
        'table': 'supertrial_data',
        'supertrial': supertrial,
        'count_trials_completed': total_trial_completed_count,
        'influence_type': influence_type,
        'number_steps': n,
        'window_size': window_size,
        'duration_seconds': duration_seconds,
        'count_subtrial_per_trial': count_subtrial_per_trial,
        'significance_threshold': significance_threshold,
        'created_datetime': datetime.now()
    }
    db_queue.put(data)    
    
    db_queue.put(None)  # Signal db_writer to stop
    db_writer_thread.join()  # Wait for the DB writer thread to finish
    print(f"...")
    print(f"Total time taken: {elapsed_time:.2f} seconds")
    print(f"Total trials executed: {total_trial_completed_count}")
    
    if total_trial_completed_count != 0:
        print(f"Average time per trial: {elapsed_time / total_trial_completed_count * 1000:.2f} milliseconds")
    else:
        print("No trials completed.")
    print(f"...")
    #cumulative_time_above_target = state.get('cumulative_time_above_target', 0)
    
    print(f'')
    print(f'Complete.')
    
    ftdi.close

    #time.sleep(5)  # Wait for 5 seconds
    cube_process.terminate()  # Terminate the cube process


if __name__ == "__main__":
    main()
