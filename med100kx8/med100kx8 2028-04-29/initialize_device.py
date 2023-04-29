# Connects to the hardware device and retrieves sets supertrial number
import sys
from pyftdi.ftdi import Ftdi
import os

# Device communication parameters
FTDI_DEVICE_LATENCY_MS = 2
FTDI_DEVICE_PACKET_USB_SIZE = 8
FTDI_DEVICE_TX_TIMEOUT = 5000

def initialize_device(serial_number)

    supertrial = 0

    if not serial_number:
        print("%%%% device not found!")
        return None

    # print("deviceId:", serial_number, "\n")
    ftdi = Ftdi()
    ftdi.open_from_url(f"ftdi://ftdi:232:{serial_number}/1")
    ftdi.set_latency_timer(FTDI_DEVICE_LATENCY_MS)
    ftdi.write_data_get_chunksize = lambda x: FTDI_DEVICE_PACKET_USB_SIZE
    ftdi.read_data_get_chunksize = lambda x: FTDI_DEVICE_PACKET_USB_SIZE

    return ftdi