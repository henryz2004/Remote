"""
BASIC FIGHTER
    FIGHTER None
    100 0

    Basic fighter for all of your fighting needs
    fighter_sprite_2.png fighter_sprite_2.png
"""

import math
import pygame
from pyoneer3 import vmath
from pyoneer3.graphics import XYSimple, XYComplex
from pyoneer3.graphics import Sprite
from pyoneer3.graphics import extract_offsets
from typing import Callable, List, Tuple, Union


pygame.init()

XYResize = Tuple[Union[int, None], Union[int, None]]   # Used to store resize target sizes, None = keep aspect ratio
XYRatio = Tuple[float, float]       # Tuple with numbers always between 0 and 1 (xScale, yScale)


def resize(surf: pygame.Surface, size: XYResize):
    aspect_ratio = surf.get_width() / surf.get_height()
    target_size = list(size)

    if size[0] is None and size[1] is None:
        return surf

    # Keep aspect ratio, resize width
    if size[0] is None:
        target_size[0] = int(size[1] * aspect_ratio)

    # Keep aspect ratio, resize height
    elif size[1] is None:
        target_size[1] = int(size[0] / aspect_ratio)

    return pygame.transform.smoothscale(surf, target_size)


class GameObject(Sprite):

    # Unit behavioral categories
    ACTIVE = 0
    PASSIVE = 0

    # Types of structures/GameObjects
    CC      = 0     # Command center
    FIGHTER = 1

    # Turrets
    GUN_STATS = {
         "FIGHTER_GUN_MK1": {
             "DAMAGE":25,
             "FIRERATE": 60,
             "TURRET_IMAGE": "fighter_turret.png",
             "TURRET_SIZE" : (None, 120),
             "SHOT_IMAGE": None,
             "RANGE": 250       # Unit in pixels
        }   # TODO: Shot image
    }

    GAME_OBJECTS = pygame.sprite.Group()

    def __init__(self,
                 team,
                 category,      # ACTIVE, PASSIVE
                 unit_type,
                 target_types,
                 stats,             # Health, mass, turn
                 sprite_path,
                 sprite_size:XYResize,
                 turrets=None,
                 thrusters=None,
                 timers=None):

        super().__init__((0, 0, 0, 0), sprite_path)     # REL_POS should only have offset and no scaling
        GameObject.GAME_OBJECTS.add(self)
        self.surf = resize(self.surf, sprite_size)

        self.team = team
        self.category = category
        self.unit_type = unit_type
        self.target_types = target_types

        self.health = stats[0]
        self.mass = stats[1]
        self.vel = (0, 0)               # Speed/heading
        self.rot_locked = False         # TODO: confine rotation between -180 and 180? necessary or not?
        self.rot_vel = 0                # Current rate of rotation
        self.turn_rate = stats[2][0]    # How fast the ship can change rotational velocity
        self.max_turn_rate = stats[2][1]

        # List containing tuples storing:
        #  - Position of turret
        #  - Gun type
        #  - Gimbal locked
        #  - Turret rotation (should be 0)
        #  - Turret turn rate
        #  - Automatic turret timer
        self.turrets: List[List[List[XYRatio, str, bool, int, int, bool], pygame.Surface, bool]] \
            = [[turret, None, False] for turret in turrets] if turrets else []      # Last bool for flag marking wheter turret should be fired
        self.thrusters: List[List[XYRatio, int, bool]] \
            = thrusters if thrusters else []  # List of position of thruster, thrust, and active

        # List of timers (current tick, duration, whether to automatically reset current tick after reaching duration callback)
        self.timers: List[List[int, int, bool, Callable]] = timers if timers else []

        self.load_turret_images()
        self.set_turret_timers()

    def load_turret_images(self):

        for turret in self.turrets:

            go_reference = GameObject.GUN_STATS[turret[0][1]]    # Turret stats reference
            turret[1] = resize(pygame.image.load(go_reference["TURRET_IMAGE"]).convert_alpha(), go_reference["TURRET_SIZE"])

    def set_turret_timers(self):        # TODO THIS AND NEXT FUNCTION, flag to set whether turret should be shot based off of angle

        for i, turret in enumerate(self.turrets):

            turret_stats = turret[0]
            gun_stats = GameObject.GUN_STATS[turret[0][1]]

            if turret_stats[-1]:
                self.timers.append([0, gun_stats["FIRERATE"]*1000, False, self.turret_fire_callback(i, len(self.timers))])

    def turret_fire_callback(self, turret_index, timer_index):

        def callback(current_tick, duration):

            turret = self.turrets[turret_index]
            if turret[2]:
                print("PEW")

                self.timers[timer_index][0] = 0

        return callback

    def offset_ship(self, offset: XYSimple):

        self.offset((0, offset[0], 0, offset[1]))

    def tick(self, tick, screen=None):

        # Update timers
        for timer in self.timers:
            print("Updating timer")

            timer[0] += tick

            # If time reached call callback
            if timer[0] >= timer[1]:
                print("Calling timer callback")
                timer[3](tick)

                if timer[2]:
                    timer[0] = 0

        self.update_ship_controls(tick, screen=screen)

    def update_ship_controls(self, tick, screen=None):

        # If this unit actively seeks out enemy units
        if self.category == GameObject.ACTIVE:

            # Find nearest enemy of type
            target, target_dist = self.locate_enemy()
            target_local_pos = vmath.sub(
                extract_offsets(target.rel_pos),
                extract_offsets(self.rel_pos)
            )

            # Perform series of calculations to control turrets, turn rate, engines, etc.
            slope, heading = self.calculate_ship_heading()
            right_vector = (-heading[1], heading[0])        # A vector pointing to the right relative to heading vector and is perpendicular to the heading vector

            _, projection, target_angle = vmath.angle_between(
                heading,
                target_local_pos,
                precomp_dist=target_dist
            )

            # Determine where the target is relative to self, either to the left or to the right by dotting to right_vector
            right_projection = vmath.dot(right_vector, target_local_pos)

            print("TA:", round(target_angle, 3), "\tRV:", list(map(lambda x: round(x, 3), right_vector)), "\tRP:", round(right_projection))

            # Visualize vectors if provided with drawing surface
            ap = self.calculate_absolute_position()
            tap = target.calculate_absolute_position()

            if screen:
                pygame.draw.line(screen, (255, 255, 255), ap, (ap[0] + heading[0] * 150, ap[1] + heading[1] * 150), 4)                                                      # White = ship_heading

                # Draw triangle connecting ship, right_projection, and target
                pygame.draw.lines(screen, (0, 0, 255), True, (ap, (ap[0]+right_vector[0]*right_projection, ap[1]+right_vector[1]*right_projection), tap), 4)               # Blue = ship - right_projection - target triangle
                pygame.draw.line(screen, (255, 0, 0), ap, (ap[0]+right_vector[0]*right_projection, ap[1]+right_vector[1]*right_projection), 4)   # Draw right_projection   # Red = right_projection
                pygame.draw.line(screen, (0, 255, 0), ap, (ap[0] + right_vector[0] * 100, ap[1] + right_vector[1] * 100), 3)  # Draw right vector                          # Green = right_vector

            # Target is to the right of ship
            if right_projection >= 0:
                self.rot_vel = max(-self.max_turn_rate * tick / 1000,
                                   (self.rot_vel - self.turn_rate * tick / 1000) * (1 if right_projection > 100 else right_projection/100))  # TODO: make turn rate magnitude based off of target_angle (larger angles = larger turn velocities) (somewhat implemented)

            else:
                self.rot_vel = min(self.max_turn_rate * tick / 1000,
                                   (self.rot_vel + self.turn_rate * tick / 1000) * (1 if right_projection < -100 else right_projection/-100))  # TODO: FIX ADJUSTING BASED OFF TICK


            # Calculate ship heading (where it's going)
            speed = vmath.magnitude(self.vel)

            # Only calculate ship heading if ship is traveling
            if speed > 0:
                d_heading = vmath.normalize((self.vel[1], self.vel[0]))
                _, d_projection, heading_angle = vmath.angle_between(
                    d_heading,
                    target_local_pos,
                    precomp_dist=target_dist
                )

                # If ship isn't traveling towards target and ship is pointed at target, activate engine
                if -10 < heading_angle < 10 and -10 < target_angle < 10:
                    self.activate_thrusters()

            else:
                self.activate_thrusters()

            # Turn the turrets, NOT BASED OFF OF TURRET POSITION, BASED OFF OF SHIP POSITION
            for turret in self.turrets:

                turret_slope = math.tan(math.radians(90 + self.rot + turret[0][3]))     # TODO: turret slope calculated incorrectly
                if -90 < self.rot + turret[0][3] < 90:
                    turret_heading = vmath.normalize((1 / turret_slope, -1))

                else:
                    turret_heading = vmath.normalize((-1 / turret_slope, 1))

                turret_right_vector = (-turret_heading[1], turret_heading[0])
                turret_right_projection = vmath.dot(turret_right_vector, target_local_pos)

                _, t_projection, t_angle = vmath.angle_between(
                    turret_heading,
                    target_local_pos,
                    precomp_dist=target_dist
                )

                # Visualize turret heading and projection
                if screen:

                    pygame.draw.line(screen, (150, 150, 150), ap, (ap[0]+turret_heading[0]*100, ap[1]+turret_heading[1]*100), 2)                                                                # Gray = turret_heading
                    pygame.draw.lines(screen, (150, 150, 255), True, (ap, (ap[0]+turret_right_vector[0]*turret_right_projection, ap[1]+turret_right_vector[1]*turret_right_projection), tap), 2)   # Light blue = ship - turret_right_projection - target triangle
                    pygame.draw.line(screen, (255, 150, 150), ap, (ap[0]+turret_right_vector[0]*turret_right_projection, ap[1]+turret_right_vector[1]*turret_right_projection), 2)                 # Light red = turret_right_projection
                    pygame.draw.line(screen, (150, 255, 150), ap, (ap[0]+turret_right_vector[0]*100, ap[1]+turret_right_vector[1]*100))                                                             # Light green = turret_right_vector

                # Update turret rotations if not gimbal locked
                if not turret[0][2]:
                    if turret_right_projection >= 0:
                        turret[0][3] -= (turret[0][4] * tick / 1000) * (1 if turret_right_projection > 20 else turret_right_projection/20)

                    else:
                        turret[0][3] += (turret[0][4] * tick / 1000) * (1 if turret_right_projection < -20 else turret_right_projection/-20)

                # Set fire marker if t_angle within certain bounds and in range
                turret_range = GameObject.GUN_STATS[turret[0][1]]["RANGE"]
                if -10 < t_angle < 10 and target_dist <= turret_range:
                    turret[0][2] = True

                else:
                    turret[0][2] = False

        self.update_ship_physics(tick)  # Actually update ship position, rotation

    def update_ship_physics(self, tick):

        # Rotate the ship (self.rot, not the sprite)
        if not self.rot_locked:
            self.rot += self.rot_vel

            if self.rot <= -180:
                self.rot = 360 - self.rot

            elif self.rot > 180:
                self.rot = self.rot - 360

        # Update ship velocity/thrusters
        if self.category == GameObject.ACTIVE:

            slope, heading = self.calculate_ship_heading()

            for thruster in self.thrusters:

                if thruster[2]:
                    self.vel = vmath.add(self.vel, (thruster[1]/self.mass*heading))

        # Update ship position based off of velocity
        self.offset_ship(self.vel)

    def calculate_ship_heading(self):

        # Calculate ship direction (where it's pointed)
        slope = math.tan(math.radians(90 + self.rot))     # Ship rotation in slope form
        if -90 < self.rot < 90:
            heading = vmath.normalize((1/slope, -1))

        else:
            heading = vmath.normalize((-1/slope, 1))

        return slope, heading

    def locate_enemy(self):

        target = None
        target_dist = 0

        # TODO: FIX: IF THERE ARE NO TARGETS OF TARGET TYPE THEN PICK CLOSEST TARGET
        for gobject in GameObject.GAME_OBJECTS:

            if gobject.team != self.team:
                if len(self.target_types) == 0 or gobject.unit_type in self.target_types:

                    dist = math.sqrt((gobject.rel_pos[1] - self.rel_pos[1]) ** 2
                                     + (gobject.rel_pos[3]- self.rel_pos[3]) ** 2)

                    if not target or dist < target_dist:
                        target = gobject
                        target_dist = dist

        return target, target_dist

    def activate_thrusters(self):

        for thruster in self.thrusters:
            thruster[2] = True

    def draw_seq(self):

        self.surf = self.c_surf.copy()

        # Draw turrets and thrusters
        for turret in self.turrets:
            turret_position = turret[0][0]
            turret_rotated_surface = pygame.transform.rotate(turret[1], turret[0][3])
            self.surf.blit(turret_rotated_surface, (turret_position[0]*self.surf.get_width()-turret_rotated_surface.get_width()/2, turret_position[1]*self.surf.get_height()-turret_rotated_surface.get_height()/2)) # Blit at center

        # TODO: Draw flames coming from fire as thrusters

        self.draw_children(False)
        self.draw()

        self.update_rect()

# Actual unit declarations
# [[energy_cost, material_Cost, desc, icon_image, icon_size], [args], [kwargs]]
fighter_unit = (
    [
        50,
        0,
        "A basic fighter for all of your basic fighting needs",
        "fighter_icon.png",
        [None, 80],
    ],
    [
        GameObject.FIGHTER,
        [],
        100,
        "fighter_sprite_2.png",
        [None, 24],
    ]
)
