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
from dbutils.pooled_db import PooledDB
from concurrent.futures import ThreadPoolExecutor
from extract_numbers import extract_numbers
from analyze_subtrial import analyze_subtrial  
from p_and_z_funcs import trialp_from_nwsv, invnorm


# Get numbers and process the trial. Uses unique threads for extraction, analyzing, and DB writing
def process_trial(ftdi, trial, supertrial, db_queue, n, count_subtrial_per_trial):
    number_queue = queue.Queue()
    stop_event = threading.Event()
    

    with ThreadPoolExecutor(max_workers=2) as executor:
        extraction_thread = executor.submit(extract_numbers, ftdi, number_queue, stop_event)
        analysis_thread = executor.submit(analyze_subtrial, number_queue, stop_event, db_queue, n, trial, supertrial, count_subtrial_per_trial)

        extraction_thread.result()
        print(f"test222222")
        trial_cum_sv, trial_weighted_sv, trial_norm_weighted_sv = analysis_thread.result()

    trial_p = trialp_from_nwsv(trial_norm_weighted_sv)
    trial_z = invnorm(trial_p)

    # Add trial data to the DB write queue
    data = {
        'table': 'trial_data',
        'supertrial': supertrial,
        'trial': trial,
        'trial_cum_sv': trial_cum_sv,
        'p_value': trial_p,
        'z_value': trial_z,
        'trial_weighted_sv': trial_weighted_sv,
        'trial_norm_weighted_sv': trial_norm_weighted_sv,
        'created_datetime': datetime.now()
    }
    db_queue.put(data)

    return trial_p, trial_z