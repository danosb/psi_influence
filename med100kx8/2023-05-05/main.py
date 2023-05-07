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
trial_count = 50 # Number of trials we'll perform
count_subtrial_per_trial = 21 # Number of subtrials per trial
serial_number = "QWR4E010"  # Replace with your serial number
window_size = 5 # Numbers of trials to include in a window
significance_threshold = 0.05 # p-value significance
moving_avg_window_count = 21 # Number of windows we'll use to calculate moving average

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
    count_nonoverlapping_window_significant = 0
    count_nonoverlapping_window_total = 0
    nonoverlapping_window_cum_p = 0.0
    nonoverlapping_window_p_value = 0.0
    nonoverlapping_window_SV = 0.0
    window_data = []
    moving_avg_data = []
    min_supertrial_z = float("100")
    min_supertrial_p = float("100")

    start_time = time.time()
    supertrial = get_supertrial(mysql_pool)

    # Start the draw_cube function in a new thread
    #draw_cube_thread = threading.Thread(target=draw_cube)
    #draw_cube_thread.start()

    cube_queue = Queue()
    cube_process = Process(target=draw_cube, args=(cube_queue,))
    cube_process.start()
    cube_queue.put((1, 2, "Started"))

    cumulative_time = 0  # Initialize cumulative_time to 0
    state = {'cumulative_time_above_target': 0}  # Define state dictionary


    for trial in range(1, trial_count + 1):
        trial_p, trial_z = process_trial(ftdi, trial, supertrial, db_queue, n, count_subtrial_per_trial)

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

            # Update nonoverlapping_window_cum_p after every window_size number of trials
            if trial % window_size == 0:
                nonoverlapping_window_cum_p += sum([data["trial_p"] for data in window_data])
                count_nonoverlapping_window_total += 1
                if nonoverlapping_window_cum_p < 0.05:
                    count_nonoverlapping_window_significant += 1
                
                nonoverlapping_window_p_value = binomtest(count_nonoverlapping_window_significant, count_nonoverlapping_window_total, 0.5, alternative='greater').pvalue
                nonoverlapping_window_SV = math.log2(1 / nonoverlapping_window_p_value)

                print(f"Non-overlapping window cumulative p: {nonoverlapping_window_cum_p}")
                print(f"Non-overlapping window count total: {count_nonoverlapping_window_total}")
                print(f"Non-overlapping window count significant: {count_nonoverlapping_window_significant}")
                print(f"Non-overlapping window p: {nonoverlapping_window_p_value}")
                print(f"Non-overlapping window SV: {nonoverlapping_window_SV}")
            else:
                nonoverlapping_window_cum_p = 0.0

            # Update cube window
            cube_queue.put(((1-(window_p))*(-1), 1 - window_p, f"Moving avg. SV: {moving_avg_window_sv}"))


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
                'nonoverlapping_window_cum_p': nonoverlapping_window_cum_p,
                'count_nonoverlapping_window_total': count_nonoverlapping_window_total,
                'count_nonoverlapping_window_significant': count_nonoverlapping_window_significant,
                'nonoverlapping_window_p_value': nonoverlapping_window_p_value,
                'nonoverlapping_window_SV': nonoverlapping_window_SV,
                'created_datetime': datetime.now()
            }
            db_queue.put(data)

    print(f"Min z for supertrial: {min_supertrial_z}")
    print(f"Min p for supertrial: {min_supertrial_p}")
    print(f"Total trials executed: {total_trial_completed_count}")
    print(state['cumulative_time_above_target'])

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
    
    db_queue.put(None)  # Signal db_writer to stop
    db_writer_thread.join()  # Wait for the DB writer thread to finish

    end_time = time.time()  # Capture the end time
    elapsed_time = end_time - start_time  # Calculate the elapsed time

    print('')
    print(f"Total time taken: {elapsed_time:.2f} seconds")
    print(f"Average time per trial: {elapsed_time / total_trial_completed_count * 1000:.2f} milliseconds")

    print(f"Complete.")

    ftdi.close

    time.sleep(5)  # Wait for 10 seconds
    cube_process.terminate()  # Terminate the cube process


if __name__ == "__main__":
    main()
