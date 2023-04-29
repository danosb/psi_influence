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
import time

FTDI_DEVICE_LATENCY_MS = 2
FTDI_DEVICE_PACKET_USB_SIZE = 8
FTDI_DEVICE_TX_TIMEOUT = 5000
n = 31 # defined bound
trial_count = 5
count_subtrial_per_trial = 21


def device_startup(serial_number):
    if not serial_number:
        print("%%%% device not found!")
        return None

    # print("deviceId:", serial_number, "\n")
    ftdi = Ftdi()
    ftdi.open_from_url(f"ftdi://ftdi:232:{serial_number}/1")
    ftdi.set_latency_timer(FTDI_DEVICE_LATENCY_MS)
    ftdi.write_data_get_chunksize = lambda x: FTDI_DEVICE_PACKET_USB_SIZE
    ftdi.read_data_get_chunksize = lambda x: FTDI_DEVICE_PACKET_USB_SIZE

    return ftdi


def device_shutdown(ftdi):
    ftdi.close()


def main():
    start_time = time.time() 
    supertrial = 0
    serial_number = "QWR4E010"  # Replace with your serial number
    ftdi = device_startup(serial_number)

    # Start a new thread for subtrial_looper
    subtrial_thread = threading.Thread(target=subtrial_looper, args=(ftdi,count_subtrial_per_trial,trial_count,n,))
    subtrial_thread.start()

    # Start a new thread for eeg_data
    eeg_thread = threading.Thread(target=eeg_data)
    eeg_thread.start()

    # Wait for both threads to complete
    subtrial_thread.join()
    eeg_thread.join()

    end_time = time.time()  # Capture the end time
    elapsed_time = end_time - start_time  # Calculate the elapsed time

    print(f"---------")
    print(f"")
    print(f"Trials complete. Total time taken: {elapsed_time} seconds")
    print(f"")
    print(f"Defined bound: ", {n})
    print(f"Defined trial count: ", {trial_count})
    print(f"Defined # subtrials per trial: ", {count_subtrial_per_trial})
    print(f"")

    # Get MySQL creds from environment variables
    username = os.getenv('MYSQL_USER')
    password = os.getenv('MYSQL_PASSWORD')
    host = os.getenv('MYSQL_HOST')
    database = os.getenv('MYSQL_DB')

    # Connect to the MySQL database
    connection = mysql.connector.connect(user=username, password=password,
                                         host=host, database=database)
    cursor2 = connection.cursor()

    # Get the max value in trial_data.supertrial
    cursor2.execute("SELECT MAX(supertrial) FROM trial_data")
    supertrial = cursor2.fetchone()[0]

    # Retrieve all trial and cumulative_sv values associated with max supertrial
    query = "SELECT trial, trial_norm_weighted_sv FROM trial_data WHERE supertrial = %s"
    cursor2.execute(query, (supertrial,))

    # Get column names
    columns = [column[0] for column in cursor2.description]

    # Fetch all rows
    results = cursor2.fetchall()

    # Print column names
    print('\t'.join(columns))

    # Print rows
    for row in results:
        print('\t'.join(str(elem) for elem in row))

    # Close the cursor and the connection
    cursor2.close()
    connection.close()

    device_shutdown(ftdi)


if __name__ == "__main__":
    main()