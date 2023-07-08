from pyftdi.ftdi import Ftdi
import os


def list_devices():
    ftdi = Ftdi.create_from_url('ftdi:///?')
    ftdi.open()
    ftdi.show_devices()

if __name__ == "__main__":
    list_devices()
