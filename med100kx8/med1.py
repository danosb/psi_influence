## Reads random numbers from the MED100Kx8 hardware device and runs  Scott Wilber's Randon Walk Amplification Bias (RWBA) alrogithm against the results.
# https://drive.google.com/file/d/1ASvbdI-uQs_4HNL3fh85g72mIRndkjdn/view

import sys
from pyftdi.ftdi import Ftdi
import math

FTDI_DEVICE_LATENCY_MS = 2
FTDI_DEVICE_PACKET_USB_SIZE = 8
FTDI_DEVICE_TX_TIMEOUT = 5000
n = 31 # defined bound

# Hard-code the empirically-generated values, for now.
N_CDF_vals = [(29, 0.0), (31, 4.6566e-10), (43, 2.5e-7), (55, 0.0000125), (65, 0.000099), (79, 0.00058575), (93, 0.00190025), (105, 0.0039455), (107, 0.0043945), (121, 0.008407), (141, 0.01659625), (149, 0.02066175), (165, 0.030027), (181, 0.04097325), (193, 0.050018), (205, 0.0596295), (217, 0.06968525), (229, 0.08007275), (241, 0.0908285), (251, 0.1000605), (263, 0.11127425), (273, 0.12071075), (283, 0.13028675), (293, 0.13996), (303, 0.14965975), (313, 0.159455), (323, 0.169184), (335, 0.1807995), (345, 0.19049125), (355, 0.20016375), (365, 0.2098285), (377, 0.2213085), (387, 0.230712), (397, 0.240088), (407, 0.2494425), (419, 0.26057975), (429, 0.26976425), (441, 0.280628), (451, 0.28950875), (463, 0.30000425), (475, 0.31068675), (487, 0.32107725), (497, 0.3295655), (509, 0.339624), (521, 0.34972), (533, 0.35958), (545, 0.36930075), (547, 0.37091775), (559, 0.38047775), (571, 0.38994775), (585, 0.40080525), (597, 0.4099845), (611, 0.4205175), (625, 0.43086725), (637, 0.43958075), (653, 0.45089025), (667, 0.46073875), (681, 0.470314), (695, 0.47976625), (711, 0.490367), (727, 0.50069425), (741, 0.50964775), (759, 0.52087975), (775, 0.53063475), (791, 0.54031025), (809, 0.55084375), (825, 0.55995425), (843, 0.57005225), (861, 0.57994375), (881, 0.59072425), (899, 0.6000415), (919, 0.61021475), (939, 0.620246), (959, 0.62984475), (981, 0.64021725), (1003, 0.6502895), (1025, 0.66007175), (1049, 0.670426), (1073, 0.68044825), (1097, 0.690253), (1123, 0.700487), (1149, 0.710324), (1175, 0.7198345), (1205, 0.7198345), (1233, 0.73038025), (1263, 0.73999), (1295, 0.74984525), (1329, 0.7599175), (1363, 0.770246), (1399, 0.78015725), (1437, 0.79014875), (1475, 0.80026), (1517, 0.80978925), (1563, 0.8198905), (1609, 0.830206), (1659, 0.83999175), (1713, 0.85001525), (1771, 0.8600645), (1831, 0.870173), (1899, 0.87985925), (1973, 0.8899505), (2055, 0.89991075), (2147, 0.9100075), (2251, 0.92004975), (2371, 0.93005225), (2513, 0.9400265), (2685, 0.95003225), (2909, 0.95996375), (3221, 0.97001825), (3757, 0.9800235), (4293, 0.99000575), (4691, 0.99499475), (5005, 0.99700025), (5543, 0.998001), (6081, 0.99900225), (6463, 0.99950225), (6789, 0.9997005), (7341, 0.99980025), (7861, 0.9999), (8247, 0.99995), (9141, 0.99997), (9647, 0.99999), (10057, 0.999995), (10995, 0.999997), (11807, 0.999999) ]


def device_startup(serial_number):
    if not serial_number:
        print("%%%% device not found!")
        return None

    print("deviceId:", serial_number, "\n")
    ftdi = Ftdi()
    ftdi.open_from_url(f"ftdi://ftdi:232:{serial_number}/1")
    ftdi.set_latency_timer(FTDI_DEVICE_LATENCY_MS)
    ftdi.write_data_get_chunksize = lambda x: FTDI_DEVICE_PACKET_USB_SIZE
    ftdi.read_data_get_chunksize = lambda x: FTDI_DEVICE_PACKET_USB_SIZE

    return ftdi


