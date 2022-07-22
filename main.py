#
# 07-22-2022 D Osburn 
# https://github.com/danosb/quantum_influence
#

import tkinter
from tkinter import *
from PIL import Image, ImageTk
from playsound import playsound
import requests
import json
import time
import numpy as np
from functools import partial
from datetime import datetime
import sqlite3
with sqlite3.connect("database.db") as db:
  cursor=db.cursor()


### Create database tables

# Basic info about the trial. A trial is composed of multiple runs. Each run has four sets of numbers.
cursor.execute('''CREATE TABLE IF NOT EXISTS trial(
    id integer PRIMARY KEY AUTOINCREMENT,
    datetime text NOT NULL,
    duration integer NOT NULL, 
    number_trials integer NOT NULL
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
    set_number integer NOT NULL,
    trial_id integer NOT NULL,
    set_sum integer NOT NULL,
    run_number integer NOT NULL,
    mod_3 integer,
    is_odd text,
    apidata_id integer NOT NULL,
    FOREIGN KEY (apidata_id) REFERENCES apidata(id) ,
    FOREIGN KEY (trial_id) REFERENCES trial(id)
    )''')


## This function kicks off the trial by validating inputs, generating data for each run, and storing in the database

def start_trial():
    # Retrieve two parameters from the GUI
    setDuration = duration.get()
    setRuncount = runs.get()

    # Validate that the two inputs are in the expected range
    if  int(setDuration) > 0 and int(setDuration) < 60 and int(setRuncount) > 0 and int(setRuncount) < 20:

        now = datetime.now() # current date and time
        date_time = now.strftime("%m/%d/%Y, %H:%M:%S")

        ## Populate basic info of trial
        cursor.execute("INSERT INTO trial(datetime,duration,number_trials)VALUES(?,?,?)",(date_time,setDuration,setRuncount))
        db.commit()

        # Retreive trial ID 
        cursor.execute("select max(id) from trial")
        trial_id = cursor.fetchone()


        loopcount = 1 

        while loopcount < int(setRuncount)+1:

            ### Retrieve four sets of quantum random numbers via API for this run

            my_headers = {'x-api-key' : '***MODIFY THIS***'}

            # Set 1 with sum and module 3 
            # .. used to determine whether to preview real or dummy results of a given run
            response1 = requests.get('https://api.quantumnumbers.anu.edu.au?length=1000&type=uint8', headers=my_headers)
            response1_dict=json.loads(response1.content)
            set1 = np.array(response1_dict['data'])
            set1sum = np.sum(set1)
            set1mod3 = set1sum % 3

            # Set 2 with sum and module 3 
            # .. used to determine what action the user should take
            response2 = requests.get('https://api.quantumnumbers.anu.edu.au?length=1000&type=uint8', headers=my_headers)
            response2_dict=json.loads(response2.content)
            set2 = np.array(response2_dict['data'])
            set2sum = np.sum(set2)
            set2mod3 = set2sum % 3

            # Set 3 with sum 
            # .. this is the dummy set that may or may not be shown during the preview
            response3 = requests.get('https://api.quantumnumbers.anu.edu.au?length=1000&type=uint8', headers=my_headers)
            response3_dict=json.loads(response3.content)
            set3 = np.array(response3_dict['data'])
            set3sum = np.sum(set3)

            # Set 4 with sum 
            # .. this set is always shown during the actual experiment
            response4 = requests.get('https://api.quantumnumbers.anu.edu.au?length=1000&type=uint8', headers=my_headers)
            response4_dict=json.loads(response4.content)
            set4 = np.array(response4_dict['data'])
            set4sum = np.sum(set4)


            # Populate apidata table for set1
            cursor.execute("INSERT INTO apidata(rawdata,trial_id)VALUES(?,?)",(str(set1),str(trial_id)))
            db.commit()    
            
            # Return set 1 ID and use to populate sets table for set 1
            cursor.execute("select max(id) from apidata")
            set1_id = cursor.fetchone()
            cursor.execute("INSERT INTO sets(set_number,trial_id,run_number,set_sum,mod_3,apidata_id)VALUES(?,?,?,?,?,?)",('1',str(trial_id),loopcount,str(set1sum),str(set1mod3),str(set1_id)))
            db.commit()  

            # Populate rawata table for set2
            cursor.execute("INSERT INTO apidata(rawdata,trial_id)VALUES(?,?)",(str(set2),str(trial_id)))
            db.commit()    
            
            # Return set 2 ID and use to populate sets table for set 2
            cursor.execute("select max(id) from apidata")
            set2_id = cursor.fetchone()
            cursor.execute("INSERT INTO sets(set_number,trial_id,run_number,set_sum,mod_3,apidata_id)VALUES(?,?,?,?,?,?)",('2',str(trial_id),loopcount,str(set2sum),str(set2mod3),str(set2_id)))
            db.commit()  

            # Populate rawata table for set3
            cursor.execute("INSERT INTO apidata(rawdata,trial_id)VALUES(?,?)",(str(set3),str(trial_id)))
            db.commit()    
            
            # Return set 3 ID and use to populate sets table for set 3
            cursor.execute("select max(id) from apidata")
            set3_id = cursor.fetchone()
            cursor.execute("INSERT INTO sets(set_number,trial_id,run_number,set_sum,is_odd,apidata_id)VALUES(?,?,?,?,?,?)",('3',str(trial_id),loopcount,str(set3sum),str(set3sum % 2),str(set3_id)))
            db.commit()    
           
            # Populate rawata table for set4
            cursor.execute("INSERT INTO apidata(rawdata,trial_id)VALUES(?,?)",(str(set4),str(trial_id)))
            db.commit()    
            
            # Return set 4 ID and use to populate sets table for set 4
            cursor.execute("select max(id) from apidata")
            set4_id = cursor.fetchone()
            cursor.execute("INSERT INTO sets(set_number,trial_id,run_number,set_sum,is_odd,apidata_id)VALUES(?,?,?,?,?,?)",('4',str(trial_id),loopcount,str(set4sum),str(set4sum % 2),str(set4_id)))
            db.commit()    

            loopcount = loopcount + 1

        # Kicks off the next function, which displays previews
        displayResults(setRuncount, trial_id, setDuration)

    else:
        error = Message(text="BAD VALUE - TRY AGAIN", width=800)
        error.place(x = 350, y = 520)
        error.config(padx=0)



