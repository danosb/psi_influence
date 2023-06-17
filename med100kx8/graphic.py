# This produces the graphic window

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import numpy as np
import os
import pygame.mixer
import time

current_sound = None
cumulative_time_beyond_target = 0 
last_time = time.time() 
start_time = time.time()  # Record the start time


# Defaults
state = {
    'rotation_speed': 1,
    'fill_percentage': 0.5,
    'text': "Loading..",
    'time_remaining': 0,
    'timer': 0,
    'cumulative_time_beyond_target': 0,
    'window_result_significant': False,
    'two_tailed': False,
}


def cube():
    vertices = (
        (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, -1),
        (1, -1, 1), (1, 1, 1), (-1, -1, 1), (-1, 1, 1)
    )
    edges = (
        (0, 1), (1, 2), (2, 3), (3, 0),
        (4, 5), (5, 6), (6, 7), (7, 4),
        (0, 4), (1, 5), (2, 6), (3, 7)
    )
    faces = [
        (0, 1, 2, 3),
        (3, 2, 7, 6),
        (6, 7, 5, 4),
        (4, 5, 1, 0),
        (1, 5, 7, 2),
        (4, 0, 3, 6)
    ]

    glBegin(GL_QUADS)
    for face in faces:
        glColor3fv((0, 0, 0))  # Change the cube color to grey
        for vertex in face:
            glVertex3fv(vertices[vertex])
    glEnd()

    glColor3fv((0, 0, 0))
    glBegin(GL_LINES)
        # ...
    glEnd()


    glColor3fv((.75, .75, .75))
    glBegin(GL_LINES)
    for edge in edges:
        for vertex in edge:
            glVertex3fv(vertices[vertex])
    glEnd()


def draw_text(position, text_string):
    glColor3fv((0, 0, 0))  # Set text color
    x, y = position
    z = 0
    glRasterPos3f(x, y, z)  # Set text position
    for character in text_string:
        glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(character))


def change_cube_properties(new_rotation_speed, new_fill_percentage, new_text, passed_time_remaining, two_tailed, close_window=False):

    global state  # Add this line to access the global state variable

    state['rotation_speed'] = new_rotation_speed * 3
    state['fill_percentage'] = new_fill_percentage
    state['text'] = new_text
    state['time_remaining'] = passed_time_remaining
    state['two_tailed'] = two_tailed

    play_mp3(new_rotation_speed)

    cumulative_time_beyond_target = state.get('cumulative_time_beyond_target', 0)
    state['cumulative_time_beyond_target'] = cumulative_time_beyond_target

    return cumulative_time_beyond_target


def play_mp3(rotation_speed):
    global current_sound
    mp3_path = os.path.dirname(os.path.abspath(__file__))  # Get the current script directory
    freq = int(100 + abs(rotation_speed) * 100)

    freq_str = str(freq).zfill(2)  # Pad with zeros on the left
    file_name = f"{freq_str}Hz.mp3"
    file_path = os.path.join(mp3_path, "mp3", file_name)
    if current_sound is not None:
        current_sound.stop()
    current_sound = pygame.mixer.Sound(file_path)
    current_sound.play()


# only for two-tailed
def draw_circle(x, y, radius, fill_color=(0, 0, 0), filled=False, text=None):
    num_segments = 100  # Number of segments used to draw the circle
    glColor3f(*fill_color)  # Set fill color

    # Draw filled circle
    if filled:
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(x, y)  # Center vertex
        for i in range(num_segments + 1):  # For each segment
            theta = float(i) / num_segments * 2.0 * np.pi  # Calculate angle
            dx = radius * np.cos(theta)  # Calculate x-coordinate of segment endpoint
            dy = radius * np.sin(theta)  # Calculate y-coordinate of segment endpoint
            glVertex2f(x + dx, y + dy)  # Draw segment endpoint
        glEnd()

    # Draw circle outline
    glColor3f(0, 0, 0)  # Set outline color
    glBegin(GL_LINE_LOOP)
    for i in range(num_segments):  # For each segment
        theta = float(i) / num_segments * 2.0 * np.pi  # Calculate angle
        dx = radius * np.cos(theta)  # Calculate x-coordinate of segment endpoint
        dy = radius * np.sin(theta)  # Calculate y-coordinate of segment endpoint
        glVertex2f(x + dx, y + dy)  # Draw segment endpoint
    glEnd()

    # Draw text
    if text is not None:
        glColor3f(0, 0, 0)  # Set text color
        draw_text((x - 15, y - 10), text)  # Draw text with a small offset from the circle center


