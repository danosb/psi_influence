# We have three methods of generating random numbers. 
# The primary one will always be the Geiger counter. The other two may also be optionally enabled.
# Geiger controls the success rate but others can be enabled for comparison
# Each trial consists of one or more runs
# Audio signals for hits/misses and pictures displayed for trial outcome

import serial
import tkinter
from tkinter import *
from PIL import Image, ImageTk
import os
import time
import requests
import json
from datetime import datetime
from scipy.stats import binomtest
import sqlite3
import numpy as np
from playsound import playsound
with sqlite3.connect("db/database.db") as db:
	cursor=db.cursor()
import time



def main_func():

	number_minutes = 150

	# choose whether to generate numbers with other sources beyond Geiger
	vacuum_enabled = False
	trurng_enabled = True

	subject_name = "Dan"

	print(f'')
	print(f'Make TWOs and not ONEs. You have a little over {number_minutes} minute(s).')

	try:
		input("Press enter to begin...")
	except SyntaxError:
		pass

	print(f'')

	#ls -l /dev/cu.usb
	ser = serial.Serial('/dev/cu.usbserial-A10K714O', 9600)

	start = datetime.now()
	end = datetime.now()
	datetime_delta = end - start
	seconds_elapsed = datetime_delta.total_seconds()

	trial_number = 0

	### Create database tables

	# Basic info about the trial. A trial is composed of multiple runs. Each run has four sets of numbers.
	cursor.execute('''CREATE TABLE IF NOT EXISTS trial(
		trial_number integer NOT NULL,
		datetime_initiated datetime NOT NULL,
		number_minutes integer,
		vacuum_enabled boolean,
		trurng_enabled boolean,
		subject_name text 
		)''')

	# Stores information for each run 
	cursor.execute('''CREATE TABLE IF NOT EXISTS run(
		datetime_initiated datetime NOT NULL,
		run_number integer,
		trial_number integer NOT NULL,
		geiger_more_even boolean,
		geiger_hit_percent text,
		geiger_p_val text,
		vacuum_more_even boolean,
		vacuum_hit_percent text,
		vacuum_p_val text,
		trurng_more_even boolean,
		trurng_hit_percent text,
		trurng_p_val text,
		vacuum_raw_data text,
		trurng_raw_data text,
		FOREIGN KEY (trial_number) REFERENCES trial(trial_number)
		)''')


	# Retreive max trial number and set new trial number
	cursor.execute("select max(trial_number) from trial")

	max_trial = cursor.fetchone()

	if str(max_trial)=='(None,)':
		trial_number = 1
	else:
		trial_number = int(str(max_trial)[1:len(max_trial)-3]) + 1

	## Populate basic info of trial
	cursor.execute("INSERT INTO trial(trial_number,datetime_initiated,number_minutes,vacuum_enabled,trurng_enabled,subject_name)VALUES(?,?,?,?,?,?)",(trial_number,str(start),number_minutes,vacuum_enabled,trurng_enabled,subject_name))
	db.commit()



	run_number = 0
	geiger_more_even = False
	vacuum_more_even = False
	trurng_more_even = False
	geiger_hits = 0
	vacuum_hits = 0
	trurng_hits = 0

	# This creates a loop that listens for input from the geiger rng
	while True:

		while int(seconds_elapsed) <= (number_minutes*60):

			geiger_read = ser.read()
			geiger_more_even = False
			run_start = datetime.now()

			if str(geiger_read)[3:6] == 'x01': #1
				run_number = run_number + 1

			if str(geiger_read)[3:6] == 'x02': #2
				run_number = run_number + 1
				geiger_hits = geiger_hits + 1
				geiger_more_even = True


			prob_geiger=binomtest(int(geiger_hits), int(run_number), 0.5, alternative='greater')
			
			# store resuls for geiger run
			cursor.execute("INSERT INTO run(run_number,trial_number, datetime_initiated,geiger_more_even, geiger_hit_percent, geiger_p_val)VALUES(?,?,?,?,?,?)",(str(run_number),str(trial_number), str(run_start),str(geiger_more_even), str(int(geiger_hits)/int(run_number)), str(prob_geiger.pvalue)))
			db.commit()

			if vacuum_enabled == True:
				vacuum_more_even = vacuum(run_number, trial_number)

				cursor.execute("select count(*) from run where vacuum_more_even='True' and trial_number=?", [trial_number])
				vacuum_hits = cursor.fetchone()
				
				prob_vacuum=binomtest(int(str(vacuum_hits)[1:len(vacuum_hits)-3]), int(run_number), 0.5, alternative='greater')

				cursor.execute("UPDATE run SET vacuum_hit_percent=?, vacuum_p_val=? WHERE run_number=? and trial_number=?", (str(int(str(vacuum_hits)[1:len(vacuum_hits)-3])/run_number), str(prob_vacuum.pvalue), str(run_number), str(trial_number)))
				db.commit()   

			if trurng_enabled == True:
				trurng_more_even = trurng(run_number, trial_number)
				
				cursor.execute("select count(*) from run where trurng_more_even='True' and trial_number=?", [trial_number])
				trurng_hits = cursor.fetchone()

				prob_trurng=binomtest(int(str(trurng_hits)[1:len(trurng_hits)-3]), int(run_number), 0.5, alternative='greater')
				
				cursor.execute("UPDATE run SET trurng_hit_percent=?, trurng_p_val=? WHERE run_number=? and trial_number=?", (str(int(str(trurng_hits)[1:len(trurng_hits)-3])/run_number), str(prob_trurng.pvalue), str(run_number), str(trial_number)))
				db.commit()  


			print(f'Run:{run_number}')


			# code will show the database row for each run
			#cursor.execute("select * from run where run_number=? and trial_number=?", (str(run_number), str(trial_number)))
			#temp = cursor.fetchone()
			#print(f'DB for run: {temp}')

			if str(geiger_read)[3:6] == 'x01': #1
				playsound('mp3/incorrect.mp3')

			if str(geiger_read)[3:6] == 'x02': #2
				playsound('mp3/correct.mp3')

			print(f' Geiger:{geiger_more_even} ({geiger_hits}/{run_number}). Overall p={str(prob_geiger.pvalue)[0:4]}')

			if vacuum_enabled == True:
				print(f' Vacuum:{vacuum_more_even} ({str(vacuum_hits)[1:len(vacuum_hits)-3]}/{run_number}). Overall p={str(prob_vacuum.pvalue)[0:4]}') 

			if trurng_enabled == True:
				print(f' TruRNG:{trurng_more_even} ({str(trurng_hits)[1:len(trurng_hits)-3]}/{run_number}). Overall p={str(prob_trurng.pvalue)[0:4]}')

			#time.sleep(1)

			end = datetime.now()
			datetime_delta = end - start
			seconds_elapsed = datetime_delta.total_seconds()

		break

	print(f'')
	print(f'We want probability (p) below 0.05 for Geiger at least (all if possible).')

	prob_geiger_pvalue = str(prob_geiger.pvalue)

	tkwindow(prob_geiger_pvalue)


