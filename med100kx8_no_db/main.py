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
from graphic import change_cube_properties,  draw_cube
from p_and_z_funcs import cdf
from process_trial import process_trial
from participant import participant_info    

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
    count_total_window_bound_tracker = 0
    window_total_p = 0.0
    window_total_SV = 0.0
    bar_fill_percent = 0.0
    cube_spin_speed = 0
    window_data = []
    influence_type = ''
    trial = 1
    window_hits_data = []
    window_z_data = []

    # Prompt for info
    influence_type, duration_seconds = participant_info()

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

            if influence_type == 'Produce more 1s': # for one-tailed, target = more 1s
                window_p = 1 - cdf(window_z)
                if window_z >= 0: 
                    window_hit = 1
  
            if influence_type == 'Produce more 0s': # for one-tailed, target = more 0s
                window_p = cdf(window_z)
                if window_z < 0:
                    window_hit = 1
  
            if window_z > 0:
                count_total_window_bound_tracker += 1
                if count_total_window_bound_tracker >= 5:
                    count_total_window_bound_tracker = 5
            elif window_z < 0:
                count_total_window_bound_tracker -= 1
                if count_total_window_bound_tracker <= -5:
                    count_total_window_bound_tracker = -5

            if influence_type == 'Alternate between producing more 0s and more 1s' and window_z >= 0: # for two-tailed where window_z >= 0
                window_p = 2 * (1 - cdf(window_z))

            if influence_type == 'Alternate between producing more 0s and more 1s' and window_z < 0: # for two-tailed where window_z < 0
                window_p = 2 * cdf(window_z)
            
            if window_p <= 0.05:
                window_result_significant = True
            else:
                window_result_significant = False

            window_sv = math.log2(1 / window_p)

            # Update window_hits_data. Tracks whether a window was a hit or not and adds it to a list of [window_size] length. This allows us to track how many windows in a window group resulted in hits. Only relevant for one-tailed.
            if len(window_hits_data) >= window_group_size:
                window_hits_data.pop(0)
            window_hits_data.append(window_hit)
            
            # Update window_z_data. Adds window_z values to a list of [window_size] length. This allows us to sum all window_z values in a window group.
            if len(window_z_data) >= window_group_size:
                window_z_data.pop(0)
            window_z_data.append(window_z)

            count_window_group_hit = sum(window_hits_data) # How many of the windows in our window group resulted in hits.
            
            window_group_z = sum(window_z_data) / math.sqrt(window_group_size)  # calculate group window_z

            if influence_type == 'Produce more 0s' or influence_type == 'Produce more 1s': # If one-tailed in either direction
                window_group_p = binomtest(count_window_group_hit, len(window_hits_data), 0.5, alternative='greater').pvalue # Perform one-tailed binomial test
            else: # for two-tailed
                if window_group_z >= 0:
                    window_group_p = 2 * (1 - cdf(window_group_z))
                else:
                    window_group_p = 2 * cdf(window_group_z)
                
            window_group_SV = math.log2(1 / window_group_p)

            end_time = time.time()  # Capture the end time
            elapsed_time = end_time - start_time  # Calculate the elapsed time

            # Set graphic variables for two-tailed
            if influence_type == 'Alternate between producing more 0s and more 1s': 
                if window_group_z < 0:
                    bar_fill_percent = window_group_p/2 
                    cube_spin_speed = (.5 - bar_fill_percent) * 2 
                else:
                    bar_fill_percent = 1 - (window_group_p/2)
                    cube_spin_speed = (bar_fill_percent - .5) * (-2) 
            else:
                bar_fill_percent = 1-window_group_p

            if influence_type == 'Produce more 0s':        
                cube_spin_speed = bar_fill_percent          
            if influence_type == 'Produce more 1s':         
                cube_spin_speed = bar_fill_percent * (-1)   

           # Update graphic window.
            cube_queue.put((cube_spin_speed, bar_fill_percent, f"Two-tailed" if influence_type == 'Alternate between producing more 0s and more 1s' else influence_type, duration_seconds - elapsed_time, True if influence_type == 'Alternate between producing more 0s and more 1s' else False))

            # Print window and window_group outcomes to console.
            print(f"...")
            print(f"Last window z-value: {window_z}")
            print(f"Last window p-value: {window_p}")
            print(f"Last window surprisal value: {window_sv}")
            print(f"Last window was hit?: {'Yes' if window_hit == 1 else 'No'}")
            print(f"Running overall window bound tracker: {count_total_window_bound_tracker}")
            print(f"Window group z-value: {window_group_z}")
            print(f"Window group p-value: {window_group_p}")
            print(f"Window group surprisal value: {window_group_SV}")

        if stop_flag.value:  # Check the value of the stop_flag
            break  # Exit the while loop
    
    # Send stop signal to graphic window
    stop_flag.value = True  # Set the stop_flag to True to stop the cube process
    cube_process.join()  # Wait for the cube process to finish

    print(f"...")
    print(f"Total time taken: {elapsed_time:.2f} seconds")
    print(f"Total trials executed: {total_trial_completed_count}")
    
    if total_trial_completed_count != 0:
        print(f"Average time per trial: {elapsed_time / total_trial_completed_count * 1000:.2f} milliseconds")
    else:
        print("No trials completed.")
    print(f"...")
    
    print(f'')
    print(f'Complete.')
    
    ftdi.close

    #time.sleep(5)  # Wait for 5 seconds
    cube_process.terminate()  # Terminate the cube process


if __name__ == "__main__":
    main()
