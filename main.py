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
import math
import random
import numpy as np
from functools import partial
from datetime import datetime
import sqlite3
with sqlite3.connect("database2.db") as db:
  cursor=db.cursor()


### Create database tables

# Basic info about the trial. A trial is composed of multiple runs. Each run has four sets of numbers.
cursor.execute('''CREATE TABLE IF NOT EXISTS trial(
    id integer PRIMARY KEY AUTOINCREMENT,
    datetime text NOT NULL,
    duration integer NOT NULL, 
    number_trials integer NOT NULL,
    name text NOT NULL
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
    mod_6 integer,
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
    setName = name.get()

    # Validate that the two inputs are in the expected range
    if  int(setDuration) > 0 and int(setDuration) < 11 and int(setRuncount) > 0 and int(setRuncount) < 61:

        now = datetime.now() # current date and time
        date_time = now.strftime("%m/%d/%Y, %H:%M:%S")

        ## Populate basic info of trial
        cursor.execute("INSERT INTO trial(datetime,duration,number_trials,name)VALUES(?,?,?,?)",(date_time,setDuration,setRuncount,setName))
        db.commit()

        # Retreive trial ID 
        cursor.execute("select max(id) from trial")
        trial_id = cursor.fetchone()


        loopcount = 1 

        while loopcount < int(setRuncount)+1:

            ### Retrieve two sets of quantum random numbers via API for this run

            my_headers = {'x-api-key' : '**YOUR API KEY HERE**'}

            # Set 1 with sum and module 6 
            # .. used to determine whether to preview real or dummy results of a given run
            response1 = requests.get('https://api.quantumnumbers.anu.edu.au?length=1002&type=uint8', headers=my_headers)
            response1_dict=json.loads(response1.content)
            set1 = np.array(response1_dict['data'])
            set1sum = np.sum(set1)
            set1mod6 = set1sum % 6

            # Set 2 with sum 
            # .. this set is always shown during the actual experiment
            response2 = requests.get('https://api.quantumnumbers.anu.edu.au?length=1000&type=uint8', headers=my_headers)
            response2_dict=json.loads(response2.content)
            set2 = np.array(response2_dict['data'])
            set2sum = np.sum(set2)

            # Populate apidata table for set1
            cursor.execute("INSERT INTO apidata(rawdata,trial_id)VALUES(?,?)",(str(set1),str(trial_id)))
            db.commit()    
            
            # Return set 1 ID and use to populate sets table for set 1
            cursor.execute("select max(id) from apidata")
            set1_id = cursor.fetchone()
            cursor.execute("INSERT INTO sets(set_number,trial_id,run_number,set_sum,mod_6,apidata_id)VALUES(?,?,?,?,?,?)",('1',str(trial_id),loopcount,str(set1sum),str(set1mod6),str(set1_id)))
            db.commit()  

           
            # Populate rawata table for set2
            cursor.execute("INSERT INTO apidata(rawdata,trial_id)VALUES(?,?)",(str(set2),str(trial_id)))
            db.commit()    
            
            # Return set 2 ID and use to populate sets table for set 2
            cursor.execute("select max(id) from apidata")
            set2_id = cursor.fetchone()
            cursor.execute("INSERT INTO sets(set_number,trial_id,run_number,set_sum,is_odd,apidata_id)VALUES(?,?,?,?,?,?)",('2',str(trial_id),loopcount,str(set2sum),str(set2sum % 2),str(set2_id)))
            db.commit()    

            loopcount = loopcount + 1

        # Kicks off the next function, which displays previews
        displayResults(setRuncount, trial_id, setDuration)

    else:
        error = Message(text="BAD VALUE - TRY AGAIN", width=800)
        error.place(x = 350, y = 540)
        error.config(padx=0)



## General User Interface (GUI)

window = Tk()
window.geometry("700x600")
window.title("Quantum Influence Experiment")

error = Message(text="Previous experiments, mostly done by Helmut Schmidt in the 70s and 80s, suggest that prior to being observed random numbers can be influenced by intention. Here, we aim to replicate and improve on these experiments by using quantum random numbers to drive all aspects of the experiment.", width=600)
error.place(x = 30, y = 10)
error.config(padx=0)

error = Message(text="Each trial in our experiment will consist of multiple runs. By default we'll do 10 runs at 1 minute each. For each run a set of random numbers is generated and summed up. The sum of those numbers will be either even or odd. Your job is to try to influence whether the sum is even or odd, according to the instruction given for that run. After each run a sound will indicate whether the sum matched the outcome you were trying to influence. Please note that we expect the ability to influence to be quite small; it will likely only show up when analyzing a very large number of runs. Don't feel bad if it seems like you aren't having a big impact. Your results are being logged to a database for later analysis.", width=600)
error.place(x = 30, y = 100)
error.config(padx=0)

error = Message(text="Before we begin, please enter basic paremeters of the experiment. Unless advised otherwise please stick with default values.", width=600)
error.place(x = 30, y = 260)
error.config(padx=0)

label3 = Label(text = "Your first name:")
label3.place(x = 30, y = 320)
label3.config(bg='lightgreen', padx=0)

name = Entry(text = "")
name.place(x=350, y=320, width=200, height=25)

label1 = Label(text = "Number of minutes for each run (default 1):")
label1.place(x = 30, y = 360)
label1.config(bg='lightgreen', padx=0)

duration = Entry(text = "")
duration.place(x=350, y=360, width=200, height=25)

label2 = Label(text = "Number of runs (default 10):")
label2.place(x = 30, y = 400)
label2.config(bg='lightgreen', padx=0)

runs = Entry(text = "")
runs.place(x=350, y=400, width=200, height=25)


error = Message(text="On the next page a number of images are going to quickly flash. Don't worry about remembering them, but PLEASE OBSERVE THEM.", width=600)
error.place(x = 30, y = 440)
error.config(padx=0)

button = Button(text = "Begin", command = start_trial)
button.place(x=350, y=500, width=75, height=35)



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

        # Retrieve modulo 6 from set1. This determines whether to show real result (set 2) or dummy result 
        cursor.execute("select mod_6 from sets where trial_id='" + str(trial_id) + "' and set_number='1' and run_number='"+ str(loopcount) + "' ")
        setmod6 = cursor.fetchone()

        # Determine if real set is odd or not (we may or may not display this)
        cursor.execute("select is_odd from sets where trial_id='" + str(trial_id) + "' and set_number=2 and run_number='" + str(loopcount) + "' ")
        is_odd = cursor.fetchone()

        # Create a psuedo-random number, which is good enough for showing dummy results
        random_num=random.random()

        # Show dummy results if mod6 > 2 -> EVEN if our psuedo-random number is even:
        if int(str(setmod6)[1:len(setmod6)-3]) > 2 and int(math.ceil(random_num)) % 2 == 0:
            image1 = Image.open("even.gif")
            test = ImageTk.PhotoImage(image1)
            label1 = tkinter.Label(image=test)
            label1.image = test

            # Position image
            label1.place(x=60, y=70)
            window.update_idletasks()
            window.update()  

        # Show dummy results if mod6 > 2 -> ODD if our psuedo-random number is odd:
        if int(str(setmod6)[1:len(setmod6)-3]) > 2 and int(math.ceil(random_num)) % 2 == 1:
            image1 = Image.open("odd.gif")
            test = ImageTk.PhotoImage(image1)
            label1 = tkinter.Label(image=test)
            label1.image = test

            # Position image
            label1.place(x=60, y=70)
            window.update_idletasks()
            window.update()  
        
        # Show real results if mod6 < 3 -> EVEN 
        if int(str(setmod6)[1:len(setmod6)-3]) < 3 and int(str(is_odd)[2:len(is_odd)-4])==0:
            image1 = Image.open("even.gif")
            test = ImageTk.PhotoImage(image1)
            label1 = tkinter.Label(image=test)
            label1.image = test

            # Position image
            label1.place(x=60, y=70)
            window.update_idletasks()
            window.update()

        # Show real results if mod6 < 3 -> ODD 
        if int(str(setmod6)[1:len(setmod6)-3]) < 3 and int(str(is_odd)[2:len(is_odd)-4])==1:
            image1 = Image.open("even.gif")
            test = ImageTk.PhotoImage(image1)
            label1 = tkinter.Label(image=test)
            label1.image = test

            # Position image
            label1.place(x=60, y=70)
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

    error = Message(text="When the numbers in a given set are summed they will produce either a single odd number (red) or a single even number (green).", width=600)
    error.place(x = 30, y = 50)
    error.config(padx=0)

    error = Message(text="For all sets, please relax and focus on trying to mentally influence the outcomes in the depicted direction. A sound will indicate whether you've succeeded or not. We suggest meditating on the feeling of a successful match sound.", width=600)
    error.place(x = 30, y = 100)
    error.config(padx=0)

    error = Message(text="We expect the ability to influence to be small; don't stress about the failures.", width=800)
    error.place(x = 30, y = 170)
    error.config(padx=0)

    error = Message(text="For this trial (trial #" + str(trial_id)[1:len(trial_id)-3] + "), there are " + runcount + " runs, each lasting " + duration + " minute(s). Total runtime: " + str(int(duration)*int(runcount)) + " minutes.", width=600)
    error.place(x = 30, y = 210)
    error.config(padx=0)

    error = Message(text="Please ensure that you won't be disrupted until the trial concludes.", width=800)
    error.place(x = 30, y = 250)
    error.config(padx=0)

    button = Button(text = "Let's Go", command = partial(exec_runs, trial_id, runcount, duration))
    button.place(x=30, y=290, width=75, height=35)


# This function kicks off actual experiment of influence. We will show set 2 in all cases. 
# Some of the set 2s have been observed but most have not.
def exec_runs(trial_id, runcount, duration):
    
    loopcount = 1 

    # Repeat for each run 
    while loopcount < int(runcount)+1:

        # Clear the window
        for widget in window.winfo_children():
            widget.destroy()

        error = Message(text="Trial number " + str(trial_id)[1:len(trial_id)-3] + ", Run number "+ str(loopcount) + " out of " + runcount + ". You have " + duration + " minute(s) per run.", width=600)
        error.place(x = 30, y = 10)
        error.config(padx=0)

        error = Message(text="Focus on trying to influence the sum of all random numbers in the set in the direction depicted in the image below for each run. A sound will indicate whether you've succeeded or not.", width=600)
        error.place(x = 30, y = 40)
        error.config(padx=0)

        # Set 2 determines which action the user should take
        cursor.execute("select mod_6 from sets where trial_id='" + str(trial_id) + "' and set_number='1' and run_number='"+ str(loopcount) + "' ")
        setmod6 = cursor.fetchone()

        # If mod6 of set 1 equals 0 or 3 then influence even
        if (int(str(setmod6)[1:len(setmod6)-3]) == 0) or (int(str(setmod6)[1:len(setmod6)-3]) == 3):
            image1 = Image.open("even.gif")
            test = ImageTk.PhotoImage(image1)
            label1 = tkinter.Label(image=test)
            label1.image = test

            # Position image
            label1.place(x=60, y=100)
            window.update_idletasks()
            window.update()

        # If mod6 of set 1 equals 1 or 4 then influence even
        if (int(str(setmod6)[1:len(setmod6)-3]) == 1) or (int(str(setmod6)[1:len(setmod6)-3]) == 4):
            image1 = Image.open("odd.gif")
            test = ImageTk.PhotoImage(image1)
            label1 = tkinter.Label(image=test)
            label1.image = test

            # Position image
            label1.place(x=60, y=100)
            window.update_idletasks()
            window.update()

        # If mod6 of set 1 equals 2 or 5 then exert no influence
        if (int(str(setmod6)[1:len(setmod6)-3]) == 2) or (int(str(setmod6)[1:len(setmod6)-3]) == 5):
            image1 = Image.open("donothing.gif")
            test = ImageTk.PhotoImage(image1)
            label1 = tkinter.Label(image=test)
            label1.image = test

            # Position image
            label1.place(x=60, y=100)
            window.update_idletasks()
            window.update()
        
        # Wait the defined duration to allow influence to elapse
        time.sleep(60*int(duration))

        # Check results and play sound

        cursor.execute("select is_odd from sets where trial_id='" + str(trial_id) + "' and set_number=2 and run_number='" + str(loopcount) + "' ")
        is_odd = cursor.fetchone()

        # If influence even and result even
        if ((int(str(setmod6)[1:len(setmod6)-3]) == 0) or (int(str(setmod6)[1:len(setmod6)-3]) == 3)) and int(str(is_odd)[2:len(is_odd)-4])==0:
            playsound('correct.mp3')

        # If influence even and result odd    
        if ((int(str(setmod6)[1:len(setmod6)-3]) == 0) or (int(str(setmod6)[1:len(setmod6)-3]) == 3)) and int(str(is_odd)[2:len(is_odd)-4])==1:
            playsound('incorrect.mp3')

        # If influence odd and result odd    
        if ((int(str(setmod6)[1:len(setmod6)-3]) == 1) or (int(str(setmod6)[1:len(setmod6)-3]) == 4)) and int(str(is_odd)[2:len(is_odd)-4])==1:
            playsound('correct.mp3')     

        # If influence odd and result even  
        if ((int(str(setmod6)[1:len(setmod6)-3]) == 1) or (int(str(setmod6)[1:len(setmod6)-3]) == 4)) and int(str(is_odd)[2:len(is_odd)-4])==0:
            playsound('incorrect.mp3')     

        # If influence nothing      
        if ((int(str(setmod6)[1:len(setmod6)-3]) == 2) or (int(str(setmod6)[1:len(setmod6)-3]) == 5)):
            playsound('correct.mp3')     
         
        loopcount = loopcount + 1

    finalScreen()


# Display results
def finalScreen():

    for widget in window.winfo_children():
        widget.destroy()

    error = Message(text="Good job! All done.", width=600)
    error.place(x = 30, y = 10)
    error.config(padx=0)

    cursor.execute("""select count(*) 
        from sets""")
    setcount = cursor.fetchone()


    # even % x odd % by:
    # Unobserved, influence to even
    # Unobserved, influence to odd
    # Unobserved, no influence
    # Observed, influence to even
    # Observed, influence to odd
    # Observed, no influence

    # Unobserved, influence to even
    cursor.execute("""select count(*) 
        from sets s1 
        join sets s2 on s1.trial_id = s2.trial_id 
            and s1.run_number = s2.run_number        
        where s1.set_number = 1
        and s2.set_number = 2
        and s1.mod_6=0""")
    unobInfEven = cursor.fetchone()

    # Unobserved, influence to even, outcome even
    cursor.execute("""select count(*) 
        from sets s1 
        join sets s2 on s1.trial_id = s2.trial_id 
            and s1.run_number = s2.run_number        
        where s1.set_number = 1
        and s2.set_number = 2
        and s1.mod_6=0
        and s2.is_odd=0""")
    unobInfEven_Even = cursor.fetchone()

    # Unobserved, influence to odd
    cursor.execute("""select count(*) 
        from sets s1 
        join sets s2 on s1.trial_id = s2.trial_id 
            and s1.run_number = s2.run_number        
        where s1.set_number = 1
        and s2.set_number = 2
        and s1.mod_6=1""")
    unobInfOdd = cursor.fetchone()

    # Unobserved, influence to odd, outcome even
    cursor.execute("""select count(*) 
        from sets s1 
        join sets s2 on s1.trial_id = s2.trial_id 
            and s1.run_number = s2.run_number        
        where s1.set_number = 1
        and s2.set_number = 2
        and s1.mod_6=1
        and s2.is_odd=0""")
    unobInfOdd_Even = cursor.fetchone()

    # Unobserved, no influence
    cursor.execute("""select count(*) 
        from sets s1 
        join sets s2 on s1.trial_id = s2.trial_id 
            and s1.run_number = s2.run_number        
        where s1.set_number = 1
        and s2.set_number = 2
        and s1.mod_6=2""")
    unobNoInf = cursor.fetchone()  

    # Unobserved, no influence, outcome even
    cursor.execute("""select count(*) 
        from sets s1 
        join sets s2 on s1.trial_id = s2.trial_id 
            and s1.run_number = s2.run_number        
        where s1.set_number = 1
        and s2.set_number = 2
        and s1.mod_6=2
        and s2.is_odd=0""")
    unobNoInf_Even = cursor.fetchone()

    # Observed, influence to even
    cursor.execute("""select count(*) 
        from sets s1 
        join sets s2 on s1.trial_id = s2.trial_id 
            and s1.run_number = s2.run_number        
        where s1.set_number = 1
        and s2.set_number = 2
        and s1.mod_6=3""")
    obInfEven = cursor.fetchone()

    # Observed, influence to even, outcome even
    cursor.execute("""select count(*) 
        from sets s1 
        join sets s2 on s1.trial_id = s2.trial_id 
            and s1.run_number = s2.run_number        
        where s1.set_number = 1
        and s2.set_number = 2
        and s1.mod_6=3
        and s2.is_odd=0""")
    obInfEven_Even = cursor.fetchone()

   # Observed, influence to odd
    cursor.execute("""select count(*) 
        from sets s1 
        join sets s2 on s1.trial_id = s2.trial_id 
            and s1.run_number = s2.run_number        
        where s1.set_number = 1
        and s2.set_number = 2
        and s1.mod_6=4""")
    obInfOdd = cursor.fetchone()

    # Observed, influence to odd, outcome even
    cursor.execute("""select count(*) 
        from sets s1 
        join sets s2 on s1.trial_id = s2.trial_id 
            and s1.run_number = s2.run_number        
        where s1.set_number = 1
        and s2.set_number = 2
        and s1.mod_6=4
        and s2.is_odd=0""")
    obInfOdd_Even = cursor.fetchone()

   # Observed, no influence
    cursor.execute("""select count(*) 
        from sets s1 
        join sets s2 on s1.trial_id = s2.trial_id 
            and s1.run_number = s2.run_number        
        where s1.set_number = 1
        and s2.set_number = 2
        and s1.mod_6=5""")
    obNoInf = cursor.fetchone()

    # Observed, no influence, outcome even
    cursor.execute("""select count(*) 
        from sets s1 
        join sets s2 on s1.trial_id = s2.trial_id 
            and s1.run_number = s2.run_number        
        where s1.set_number = 1
        and s2.set_number = 2
        and s1.mod_6=5
        and s2.is_odd=0""")
    obNoInf_Even = cursor.fetchone()

    # To prevent division by zero errors    
    if int(str(unobInfEven)[1:len(unobInfEven)-3]) > 0 and int(str(unobInfOdd)[1:len(unobInfOdd)-3]) > 0 and int(str(unobNoInf)[1:len(unobNoInf)-3]) > 0 and int(str(obInfEven)[1:len(obInfEven)-3]) > 0 and int(str(obInfOdd)[1:len(obInfOdd)-3]) > 0 and int(str(obNoInf)[1:len(obNoInf)-3]) > 0:

        error = Message(text="Here are the overall stats for your database:", width=600)
        error.place(x = 30, y = 80)
        error.config(padx=0)

        error = Message(text="Total Runs", width=600)
        error.place(x = 300, y = 120)
        error.config(padx=0)

        error = Message(text="Percent Odd", width=600)
        error.place(x = 400, y = 120)
        error.config(padx=0)

        error = Message(text="Percent Even", width=600)
        error.place(x = 500, y = 120)
        error.config(padx=0)

        error = Message(text="Unobserved, Influence to Even", width=600)
        error.place(x = 50, y = 150)
        error.config(padx=0)

        error = Message(text=str(int(str(unobInfEven)[1:len(unobInfEven)-3])), width=600)
        error.place(x = 300, y = 150)
        error.config(padx=0)

        error = Message(text=str(int(str(unobInfEven_Even)[1:len(unobInfEven_Even)-3])/int(str(unobInfEven)[1:len(unobInfEven)-3])*100)[0:5], width=600)
        error.place(x = 400, y = 150)
        error.config(padx=0)

        error = Message(text=str(100-(int(str(unobInfEven_Even)[1:len(unobInfEven_Even)-3]))/(int(str(unobInfEven)[1:len(unobInfEven)-3]))*100)[0:5], width=600)
        error.place(x = 500, y = 150)
        error.config(padx=0)

        error = Message(text="Unobserved, Influence to Odd", width=600)
        error.place(x = 50, y = 180)
        error.config(padx=0)

        error = Message(text=str(int(str(unobInfOdd)[1:len(unobInfOdd)-3])), width=600)
        error.place(x = 300, y = 180)
        error.config(padx=0)

        error = Message(text=str(int(str(unobInfOdd_Even)[1:len(unobInfOdd_Even)-3])/int(str(unobInfOdd)[1:len(unobInfOdd)-3])*100)[0:5], width=600)
        error.place(x = 400, y = 180)
        error.config(padx=0)

        error = Message(text=str(100-(int(str(unobInfOdd_Even)[1:len(unobInfOdd_Even)-3]))/(int(str(unobInfOdd)[1:len(unobInfOdd)-3]))*100)[0:5], width=600)
        error.place(x = 500, y = 180)
        error.config(padx=0)

        error = Message(text="Unobserved, No Influence", width=600)
        error.place(x = 50, y = 210)
        error.config(padx=0)

        error = Message(text=str(int(str(unobNoInf)[1:len(unobNoInf)-3])), width=600)
        error.place(x = 300, y = 210)
        error.config(padx=0)

        error = Message(text=str(int(str(unobNoInf_Even)[1:len(unobNoInf_Even)-3])/int(str(unobNoInf)[1:len(unobNoInf)-3])*100)[0:5], width=600)
        error.place(x = 400, y = 210)
        error.config(padx=0)

        error = Message(text=str(100-(int(str(unobNoInf_Even)[1:len(unobNoInf_Even)-3]))/(int(str(unobNoInf)[1:len(unobNoInf)-3]))*100)[0:5], width=600)
        error.place(x = 500, y = 210)
        error.config(padx=0)

        error = Message(text="Observed, Influence to Even", width=600)
        error.place(x = 50, y = 240)
        error.config(padx=0)

        error = Message(text=str(int(str(obInfEven)[1:len(obInfEven)-3])), width=600)
        error.place(x = 300, y = 240)
        error.config(padx=0)

        error = Message(text=str(int(str(obInfEven_Even)[1:len(obInfEven_Even)-3])/int(str(obInfEven)[1:len(obInfEven)-3])*100)[0:5], width=600)
        error.place(x = 400, y = 240)
        error.config(padx=0)

        error = Message(text=str(100-(int(str(obInfEven_Even)[1:len(obInfEven_Even)-3]))/(int(str(obInfEven)[1:len(obInfEven)-3]))*100)[0:5], width=600)
        error.place(x = 500, y = 240)
        error.config(padx=0)

        error = Message(text="Observed, Influence to Odd", width=600)
        error.place(x = 50, y = 270)
        error.config(padx=0)

        error = Message(text=str(int(str(obInfOdd)[1:len(obInfOdd)-3])), width=600)
        error.place(x = 300, y = 270)
        error.config(padx=0)

        error = Message(text=str(int(str(obInfOdd_Even)[1:len(obInfOdd_Even)-3])/int(str(obInfOdd)[1:len(obInfOdd)-3])*100)[0:5], width=600)
        error.place(x = 400, y = 270)
        error.config(padx=0)

        error = Message(text=str(100-(int(str(obInfOdd_Even)[1:len(obInfOdd_Even)-3]))/(int(str(obInfOdd)[1:len(obInfOdd)-3]))*100)[0:5], width=600)
        error.place(x = 500, y = 270)
        error.config(padx=0)

        error = Message(text="Observed, No Influence", width=600)
        error.place(x = 50, y = 300)
        error.config(padx=0)

        error = Message(text=str(int(str(obNoInf)[1:len(obNoInf)-3])), width=600)
        error.place(x = 300, y = 300)
        error.config(padx=0)

        error = Message(text=str(int(str(obNoInf_Even)[1:len(obNoInf_Even)-3])/int(str(obNoInf)[1:len(obNoInf)-3])*100)[0:5], width=600)
        error.place(x = 400, y = 300)
        error.config(padx=0)

        error = Message(text=str(100-(int(str(obNoInf_Even)[1:len(obNoInf_Even)-3]))/(int(str(obNoInf)[1:len(obNoInf)-3]))*100)[0:5], width=600)
        error.place(x = 500, y = 300)
        error.config(padx=0)

    else:

        error = Message(text="Complete more runs before data summary is shown.", width=600)
        error.place(x = 30, y = 340)
        error.config(padx=0)


    error = Message(text="You can close this window when you're ready.", width=600)
    error.place(x = 30, y = 380)
    error.config(padx=0)

## Terminate database connection and end program

window.mainloop()
db.close()