# Creates a window with the result
def tkwindow(prob_geiger_pvalue):
	
	if float(prob_geiger_pvalue)<=0.05:
		
		window = Tk()
		window.geometry("600x600")
		window.title("Quantum Influence Experiment")

		image1 = Image.open("gif/successnew.gif")
		test = ImageTk.PhotoImage(image1)
		label1 = tkinter.Label(image=test)
		label1.image = test

		# Position image
		label1.place(x=0, y=0)
		window.update_idletasks()
		window.update()

		error = Message(text="The goal is Geiger probability (p) less than or equal to 0.05 ", width=600)
		error.place(x = 15, y = 5)
		error.config(padx=0)

		error = Message(text="Gieger probability result is " + str(prob_geiger_pvalue) + ". You did it!!!", width=600)
		error.place(x = 15, y = 45)
		error.config(padx=0)

		error = Message(text="Please close this window.", width=600)
		error.place(x = 15, y = 565)
		error.config(padx=0)

		playsound('trial_complete.mp3')
		time.sleep(.3)
		print(f'SUCCESS! Great job!')
		playsound('mp3/success.mp3')

	else:

		window = Tk()
		window.geometry("600x600")
		window.title("Quantum Influence Experiment")

		image1 = Image.open("gif/failnew.gif")
		test = ImageTk.PhotoImage(image1)
		label1 = tkinter.Label(image=test)
		label1.image = test

		 # Position image
		label1.place(x=0, y=0)
		window.update_idletasks()
		window.update()

		error = Message(text="The goal is Geiger probability (p) less than or equal to 0.05 ", width=600)
		error.place(x = 15, y = 5)
		error.config(padx=0)

		error = Message(text="Gieger probability result is " + str(prob_geiger_pvalue) + ". Better luck next time.", width=600)
		error.place(x = 15, y = 45)
		error.config(padx=0)

		error = Message(text="Please close this window.", width=600)
		error.place(x = 15, y = 565)
		error.config(padx=0)


		playsound('mp3/trial_complete.mp3')
		time.sleep(.3)
		print(f'Better luck next time..')
		playsound('mp3/better_luck.mp3')

	print(f'Please close the window.')
	window.mainloop()


