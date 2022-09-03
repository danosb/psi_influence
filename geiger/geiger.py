import serial

#ls -l /dev/cu.usb
ser = serial.Serial('/dev/cu.usbserial-A10K714O', 9600)

trial_count = 1
loop_count = 0
result=""

while True:

	while loop_count<trial_count:

		output = ser.read()


		if str(output)[3:6]=='x7f': #1
			loop_count = loop_count+1
			result="1"

		if str(output)[2:3]=='?': #2
			loop_count = loop_count+1
			result="2"

		if str(output)[3:6]!='x00': #ignore
			print(f'{result}, trial #{loop_count}')

	break



print(f'success')
 
#b'?'   --2
#b'\x00'  --ignore
#b'\x7f'   ---1