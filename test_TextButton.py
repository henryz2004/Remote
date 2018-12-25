import pygame
from pyoneer3.graphics import UIElement, TextButton, Screen, Scene

pygame.init()


def render():

    screen.render((0, 0, 0))
    pygame.display.flip()


def t1_mbd_handler(*_):

    print("Clicked!")


s = pygame.display.set_mode((500, 500))
screen = Screen(s)

s0 = Scene(screen, active=True)
u0 = UIElement((0, 10, 0, 10), pygame.Surface((300, 200)))
u0.surf.fill((255, 255, 255))
u0.update()
u0.set_parent(s0)

t1 = TextButton((0, 50, 0, 50), (100, 100), "Testing", pygame.font.Font(None, 15), True, (0, 0, 0))
t1.surf.fill((255, 0, 0))
t1.blit_text()
t1.set_parent(u0)
t1.bind_mbd(t1_mbd_handler)

u1 = UIElement((0, 0, 0, 0), pygame.Surface((50, 50)))
u1.surf.fill((0, 255, 0))
u1.update()
u1.set_parent(t1)

u2 = UIElement((0.1, 0, 0, 2), pygame.Surface((50, 70)), render_priority=-10)
u2.surf.fill((255, 255, 0))
u2.update()
u2.set_parent(t1)

running = True
while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

        else:
            t1.handle_event(e)

    render()
