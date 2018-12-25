import pygame
from collections import namedtuple
from typing import Callable, Dict, List, Tuple, Union
pygame.init()


XYComplex = namedtuple('XYComplex', 'xScale xOffset yScale yOffset')
XYSimple = namedtuple('XYSimple', 'xOffset yOffset')


def convert_absolute(coord: XYComplex, surf: pygame.Surface) -> XYSimple:

    return XYSimple(coord[1] + surf.get_width() * coord[0],
                    coord[3] + surf.get_height() * coord[2])


class Screen:

    def __init__(self, screen):

        self.screen = screen
        self.scenes: List[Scene] = []

    def render(self, background_color):

        self.screen.fill(background_color)

        for scene in self.scenes:
            if scene and scene.active:
                scene.draw()


class Scene:

    def __init__(self, screen, active=False):

        self.active = active
        self.surf = screen.screen
        self.children = []

        screen.scenes.append(self)

    def get_descendants(self):

        descendants = self.children
        for child in self.children:
            descendants.extend(child.get_descendants())
        return descendants

    def draw(self):

        self.children.sort(key=lambda c: c.priority)
        for child in self.children:
            child.draw_children()
            child.draw()


class EventListener:

    def __init__(self):

        # Dictionary of all handler functions (functions that take in/handle events)
        self.handlers: Dict[str, Callable] = {'mbd': None, 'mover':None, 'uevent': None}

    def bind_mbd(self, handler):
        """Bind handler to mouse button down event takes in self and event"""

        self.handlers['mbd'] = handler

    def bind_mover(self, handler):
        """Bind handler to mouse over event takes in self and event"""

        self.handlers['mover'] = handler

    def bind_u(self, handler):
        """Universal event handler function takes in self and event"""

        self.handlers['uevent'] = handler

    def unbind_mbd(self):

        self.handlers['mbd'] = None

    def unbind_mover(self):

        self.handlers['mover'] = None

    def unbind_u(self):

        self.handlers['uevent'] = None

    def handle_event(self, event):

        # Call mouse-button down handler
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                if self.handlers['mbd']:
                    self.handlers['mbd'](self, event)

        elif event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                if self.handlers['mover']:
                    self.handlers['mover'](self, event)

        if self.handlers['uevent']:
            self.handlers['uevent'](self, event)  # Handles all non-default events


class UIElement(EventListener):

    def __init__(self, pos: XYComplex, surf, render_priority=1):
        super().__init__()

        self.rel_pos = pos               # Tuple in Roblox UDim2 format (xScale, xOffset, yScale, yOffset)
        self.surf = surf
        self.c_surf = None               # MANDATORY update call before drawing!
        self.rect = None
        self.priority = render_priority  # Prioritizes which elements get rendered first. Higher numbers take precedence

        self.parent = None
        self.children = []

    def set_parent(self, parent):

        self.parent: Union[Scene, UIElement] = parent
        self.parent.children.append(self)

    def get_descendants(self):

        descendants = self.children
        for child in self.children:
            descendants.extend(child.get_descendants())
        return descendants

    def calculate_absolute_position(self):

        # Calculate absolute position of parents in their parents up to top
        position_chain: List[XYSimple] = []
        current_object = self
        while isinstance(current_object, UIElement):
            position_chain.append(convert_absolute(current_object.rel_pos, current_object.parent.surf))
            current_object = current_object.parent

        # Sum up position_chain to get absolute position of self by unzipping to get list of x and y values and then sum
        individual_xy = list(zip(*position_chain))
        return XYSimple(sum(individual_xy[0]), sum(individual_xy[1]))

    def update_surface(self):

        assert self.surf, "Attempted to update without surface"

        self.c_surf = self.surf.copy()
        self.rect = self.surf.get_rect()
        self.rect.topleft = self.calculate_absolute_position()

    def draw_children(self):

        assert self.surf, "Attempted to render UIElement children without surface"

        # Reset self.surf by overriding it with c_surf
        self.surf = self.c_surf.copy()

        self.children.sort(key=lambda c: c.priority)       # Sort children in order based off of priority
        for child in self.children:
            child.draw_children()
            child.draw()

    def draw(self):

        assert self.surf, "Attempted to render UIElement without surface"
        assert self.parent, "Attempted to draw on nothing"

        self.parent.surf.blit(self.surf, convert_absolute(self.rel_pos, self.parent.surf))


class Text(UIElement):

    def __init__(self, pos: XYComplex, size: XYSimple, text, fill_color, font, *font_args, render_priority=1):
        # noinspection PyTypeChecker
        super().__init__(pos, None, render_priority)

        self._text = text
        self.fill_color = fill_color
        self.font = font
        self.font_args = font_args
        self.text_surf = self.font.render(str(self._text), *self.font_args)
        self.surf = pygame.Surface(size, pygame.SRCALPHA)
        self.surf.fill(self.fill_color)
        self.blit_text()

    def blit_text(self):

        # TODO: ADD TEXT POSITIONING
        # DO NOT UPDATE_SURFACE, THAT IS UP TO USER
        self.surf.blit(
            self.text_surf,
            (int(self.surf.get_width() / 2) - int(self.text_surf.get_width() / 2),
             int(self.surf.get_height() / 2) - int(self.text_surf.get_height() / 2))
        )     # Blit text to center of button;

    @property
    def text(self):

        return self._text

    @text.setter
    def text(self, value):

        self._text = str(value)
        self.text_surf = self.font.render(str(self._text), *self.font_args)
        self.surf.fill(self.fill_color)
        self.blit_text()