## General User Interface (GUI)

window = Tk()
window.geometry("700x600")
window.title("Quantum Influence Experiment")

error = Message(text="Previous experiments, mostly done by Helmut Schmidt in the 70s and 80s, suggest that prior to being observed random numbers can be influenced by intention.", width=600)
error.place(x = 30, y = 10)
error.config(padx=0)

error = Message(text="Here we aim to replicate these experiments with some small tweaks. Namely, we will use random numbers generated by measuring the quantum fluctuations of the vacuum. ", width=600)
error.place(x = 30, y = 50)
error.config(padx=0)

error = Message(text="We will also generate additional quantum random numbers to drive two important aspects of the experiment.", width=600)
error.place(x = 30, y = 90)
error.config(padx=0)

error = Message(text="First, they will determine whether a given set of random numbers is observed prior to the experiment or not. We expect numbers that are observed to not be open to influence.", width=600)
error.place(x = 30, y = 130)
error.config(padx=0)

error = Message(text="Second, we will use quantum random numbers to determine what type of influence to exert upon a given set of numbers.", width=600)
error.place(x = 30, y = 170)
error.config(padx=0)

error = Message(text="We start with a unique set of 1000 quantum numbers for each run, and then sum them.", width=600)
error.place(x = 30, y = 210)
error.config(padx=0)

error = Message(text="For each set you will be instructed to do one of the following:", width=600)
error.place(x = 30, y = 240)
error.config(padx=0)

error = Message(text="1. Influence the sum to be positive", width=600)
error.place(x = 30, y = 260)
error.config(padx=0)

error = Message(text="2. Influence the sum to be negative", width=600)
error.place(x = 30, y = 280)
error.config(padx=0)

error = Message(text="3. Make no attempt to influence", width=600)
error.place(x = 30, y = 300)
error.config(padx=0)

error = Message(text="Before we begin, please enter basic paremeters of the experiment. Usually it's best to stick with default values.", width=600)
error.place(x = 30, y = 340)
error.config(padx=0)

label1 = Label(text = "Enter number of minutes for each run (1 default):")
label1.place(x = 30, y = 390)
label1.config(bg='lightgreen', padx=0)

duration = Entry(text = "")
duration.place(x=350, y=390, width=200, height=25)

label2 = Label(text = "Enter number of runs (10 default):")
label2.place(x = 30, y = 430)
label2.config(bg='lightgreen', padx=0)

runs = Entry(text = "")
runs.place(x=350, y=430, width=200, height=25)

