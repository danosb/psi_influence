# 
# Uses TruRNGv3 random number generator
# Very basic program here that uses no pictures or sounds, just loops through..
# ..grabbing large sets of numbers and calculating probabilities

import os
from scipy.stats import binomtest

test_count=10000
test_loop=0
sets_even=0
sets_odd=0
overall_count_even=0
overall_count_odd=0

while test_loop<test_count:

    # cat /dev/cu.usbmodem [tab]
    os.system('dd if=/dev/cu.usbmodem14201 of=/Users/Admin/Downloads/random.txt bs=640 count=640 &> /dev/null &')

    with open('/Users/Admin/Downloads/random.txt', 'rb', buffering=0) as file:
        contents = file.read()

    set_count_even = 0
    set_count_odd = 0
    loopcount = 0

    for content in contents:
        loopcount += 1
        if chr(content)=='0' or chr(content)=='2' or chr(content)=='4' or chr(content)=='6' or chr(content)=='8':
            set_count_even = set_count_even + 1
            overall_count_even = overall_count_even + 1

        if chr(content)=='1' or chr(content)=='3' or chr(content)=='5' or chr(content)=='7' or chr(content)=='9':
            set_count_odd = set_count_odd + 1
            overall_count_odd = overall_count_odd + 1

    #print(f'Count even: {count_even}, Count odd: {count_odd}. Percent even: {str((count_even/(count_odd+count_even))*100)[0:5]}') 

    if set_count_even > set_count_odd:
        sets_even = sets_even + 1

    if set_count_even < set_count_odd:
        sets_odd = sets_odd + 1

    prob_set=binomtest(int(sets_even), int(sets_even+sets_odd), 0.5, alternative='greater')
    prob_count=binomtest(int(overall_count_even), int(overall_count_even+overall_count_odd), 0.5, alternative='greater')

    test_loop =test_loop + 1

    if test_loop % 100 == 0:
        print(f'{test_loop} - Sets even: {sets_even}, Sets odd: {sets_odd}. {str((sets_even/(sets_odd+sets_even))*100)[0:5]}% even. {str(float((prob_set.pvalue))*100)[:5]}% chance.') 
        print(f'{test_loop} - Count even: {overall_count_even}, Count odd: {overall_count_odd}. {str((overall_count_even/(overall_count_odd+overall_count_even))*100)[0:5]}% even. {str(float((prob_count.pvalue))*100)[:5]}% chance.') 
        

    file.close()
