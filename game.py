import pygame
from pyoneer3.animation import AnimationService
from pyoneer3.animation import Translation
from pyoneer3.interpolation import LinearInterpolator
from pyoneer3.graphics import Option
from pyoneer3.graphics import Screen
from pyoneer3.graphics import Scene
from pyoneer3.graphics import ScrollingFrame
from pyoneer3.graphics import Text
from pyoneer3.graphics import UIElement
from pyoneer3.graphics import Image
from pyoneer3.graphics import clamp_color
from gameplay import GameObject
from typing import Dict, List, Tuple


def render():

    screen.render(BLACK)
    pygame.display.flip()


def mainloop():
    global running

    while running:
        tick = CLOCK.tick(FPS_CAP)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

            # Have all of the event listeners in the currently active scene(s) handle their respective events
            else:
                for scene in screen.scenes:                             # For each scene
                        for c in scene.get_descendants():               # For each element in scene
                            if any(c.handlers.values()):                # If element has any active bound listeners
                                c.handle_event(e, tick=tick)                       # Handle event
                            if isinstance(c, GameObject):
                                c.tick(tick)
        render()


def text_menter(brightness=15):

    def handler(uie, event):

        text_menter.og_color = uie.font_args[1]

        uie.font_args[1] = clamp_color([c + brightness for c in uie.font_args[1]])
        uie.draw_text()

        uie.update()

    return handler


def text_mexit(uie, event):

    uie.font_args[1] = text_menter.og_color
    uie.draw_text()
    uie.update()


def surf_menter(brightness=15):

    def handler(uie, event):

        uie.surf.fill(clamp_color([c + brightness for c in uie.fill_color]))
        uie.update()

    return handler


def surf_mexit(uie, event):

    uie.surf.fill(uie.fill_color)
    uie.update()


def tab_menter(brightness=15):

    surf_handler = surf_menter(brightness)

    def event_handler(uie, event):

        if not uie.selected:
            surf_handler(uie, event)

    return event_handler


def tab_mexit(uie, event):

    if not uie.selected:
        surf_mexit(uie, event)


def tab_mbd(uie, event):

    select_tab(uie)


def select_tab(uie):

    for tab, elems, in pages.items():
        tab.selected = tab == uie
        tab.surf.fill(tab.fill_color)
        tab.update()

        for e in elems:
            e.active = tab == uie
            e.visible = tab == uie

    uie.surf.fill(WHITE)
    uie.update()


def game_start(*_):

    start_scene.active = False
    sidebar.active = True


def game_quit(*_):
    global running

    running = False


