# Requests and passes information from the participant

import os

def clear_terminal():
    # Clear terminal screen for different operating systems
    os.system('cls' if os.name == 'nt' else 'clear')


def participant_info():
    clear_terminal()

    name = input("Please enter your name: ")
    print(f'')

    age = input("Please enter your age: ")
    print(f'')

    gender = ""
    while gender.upper() not in ["M", "F"]:
        gender = input("Please enter your gender (M/F): ")
    print(f'')

    # Input validation for name (letters only)
    while not name.isalpha():
        print("Invalid input. Name should contain letters only.")
        name = input("Please enter your name: ")

    # Input validation for age (integer)
    while not age.isdigit():
        print("Invalid input. Age should be a positive integer.")
        age = input("Please enter your age: ")
    age = int(age)

    feeling = int(input("How are you feeling overall today? (1-5: 1=Awful, 5=Great): "))
    print(f'')

    energy_level = int(input("How is your energy level today? (1-5: 1=Very low, 5=Very high): "))
    print(f'')

    focus_level = int(input("How is your level of focus today? (1-5: 1=Very low, 5=Very high): "))
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

    # Print the entered information
    #print("\nEntered Information:")
    #print("Name:", name)
    #print("Age:", age)
    #print("Feeling:", feeling)
    #print("Energy Level:", energy_level)
    #print("Focus Level:", focus_level)
    #print("Meditated:", meditated)
    #print("Technique:", technique_description)

    return name, age, gender, feeling, energy_level, focus_level, meditated, eaten, technique_description