def draw_gradient_fill_bar(x, y, width, height, fill_percentage, two_tailed=False, target_height=0.95, lower_target_height=0.05):
    global cumulative_time_beyond_target, last_time  # Declare the variables as global

    current_time = time.time()  # Get the current time
    delta_time = current_time - last_time  # Calculate the time elapsed since the last update
    last_time = current_time  # Update last_time to the current time


    min_color = (0, 0, 255)  # Blue color
    max_color = (0, 255, 0)  # Green color
    lower_color = (255, 0, 0)  # Red color
    border_color = (0, 0, 0)  # Black color

    target_y = y + int(height * target_height)  # Calculate y-coordinate of target line
    lower_target_y = y + int(height * lower_target_height)  # Calculate y-coordinate of lower target line
    
    time_remaining = state.get('time_remaining', 0)  # Get current cumulative time above target

    if two_tailed:
        mid_y = y + int(height / 2)  # Calculate the middle of the bar
        if fill_percentage < 0.5:
            fill_start = mid_y
            fill_end = mid_y - int((0.5 - fill_percentage) * height)
            fill_color = lower_color if fill_end <= lower_target_y else min_color
        else:
            fill_start = mid_y
            fill_end = mid_y + int((fill_percentage - 0.5) * height)
            fill_color = max_color if fill_end >= target_y else min_color
    else:
        fill_start = y
        fill_end = y + int(height * fill_percentage)
        fill_color = max_color if fill_end >= target_y else min_color

    if two_tailed and (fill_end >= target_y or fill_end <= lower_target_y):
        cumulative_time_beyond_target += delta_time
    if not two_tailed and fill_end >= target_y:
        cumulative_time_beyond_target += delta_time 

    glBegin(GL_QUADS)
    glColor3f(*fill_color)
    glVertex2f(x, fill_start)
    glVertex2f(x + width, fill_start)
    glVertex2f(x + width, fill_end)
    glVertex2f(x, fill_end)
    glEnd()

    # Draw the border
    glColor3f(*border_color)
    glBegin(GL_LINE_LOOP)
    glVertex2f(x, y)
    glVertex2f(x + width, y)
    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)
    glEnd()

    # Draw target lines
    glColor3f(0, 0, 0)  # Set line color to black
    glBegin(GL_LINES)
    glVertex2f(x, target_y)
    glVertex2f(x + width, target_y)
    if two_tailed:
        glVertex2f(x, lower_target_y)
        glVertex2f(x + width, lower_target_y)
    glEnd()

    # Draw target labels
    upper_target_label = "1 Target" if two_tailed else "Target"
    lower_target_label = "0 Target"
    glColor3f(0, 0, 0)  # Set text color to black
    x_offset = 6  # Offset from left border of bar chart
    y_offset = 25  # Offset from target line
    draw_text((x + x_offset - 8, target_y + 50 - y_offset), upper_target_label,)
    if two_tailed:
        draw_text((x + x_offset - 8, lower_target_y - y_offset - 15), lower_target_label)

    # Draw cumulative time above target label
    cumulative_time_label = f"Total time beyond target: {cumulative_time_beyond_target -.63:.2f}s"
    glColor3f(0, 0, 0)  # Set text color to black
    x_offset = 15  # Offset from left border of screen
    y_offset = 570  # Offset from top border of screen
    draw_text((x_offset, y_offset), cumulative_time_label)

    # Draw time remaining label if two_tailed is False
    if not two_tailed:
        time_remaining_minutes = int((time_remaining + 1) // 60)
        time_remaining_seconds = int((time_remaining + 1) % 60)
        time_remaining_label = f"Time remaining: {time_remaining_minutes:02d}:{time_remaining_seconds:02d}"
        glColor3f(0, 0, 0)  # Set text color to black
        x_offset = 555  # Offset from left border of screen
        y_offset = 570  # Offset from top border of screen
        draw_text((x_offset, y_offset), time_remaining_label)

    # Update state with new cumulative time
    state['cumulative_time_beyond_target'] = cumulative_time_beyond_target
    state['time_remaining'] = time_remaining

    # Return cumulative time
    return cumulative_time_beyond_target


def draw_cube(queue, stop_flag):
    global state

    pygame.init()
    pygame.mixer.init()  # Initialize the mixer
    pygame.display.set_caption("Mental Influence Experiment")
    pygame.mixer.set_num_channels(1)  # Set the number of channels

    display = (800, 600)
    screen = pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    gluPerspective(45, (display[0] / display[1]), 0.1, 50.0)
    glTranslatef(0.0, 0.0, -5)

    glClearColor(1, 1, 1, 1)  # Set the clear color to white

    clock = pygame.time.Clock()

    circle_fill_color = (1, 1, 1)  # Initial circle fill color is white
    circle_word = ''  # Initial circle word is empty
    last_state_change_value = None  # Initialize the last state change value

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_x:
                    stop_flag.value = True

        if stop_flag.value:  # Check the value of the stop_flag
            return  # Exit the function and stop the while loop

        if not queue.empty():
            new_properties = queue.get()
            change_cube_properties(*new_properties[:])  # Pass only the first four elements

        # Check if the two-tailed flag is set and if the fill percentage exceeds the thresholds
        if state['two_tailed']:
            if state['fill_percentage'] >= 0.95 and last_state_change_value != 'On':
                circle_fill_color = (0, 1, 0)  # Green
                circle_word = 'On'
                last_state_change_value = 'On'
            elif state['fill_percentage'] <= 0.05 and last_state_change_value != 'Off':
                circle_fill_color = (1, 0, 0)  # Red
                circle_word = 'Off'
                last_state_change_value = 'Off'

        glRotatef(state['rotation_speed'], 1, 0, 0)  # Rotate the cube vertically
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        cube()

        # Calculate the total elapsed time
        total_elapsed_time = time.time() - start_time

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, display[0], 0, display[1])
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # Calculate the total elapsed time
        total_elapsed_time = time.time() - start_time

        # Calculate hours, minutes, seconds and milliseconds
        hours, rem = divmod(total_elapsed_time, 3600)
        minutes, seconds = divmod(rem, 60)
        seconds, milliseconds = divmod(seconds, 1)
        
        # Draw the total elapsed time
        elapsed_time_label = f"Elapsed time: {int(hours):02}:{int(minutes):02}:{int(seconds):02}"
        glColor3f(0, 0, 0)  # Set text color to black
        x_offset = 555  # Offset from left border of screen
        y_offset = 10  # Offset from bottom border of screen
        draw_text((x_offset, y_offset), elapsed_time_label)
        
        draw_gradient_fill_bar(700, 100, 80, 400, state['fill_percentage'], state['two_tailed'])

        # Draw "Press X to exit" label
        exit_label = "Press X to exit"
        glColor3f(0, 0, 0)  # Set text color to black
        x_offset = 10  # Offset from left border of screen
        y_offset = 10  # Offset from bottom border of screen
        draw_text((x_offset, y_offset), exit_label)

        # Check if two-tailed is True, if so, draw the circle
        if state['two_tailed']:
            circle_radius = 50  # Circle radius
            circle_center = (100, display[1] / 2)  # Circle center coordinates (100 px from the left border and at the center of the screen vertically)
            
            # Draw the circle
            draw_circle(circle_center[0], circle_center[1], circle_radius, fill_color=circle_fill_color, filled=True, text=circle_word)

        # Reset matrices
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

        pygame.display.flip()  # Update the display
        clock.tick(60)  # Limit the frame rate to 60 FPS

