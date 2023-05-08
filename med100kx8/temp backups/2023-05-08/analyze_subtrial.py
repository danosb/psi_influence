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

                #print(f"--------------")
                #print(f"Sub-trial number: ", subtrial_number)
                #print(f"Supertrial: ", supertrial)
                #print(f"Trial: ", trial)
                #print("Numbers generated (int): ", int_array)
                #print("Bidirectional count: ", bidirectional_count)
                #print("Bidirectional positive?: ", bidirectional_is_pos)
                #print("Number of steps: ", number_steps)
                #print(f"x1,y1: ",{x1},",",{y1})
                #print(f"x2,y2: ",{x2},",",{y2})
                #print(f"x3,y3: ",{x3},",",{y3})
                #print(f"a: ",{a})
                #print(f"b: ",{b})
                #print(f"c: ",{c})
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
