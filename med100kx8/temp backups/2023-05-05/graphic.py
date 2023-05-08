import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import numpy as np


# Defaults
state = {
    'rotation_speed': 1,
    'fill_percentage': 0.5,
    'text': "Loading..",
    'timer': 0,
    'cumulative_time_above_target': 0,
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


# update_state({'rotation_speed': 2, 'fill_percentage': 0.7, 'text': "New Text"})
def change_cube_properties(new_rotation_speed, new_fill_percentage, new_text, close_window=False):
    global state  # Add this line to access the global state variable

    state['rotation_speed'] = new_rotation_speed
    state['fill_percentage'] = new_fill_percentage
    state['text'] = new_text


    
    if close_window:
        stop_main_loop()

        
def draw_gradient_fill_bar(x, y, width, height, fill_percentage, target_height=0.95):
    global state, cumulative_time_above_target

    min_color = (0, 0, 255)  # Blue color
    max_color = (0, 255, 0)  # Green color
    border_color = (0, 0, 0)  # Black color

    fill_height = int(height * fill_percentage)
    target_y = y + int(height * target_height)  # Calculate y-coordinate of target line

    cumulative_time_above_target = state.get('cumulative_time_above_target', 0)  # Get current cumulative time above target

    if fill_height >= target_y - y:
        cumulative_time_above_target += 1/60  # Increase cumulative time by 1 second / 60 frames per second
        fill_color = max_color
    else:
        fill_color = [np.interp(fill_height / height, [0, 1], [min_color[j], min_color[j]]) for j in range(3)]

    glBegin(GL_QUADS)
    for i in range(height):
        if i < fill_height:
            glColor3f(*fill_color)
        else:
            glColor3f(1, 1, 1)  # Set the unfilled part to white
        glVertex2f(x, y + i)
        glVertex2f(x + width, y + i)
        glVertex2f(x + width, y + i + 1)
        glVertex2f(x, y + i + 1)
    glEnd()

    # Draw the border
    glColor3f(*border_color)
    glBegin(GL_LINE_LOOP)
    glVertex2f(x, y)
    glVertex2f(x + width, y)
    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)
    glEnd()

    # Draw target line
    glColor3f(0, 0, 0)  # Set line color to black
    glBegin(GL_LINES)
    glVertex2f(x, target_y)
    glVertex2f(x + width, target_y)
    glEnd()

    # Draw target label
    target_label = "Target"
    glColor3f(0, 0, 0)  # Set text color to black
    x_offset = 6  # Offset from left border of bar chart
    y_offset = 25 # Offset from target line
    draw_text((x + x_offset, target_y - y_offset), target_label)

    # Draw cumulative time above target label
    cumulative_time_label = f"Total time above target: {cumulative_time_above_target:.2f}s"
    glColor3f(0, 0, 0)  # Set text color to black
    x_offset = 10  # Offset from left border of screen
    y_offset = 570 # Offset from top border of screen
    draw_text((x_offset, y_offset), cumulative_time_label)

    # Update state with new cumulative time
    state['cumulative_time_above_target'] = cumulative_time_above_target

    # Return cumulative time
    return cumulative_time_above_target




def draw_cube(queue):
    global state
    pygame.init()
    display = (800, 600)
    screen = pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    gluPerspective(45, (display[0] / display[1]), 0.1, 50.0)
    glTranslatef(0.0, 0.0, -5)

    glClearColor(1, 1, 1, 1)  # Set the clear color to white

    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        if not queue.empty():
            new_properties = queue.get()
            change_cube_properties(*new_properties)

        glRotatef(state['rotation_speed'], 1, 0, 0)  # Rotate the cube vertically
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        cube()

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, display[0], 0, display[1])
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        draw_text((10, 15), state['text']) # Bottom left text position 
        draw_gradient_fill_bar(700, 100, 80, 400, state['fill_percentage'])
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

        pygame.display.flip()
        clock.tick(60)
