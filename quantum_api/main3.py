#
# 07-22-2022 D Osburn 
# https://github.com/danosb/quantum_influence
#

# 6 sec pauses, always even *probability calc may be broken

#import tkinter
#from tkinter import *
#from PIL import Image, ImageTk
from playsound import playsound
import requests
import json
import time
import os
import math
import random
import numpy as np
#from functools import partial
from datetime import datetime
from scipy.stats import binomtest
import sqlite3
with sqlite3.connect("database3.db") as db:
  cursor=db.cursor()

def main_func():
    ### Create database tables

    # Basic info about the trial. A trial is composed of multiple runs. Each run has four sets of numbers.
    cursor.execute('''CREATE TABLE IF NOT EXISTS trial(
        id integer PRIMARY KEY AUTOINCREMENT,
        datetime text NOT NULL,
        duration integer , 
        number_trials integer ,
        name text 
        )''')

    # Stores raw quantum random numbers retreived via API
    cursor.execute('''CREATE TABLE IF NOT EXISTS apidata(
        id integer PRIMARY KEY AUTOINCREMENT ,
        rawdata text NOT NULL,
        trial_id integer NOT NULL,
        FOREIGN KEY (trial_id) REFERENCES trial(id) 
        )''')

    # Stores information for each of the four number sets
    cursor.execute('''CREATE TABLE IF NOT EXISTS sets(
        id integer PRIMARY KEY AUTOINCREMENT,
        set_number integer,
        trial_id integer ,
        set_sum integer NOT NULL,
        run_number integer,
        mod_6 integer,
        is_odd text,
        apidata_id integer NOT NULL,
        FOREIGN KEY (apidata_id) REFERENCES apidata(id) ,
        FOREIGN KEY (trial_id) REFERENCES trial(id)
        )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS trail_result(
        id integer PRIMARY KEY AUTOINCREMENT,
        trial_id integer NOT NULL,
        total_items integer NOT NULL,
        count_even integer NOT NULL,
        p_value decimal NOT NULL,
        FOREIGN KEY (trial_id) REFERENCES trial(id)
        )''')


    now = datetime.now() # current date and time
    date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
    setRuncount = 60
    setDuration = 6

    loopcount = 1 
    ## Populate basic info of trial
    cursor.execute("INSERT INTO trial(datetime,number_trials, duration)VALUES(?,?,?)",(date_time, setRuncount,setDuration))
    db.commit()

    # Retreive trial ID 
    cursor.execute("select max(id) from trial")
    trial_id = cursor.fetchone()

    totalitems=0
    counteven=0
    countodd=0
    countruns=0
    countsuccess=0
    trial_result="TBD"


    print(f'')
    print(f'')
    print(f'This trial (#{int(str(trial_id)[1:len(trial_id)-3])}) will last roughly {str(round(int(setRuncount)*int(setDuration)/60))} minute(s), with {str(setRuncount)} runs each lasting {str(setDuration)} seconds.')
    print(f'')
    print(f'During run we will retrieve a set of 1,024 random numbers. Your goal is to influence these sets to have more EVEN than ODD numbers.')
    print(f'')
    print(f'A single ding means you got more evens for a given set. A double ding means you hit statistical significance for a given set. Get those double dings!')
    print(f'')
    print(f'At the end we will calculate statistical significance based on how many sets had more evens.')
    print(f'')
    try:
        input("Good luck! Press enter to begin...")
    except SyntaxError:
        pass
    print(f'')
    print(f'')

    print(f'Ok, go!')

    while loopcount < setRuncount+1:

        # we'll split the sleep to before and after the numbers are retrieved
        #sleep(setDuration/2)
        playsound('3secsilence.mp3')


        ### Retrieve quantum random numbers via API 
        my_headers = {'x-api-key' : '[redacted]'}

        # Set 1 with sum and module 6 
        # .. used to determine whether to preview real or dummy results of a given run
        response1 = requests.get('https://api.quantumnumbers.anu.edu.au?length=1024&type=uint8', headers=my_headers)
        response1_dict=json.loads(response1.content)
        set1 = np.array(response1_dict['data'])
        set1sum = np.sum(set1)

        # Populate apidata table for set1
        cursor.execute("INSERT INTO apidata(rawdata,trial_id)VALUES(?,?)",(str(set1),str(trial_id)))
        db.commit()    
        
        # Return set 1 ID and use to populate sets table for set 1
        cursor.execute("select max(id) from apidata")
        set1_id = cursor.fetchone()
        cursor.execute("INSERT INTO sets(set_number,set_sum,is_odd,run_number,apidata_id)VALUES(?,?,?,?,?)",('1',str(set1sum),str(set1sum % 2),loopcount,str(set1_id)))
        db.commit()  

        #sleep(setDuration/2)
        playsound('3secsilence.mp3')

        totalitems_set=0
        counteven_set=0
        countodd_set=0

        for x in set1:
           
            if x%2==1:
                countodd=countodd+1
                countodd_set=countodd_set+1

            else:
                counteven=counteven+1
                counteven_set=counteven_set+1

            totalitems=totalitems+1
            totalitems_set=totalitems_set+1
            
        countruns=countruns+1

        res_set=binomtest(int(counteven_set), int(totalitems_set), 0.5, alternative='greater')

        if int(counteven_set)/int(totalitems_set) > 0.5 and float(res_set.pvalue) <= 0.05:
            print(f'Set {str(loopcount)}/{str(setRuncount)}: {str(counteven_set)} / {str(totalitems_set)} = {str(int(counteven_set)/int(totalitems_set)*100)[0:5]}% even. Statistically significant!!!')
            playsound('very_correct.mp3')
            countsuccess=countsuccess+1

        if int(counteven_set)/int(totalitems_set) > 0.5 and float(res_set.pvalue) > 0.05:
            print(f'Set {str(loopcount)}/{str(setRuncount)}: {str(counteven_set)} / {str(totalitems_set)} = {str(int(counteven_set)/int(totalitems_set)*100)[0:5]}% even. More evens!')
            playsound('correct.mp3')
            countsuccess=countsuccess+1

        if int(counteven_set)/int(totalitems_set) <= 0.5:
            print(f'Set {str(loopcount)}/{str(setRuncount)}: {str(counteven_set)} / {str(totalitems_set)} = {str(int(counteven_set)/int(totalitems_set)*100)[0:5]}% even. No joy.')
            playsound('incorrect.mp3')    

        loopcount = loopcount+1

    print(f'')
    print(f'')
    print(f'')
    #print(f'Total items: {totalitems}, Count even: {counteven}, Percent Even: {str(int(counteven)/int(totalitems)*100)[0:5]}')
    print(f'Total runs: {countruns}, Count more evens: {countsuccess}, Percent more even: {str(int(countsuccess)/int(countruns)*100)[0:5]}')
    #res=binomtest(int(counteven), int(totalitems), 0.5, alternative='greater')
    res=binomtest(int(countsuccess), int(countruns), 0.5, alternative='greater')
    print(f'')
    print(f'There is a {str(float((res.pvalue))*100)[:5]}% probability of this happening by chance.')
    print(f'')

    #if int(counteven)/int(totalitems) > 0.5 and float(res.pvalue) <= 0.05:
    if int(countsuccess)/int(countruns) > 0.5 and float(res.pvalue) <= 0.05:
        print(f'You did it!! Statistically significant influence!!')
        trail_result="success"

    #if int(counteven)/int(totalitems) > 0.5 and float(res.pvalue) > 0.05:
    if int(countsuccess)/int(countruns) > 0.5 and float(res.pvalue) > 0.05:
        print(f'You got more evens, but it was not statistically significant.')
        trail_result="more_evens"

    #if int(counteven)/int(totalitems) <= 0.5:
    if int(countsuccess)/int(countruns) <= 0.5:
        print(f'Better luck next time.')
        trail_result="not_more_evens"

    print(f'')
    print(f'')
    cursor.execute("INSERT INTO trail_result(trial_id, total_items, count_even, p_value )VALUES(?,?,?,?)",(trial_result, int(totalitems), int(counteven), float(res.pvalue)))
    db.commit()

    try:
        input("Press enter to end...")
    except SyntaxError:
        pass
    print(f'')

def sleep(duration, get_now=time.perf_counter):
    now = get_now()
    end = now + duration
    while now < end:
        now = get_now()


main_func()

db.close()
