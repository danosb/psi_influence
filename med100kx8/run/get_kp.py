# The Kp index, also known as the Kp geomagnetic index, is a measurement of the global geomagnetic activity level. It quantifies the disturbances in the Earth's magnetic field caused by solar activity, specifically related to coronal mass ejections (CMEs) and solar flares.
# Details of this data are contained at the URL included below.

import urllib.request
import datetime

def get_kp():
    url = "https://www-app3.gfz-potsdam.de/kp_index/Kp_ap_Ap_SN_F107_nowcast.txt"
    response = urllib.request.urlopen(url)
    lines = response.read().decode('utf-8').split('\n')

    current_time = datetime.datetime.utcnow()
    current_hour = current_time.hour
    current_day = current_time.day
    current_month = current_time.month

    # Determine the most recently completed 3 hour period
    completed_hour_block = current_hour // 3 if current_hour != 0 else 7

    index_dict = {
        'Kp': [(33 + 7*i, 39 + 7*i) for i in range(8)],
        'ap': [(89 + 5*i, 93 + 5*i) for i in range(8)]
    }

    values_dict = {
        'month': '',
        'day': '',
        'BSR': '',
        'Kp': '',
        'ap': '',
        'Ap': '',
        'SN': '',
        'F10.7obs': '',
        'F10.7adj': ''
    }

    for line in reversed(lines):
        if line.startswith('#'):
            continue
        else:
            month = line[5:7].strip()
            day = line[8:10].strip()
            
            if month and day:
                if int(month) <= current_month and int(day) <= current_day:
                    BSR = line[25:29].strip()
                    if BSR != '-1.0' and values_dict['BSR'] == '':
                        values_dict['BSR'] = BSR

                    for key in ['Kp', 'ap']:
                        for i in range(completed_hour_block, -1, -1):
                            value = line[index_dict[key][i][0]:index_dict[key][i][1]].strip()
                            if value and float(value) != -1.0 and values_dict[key] == '':
                                values_dict[key] = value
                                break

                    Ap = line[130:134].strip()
                    if Ap  and values_dict['Ap'] == '':
                        values_dict['Ap'] = Ap

                    SN = line[135:138].strip()
                    if SN and values_dict['SN'] == '':
                        values_dict['SN'] = SN

                    F107obs = line[139:147].strip()
                    if F107obs and float(F107obs) != -1.0 and values_dict['F10.7obs'] == '':
                        values_dict['F10.7obs'] = F107obs

                    F107adj = line[148:156].strip()
                    if F107adj and float(F107adj) != -1.0 and values_dict['F10.7adj'] == '':
                        values_dict['F10.7adj'] = F107adj

                    # If all values are filled, break the loop
                    if all(value != '' for value in values_dict.values()):
                        break

            # Update day and month values
            if month: values_dict['month'] = month
            if day: values_dict['day'] = day

    print(values_dict)
    
    
    return values_dict['Kp'], values_dict['BSR'], values_dict['Ap'], values_dict['Ap'], values_dict['SN'], values_dict['F10.7obs'], values_dict['F10.7adj']
