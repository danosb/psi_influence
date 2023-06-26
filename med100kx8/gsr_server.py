# this should run on a Raspberry pi server. It allows for pulling of Galvanic Skin Response (GSR) data from https://wiki.seeedstudio.com/Grove-GSR_Sensor/

import sys
import time
from flask import Flask, Response
from grove.adc import ADC


# run with python gsr_server.py 0 

class GroveGSRSensor:
    def __init__(self, channel):
        self.channel = channel
        self.adc = ADC()

    @property
    def GSR(self):
        value = self.adc.read(self.channel)
        return value

app = Flask(__name__)

@app.route('/gsr')
def stream_gsr():
    if len(sys.argv) < 2:
        return "Usage: {} adc_channel".format(sys.argv[0]), 400

    def read_gsr():
        sensor = GroveGSRSensor(int(sys.argv[1]))
        while True:
            yield 'data: {}\n\n'.format(sensor.GSR)
            time.sleep(1)

    return Response(read_gsr(), mimetype='text/event-stream')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: {} adc_channel'.format(sys.argv[0]))
        sys.exit(1)

    app.run(host='0.0.0.0', port=5000)