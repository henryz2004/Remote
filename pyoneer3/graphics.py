import pygame
from collections import namedtuple
from typing import List, Union
pygame.init()


XYComplex = namedtuple('XYComplex', 'xScale xOffset yScale yOffset')
XYSimple = namedtuple('XYSimple', 'xOffset yOffset')


def convert_absolute(coord: XYComplex, surf: pygame.Surface) -> XYSimple:

    return XYSimple(coord[1] + surf.get_width() * coord[0],
                    coord[3] + surf.get_height() * coord[2])


def extract_offsets(coord: XYComplex) -> XYSimple:

    return XYSimple(coord[1], coord[3])


def clamp_color(rgb):

    r = rgb[0]
    g = rgb[1]
    b = rgb[2]

    if r < 0:
        r = 0
    elif r > 255:
        r = 255

    if g < 0:
        g = 0
    elif g > 255:
        g = 255

    if b < 0:
        b = 0
    elif b > 255:
        b = 255

    return r, g, b


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

        descendants = self.children[:]
        for child in self.children:
            descendants.extend(child.get_descendants())
        return descendants

    def draw(self):

        self.children.sort(key=lambda c: c.priority)
        for child in self.children:
            child.draw_seq()


class UIElement:
    # TODO: XYComplex position

    def __init__(self, pos: XYComplex, surf, fill_color=None, render_priority=1):
        super().__init__()

        self.rel_pos = pos               # Tuple in Roblox UDim2 format (xScale, xOffset, yScale, yOffset)

        self.surf = surf
        self.c_surf = None               # MANDATORY update call before drawing!
        self.rect = None
        self.fill_color = fill_color if fill_color else (0, 0, 0)       # *NO FUNCTIONALITY, SIMPLY A MARKER*
        self.priority = render_priority  # Prioritizes which elements get rendered first. Higher numbers take precedence
        self.visible = True

        # Dictionary of all handler functions (functions that take in/handle events)
        self.active = True          # Determines whether events will be handled
        self.handlers = {'mbd': None, 'mover': None,  'menter': None, 'mexit': None, 'uevent': []}
        self.mouse_inside = False       # Event flag used for mouse-enter and mouse-exit events

        self.parent = None
        self.children = []

    def set_parent(self, parent):

        self.parent: Union[Scene, UIElement] = parent
        self.parent.children.append(self)

    def get_descendants(self):

        descendants = self.children[:]
        for child in self.children:
            descendants.extend(child.get_descendants())
        return descendants

    def offset(self, offset: XYComplex):

        self.rel_pos = tuple(self.rel_pos[i] + c for i, c in enumerate(offset))

    def center_position(self, pos: XYComplex):

        assert self.surf, "Cannot center without surface"

        self.rel_pos = (
            pos.xScale,
            pos.xOffset - self.surf.get_width()/2,
            pos.yScale,
            pos.yOffset - self.surf.get_height()/2
        )

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

    def update_rect(self):

        self.rect = self.surf.get_rect()
        self.rect.topleft = self.calculate_absolute_position()

    def update(self):

        assert self.surf, "Attempted to update without surface"

        self.c_surf = self.surf.copy()
        self.update_rect()

    def draw_children(self, reset_surf=True):

        assert self.surf, "Attempted to render UIElement children without surface"

        # Only draw children if self is visible
        if not self.visible:
            return

        if reset_surf:
            # Reset self.surf by overriding it with c_surf
            self.surf = self.c_surf.copy()

        self.children.sort(key=lambda c: c.priority)       # Sort children in order based off of priority
        for child in self.children:
            child.draw_seq()

    def draw(self):

        assert self.surf, "Attempted to render UIElement without surface"
        assert self.parent, "Attempted to draw on nothing"

        # Only draw self if self is visible
        if not self.visible:
            return

        self.parent.surf.blit(self.surf, convert_absolute(self.rel_pos, self.parent.surf))

    def draw_seq(self):

        self.draw_children()
        self.draw()

    # Event methods
    def bind_mbd(self, handler):
        """Bind handler to mouse button down event takes in self and event"""

        self.handlers['mbd'] = handler

    def bind_mover(self, handler):
        """Bind handler to mouse over event takes in self and event"""

        self.handlers['mover'] = handler

    def bind_menter(self, handler):

        self.handlers['menter'] = handler

    def bind_mexit(self, handler):

        self.handlers['mexit'] = handler

    def bind_u(self, handler):
        """Universal event handler function takes in self and event"""

        self.handlers['uevent'].append(handler)

    def unbind_mbd(self):

        self.handlers['mbd'] = None

    def unbind_mover(self):

        self.handlers['mover'] = None

    def unbind_menter(self):

        self.handlers['menter'] = None

    def unbind_mexit(self):

        self.handlers['mexit'] = None

    def unbind_u(self, index=-1):

        return self.handlers['uevent'].pop(index)

    def handle_event(self, event, tick=None):

        if not self.active:
            return

        mouse_motion = False

        # Call mouse-button down handler
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                if self.handlers['mbd']:
                    self.handlers['mbd'](self, event)

        elif event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                mouse_motion = True     # Flag used for mexit event

                # Update mouse_inside flag for menter and mexit events and handle menter event
                # If mouse was not inside on the previous event (but now is), mouse has entered
                if not self.mouse_inside:
                    self.mouse_inside = True
                    if self.handlers['menter']:
                        self.handlers['menter'](self, event)

                # Handle mover event
                if self.handlers['mover']:
                    self.handlers['mover'](self, event)

            # If the mouse didn't move inside self.rect and it used to be inside, mouse has exited
            if not mouse_motion and self.mouse_inside:
                self.mouse_inside = False
                if self.handlers['mexit']:
                    self.handlers['mexit'](self, event)

        for uhandler in self.handlers['uevent']:
            uhandler(self, event, tick)  # Handles all non-default events, pass in tick (time elasped)


