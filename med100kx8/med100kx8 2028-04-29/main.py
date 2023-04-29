# Reads random numbers from the MED100Kx8 hardware device and other data sources, analyses data
# Performs Scott Wilber's RWBA
# We'll use multi-threading to pull in data from multiple sources (e.g. , MED100Kx8, Emotiv Epoch EEG) in parallel
# Results are stored and retrieved from a MySQL database 

import sys
from pyftdi.ftdi import Ftdi
import math
import mysql.connector
from datetime import datetime
import os
import threading
from subtrial_looper import subtrial_looper
from eeg import eeg_data
from final_output import final_output
import time


n = 31 # Defined number of steps required to complete a random walk
trial_count = 5 # Number of trials we'll perform
count_subtrial_per_trial = 21 # Number of subtrials per trial
serial_number = "QWR4E010"  # Replace with your serial number


def main():
    start_time = time.time() 


    ftdi = initialize_device()
 

    # Start a new thread for subtrial_looper
    subtrial_thread = threading.Thread(target=subtrial_looper, args=(ftdi,count_subtrial_per_trial,trial_count,n,supertrial,))
    subtrial_thread.start()

    # Start a new thread for eeg_data
    eeg_thread = threading.Thread(target=eeg_data)
    eeg_thread.start()

    # Wait for both threads to complete
    subtrial_thread.join()
    eeg_thread.join()

    end_time = time.time()  # Capture the end time
    elapsed_time = end_time - start_time  # Calculate the elapsed time
   
    # Start a new thread for final_output
    final_output = threading.Thread(target=final_output, args=(supertrial,))
    final_output.start()

    ftdi.close()


if __name__ == "__main__":
    main()