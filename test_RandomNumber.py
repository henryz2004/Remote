import pygame
import random
from pyoneer3.graphics import UIElement, Text, Screen, Scene

pygame.init()


def render():

    screen.render((0, 0, 0))
    pygame.display.flip()


def gen_mbd_handler(*_):

    print("Clicked!")

    gen_output.text = random.randint(1, 100)
    gen_output.blit_text()
    gen_output.update()


s = pygame.display.set_mode((1000, 750))
screen = Screen(s)

s0 = Scene(screen, active=True)        # Generate random number scene

rhs = UIElement((0.5, 0, 0, 0), pygame.Surface((1000, 750)))
rhs.surf.fill((255, 255, 255))
rhs.set_parent(s0)
rhs.update()

gen_button = Text((0.1, -50, 0.1, -50), (200, 100), "Generate random number", (255, 0, 0), pygame.font.Font(None, 20), True, (0, 0, 0))
gen_button.set_parent(rhs)
gen_button.update()
gen_button.bind_mbd(gen_mbd_handler)

gen_output = Text((0.3, -50, 0.1, -50), (200, 100), "", (255, 255, 0), pygame.font.Font(None, 25), True, (0, 0, 0))
gen_output.set_parent(rhs)
gen_output.update()

running = True
while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

        else:
            gen_button.handle_event(e)

    render()
