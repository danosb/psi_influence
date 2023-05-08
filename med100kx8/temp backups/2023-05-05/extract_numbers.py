import queue
import time
from pyftdi.ftdi import Ftdi


# Function to extract numbers from the RNG. This happens indefinitely until a stop signal is received (analysis for the trial completes)
def extract_numbers(ftdi, number_queue, stop_event):

    number_buffer = bytearray()  # buffer for constructing random numbers, ensures we drop no contiguous bytes
    number_buffer.clear()  # Clear the number_buffer when the function is called

    while not stop_event.is_set():  # while stop event is not triggered
        # Request a new random number
        init_comm = b'\x96'
        bytes_txd = ftdi.write_data(init_comm)

        # Read bytes from the buffer first if possible
        bytes_to_read = 32
        dx_data = ftdi.read_data(bytes_to_read)
        if dx_data:
            number_buffer.extend(dx_data)  # Add the received data to the number buffer

            # If we have at least 8 bytes in the number buffer, construct random numbers
            while len(number_buffer) >= 8:
                number = int.from_bytes(number_buffer[:8], "big")  # Construct the random number
                number_queue.put(number)  # Put the number into the queue
                number_buffer = number_buffer[8:]  # Remove the used bytes from the number buffer

        time.sleep(0.001)  # Sleep for a short time to avoid busy waiting

    return ()