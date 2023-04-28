# Loops, calling functions to retrieve and calculate data from the MED100Kx8 RNG

import mysql.connector
from pyftdi.ftdi import Ftdi
import os
from datetime import datetime
from random_walk import random_walk_steps, interop
from eeg import eeg_data


def subtrial_looper(ftdi, count_subtrial_per_trial, trial_count, n):
    bidirectional_is_pos = False
    trial = 1
    trial_cum_sv = 0
    trial_weighted_sv = 0
    trial_norm_weighted_sv = 0

    # Get MySQL creds from environment variables
    username = os.getenv('MYSQL_USER')
    password = os.getenv('MYSQL_PASSWORD')
    host = os.getenv('MYSQL_HOST')
    database = os.getenv('MYSQL_DB')

    # Connect to the MySQL database
    connection = mysql.connector.connect(user=username, password=password,
                              host=host, database=database)
    cursor = connection.cursor()

    # Get the current max supertrial
    cursor.execute("SELECT MAX(supertrial) FROM subtrial_data")
    result = cursor.fetchone()
    if result[0] is None:
        supertrial = 1
    else:
        supertrial = result[0] + 1

    for trial in range(trial_count):
        # Initialize the cumulative surprisal value for this trial
        trial_weighted_sv = 0
        
        # Loop through for each sub-trial
        for _ in range(count_subtrial_per_trial):
            numbers_generated, bidirectional_count, number_steps, bidirectional_is_pos = random_walk_steps(ftdi, n)
            x1, x2, x3, y1, y2, y3, a, b, c, p_calculated, SV = interop(ftdi, number_steps)
            
            # Calculate cumulative surprisal value across the trial
            if bidirectional_is_pos:
                trial_weighted_sv += SV
                trial_cum_sv += SV
                trial_norm_weighted_sv = trial_weighted_sv / trial_cum_sv
            else:
                trial_weighted_sv -= SV
                trial_cum_sv += SV
                trial_norm_weighted_sv = trial_weighted_sv / trial_cum_sv

            print(f"--------------")
            print(f"Sub-trial number: ", {_+1})
            print(f"Supertrial: ", supertrial)
            print(f"Trial: ", trial+1)
            print("Numbers generated (int): ", numbers_generated)
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
            print(f"Sum SV for trial  {trial+1}: {trial_cum_sv}")
            print(f"Cumulative weighted SV for trial {trial+1}: {trial_weighted_sv}")
            print(f"Cumulative weighted SV for trial {trial+1}: {trial_norm_weighted_sv}")


            # Insert the data into the subtrial_data table
            insert_query = (
                "INSERT INTO subtrial_data (supertrial, trial, subtrial_number, numbers_generated, bidirectional_count, number_steps, bidirectional_is_pos, x1, x2, x3, y1, y2, y3, a, b, c, p_calculated, SV, created_datetime) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            )
            cursor.execute(insert_query, (supertrial, trial+1, _+1, str(numbers_generated), bidirectional_count, number_steps, bidirectional_is_pos, x1, x2, x3, y1, y2, y3, a, b, c, p_calculated, SV, datetime.now()))
    
        # Insert the data into the trial_data table
        insert_query = (
            "INSERT INTO trial_data (supertrial, trial, trial_cum_sv, trial_weighted_sv, trial_norm_weighted_sv, created_datetime) "
            "VALUES (%s, %s, %s, %s, %s, %s)"
        )
        cursor.execute(insert_query, (supertrial+1, trial+1, trial_cum_sv, trial_weighted_sv, trial_norm_weighted_sv, datetime.now()))

    # Commit the changes  
    connection.commit()

    # Close the connection
    cursor.close()
    connection.close()