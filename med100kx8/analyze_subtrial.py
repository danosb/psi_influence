# Uses Scott Wilber's Random Walk Bias Amplification algorithm:
# ..https://drive.google.com/file/d/1ASvbdI-uQs_4HNL3fh85g72mIRndkjdn/view

import queue
import json
from datetime import datetime
import math


# Function to analyze subtrials and add to DB write-queue
def analyze_subtrial(number_queue, stop_event, db_queue, n, trial, supertrial, count_subtrial_per_trial):

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

                if number_steps < 209:
                    p_calculated = 0.0625
                elif number_steps > 1613:
                    p_calculated = 0.840896
                else:
                    x = math.log(number_steps)
                    p_calculated = - 14753.24169815 \
                        + 27287.435642795*x \
                        - 22758.051790793*x**2 \
                        + 11296.73926749*x**3 \
                        - 3708.2656031604*x**4 \
                        + 845.26673369466*x**5 \
                        - 136.52944311971*x**6 \
                        + 15.628082615014*x**7 \
                        - 1.2424970617642*x**8 \
                        + 0.065349290419121*x**9 \
                        - 0.0020465302532178*x**10 \
                        + 0.000028912696259115*x**11
            
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
                    'p_calculated': p_calculated,
                    'SV': SV,
                    'created_datetime': datetime.now()
                }
              
                db_queue.put(data)
               
                #print(f"--------------")
                #print(f"Sub-trial number: ", subtrial_number)
                #print(f"Supertrial: ", supertrial)
                #print(f"Trial: ", trial)
                #print("Numbers generated (int): ", int_array)
                #print("Bidirectional count: ", bidirectional_count)
                #print("Bidirectional positive?: ", bidirectional_is_pos)
                #print("Number of steps: ", number_steps)
                #print(f"p calculated for subtrial: ",{p_calculated})
                #print(f"Surprisal Value (SV) for subtrial: ",{SV})
                #print(f"Cumulative SV for trial  {trial}: {trial_cum_sv}")
                #print(f"Cumulative weighted SV for trial {trial}: {trial_weighted_sv}")
                #print(f"Cumulative weighted normalized SV for trial {trial}: {trial_norm_weighted_sv}")

                bidirectional_count = 0
                bidirectional_is_pos = False
                number_steps = 0
                int_array = []
     

    stop_event.set() # We processed all subtrials, set the stop event to end extract

    return (trial_cum_sv, trial_weighted_sv, trial_norm_weighted_sv)
