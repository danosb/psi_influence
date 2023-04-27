import time


# Placeholder for now. Later this will be used to stream in EEG data
def eeg_data():

    print(f"Starting: {time.time()}")
    # I will use Node-Red to create a node that receives data the Emotiv EEG including not just brainwave.. 
    # data  but also metrics that include excitement, interest, engagement, stress, focus, relaxation
    # Then I'll use the Mosquitto messaging framework to send to Python.
    # I've got this streaming working, but need to figureo out how to manage so much data coming in.
