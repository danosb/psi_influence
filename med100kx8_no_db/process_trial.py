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
from concurrent.futures import ThreadPoolExecutor
from extract_numbers import extract_numbers
from analyze_subtrial import analyze_subtrial  
from p_and_z_funcs import trialp_from_nwsv, invnorm


# Get numbers and process the trial. Uses unique threads for extraction and analyzing
def process_trial(ftdi, trial, n, count_subtrial_per_trial, influence_type):
    number_queue = queue.Queue()
    stop_event = threading.Event()
    

    with ThreadPoolExecutor(max_workers=2) as executor:
        extraction_thread = executor.submit(extract_numbers, ftdi, number_queue, stop_event)
        analysis_thread = executor.submit(analyze_subtrial, number_queue, stop_event, n, trial, count_subtrial_per_trial)

        extraction_thread.result()
       
        trial_cum_sv, trial_weighted_sv, trial_norm_weighted_sv, trial_count_bidirectional_is_pos = analysis_thread.result()

    trial_p = trialp_from_nwsv(trial_norm_weighted_sv, influence_type)
    trial_z = invnorm(trial_p)


    return trial_p, trial_z, trial_count_bidirectional_is_pos