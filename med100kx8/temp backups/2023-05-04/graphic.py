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
    rotation_speed = new_rotation_speed
    fill_percentage = new_fill_percentage
    text_to_display = new_text

    if close_window:
        stop_main_loop()


def draw_gradient_fill_bar(x, y, width, height, fill_percentage):
    min_color = (0, 0, 255)  # Blue color
    max_color = (0, 0, 255)  # Blue color
    border_color = (0, 0, 0)  # Black color

    fill_height = int(height * fill_percentage)

    glBegin(GL_QUADS)
    for i in range(height):
        if i < fill_height:
            glColor3f(*[np.interp(i / height, [0, 1], [min_color[j], max_color[j]]) for j in range(3)])
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


def draw_cube():
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

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    change_cube_properties(state['rotation_speed'] + 1, state['fill_percentage'], state['text'])

                if event.key == pygame.K_DOWN:
                    change_cube_properties(state['rotation_speed'] - 1, state['fill_percentage'], state['text'])


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
        draw_text((10, 10), state['text'])
        draw_gradient_fill_bar(700, 100, 60, 400, state['fill_percentage'])
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    draw_cube()