button = Button(text = "Begin", command = start_trial)
button.place(x=350, y=480, width=75, height=35)



# This function displays previews. It will show either real or dummy results for a given, as dictated by prior logic.
# We expect results that are observed prior to experiment to not be open to influence.
def displayResults(runcount, trial_id, duration):

    loopcount = 1 

    # Repeat for each run
    while loopcount < int(runcount)+1:
        
        # Clear the window
        for widget in window.winfo_children():
            widget.destroy()

        error = Message(text="Please observe the images below. No need to remember them.", width=800)
        error.place(x = 30, y = 10)
        error.config(padx=0)

        error = Message(text="Trial number " + str(trial_id)[1:len(trial_id)-3] + ", Run number "+ str(loopcount) + ":", width=600)
        error.place(x = 30, y = 30)
        error.config(padx=0)

        #Retreive modulo 3 from set1. This determines whether to show real (set 4) or dummy (set 3)
        cursor.execute("select mod_3 from sets where trial_id='" + str(trial_id) + "' and set_number='1' and run_number='"+ str(loopcount) + "' ")
        setmod3 = cursor.fetchone()

        # Show dummy results if mod3 in (0, 1)
        if int(str(setmod3)[1:len(setmod3)-3]) == 0 or int(str(setmod3)[1:len(setmod3)-3]) == 1:
            cursor.execute("select is_odd from sets where trial_id='" + str(trial_id) + "' and set_number=3 and run_number='" + str(loopcount) + "' ")
            is_odd = cursor.fetchone()

        # Show real results if mod3=2    
        else:
            cursor.execute("select is_odd from sets where trial_id='" + str(trial_id) + "' and set_number=4 and run_number='" + str(loopcount) + "' ")
            is_odd = cursor.fetchone()

        # Now we'll show the image that corresponds to the sum (odd/even) for the defined set    
        if int(str(is_odd)[2:len(is_odd)-4])==1:
            image1 = Image.open("odd.gif")
            test = ImageTk.PhotoImage(image1)

            label1 = tkinter.Label(image=test)
            label1.image = test

            # Position image
            label1.place(x=30, y=70)
            window.update_idletasks()
            window.update()
            
        else:
            image1 = Image.open("even.gif")
            test = ImageTk.PhotoImage(image1)
            label1 = tkinter.Label(image=test)
            label1.image = test

            # Position image
            label1.place(x=30, y=70)
            window.update_idletasks()
            window.update()

        # Wait 2 seconds and move to next run/set in trial
        time.sleep(2)
        loopcount = loopcount + 1

    for widget in window.winfo_children():
        widget.destroy()
 
    error = Message(text="Done! Ready for the runs?", width=800)
    error.place(x = 30, y = 10)
    error.config(padx=0)

    error = Message(text="We have generated sets of random numbers by measuring the quantum fluctuations of the vacuum. One set for each run.", width=600)
    error.place(x = 30, y = 50)
    error.config(padx=0)

    error = Message(text="Existing experiments suggest that prior to being observed these numbers can be influenced by intention.", width=600)
    error.place(x = 30, y = 90)
    error.config(padx=0)

    error = Message(text="When the numbers in a given set are summed they will produce either a single odd number (red) or a single even number (green).", width=600)
    error.place(x = 30, y = 130)
    error.config(padx=0)

    error = Message(text="For all sets, please relax and focus on trying to mentally influence the outcomes in the depicted direction.", width=600)
    error.place(x = 30, y = 170)
    error.config(padx=0)

    error = Message(text="A beep will signify the start of each run.", width=800)
    error.place(x = 30, y = 210)
    error.config(padx=0)

    error = Message(text="For this trial (trial #" + str(trial_id)[1:len(trial_id)-3] + "), there are " + runcount + " runs, each lasting " + duration + " minute(s)." , width=800)
    error.place(x = 30, y = 240)
    error.config(padx=0)

    error = Message(text="Please ensure that you won't be disrupted until the trial concludes.", width=800)
    error.place(x = 30, y = 270)
    error.config(padx=0)

    button = Button(text = "Let's Go", command = partial(exec_runs, trial_id, runcount, duration))
    button.place(x=30, y=310, width=75, height=35)


