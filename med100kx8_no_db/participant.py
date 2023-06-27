# Requests and passes information from the participant

import os

def clear_terminal():
    # Clear terminal screen for different operating systems
    os.system('cls' if os.name == 'nt' else 'clear')


def participant_info():
    clear_terminal()

    influence_mapping = {
        1: "Produce more 0s",
        2: "Produce more 1s",
        3: "Alternate between producing more 0s and more 1s"
    }

    # Print technique mappings
    print("Influence Options:")
    for key, value in influence_mapping.items():
        print(key, ": ", value)
    print(f'')
    
    influence = int(input("What direction of influence? (Enter the corresponding number): "))
    print(f'')

    # Input validation for technique (integer within a valid range)
    while influence not in influence_mapping.keys():
        print("Invalid input. Please enter a valid technique number.")
        influence = int(input("What direction of influence? (Enter the corresponding number): "))

    # Retrieve the technique description based on the entered number
    influence_description = influence_mapping.get(influence)

    duration_seconds = input("How many seconds should this supertrial last? (0=indefinite): ")
    print(f'')

    # Input validation for age (integer)
    while not duration_seconds.isdigit():
        print("Invalid input. Seconds should be a positive integer.")
        age = input("How many seconds should this supertrial last?: ")
        print(f'')
    duration_seconds = int(duration_seconds)


    print(f'')
    print(f'Thank you, starting trial now...')
    print(f'')

    return influence_description, duration_seconds
