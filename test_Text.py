import pygame
from pyoneer3.graphics import UIElement, Text

pygame.init()


def render():

    screen.fill((0, 0, 0))
    u0.draw_children()
    u0.draw(screen)
    pygame.display.flip()


screen = pygame.display.set_mode((500, 500))
u0 = UIElement((0, 10, 0, 10), pygame.Surface((300, 200)))
u0.surf.fill((255, 255, 255))
u0.update()
t1 = Text((0, 50, 0, 50), (100, 100), "Testing", pygame.font.Font(None, 15), True, (0, 0, 0))
t1.surf.fill((255, 0, 0))
t1.blit_text()
t1.set_parent(u0)
u1 = UIElement((0, 0, 0, 0), pygame.Surface((50, 50)))
u1.surf.fill((0, 255, 0))
u1.update()
u1.set_parent(t1)

running = True
while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
    render()
