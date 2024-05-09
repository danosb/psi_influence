# Pulls number from a random number generator, analyzes
# Provides real-time feedback about mental influence exerted

import queue
import random
import time
import threading
import sys
from pyftdi.ftdi import Ftdi
import json
from datetime import datetime
import math
import os
import contextlib
import io
from scipy.stats import binomtest
from multiprocessing import Process, Queue, Value
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from p_and_z_funcs import cdf
from process_trial import process_trial

n = 31 # Defined number of steps required to complete a random walk
count_subtrial_per_trial = 21 # Number of subtrials per trial
window_size = 5 # Numbers of trials to include in a window
window_group_size = 10 # Number of windows in a group
significance_threshold = 0.05 # p-value significance

# Device communication parameters
FTDI_DEVICE_LATENCY_MS = 2
FTDI_DEVICE_PACKET_USB_SIZE = 8
FTDI_DEVICE_TX_TIMEOUT = 5000

# Get FTDI URL dynamically
def list_devices():
    # Create a string buffer and redirect stdout to it
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        Ftdi().show_devices()

    # Extract the device URL from the buffer's contents
    output = buffer.getvalue()
    lines = output.split("\n")
    for line in lines:
        if "ftdi://" in line:
            return line.split()[0]  # The URL is the first part of the line

    return None

device_url = list_devices()

ftdi = Ftdi()
ftdi.open_from_url(device_url)
ftdi.set_latency_timer(FTDI_DEVICE_LATENCY_MS)
ftdi.write_data_get_chunksize = lambda x: FTDI_DEVICE_PACKET_USB_SIZE
ftdi.read_data_get_chunksize = lambda x: FTDI_DEVICE_PACKET_USB_SIZE


# Main function, loops for trials
def main():
    # Initialize stuff
    trial_p, trial_z = 0.0, 0.0
    total_trial_completed_count = 0
    count_window_group_hit = 0
    time_beyond_target = 0.0
    window_total_p = 0.0
    window_data = []
    trial = 1
    window_hits_data = []

    influence_type = 'Produce more 1s'
    duration_seconds = 60
    
    last_time = 0.0
    start_time = time.time()
    time_remaining = duration_seconds
    elapsed_time = 0 
    cumulative_time = 0  # Initialize cumulative_time to 0
    
    os.system('cls' if os.name == 'nt' else 'clear')
    
    while (((time.time() - start_time) < duration_seconds) or duration_seconds == 0):

        trial_p, trial_z, trial_count_bidirectional_is_pos = process_trial(ftdi, trial, n, count_subtrial_per_trial, influence_type)

        # Update window_data
        if len(window_data) >= window_size:
            window_data.pop(0)
        window_data.append({"trial_p": trial_p, "trial_z": trial_z, "trial_count_bidirectional_is_pos": trial_count_bidirectional_is_pos})
        total_trial_completed_count = trial
        trial += 1

        # Calculate window_z, window_p, window_sv, and window_result_significant
        if len(window_data) == window_size and (trial - 1) % window_size == 0: # loops for each window

            window_z = sum([data["trial_z"] for data in window_data]) / math.sqrt(window_size) # sum all trial_z values for a window, divide by square root of window size
    
            window_hit = 0

            window_p = 1 - cdf(window_z)
            if window_z >= 0: 
                window_hit = 1
        
            # Update window_hits_data. Tracks whether a window was a hit or not and adds it to a list of [window_size] length. This allows us to track how many windows in a window group resulted in hits. Only relevant for one-tailed.
            if len(window_hits_data) >= window_group_size:
                window_hits_data.pop(0)
            window_hits_data.append(window_hit)

            count_window_group_hit = sum(window_hits_data) # How many of the windows in our window group resulted in hits.
            
            window_group_p = binomtest(count_window_group_hit, len(window_hits_data), 0.5, alternative='greater').pvalue # Perform one-tailed binomial test

            if window_group_p <= 0.05:
                window_group_result_significant = True
            else:
                window_group_result_significant = False

            end_time = time.time()  # Capture the end time

            elapsed_time = end_time - start_time  # Calculate the elapsed time

            if window_group_result_significant == True:
                    time_beyond_target = time_beyond_target + (end_time - last_time)

            last_time = end_time

            window_group_p_converted = (1-window_group_p)*100

            # Print window_group p-value to console.
            print(f"Window group p-value (target >= 95): {window_group_p_converted:.2f}")
            print(f"Time beyond target (s): {time_beyond_target:.2f}")

    print(f"...")
    print(f"Total time taken: {elapsed_time:.2f} seconds")
    print(f"Total trials executed: {total_trial_completed_count}")
    print(f"Total time beyond target (s): {time_beyond_target:.2f}")
    
    if total_trial_completed_count != 0:
        print(f"Average time per trial: {elapsed_time / total_trial_completed_count * 1000:.2f} milliseconds")
    else:
        print("No trials completed.")
    print(f"...")
    
    print(f'')
    print(f'Complete.')
    
    ftdi.close


if __name__ == "__main__":
    main()
