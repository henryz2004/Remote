from gameplay import GameObject
from pyoneer3.graphics import Screen, Scene, XYSimple
import pygame


pygame.init()


def render():

    screen.render((0, 0, 0))


s = pygame.display.set_mode((1500, 1200))
screen = Screen(s)

s0 = Scene(screen, active=True)        # Generate random number scene

test_fighter = GameObject(
    0,
    GameObject.ACTIVE,
    GameObject.FIGHTER,
    target_types=[],
    stats={"HP": 100, "MASS": 1, "CRUISE": 100, "TURN": {"AGILITY": 10, "MAX_RATE": 60}},
    sprite_path="fighter_sprite_turretless.png",
    sprite_size=(None, 200),
    turrets=[
        [(0.25, 0.75), "FIGHTER_GUN_MK1", False, 0, 32, False],
        [(0.75, 0.75), "FIGHTER_GUN_MK1", False, 0, 32, False]
    ]
)
test_fighter.set_parent(s0)
test_fighter.rel_pos = (0, 150, 0, 150)
test_fighter.update()

test_enemy = GameObject(
    1,
    GameObject.ACTIVE,
    GameObject.FIGHTER,
    target_types=[],
    stats={"HP": 100, "MASS": 1, "CRUISE": 100, "TURN": {"AGILITY": 10, "MAX_RATE": 60}},
    sprite_path="fighter_sprite_turretless.png",
    sprite_size=(None, 200),
    turrets=[[(0.5, 0.5), "FIGHTER_GUN_MK1", False, 0, 60, False]],
    thrusters=[[(0.5, 1), 1, False]]
)
test_enemy.set_parent(s0)
test_enemy.rel_pos = (0, 500, 0, 500)
test_enemy.update()

test_enemy2 = GameObject(
    1,
    GameObject.ACTIVE,
    GameObject.FIGHTER,
    target_types=[],
    stats={"HP": 100, "MASS": 1, "CRUISE": 100, "TURN": {"AGILITY": 10, "MAX_RATE": 60}},
    sprite_path="fighter_sprite_turretless.png",
    sprite_size=(None, 200),
    turrets=[[(0.5, 0.5), "FIGHTER_GUN_MK1", False, 0, 60, False]]
)
test_enemy2.set_parent(s0)
test_enemy2.rel_pos = (0, 750, 0, 200)
test_enemy2.update()

clock = pygame.time.Clock()

running = True
while running:
    tick = clock.tick(60)

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

        elif e.type == pygame.MOUSEMOTION:
            test_fighter.rel_pos = (0, e.pos[0], 0, e.pos[1])

        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                running = False

    render()
    test_fighter.tick(tick, screen=s, label="FIGHTER")
    test_enemy.tick(tick, label="ROCKET")#, screen=s)
    test_enemy2.tick(tick)#, screen=s)
    pygame.display.flip()