if __name__ == "__main__":

    pygame.init()

    # Define constants
    WHITE      = (255, 255, 255)
    NEAR_WHITE = (245, 245, 245)
    LG_00      = (230, 230, 230)
    LG_01      = (175, 175, 175)
    BLACK      = (0,   0,   0)
    RED        = (255, 0,   0)
    GREEN      = (0,   255, 0)
    BLUE       = (0,   0,   255)

    DIGITALL_86P = pygame.font.Font("Digitall.ttf", 86)
    DIGITALL_36P = pygame.font.Font("Digitall.ttf", 36)
    SIMPLE_36P = pygame.font.SysFont("twcencondensedextrafranklingothicdemi", 24)

    CLOCK = pygame.time.Clock()
    FPS_CAP = 90

    # Graphics and TODO: Animations
    s = pygame.display.set_mode((1200, 750))
    screen = Screen(s)

    # Start scene
    start_scene = Scene(screen, active=True)

    title_text = Text((0.5, -160, 0.3, 0), (320, 80), "REMOTE", (100, 100, 100, 0), DIGITALL_86P, True, LG_00)
    title_text.set_parent(start_scene)
    title_text.bind_menter(text_menter())
    title_text.bind_mexit(text_mexit)
    title_text.update()

    start_button = Text((0.5, -60, 0.3, 80+10), (120, 40), "START", (100, 100, 100, 0), DIGITALL_36P, True, LG_01)
    start_button.set_parent(start_scene)
    start_button.bind_mbd(game_start)
    start_button.bind_menter(text_menter(100))
    start_button.bind_mexit(text_mexit)
    start_button.update()

    exit_button = Text((0.5, -60, 0.3, 90+40+5), (120, 40), "EXIT", (100, 100, 100, 0), DIGITALL_36P, True, LG_01)
    exit_button.set_parent(start_scene)
    exit_button.bind_mbd(game_quit)
    exit_button.bind_menter(text_menter(100))
    exit_button.bind_mexit(text_mexit)
    exit_button.update()

    # Sidebar UI during combat
    sidebar = Scene(screen, active=False)

    sidebar_background = UIElement((0, 10, 0, 10), pygame.Surface((300-20, s.get_height()-20)))
    sidebar_background.set_parent(sidebar)
    sidebar_background.surf.fill(WHITE)
    sidebar_background.update()

    tabs: List[UIElement] = []
    pages: Dict[UIElement, List[UIElement]] = {}    # Sidebar tabs (weapons/turrets, energy, ships, misc) : selections under category
    tab_rsrc = ["turret00.png", "bolt00.png", "fighter.png", "brick.png"]

    # List of objects containing stats such as name, cost, and so forth    # TODO CHANGE
    # index corresponding to tab
    tab_selections: List[List[Tuple[str, str]]]  = [
        [],
        [],
        [("fighter_icon.png", "FIGHTER")],
        []
    ]

    for i, tab_img in enumerate(tab_rsrc):

        tab = Option((i*0.25, 0, 0, 0), pygame.Surface((70, 40)), fill_color=LG_00)
        tab.set_parent(sidebar_background)
        tab.surf.fill(tab.fill_color)
        tab.bind_menter(tab_menter())
        tab.bind_mexit(tab_mexit)
        tab.bind_mbd(tab_mbd)
        tab.update()

        tab_img = Image((0.5, -12, 0, 7), tab_rsrc[i])
        tab_img.set_parent(tab)
        tab_img.surf = pygame.transform.smoothscale(tab_img.surf, (25, 25))
        tab_img.update()

        tab_sf = ScrollingFrame((0, 0, 0, 40), (280, 800), (1, 0, 1, -40), scroll_fill=(235, 235, 245))
        tab_sf.set_parent(sidebar_background)
        tab_sf.update()

        tab_sf_background = UIElement((0, 0, 0, 0), pygame.Surface((280, 800)))
        tab_sf_background.set_parent(tab_sf)
        tab_sf_background.surf.fill(WHITE)
        tab_sf.active = False
        tab_sf.visible = False
        tab_sf.scroll_speed = 20
        tab_sf_background.update()

        for j, selections in enumerate(tab_selections[i]):

            block = UIElement((0, 10, 0, 10+100*j), pygame.Surface((260, 100)), fill_color=LG_00) #Text((0, 10, 0, 50), (260-20, 100), i, BLACK, DIGITALL_86P, True, LG_00)
            block.set_parent(tab_sf)
            block.surf.fill(LG_00)
            block.update()

            block_pic = Image((0, 10, 0, 10), selections[0])
            block_pic.set_parent(block)
            pic_width = int((block_pic.surf.get_width() / block_pic.surf.get_height()) * 80)
            block_pic.surf = pygame.transform.smoothscale(block_pic.surf, (pic_width, 80))
            block_pic.update()

            block_text = Text((0, pic_width+20, 0, 4), (260-pic_width-25, 20), selections[1], (0, 0, 0), SIMPLE_36P, True, WHITE)       # TODO CHANGE instead of selections[1] do selections[1].name or something
            block_text.set_parent(block)
            block_text.update()

        tabs.append(tab)
        pages[tab] = [tab_sf]

    select_tab(tabs[0])

    running = True
    mainloop()
