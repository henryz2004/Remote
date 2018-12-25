from graphics import UIElement
import pygame

pygame.init()


def render():

    screen.fill((0, 0, 0))
    u0.draw_children()
    screen.blit(u0.surf, (u0.rel_pos[1], u0.rel_pos[3]))
    pygame.display.flip()


screen = pygame.display.set_mode((500, 500))
u0 = UIElement((0, 10, 0, 10), pygame.Surface((300, 200)))
u0.surf.fill((255, 255, 255))
u1 = UIElement((0, 50, 0, 50), pygame.Surface((100, 100)))
u1.surf.fill((255, 0, 0))
u1.set_parent(u0)

running = True
while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
    render()
