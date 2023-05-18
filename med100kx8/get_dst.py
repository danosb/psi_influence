# Returns real-time Dst index
# The Solar DST (Solar Dst Index) is a measure of the disturbance level in the Earth's magnetosphere caused by solar wind variations. It is used to quantify the intensity of geomagnetic storms and their effects on Earth's magnetic field. The Solar DST index is derived from measurements of the Earth's magnetic field at various locations around the world and provides a numerical value that represents the strength of the disturbance.

import requests
import datetime
from pytz import timezone

def get_dst():
    url = "https://wdc.kugi.kyoto-u.ac.jp/dst_realtime/presentmonth/dst2305.for.request"

    response = requests.get(url)
    data = response.text.split('\n')

    now = datetime.datetime.now(timezone('UTC'))
    current_hour = now.hour
    current_day = now.day

    if current_hour == 0:
        if current_day == 1:
            raise ValueError("Data for current time is not available")
        else:
            current_hour = 24
            current_day -= 1

    # Mapping of hour to start position in the row
    index_dict = {
        1: 20, 2: 24, 3: 28, 4: 32, 5: 36, 6: 40, 7: 44, 8: 48, 9: 52, 10: 56, 
        11: 60, 12: 64, 13: 68, 14: 72, 15: 76, 16: 80, 17: 84, 18: 88, 19: 92, 
        20: 96, 21: 100, 22: 104, 23: 108, 24: 112
    }

    # Get start and end position for value
    start = index_dict[current_hour]
    end = start + 4

    # Read values
    for row in data:
        day_str = row[8:10]

        # Check if the day string is valid integer
        try:
            day = int(day_str)
        except ValueError:
            continue

        if day == current_day:
            value = row[start:end].strip()
            # print(f"The value for hour {current_hour} on day {current_day} is {value}")
            break
            
    return value