def device_shutdown(ftdi):
    ftdi.close()


# Performs random walk to determine number_steps
def random_walk_steps(ftdi):
    bidirectional_count = 0
    bidirectional_is_pos = False
    number_steps = 0
    numbers_generated = []

    # Goes through each digit from left to right and evaluates whether that digit is a 1 or a 0. If the digit is not a one or a zero then ignore it and move to the next digit. we will keep a counter as we iterate through the digits, called bidirectional_count
    while abs(bidirectional_count) < n:
        # Request a new random number. We get as many we need in order to reach the bound.
        init_comm = b'\x96'
        ftdi.purge_buffers()
        bytes_txd = ftdi.write_data(init_comm)

        if bytes_txd != len(init_comm):
            print("%%%% Write Failed!")
            sys.exit(-1)

        bytes_to_rx = 8
        dx_data = ftdi.read_data(bytes_to_rx)

        if len(dx_data) != bytes_to_rx:
            print("%%%% Read Failed!")
            sys.exit(-1)

        received_int = int.from_bytes(dx_data, "big") # Stores the int value
        numbers_generated.append(received_int) # Adds int value to an array
        binary_version = bin(received_int)[2:] # Converts the int version to binary

        # Process the binary version of the random number. Goes through each digit from left to right and evaluates whether that digit is a 1 or a 0. 
        # If an analyzed digit is a 1, then we we add 1 to the bidirectional_count. If it's a 0 then we subtract one.
        for digit in binary_version:
            if digit == '1':
                bidirectional_count += 1
            elif digit == '0':
                bidirectional_count -= 1
       #  Keeps track of how many digits are analyzed.
            if digit in ('0', '1'):
                number_steps += 1
            # Stop when the absolute value of bidirectional_count reaches our defined "n" value.
            if abs(bidirectional_count) == n:
                if(bidirectional_count) < 0:
                    bidirectional_is_pos = True
                break

    return numbers_generated, bidirectional_count, number_steps, bidirectional_is_pos

# Compute various variables as a result of getting random walk outcomes.
def interop(number_steps):
    
    # Find x1, y1, x2, y2, x3, and y3 by checking for the first x-value greater than or equal to number_steps
    for i, (x, _) in enumerate(N_CDF_vals):
        if x >= number_steps:
            x3, y3 = N_CDF_vals[i]
            x2, y2 = N_CDF_vals[i - 1]
            x1, y1 = N_CDF_vals[i - 2]
            break

    # Compute a, b, c
    a = (x2 * (x2 - x3) * x3 * y1 + x1 * x3 * (x3 - x1) * y2 + x1 * (x1 - x2) * x2 * y3) / ((x1 - x2) * (x1 - x3) * (x2 - x3))
    b = (x3**2 * (y1 - y2) + x1**2 * (y2 - y3) + x2**2 * (y3 - y1)) / ((x1 - x2) * (x1 - x3) * (x2 - x3))
    c = (x3 * (y2 - y1) + x2 * (y1 - y3) + x1 * (y3 - y2)) / ((x1 - x2) * (x1 - x3) * (x2 - x3))

    # Calculate CDF_calculated
    CDF_calculated = a + b * number_steps + c * (number_steps**2)

    # Calculate SV
    SV = math.log2(1 / CDF_calculated)

    return x1, x2, x3, y1, y2, y3, a, b, c, CDF_calculated, SV


def main():
    serial_number = "QWR4E010"  # Replace with your serial number
    ftdi = device_startup(serial_number)

    if not ftdi:
        input("Press any key to exit.")
        sys.exit(-1)

    # Perform random walk
    numbers_generated, bidirectional_count, number_steps, bidirectional_is_pos = random_walk_steps(ftdi)

    # Compute variables
    x1, x2, x3, y1, y2, y3, a, b, c, CDF_calculated, SV = interop(number_steps)

    print("Numbers generated (int): ", numbers_generated)
    print("Bidirectional count: ", bidirectional_count)
    print("Bidirectional positive?: ", bidirectional_is_pos)
    print("Number of steps: ", number_steps)
    print(f"x1,y1: ",{x1},",",{y1})
    print(f"x2,y2: ",{x2},",",{y2})
    print(f"x3,y3: ",{x3},",",{y3})
    print(f"a: ",{a})
    print(f"b: ",{b})
    print(f"c: ",{c})
    print(f"CDF (p) calculated: ",{CDF_calculated})
    print(f"Surprisal Value (SV): ",{SV})

    device_shutdown(ftdi)


if __name__ == "__main__":
    main()