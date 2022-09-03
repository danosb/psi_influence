# user tries to make more zeros only. 

import os
from scipy.stats import binomtest

test_count=10000
test_loop=0
overall_count_zero=0
overall_count=0

while test_loop<test_count:

    # cat /dev/cu.usbmodem [tab]
    os.system('dd if=/dev/cu.usbmodem14201 of=/Users/Admin/Downloads/random.txt bs=640 count=640 &> /dev/null &')

    with open('/Users/Admin/Downloads/random.txt', 'rb', buffering=0) as file:
        contents = file.read()

    loopcount = 0

    for content in contents:

        loopcount += 1

        if chr(content)=='0':
            overall_count_zero = overall_count_zero + 1

        if content !=0 :
            overall_count = overall_count + 1 

    
    prob_count=binomtest(int(overall_count_zero), int(overall_count), 0.00392156862, alternative='greater')

    test_loop =test_loop + 1

    if test_loop % 100 == 0:
        print(f'{test_loop}/{test_count} - Count zeros: {overall_count_zero}/{overall_count}, {str((overall_count_zero/overall_count)*100)[0:5]}% zero. {str(float((prob_count.pvalue))*100)[:5]}% chance.') 
        

    file.close()
