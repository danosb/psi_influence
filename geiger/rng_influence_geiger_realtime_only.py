# This uses geiger-generated numbers generated in real-time
# All results are combined into a single probability.
# That probability controls a line chart and also the pitch of an audio tone, giving real-time feedback.



# Everything is under this block in order to make multi-processing work 
if __name__ == '__main__': 
	import serial
	import tkinter
	from tkinter import *
	from PIL import Image, ImageTk
	import matplotlib.pyplot as plt
	import os
	import time
	import requests
	import threading
	import json
	from datetime import datetime
	from scipy.stats import binomtest
	import sqlite3
	import numpy as np
	from playsound import playsound
	import sqlite3
	import time
	import matplotlib.animation as animation
	import multiprocessing


	def realtime(number_minutes):

		global start, trial_number

		# Time dif
		start = datetime.now()
		end = datetime.now()
		diff = end - start
		diff_sec = diff.total_seconds() 

		trial_number = 0

		# Define connection to database
		conn1 = sqlite3.connect('db/database.db', check_same_thread=False )
		cursor = conn1.cursor()

		### Create database tables

		# Basic info about the trial. A trial is composed of multiple runs. Each run has four sets of numbers.
		cursor.execute('''CREATE TABLE IF NOT EXISTS trial(
			trial_number integer NOT NULL,
			datetime_initiated datetime NOT NULL,
			number_minutes integer
			)''')

		# Stores information for each run 
		cursor.execute('''CREATE TABLE IF NOT EXISTS run(
			is_prerun boolean,
			is_observed boolean,
			run_number integer,
			trial_number integer NOT NULL,
			sec_elapsed decimal,
			geiger_more_even boolean,
			geiger_hit_percent text,
			geiger_p_val text,
			FOREIGN KEY (trial_number) REFERENCES trial(trial_number)
			)''')

		# Stores information for each run 
		cursor.execute('''CREATE TABLE IF NOT EXISTS result(
			trial_number integer,
			sec_elapsed decimal,
			prob_all int,
			prob_obs int,
			prob_unobs int,
			prob_real int
			)''')

		# Retreive max trial number and set new trial number
		cursor.execute("select max(trial_number) from trial")

		max_trial = cursor.fetchone()

		if str(max_trial)=='(None,)':
			trial_number = 1
		else:
			trial_number = int(str(max_trial)[1:len(max_trial)-3]) + 1

		## Populate basic info of trial
		cursor.execute("INSERT INTO trial(trial_number,datetime_initiated,number_minutes)VALUES(?,?,?)",(trial_number,str(start),number_minutes))
		conn1.commit()


		#ls -l /dev/cu.usb
		ser = serial.Serial('/dev/cu.usbserial-A10K714O', 9600)

		is_observed = True
		is_prerun = False

		# Time dif
		end = datetime.now()
		diff = end - start
		diff_sec = diff.total_seconds() 

		run_number = 0
		geiger_more_even = False
		geiger_hits = 0

		# This creates a loop that listens for input from the geiger rng
		while True:

			while float(diff_sec) <= float(number_minutes*60):

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
				
				# update the end time for this run and get elapsed
				end = datetime.now()
				diff = end - start
				diff_sec = diff.total_seconds()

				# store resuls for geiger run
				cursor.execute("INSERT INTO run(run_number,trial_number, geiger_more_even, geiger_hit_percent, geiger_p_val, sec_elapsed, is_observed, is_prerun)VALUES(?,?,?,?,?,?,?,?)",(str(run_number),str(trial_number),geiger_more_even, str(int(geiger_hits)/int(run_number)), str(1-prob_geiger.pvalue), diff_sec, is_observed, is_prerun))
				conn1.commit()

				# code will show the database row for each run
				#cursor.execute("select * from run where run_number=? and trial_number=?", (str(run_number), str(trial_number)))
				#temp = cursor.fetchone()
				#print(f'DB for run: {temp}')

			break

		conn1.close

		# print(f'Real-time Results: {geiger_hits}/{run_number}, p={str(1-prob_geiger.pvalue)[0:4]}')

		#print(f'Thread 1 complete')

		return run_number

	def results():
		global start, run_count_all, hit_count_all, run_count_obs, hit_count_obs, run_count_unobs, hit_count_unobs 
		global run_count_real, hit_count_real, prob_all, prob_obs, prob_unobs, prob_real

		end = datetime.now()
		diff = end - start
		diff_sec = diff.total_seconds()

		while float(diff_sec) <= float(number_minutes*60+20):
			end = datetime.now()
			diff = end - start
			diff_sec = diff.total_seconds()

		# Define connection to database
		conn1 = sqlite3.connect('db/database.db', check_same_thread=False)
		cursor = conn1.cursor()

		playsound('mp3/trial_complete.mp3')


		print(f'')
		print(f'Overall: {str(hit_count_all)[1:len(hit_count_all)-3]}/{str(run_count_all)[1:len(run_count_all)-3]}, p={str(prob_all)[1:6]}') 
		print(f'')
		print(f'Trial complete. Please close the graph window.')
		print(f'')

		#print(f'Thread 3 complete')

	def animate(i):

		global xvar, yvar, prob_last, start, trial_number,run_count_all, hit_count_all, run_count_obs, hit_count_obs
		global run_count_unobs, hit_count_unobs, run_count_real, hit_count_real, freq_file, p1, p2
		global prob_all, prob_obs, prob_unobs, prob_real, freq_last_set, thread_killer_1, thread_killer_2

		end = datetime.now()
		diff = end - start
		diff_sec = diff.total_seconds()

		# Define connection to database
		conn1 = sqlite3.connect('db/database.db', check_same_thread=False)
		cursor = conn1.cursor()

		cursor.execute("select count(*) from run where trial_number=?1 and sec_elapsed<?2", [trial_number, diff_sec])
		run_count_all = cursor.fetchone()

		cursor.execute("select count(*) from run where trial_number=?1 and sec_elapsed<?2 and geiger_more_even=True", [trial_number, diff_sec])
		hit_count_all = cursor.fetchone()


		# calculate p-values
		if int(str(hit_count_all)[1:len(hit_count_all)-3]) > 0:
			prob_all_raw=binomtest(int(str(hit_count_all)[1:len(hit_count_all)-3]), int(str(run_count_all)[1:len(run_count_all)-3]), 0.5, alternative='greater')
			prob_all = 1-prob_all_raw.pvalue
		else:
			prob_all = 0

		end = datetime.now()
		diff = end - start
		diff_sec = diff.total_seconds()

		if float(prob_last) != float(prob_all):
			# print(f'Sec:{diff_sec}, Prob:{prob_all}')
			xvar.append(diff_sec)
			yvar.append(prob_all)
			ax1.clear()
			ax1.plot(xvar,yvar)
		
			# Insert overall results into result table
			cursor.execute("INSERT INTO result(trial_number,sec_elapsed,prob_all )VALUES(?,?,?)",(trial_number,diff_sec,prob_all))
			conn1.commit()


			# Play sound corresponding to overall probability
			  
			if prob_all > 0 and len(str(round((prob_all) * 100)))==2:
				freq_file = 'mp3/1' + str(round((prob_all) * 100)) + 'Hz.mp3'
			elif prob_all > 0 and len(str(round((prob_all) * 100)))==1:
				freq_file = 'mp3/10' + str(round((prob_all) * 100)) + 'Hz.mp3'
			else: 
				freq_file = 'mp3/100Hz.mp3'

			# First run
			if freq_last_set == 0:

				p1 = multiprocessing.Process(target=playsound, args=(freq_file,))
				p1.start()
				freq_last_set = 1

			elif freq_last_set == 1:

				p2 = multiprocessing.Process(target=playsound, args=(freq_file,))
				p2.start()
				time.sleep(.5)
				p1.terminate()

				freq_last_set = 2
				
			# else it equals 2
			else:

				p1 = multiprocessing.Process(target=playsound, args=(freq_file,))
				p1.start()
				time.sleep(.5)
				p2.terminate()

				freq_last_set = 1


		prob_last = prob_all

		conn1.close


	# Set defaults, mostly for global variables
	number_minutes = 10
	trial_number = 0 
	unobserved_run_count = 0
	prob_last = 0.0
	run_count_all = 0
	hit_count_all = 0
	prob_all = 0.0
	freq_last_set = 0
	sound_number = 0
	p1 = multiprocessing.Process(target=playsound, args=('mp3/100Hz.mp3',))
	p2 = multiprocessing.Process(target=playsound, args=('mp3/100Hz.mp3',))
	print(f'')
	print(f'')
	print(f'Your task is to increase the height of the line')
	print(f'and/or the pitch of the sound of the third group.')
	print(f'')
	print(f'This trial will last a little over {number_minutes} minutes.')
	print(f'')
	try:
		input("Press enter to begin...")

	except SyntaxError:
		pass
	print(f'Kicking off...')

	# Set start time
	start = datetime.now()

	# Thread 1:
	t1 = threading.Thread(target=realtime, args=(number_minutes,))
	t1.start()

	# Thread 3:
	t3 = threading.Thread(target=results, args=( ))
	t3.start()


	# Initiate graph
	fig = plt.figure()			
	plt.title('Group results combined - Seconds vs. Probability (0-1)')

	# Need to hide these, otherwise the animation duplicates
	plt.xticks([])
	plt.yticks([])

	ax1 = fig.add_subplot(111)

	xvar = []
	yvar = []

	# This will loop the animate function -> interval * frames
	ani = animation.FuncAnimation(fig, animate, interval=100,frames = int(number_minutes*600), repeat = False)
	plt.show()

	p1.terminate()
	p2.terminate()