class ScrollingFrame(UIElement):
    """Simple Vertical Scroller"""

    def __init__(self, pos: XYComplex, scroll_limits: XYSimple, window_size: XYComplex, scroll_fill=None, render_priority=1):
        super().__init__(pos, None, render_priority)

        self.window = None
        self.window_size: XYComplex = window_size

        self.scroll_limits: XYSimple = scroll_limits
        self.scroll_pos = 0
        self.scroll_speed = 10
        self.scrollable = True
        self.mouse_over = False     # Whether the mouse is over the scrolling frame

        self.scroll_fill = scroll_fill if scroll_fill else (230, 230, 230)
        self.scrollbar_surf = None
        self.scrollbar_padding = 4
        self.scrollbar_width = 2
        self.show_scrollbar = True

        self.bind_u(self.scroll_handler)
        self.bind_menter(self._menter)
        self.bind_mexit(self._mexit)

    def _menter(self, *_):
        print("menter")
        self.mouse_over = True

    def _mexit(self, *_):
        print("mexit")
        self.mouse_over = False

    def update_rect(self):
        """Overrides update_rect of parent - rect is not self.surf's rect, it is self.window's rect"""

        self.rect = self.window.get_rect()
        self.rect.topleft = self.calculate_absolute_position()

    def update(self):

        window_size_simple: XYSimple = convert_absolute(self.window_size, self.parent.surf)

        # Move contents of scrolling frame
        self.window = pygame.Surface(window_size_simple, pygame.SRCALPHA)
        self.window.fill((0, 0, 0, 0))
        self.surf = pygame.Surface(self.scroll_limits, pygame.SRCALPHA)
        self.surf.fill((0, 0, 0, 0))
        self.scroll()       # Blits self.surf onto self.window at correct position

        # Create (vertical) scrollbar
        window_percent = window_size_simple[1] / self.scroll_limits[1]          # Percent of total area being shown on window
        scrollbar_freedom = (window_size_simple[1] - self.scrollbar_padding*2)  # How tall the entire scrolling part is

        self.scrollbar_surf = pygame.Surface(
            (self.scrollbar_width, window_percent * scrollbar_freedom),
            pygame.SRCALPHA
        )
        self.scrollbar_surf.fill(self.scroll_fill)

        super().update()

    def draw(self):

        assert self.window, "Attempted to render UIElement without window surface"
        assert self.parent, "Attempted to draw on nothing"

        # Only draw self if self is visible
        if not self.visible:
            return

        window_size_simple: XYSimple = convert_absolute(self.window_size, self.parent.surf)
        scrollbar_progress = -self.scroll_pos / self.scroll_limits[1]  # Percent scrollbar should be down the screen
        scrollbar_freedom = (window_size_simple[1] - self.scrollbar_padding*2)

        self.scroll()

        # Blit scrollbar
        if self.show_scrollbar and self.scrollbar_surf.get_height() < scrollbar_freedom:
            self.window.blit(
                self.scrollbar_surf,
                convert_absolute(
                    (1, -int(self.scrollbar_padding) - self.scrollbar_width,
                     0, int(self.scrollbar_padding) + scrollbar_progress * scrollbar_freedom),
                    self.window
                )
            )
        self.parent.surf.blit(self.window, convert_absolute(self.rel_pos, self.parent.surf))

    def scroll_handler(self, uie, event, tick):

        if not self.mouse_over or not self.scrollable or not self.parent.surf:
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:           # Scroll up
                absolute_window_size = convert_absolute(self.window_size, self.parent.surf)
                self.scroll_pos += min(
                    self.scroll_speed, -self.scroll_pos
                )

            elif event.button == 5:         # Scroll down
                absolute_window_size = convert_absolute(self.window_size, self.parent.surf)

                if absolute_window_size[1] < self.scroll_limits[1]:
                    self.scroll_pos -= min(
                        self.scroll_speed, self.scroll_limits[1] + self.scroll_pos - absolute_window_size[1]
                    )

            self.scroll()

    def scroll(self):

        self.window.fill((0, 0, 0, 0))
        self.window.blit(self.surf, (0, self.scroll_pos))


