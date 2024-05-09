from pyftdi.ftdi import Ftdi

def list_devices():
    ftdi = Ftdi()
    ftdi.show_devices()

if __name__ == "__main__":
    list_devices()