# This function kicks off actual experiment of influence. We will show set 4 in all cases. 
# Some of the set 4s have been observed but most have not.
def exec_runs(trial_id, runcount, duration):
    
    loopcount = 1 

    # Repeat for each run 
    while loopcount < int(runcount)+1:

        # Clear the window
        for widget in window.winfo_children():
            widget.destroy()

        # Play beep to signify new run
        playsound('beep-01a.mp3')

        error = Message(text="Trial number " + str(trial_id)[1:len(trial_id)-3] + ", Run number "+ str(loopcount) + " out of " + runcount + ". You have " + duration + " minute(s) per run.", width=600)
        error.place(x = 30, y = 10)
        error.config(padx=0)

        error = Message(text="A beep signifies the start of each new run.", width=800)
        error.place(x = 30, y = 40)
        error.config(padx=0)

        error = Message(text="Focus on trying to influence the sum of all random numbers in the set in the direction depicted in the image below for each run.", width=600)
        error.place(x = 30, y = 80)
        error.config(padx=0)

        # Set 2 determines which action the user should take
        cursor.execute("select mod_3 from sets where trial_id='" + str(trial_id) + "' and set_number='2' and run_number='"+ str(loopcount) + "' ")
        setmod3 = cursor.fetchone()

        # If mod3 of set 2 = 0 then influence even
        if int(str(setmod3)[1:len(setmod3)-3]) == 0:
            image1 = Image.open("even.gif")
            test = ImageTk.PhotoImage(image1)
            label1 = tkinter.Label(image=test)
            label1.image = test

            # Position image
            label1.place(x=30, y=140)
            window.update_idletasks()
            window.update()

        # If mod3 of set 2 = 1 then influence odd
        if int(str(setmod3)[1:len(setmod3)-3]) == 1:
            image1 = Image.open("odd.gif")
            test = ImageTk.PhotoImage(image1)
            label1 = tkinter.Label(image=test)
            label1.image = test

            # Position image
            label1.place(x=30, y=140)
            window.update_idletasks()
            window.update()

        # If mod3 of set 2 = 2 then do nothing
        if int(str(setmod3)[1:len(setmod3)-3]) == 2:
            image1 = Image.open("donothing.gif")
            test = ImageTk.PhotoImage(image1)
            label1 = tkinter.Label(image=test)
            label1.image = test

            # Position image
            label1.place(x=30, y=140)
            window.update_idletasks()
            window.update()
        
        # Wait the defined duration to allow influence to elapse
        time.sleep(60*int(duration))
        
        loopcount = loopcount + 1

    for widget in window.winfo_children():
        widget.destroy()

    error = Message(text="Good job! Almost done. Please quickly view all images one last time.", width=600)
    error.place(x = 30, y = 10)
    error.config(padx=0)

    button = Button(text = "Show me", command = partial(finalDisplay, trial_id, runcount, duration))
    button.place(x=30, y=50, width=75, height=35)



# To conclude, we will show all set 4 images to the user. This should solidy results.
def finalDisplay(trial_id, runcount, duration):

    loopcount = 1 

    # Repeat for each run
    while loopcount < int(runcount)+1:
        
        # Clear the window
        for widget in window.winfo_children():
            widget.destroy()
        error = Message(text="Please observe the images below. No need to remember them.", width=800)
        error.place(x = 30, y = 10)
        error.config(padx=0)

        error = Message(text="Trial number " + str(trial_id)[1:len(trial_id)-3] + ", Run number "+ str(loopcount) + ":", width=800)
        error.place(x = 30, y = 30)
        error.config(padx=0)

        cursor.execute("select is_odd from sets where trial_id='" + str(trial_id) + "' and set_number=4 and run_number='" + str(loopcount) + "' ")
        is_odd = cursor.fetchone()

        # If the sum of set 4 is odd then show odd image
        if int(str(is_odd)[2:len(is_odd)-4])==1:
            image1 = Image.open("odd.gif")
            test = ImageTk.PhotoImage(image1)

            label1 = tkinter.Label(image=test)
            label1.image = test

            # Position image
            label1.place(x=30, y=70)
            window.update_idletasks()
            window.update()
        
        # If the sum of set 4 is odd then show even image
        else:
            image1 = Image.open("even.gif")
            test = ImageTk.PhotoImage(image1)
            label1 = tkinter.Label(image=test)
            label1.image = test

            # Position image
            label1.place(x=30, y=70)
            window.update_idletasks()
            window.update()

        time.sleep(2)
        loopcount = loopcount + 1

    for widget in window.winfo_children():
        widget.destroy()

    error = Message(text="Finished, thanks!", width=800)
    error.place(x = 30, y = 10)
    error.config(padx=0)



## Terminate database connection and end program

window.mainloop()
db.close()