class Option(UIElement):

    def __init__(self, pos: XYComplex, surf, fill_color=None, render_priority=1):
        super().__init__(pos, surf, fill_color, render_priority)

        self.selected = False


class Text(UIElement):

    def __init__(self, pos: XYComplex, size: XYSimple, text, fill_color, font, *font_args, render_priority=1):
        # noinspection
        super().__init__(pos, None, fill_color, render_priority)

        self._text = text
        self.font = font
        self.font_args = list(font_args)
        self.text_surf = None
        self.surf = pygame.Surface(size, pygame.SRCALPHA)
        self.draw_text()

    def render_text(self):

        self.text_surf = self.font.render(str(self._text), *self.font_args)

    def blit_text(self):

        # TODO: ADD TEXT POSITIONING
        # DO NOT UPDATE_SURFACE, THAT IS UP TO USER
        self.surf.fill(self.fill_color)
        self.surf.blit(
            self.text_surf,
            (int(self.surf.get_width() / 2) - int(self.text_surf.get_width() / 2),
             int(self.surf.get_height() / 2) - int(self.text_surf.get_height() / 2))
        )     # Blit text to center of button;

    def draw_text(self):
        """Renders and blits text surf on final surf"""

        self.render_text()
        self.blit_text()

    @property
    def text(self):

        return self._text

    @text.setter
    def text(self, value):

        self._text = str(value)
        self.draw_text()


class Image(UIElement):

    def __init__(self, pos: XYComplex, image_path, render_priority=1):
        super().__init__(pos, pygame.image.load(image_path).convert_alpha(), render_priority)

        self.image_path = image_path


class Sprite(Image, pygame.sprite.Sprite):

    def __init__(self, pos: XYComplex, image_path, anchor=1, render_priority=1):
        super().__init__(pos, image_path, render_priority)

        self.anchor = anchor
        self.rot = 0  # Sprite rotation

    def update_rect(self):

        rotated_surf = pygame.transform.rotate(self.surf, self.rot)

        self.rect = rotated_surf.get_rect()

        # Anchor at topleft
        if self.anchor == 0:
            self.rect.topleft = self.calculate_absolute_position()

        # Anchor at mid:
        elif self.anchor == 1:
            self.rect.center = self.calculate_absolute_position()

    def draw(self):
        assert self.surf, "Attempted to render UIElement without surface"
        assert self.parent, "Attempted to draw on nothing"

        # Only draw self if self is visible
        if not self.visible:
            return

        rotated_surf = pygame.transform.rotate(self.surf, self.rot)

        if self.anchor == 0:
            self.parent.surf.blit(rotated_surf, convert_absolute(self.rel_pos, self.parent.surf))

        else:
            x, y = convert_absolute(self.rel_pos, self.parent.surf)
            self.parent.surf.blit(rotated_surf, (x - rotated_surf.get_width()/2, y - rotated_surf.get_height()/2))