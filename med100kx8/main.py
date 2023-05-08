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
from scipy.stats import binomtest
from multiprocessing import Process, Queue
import multiprocessing
from dbutils.pooled_db import PooledDB
from concurrent.futures import ThreadPoolExecutor
from graphic import change_cube_properties
from graphic import draw_cube
from get_supertrial import get_supertrial
from write_to_database import write_to_database
from p_and_z_funcs import cdf
from process_trial import process_trial


n = 31 # Defined number of steps required to complete a random walk
count_subtrial_per_trial = 21 # Number of subtrials per trial
serial_number = "QWR4E010"  # Replace with your serial number
window_size = 5 # Numbers of trials to include in a window
significance_threshold = 0.05 # p-value significance
duration_seconds = 600 # Number of seconds the supertrial will last
participant_name = "Dan"


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
    db_queue = queue.Queue()  # Initialize the DB queue outside the loop
    db_writer_thread = threading.Thread(target=write_to_database, args=(mysql_pool, db_queue,))
    db_writer_thread.start()  # Start the DB writer thread
    trial_p = 0.0
    trial_z = 0.0
    total_trial_completed_count = 0
    count_window_hit = 0
    count_window_total = 0
    window_total_p = 0.0
    window_total_SV = 0.0
    window_total_reached_target = 0
    window_data = []
    trial = 1

    start_time = time.time()
    time_remaining = duration_seconds
    supertrial = get_supertrial(mysql_pool)
    elapsed_time = 0 

    cube_queue = Queue()
    cube_process = Process(target=draw_cube, args=(cube_queue,))
    cube_process.start()
    cube_queue.put((1, 2, "Started", 0, False))

    cumulative_time = 0  # Initialize cumulative_time to 0
    state = {'cumulative_time_above_target': 0}  # Define state dictionary

    while (time.time() - start_time) < duration_seconds:
    
        trial_p, trial_z = process_trial(ftdi, trial, supertrial, db_queue, n, count_subtrial_per_trial)

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
            window_result_significant = window_p < 0.5

            count_window_total += 1
            if window_result_significant:
                count_window_hit += 1
                
            window_total_p = binomtest(count_window_hit, count_window_total, 0.5, alternative='greater').pvalue
            window_total_SV = math.log2(1 / window_total_p)

            if window_total_p <= significance_threshold:
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

            # Update cube window
            cube_queue.put(((1-window_total_p)*(-1), 1-window_total_p, f"Overall surprisal value (higher is better): {window_total_SV:.3f}", duration_seconds - elapsed_time))

    
    # Send stop signal to graphic window
    cube_queue.put(((1-window_total_p)*(-1), 1-window_total_p, f"Overall surprisal value (higher is better): {window_total_SV:.3f}", duration_seconds - elapsed_time), True)

    # Add supertrial data to DB write queue
    data = {
        'table': 'supertrial_data',
        'supertrial': supertrial,
        'count_trials_completed': total_trial_completed_count,
        'number_steps': n,
        'window_size': window_size,
        'duration_seconds': duration_seconds,
        'count_subtrial_per_trial': count_subtrial_per_trial,
        'significance_threshold': significance_threshold,
        'participant_name': participant_name,
        'created_datetime': datetime.now()
    }
    db_queue.put(data)    
    
    db_queue.put(None)  # Signal db_writer to stop
    db_writer_thread.join()  # Wait for the DB writer thread to finish
    print(f"...")
    print(f"Total time taken: {elapsed_time:.2f} seconds")
    print(f"Total trials executed: {total_trial_completed_count}")
    print(f"Average time per trial: {elapsed_time / total_trial_completed_count * 1000:.2f} milliseconds")
    print(f"...")
    #cumulative_time_above_target = state.get('cumulative_time_above_target', 0)
    
    print(f'')
    print(f'Complete.')
    
    ftdi.close

    #time.sleep(5)  # Wait for 5 seconds
    cube_process.terminate()  # Terminate the cube process


if __name__ == "__main__":
    main()
