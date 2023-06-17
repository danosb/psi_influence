# Requests and passes information from the participant

import os

def clear_terminal():
    # Clear terminal screen for different operating systems
    os.system('cls' if os.name == 'nt' else 'clear')


def participant_info():
    clear_terminal()

    name = input("Please enter your name: ")
    print(f'')

    # Input validation for name (letters only)
    while not name.isalpha():
        print("Invalid input. Name should contain letters only.")
        name = input("Please enter your name: ")
        print(f'')

    gender = ""
    while gender.upper() not in ["M", "F"]:
        gender = input("Please enter your gender (M/F): ")
    print(f'')

    age = input("Please enter your age: ")
    print(f'')

    # Input validation for age (integer)
    while not age.isdigit():
        print("Invalid input. Age should be a positive integer.")
        age = input("Please enter your age: ")
        print(f'')
    age = int(age)

    feeling = int(input("How are you feeling overall today? (1-5: 1=Awful, 5=Great): "))
    print(f'')

    energy_level = int(input("How is your energy level today? (1-5: 1=Very low, 5=Very high): "))
    print(f'')

    focus_level = int(input("How is your level of focus today? (1-5: 1=Very low, 5=Very high): "))
    print(f'')

    while True:
        temperature = input("What is the local (indoor) temperature in Fahrenheit?: ")
        print(f'')
        try:
            temperature = float(temperature)
            break  # Exit the loop if a valid float is entered
        except ValueError:
            print("Invalid input. Temperature in Fahrenheit: ")
            print(f'')
        
    while True:
        humidity = input("What is the local (indoor) humidity?: ")
        print(f'')
        try:
            humidity = float(humidity)
            break  # Exit the loop if a valid float is entered
        except ValueError:
            print("Invalid input. Enter humidity: ")
            print(f'')


    meditated_input = ""
    while meditated_input.upper() not in ["Y", "N"]:
        meditated_input = input("Did you meditate directly before the experiment today? (Y/N): ")

    meditated = True if meditated_input.upper() == "Y" else False
    print(f'')

    eaten_input = ""
    while eaten_input.upper() not in ["Y", "N"]:
        eaten_input = input("Have you eaten within the last 90 minutes? (Y/N): ")

    eaten = True if eaten_input.upper() == "Y" else False
    print(f'')

    influence_mapping = {
        1: "Produce more 0s (time-bound)",
        2: "Produce more 1s (time-bound)",
        3: "Alternate between producing more 0s and more 1s (continuous)"
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

    if influence_description !="Alternate between producing more 0s and more 1s (continuous)":
        duration_seconds = input("How many seconds should this supertrial last?: ")
        print(f'')

        # Input validation for age (integer)
        while not duration_seconds.isdigit():
            print("Invalid input. Seconds should be a positive integer.")
            age = input("How many seconds should this supertrial last?: ")
            print(f'')
        duration_seconds = int(duration_seconds)
    else:
        duration_seconds = 0


    technique_mapping = {
        1: "Visualization",
        2: "Attempt to identify/merge with the device or process",
        3: "Affirmation or assertive based approach",
        4: "Passive attention",
        5: "Generation of intense energy or emotion",
        6: "Focus on feelings on successful outcome",
        7: "General mind-quieting and focus",
        8: "Focus on feeling love",
        9: "General focus / other"
    }


    # Print technique mappings
    print("Technique Options:")
    for key, value in technique_mapping.items():
        print(key, ": ", value)
    print(f'')
    
    technique = int(input("What technique will you primarily employ today? (Enter the corresponding number): "))

    # Input validation for technique (integer within a valid range)
    while technique not in technique_mapping.keys():
        print("Invalid input. Please enter a valid technique number.")
        technique = int(input("What technique will you primarily employ today? (Enter the corresponding number): "))

    # Retrieve the technique description based on the entered number
    technique_description = technique_mapping.get(technique)
    print(f'')
    print(f'Thank you, starting trial now...')
    print(f'')

    return name, age, gender, feeling, energy_level, focus_level, meditated, eaten, technique_description, influence_description, duration_seconds, temperature, humidity
