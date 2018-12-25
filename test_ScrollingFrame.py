import pygame
from pyoneer3.graphics import Screen, Scene, Text, ScrollingFrame, UIElement

pygame.init()


def render():

    screen.render((0, 0, 0))
    pygame.display.flip()

s = pygame.display.set_mode((100, 100))
screen = Screen(s)

s0 = Scene(screen, active=True)

sf = ScrollingFrame((0, 0, 0, 0), (100, 200), (0, 100, 0, 100))
sf.set_parent(s0)
sf.update()

background = UIElement((0, 0, 0, 0), pygame.Surface((100, 200), pygame.SRCALPHA))
background.set_parent(sf)
background.surf.fill((255, 0, 0, 100))
background.update()

t = Text((0, 0, 0, 0), (100, 10), "Top", (255, 255, 255), pygame.font.Font(None, 20), True, (0, 0, 0))
t.set_parent(background)
t.update()

t1 = Text((0, 0, 1, -10), (100, 10), "Bottom", (255, 255, 255), pygame.font.Font(None, 20), True, (0, 0, 0))
t1.set_parent(background)
t1.update()
running = True
while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

        else:
            sf.handle_event(e)

    render()