# This function retrieves measurements of the quantum vacuum via API
def vacuum(run_number, trial_number):

	# authentication
	my_headers = {'x-api-key' : '**redacted**'}

	# Set 1 with sum and module 6 
	response = requests.get('https://api.quantumnumbers.anu.edu.au?length=1024&type=uint8', headers=my_headers)
	response_dict=json.loads(response.content)
	apiresults = np.array(response_dict['data'])

	count_total = 0
	count_two = 0
	count_one = 0
	more_even = False
	results_string = ""

	# We will only count entries that end in either 1s or 2s
	for x in apiresults:

		if x%10 == 1:
			count_one = count_one + 1

		if x%10 == 2:
			count_two = count_two + 1
			
		if x%10 == 1 or x%10 == 2:
			count_total = count_total + 1
			results_string = results_string + ' ' + str(x)

	if count_two / count_total >= 0.5:
		more_even = True # we also include if number of even is same as number of odd

	# Populate vacuum data for this run
	cursor.execute("UPDATE run SET vacuum_raw_data=?, vacuum_more_even=? WHERE run_number=? and trial_number=?", (str(results_string), str(more_even), str(run_number), str(trial_number)))
	db.commit()   

	return more_even



# This function retrieves random numbers from the TruRNG hardware device
def trurng(run_number, trial_number):

	# cat /dev/cu.usbmodem [tab]
	os.system('dd if=/dev/cu.usbmodem14401 of=/Users/Admin/Downloads/random.txt bs=640 count=640 &> /dev/null &')

	with open('/Users/Admin/Downloads/random.txt', 'rb', buffering=0) as file:
		contents = file.read()

	count_two = 0
	count_total = 0
	more_even = False
	all_decoded = ""

	loopcount = 0

	# We will only count entries that are either 1s or 2s
	for content in contents:

		if chr(content) == '1' or chr(content) == '2':
			count_total = count_total + 1
			loopcount += 1
			all_decoded = all_decoded + chr(content)

		if chr(content) == '2':
			count_two = count_two + 1

	if count_two / loopcount >= 0.5:
		more_even = True # we also include if number of even is same as number of odd

	# Populate vacuum data for this run
	cursor.execute("UPDATE run SET trurng_raw_data=?, trurng_more_even=? WHERE run_number=? and trial_number=?", (str(all_decoded), str(more_even), str(run_number), str(trial_number)))

	db.commit()   

	return more_even


main_func()

print(f'')

db.close()

