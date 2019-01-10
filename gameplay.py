"""
BASIC FIGHTER
    FIGHTER None
    100 0

    Basic fighter for all of your fighting needs
    fighter_sprite_2.png fighter_sprite_2.png
"""

import math
import pygame
import time
from pyoneer3 import vmath
from pyoneer3.graphics import XYSimple, XYComplex
from pyoneer3.graphics import Sprite, ppm_detected
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
    # TODO: Refactor out unnecessary methods, add music/sound capabilities by passing in mixer argument in tick

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
             "SHOT_IMAGE": None,            # TODO: More shot functionality/customizability
             "SHOT_SPEED": 200,             # Pixels per second
             "RANGE": 250       # Unit in pixels
        }   # TODO: Shot image
    }

    # Image path dictionary
    IPD = {
        "EXHAUST": {
            "simplejet": {
                "SRC": "flames_fighter.png",
                "SIZE": (None, 30)
            }
        }
    }

    GAME_OBJECTS = pygame.sprite.Group()

    def __init__(self,
                 team,
                 category,      # ACTIVE, PASSIVE
                 unit_type,
                 target_types,
                 stats,             # Health, mass, turn, cruising speed
                 sprite_path,
                 sprite_size: XYResize,
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

        self.health = stats["HP"]
        self.max_health = self.health   # Stores original hp value for things like health bar, etc.
        self.mass = stats["MASS"]
        self.vel = (0, 0)               # Speed/heading in PIXELS PER FRAME
        self.cruise_vel = stats["CRUISE"]   # PIXELS PER SECOND
        self.max_vel = stats["MAX_VEL"]     # PIXELS PER SECOND
        self.rot_locked = False         # TODO: confine rotation between -180 and 180? necessary or not?
        self.rot_vel = 0                # Current rate of rotation
        self.turn_rate = stats["TURN"]["AGILITY"]  # How fast the ship can change rotational velocity
        self.max_turn_rate = stats["TURN"]["MAX_RATE"]
        self.retrograde = False

        # List containing tuples storing:
        #  - Position of turret
        #  - Gun type
        #  - Gimbal locked
        #  - Turret rotation (should be 0)
        #  - Turret turn rate
        #  - Automatic turret timer
        self.turrets: List[List[List[XYRatio, str, bool, int, int, bool], pygame.Surface, bool]] \
            = [[turret, None, False] for turret in turrets] if turrets else []      # Last bool for flag marking wheter turret should be fired

        # - Position
        # - Engine fire type (what the flames coming out look like)
        # - Thrust  # TODO: Set up initializing thruster sprites
        self.thrusters: List[List[List[XYRatio, str, int], pygame.Surface, bool]] \
            = [[thruster, None, False] for thruster in thrusters] if thrusters else []  # Stats, sprite, active

        # List of timers (current tick, duration, whether to automatically reset current tick after reaching duration callback)
        self.timers: List[List[int, int, bool, Callable]] = timers if timers else []

        self.load_turret_images()
        self.load_exhaust_images()
        self.set_turret_timers()

    def load_turret_images(self):

        for turret in self.turrets:

            go_reference = GameObject.GUN_STATS[turret[0][1]]    # Turret stats reference
            turret[1] = resize(pygame.image.load(go_reference["TURRET_IMAGE"]).convert_alpha(), go_reference["TURRET_SIZE"])

    def load_exhaust_images(self):

        for thruster in self.thrusters:

            ipd_ref = GameObject.IPD["EXHAUST"][thruster[0][1]]     # Get image-path-dictionary reference for image path and size of image
            img_path = ipd_ref["SRC"]
            img_scale = ipd_ref["SIZE"]
            thruster[1] = resize(pygame.image.load(img_path).convert_alpha(), img_scale)

    def set_turret_timers(self):        # TODO THIS AND NEXT FUNCTION, flag to set whether turret should be shot based off of angle

        for i, turret in enumerate(self.turrets):

            turret_stats = turret[0]
            gun_stats = GameObject.GUN_STATS[turret[0][1]]

            if turret_stats[-1]:
                self.timers.append([0, 60000/gun_stats["FIRERATE"], False, self.turret_fire_callback(i, len(self.timers))])

    def turret_fire_callback(self, turret_index, timer_index):

        def callback(current_tick):

            turret = self.turrets[turret_index]
            if turret[2]:
                self.timers[timer_index][0] = 0     # TODO: Turret fire

        return callback

    def offset_ship(self, offset: XYSimple):

        self.offset((0, offset[0], 0, offset[1]))

    def tick(self, tick, screen=None, label=None):

        # Update timers
        for timer in self.timers:

            timer[0] += tick

            # If time reached call callback
            if timer[0] >= timer[1]:
                timer[3](tick)

                if timer[2]:
                    timer[0] = 0

        self.update_ship_controls(tick, screen=screen, label=label)

    def update_ship_controls(self, tick, screen=None, label=None):

        # If this unit actively seeks out enemy units
        if self.category == GameObject.ACTIVE:

            # Find nearest enemy of type
            target, target_dist = self.locate_enemy()

            ap = self.calculate_absolute_position()     # Absolute position of self
            tap = target.calculate_absolute_position()  # Absolute position of target

            target_local_pos = vmath.sub(
                tap,
                ap
            )

            # Perform series of calculations to control turrets, turn rate, engines, etc.
            # TODO: Possible optimization by removing right_vector and projections. Unnecessary
            slope, heading = self.calculate_ship_heading()
            d_heading = vmath.normalize(self.vel)
            right_vector = (-heading[1], heading[0])        # A vector pointing to the right relative to heading vector and is perpendicular to the heading vector
            speed = vmath.magnitude(self.vel)

            if self.retrograde:

                right_projection = vmath.dot(right_vector, (-100*d_heading[0], -100*d_heading[1]))

                _, projection, target_angle = vmath.angle_between(
                    heading,
                    vmath.smult(-1, d_heading)
                )

            else:

                right_projection = vmath.dot(right_vector, target_local_pos)

                _, projection, target_angle = vmath.angle_between(
                    heading,
                    target_local_pos,
                    precomp_dist=target_dist
                )

            # Visualize vectors if provided with drawing surface
            if screen:

                pygame.draw.line(screen, (255, 255, 255), ap, (ap[0] + heading[0] * 150, ap[1] + heading[1] * 150), 4)          # Draw heading                                               # White = ship_heading

                # Draw bounding box around self.surf
                pygame.draw.rect(screen, (255, 255, 0), (ap[0]-self.surf.get_width()/2, ap[1]-self.surf.get_height()/2, self.surf.get_width(), self.surf.get_height()), 1)

                # Draw triangle connecting ship, right_projection, and target
                pygame.draw.lines(screen, (0, 0, 255), True, (ap, (ap[0]+right_vector[0]*right_projection, ap[1]+right_vector[1]*right_projection), tap), 4)               # Blue = ship - right_projection - target triangle
                pygame.draw.line(screen, (255, 0, 0), ap, (ap[0]+right_vector[0]*right_projection, ap[1]+right_vector[1]*right_projection), 4)   # Draw right_projection   # Red = right_projection
                pygame.draw.line(screen, (0, 255, 0), ap, (ap[0] + right_vector[0] * 100, ap[1] + right_vector[1] * 100), 3)  # Draw right vector                          # Green = right_vector

                # Velocity vector
                pygame.draw.line(screen, (255, 255, 255), ap,
                                 (ap[0] + self.vel[0] * 1000 / tick, ap[1] + self.vel[1] * 1000 / tick),
                                 5)
                pygame.draw.line(screen, (0, 0, 0), ap,
                                 (ap[0] + self.vel[0] * 1000 / tick, ap[1] + self.vel[1] * 1000 / tick),
                                 3)

                # Cruising vector
                h = vmath.normalize(self.vel)
                pygame.draw.line(screen, (255, 0, 0), ap,
                                 (ap[0] + h[0] * self.cruise_vel, ap[1] + h[1] * self.cruise_vel),
                                 5)
                pygame.draw.line(screen, (0, 0, 0), ap,
                                 (ap[0] + h[0] * self.cruise_vel, ap[1] + h[1] * self.cruise_vel),
                                 3)

            # Target is to the right of ship
            if right_projection >= 0:
                rot_change = vmath.clamp(-(target_angle+self.rot_vel/(self.turn_rate*tick/1000))*tick/1000, -self.turn_rate * tick / 1000, self.turn_rate * tick / 1000)  # TODO: make turn rate magnitude based off of target_angle (larger angles = larger turn velocities) (somewhat implemented)

            else:
                rot_change = vmath.clamp((target_angle-self.rot_vel/(self.turn_rate*tick/1000))*tick/1000, -self.turn_rate * tick / 1000, self.turn_rate * tick / 1000)

            self.rot_vel = vmath.clamp(self.rot_vel+rot_change, -self.max_turn_rate*tick/1000, self.max_turn_rate*tick/1000)

            # Ship thruster control
            if speed > 0:

                # If retrograde flag set, burn retrograde until speed < 2/3 * cruising speed
                if self.retrograde:

                    if speed*1000/tick >= 2*self.cruise_vel/3:

                        if target_angle < 10:
                            self.toggle_thrusters(True)

                        else:
                            self.toggle_thrusters(False)

                    else:
                        self.retrograde = False

                else:

                    if speed*1000/tick >= self.max_vel:
                        self.retrograde = True

                    else:

                        _, d_projection, heading_angle = vmath.angle_between(
                            d_heading,
                            target_local_pos,
                                precomp_dist=target_dist
                            )

                        # If ship isn't traveling towards target and ship is pointed at target, and ship is traveling under cruising speed, activate engine
                        if target_angle < 10:

                            if speed < self.cruise_vel * tick / 1000:
                                self.toggle_thrusters(True)

                            elif not (heading_angle < 10):
                                self.toggle_thrusters(True)

                            else:
                                self.toggle_thrusters(False)

                        else:
                            self.toggle_thrusters(False)

            else:
                self.toggle_thrusters(True)

            # Turn the turrets based off of turret position
            for turret in self.turrets:
                if turret[0][2]:    # If gimbal locked then don't pivot turrets
                    print(turret)
                    continue

                # Calculate absolute XY coordinate of turret
                turret_pos_scale: XYRatio = turret[0][0]    # Tuple of ratios representing turret position on self sprite
                turret_surf = turret[1]

                turret_x_unrot, turret_y_unrot, *_, turret_ap = self.calculate_rotated_position_of(turret_pos_scale, origin_ap=ap)

                turret_slope = math.tan(math.radians(90 + self.rot + turret[0][3]))
                if -90 < self.rot + turret[0][3] < 90:
                    turret_heading = vmath.normalize((1 / turret_slope, -1))

                else:
                    turret_heading = vmath.normalize((-1 / turret_slope, 1))

                # Calculate position of target relative to turret_ap
                target_rel_pos = vmath.sub(
                    tap,
                    turret_ap
                )

                turret_right_vector = (-turret_heading[1], turret_heading[0])
                turret_right_projection = vmath.dot(turret_right_vector, target_rel_pos)

                _, t_projection, t_angle = vmath.angle_between(
                    turret_heading,
                    target_rel_pos
                )

                # Visualize turret heading and projection
                if screen:

                    # Draw unrotated and rotated positions
                    pygame.draw.circle(screen, (255, 255, 255), (int(ap[0] + turret_x_unrot), int(ap[1] + turret_y_unrot)), 4)
                    pygame.draw.circle(screen, (255, 255, 255), list(map(int, turret_ap)), 3)
                    pygame.draw.circle(screen, (255, 0, 255), tap, 5)
                    pygame.draw.circle(screen, (100, 0, 100), (int(turret_ap[0]+target_rel_pos[0]), int(turret_ap[1]+target_rel_pos[1])), 3)

                    pygame.draw.line(screen, (150, 150, 150), turret_ap, (turret_ap[0]+turret_heading[0]*100, turret_ap[1]+turret_heading[1]*100), 2)                                                                # Gray = turret_heading
                    pygame.draw.lines(screen, (150, 150, 255), True, (turret_ap, (turret_ap[0]+turret_right_vector[0]*turret_right_projection, turret_ap[1]+turret_right_vector[1]*turret_right_projection), tap), 2)   # Light blue = turret - turret_right_projection - target triangle
                    pygame.draw.line(screen, (255, 150, 150), turret_ap, (turret_ap[0]+turret_right_vector[0]*turret_right_projection, turret_ap[1]+turret_right_vector[1]*turret_right_projection), 2)                 # Light red = turret_right_projection
                    pygame.draw.line(screen, (150, 255, 150), turret_ap, (turret_ap[0]+turret_right_vector[0]*100, turret_ap[1]+turret_right_vector[1]*100))                                                             # Light green = turret_right_vector

                # Update turret rotations if not gimbal locked
                if not turret[0][2]:

                    turret_drot = 0     # Turret delta rotation - how much the turret will rotate by

                    if turret_right_projection >= 0:
                        turret_drot = -(turret[0][4] * tick / 1000) * (1 if t_angle > 5 else t_angle/5)

                    else:
                        turret_drot = (turret[0][4] * tick / 1000) * (1 if t_angle > 5 else t_angle/5)

                    turret[0][3] += turret_drot

                # Set fire marker if t_angle within certain bounds and in range
                turret_range = GameObject.GUN_STATS[turret[0][1]]["RANGE"]
                if (t_angle < 10) and target_dist <= turret_range:
                    turret[2] = True

                else:
                    turret[2] = False

        self.update_ship_physics(tick, label=label)  # Actually update ship position, rotation

    def update_ship_physics(self, tick, label=None):

        # Rotate the ship (self.rot, not the sprite)
        if not self.rot_locked:
            self.rot += self.rot_vel

        # Update ship velocity/thrusters
        if self.category == GameObject.ACTIVE:

            slope, heading = self.calculate_ship_heading()

            for thruster in self.thrusters:

                if thruster[2]:
                    self.vel = vmath.add(self.vel, vmath.smult((thruster[0][2]/self.mass)*tick/1000, heading))

        # Clamp ship and turret rotation between -180 and 180, TODO: DETERMINE IF NECESSARY
        if self.rot <= -180:
            self.rot = 360 - self.rot
        elif self.rot > 180:
            self.rot = self.rot - 360

        for turret in self.turrets:
            if turret[0][3] <= -180:
                turret[0][3] = 360 - turret[0][3]
            elif turret[0][3] > 180:
                turret[0][3] = turret[0][3] - 360

        # Update ship position based off of velocity
        self.offset_ship(self.vel)

    def receive_damage(self, damage, mixer=None):       # Mixer is for sounds and sound effects

        # Take away damage from health and then handle destruction if health is 0 or less
        self.health -= damage

        if self.health <= 0:
            self.destroy(mixer=mixer)

    def destroy(self, explosion=True, mixer=None):

        # Draw any explosion graphics, etc., remove self from sprite groups, and unparent self to stop rendering it
        if explosion:
            pass    # TODO

        self.kill()     # Remove from groups
        self.parent = None

    def ratio_to_offset_center(self, ratio):
        """Similar to to_simple() but with no offset and relative to the center of self (self.rel_pos)"""

        return (self.surf.get_width() * (ratio[0] - 0.5),
                self.surf.get_height() * (ratio[1] - 0.5))

    def complex_to_offset_center(self, xy_complex):

        return (xy_complex[0] + self.surf.get_width() * (xy_complex[1] - 0.5),
                xy_complex[2] + self.surf.get_height() * (xy_complex[3] - 0.5))

    def calculate_ship_heading(self):

        # Calculate ship direction (where it's pointed)
        slope = math.tan(math.radians(90 + self.rot))     # Ship rotation in slope form
        if -90 < self.rot < 90:
            heading = vmath.normalize((1/slope, -1))

        else:
            heading = vmath.normalize((-1/slope, 1))

        return slope, heading

    def calculate_rotated_position_of(self, local_pos, origin_ap=None):
        "Returns a variety of variables containing information about position relative to self when rotation is applied"

        ap = origin_ap if origin_ap else self.calculate_absolute_position()

        if len(local_pos) == 2:
            rel_x_unrot, rel_y_unrot = self.ratio_to_offset_center(local_pos)

        elif len(local_pos) == 4:
            rel_x_unrot, rel_y_unrot = self.complex_to_offset_center(local_pos)

        else:
            raise ValueError("local_pos argument must be tuple of length 2 or 4 (ratio or xycomplex). Current length:", len(local_pos))

        rel_x_rot = rel_x_unrot * math.cos(math.radians(-self.rot)) - rel_y_unrot * math.sin(math.radians(-self.rot))
        rel_y_rot = rel_y_unrot * math.cos(math.radians(-self.rot)) + rel_x_unrot * math.sin(math.radians(-self.rot))

        ap_rot = (ap[0] + rel_x_rot, ap[1] + rel_y_rot)

        return rel_x_unrot, rel_y_unrot, rel_x_rot, rel_y_rot, ap_rot

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

    def toggle_thrusters(self, activation):

        for thruster in self.thrusters:
            thruster[2] = activation

    def draw_seq(self):

        bb = True      # Whether or not to draw  bounding boxes
        draw_mask = False

        self.surf = self.c_surf.copy()
        rotated_sprite = pygame.transform.rotate(self.surf, self.rot)   # Used for mask updating

        # Draw turrets and thrusters
        for turret in self.turrets:

            turret_sprite = turret[1].copy()
            turret_position = turret[0][0]

            turret_rotated_surface = pygame.transform.rotate(turret_sprite, turret[0][3])

            # Draw unrotated bounding box around turret
            if bb:
                pygame.draw.rect(turret_rotated_surface, (155, 155, 155), (0, 0, turret_rotated_surface.get_width(), turret_rotated_surface.get_height()), 1)

            self.surf.blit(
                turret_rotated_surface,
                (turret_position[0]*self.surf.get_width()-turret_rotated_surface.get_width()/2,
                 turret_position[1]*self.surf.get_height()-turret_rotated_surface.get_height()/2)
            ) # Blit at center

        # Draw thruster exhaust on parent surface because this will likely surpass the clipping of self surface
        for thruster in self.thrusters:

            exhaust_sprite = thruster[1].copy()
            rotated_exhaust = pygame.transform.rotate(exhaust_sprite, self.rot)

            # Offset so that the anchor point is top center
            thruster_position = (0, thruster[0][0][0], exhaust_sprite.get_height()/2-2, thruster[0][0][1])

            *_, thruster_draw_position = self.calculate_rotated_position_of(thruster_position)

            if thruster[2]:
                self.parent.surf.blit(
                    rotated_exhaust,
                    (thruster_draw_position[0]-rotated_exhaust.get_width()/2,
                     thruster_draw_position[1]-rotated_exhaust.get_height()/2,)
                )

        # Draw rotated bounding box around self sprite
        if bb:
            pygame.draw.rect(self.surf, (255, 255, 255), (0, 0, self.surf.get_width(), self.surf.get_height()), 2)
            pygame.draw.rect(self.parent.surf, (255, 255, 255), self.rect, 2)

        self.draw_children(False)
        self.draw(bb=bb)

        self.update_rect()

        if self.has_mask:
            self.mask = pygame.mask.from_surface(rotated_sprite)

        if draw_mask:
            olist = self.mask.outline()
            pygame.draw.polygon(self.parent.surf, (200, 150, 150), list(map(lambda point: (point[0]+self.rect.topleft[0], point[1]+self.rect.topleft[1]), olist)), 0)


class Projectile(Sprite):

    PROJECTILES = pygame.sprite.Group()

    def __init__(self,
                 team,
                 stats,     # Damage, travel velocity (vector in pixels per second)
                 sprite,    # Either a string (filepath) or surface
                 sprite_size: XYResize,
                 static_mask=True):

        super().__init__((0, 0, 0, 0), sprite)
        Projectile.PROJECTILES.add(self)
        self.surf = resize(self.surf, sprite_size)

        self.team = team

        self.damage = stats["DAMAGE"]
        self.vel = stats["VEL"]         # Velocity in pixels per second

        self.static_mask = static_mask      # Whether or not to update mask every tick()

    def tick(self, tick, screen=None, mixer=None):      # Mixer is for sound effects

        # Test for collisions and move projectile
        self.handle_gameobject_interactions(mixer=mixer)   # Handle GameObject collision with this
        self.update_physics(tick)

    def handle_gameobject_interactions(self, mixer=None):

        go_collision = pygame.sprite.spritecollideany(self, GameObject.GAME_OBJECTS, ppm_detected)

        if go_collision:

            # Damage ship if ship is not on same team as this
            if go_collision.team != self.team:
                go_collision.receive_damage(self.damage)    # TODO: Implement

                self.kill()     # TODO: Play hit music
                self.parent = None

    def update_physics(self, tick):

        # Add velocity to positional offsets
        self.rel_pos[1] += self.vel[0] * tick/1000
        self.rel_pos[3] += self.vel[1] * tick / 1000

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
