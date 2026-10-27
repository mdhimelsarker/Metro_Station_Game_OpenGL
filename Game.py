from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import math

# Game States
STATE_START = 0
STATE_RUNNING = 1
STATE_WIN = 2
STATE_LOSE = 3
STATE_STATION_STOP = 4

# Physics & Game Variables
train_position = -1200.0  # Moves along Y axis
velocity = 0.0
acceleration = 0.08
brake_power = 0.35
max_speed = 15.0
friction = 0.001
game_state = STATE_START

# Station and Stop Zone details
dest_centers = [650.0 + i * 1850.0 for i in range(9)]
station_names = [
    "Uttara North",
    "Uttara Center",
    "Uttara South",
    "Pallabi",
    "Mirpur 11",
    "Mirpur 10",
    "Kazipara",
    "Shewrapara",
    "Agargaon"
]
current_station_idx = 0
tolerance = 45.0

# Multi-station play variables
station_stop_timer = 0
door_open_ratio = 0.0
score = 0
overspeed_timer = 0
speed_limit = 12.5
stop_message = ""
stop_points = 0
lose_reason = ""
has_departed = False
key_states = {b'w': False, b' ': False}
cheat_mode = False

# Camera Orbit Variables
camera_angle = 4.712   # Radians around train Y axis (directly behind the train)
camera_height = 160.0  # Z height of camera
camera_radius = 280.0  # Orbit radius

# Camera Modes
CAMERA_THIRD_PERSON = 0
CAMERA_FIRST_PERSON = 1
camera_mode = CAMERA_THIRD_PERSON


# Setup procedural background buildings
buildings = []
# Left side buildings (Y from -20000 to 20000)
for y in range(-20000, 20100, 250):
    h = 180 + (abs(y) % 7) * 45
    w = 60 + (abs(y) % 3) * 20
    d = 70 + (abs(y) % 5) * 15
    r = 0.55 + (abs(y) % 4) * 0.06
    g = 0.60 + (abs(y) % 3) * 0.08
    b = 0.65 + (abs(y) % 5) * 0.05
    buildings.append({
        'x': -180 - w/2,
        'y': y,
        'z': h/2,
        'w': w,
        'd': d,
        'h': h,
        'color': (r, g, b)
    })

# Right side buildings (Y from -20000 to 20000, further back behind the platform)
for y in range(-20000, 20100, 300):
    h = 150 + (abs(y) % 9) * 40
    w = 70 + (abs(y) % 4) * 15
    d = 80 + (abs(y) % 3) * 20
    # Bright daylight colors: pastels, light greys, beige, terra cotta
    r = 0.52 + (abs(y) % 5) * 0.06
    g = 0.58 + (abs(y) % 4) * 0.07
    b = 0.64 + (abs(y) % 6) * 0.04
    buildings.append({
        'x': 200 + w/2,
        'y': y,
        'z': h/2,
        'w': w,
        'd': d,
        'h': h,
        'color': (r, g, b)
    })

# Far Left background buildings (placed behind the left buildings, further out at X ≈ -340)
for y in range(-20000, 20100, 280):  # slightly offset in Y to fill gaps
    h = 160 + (abs(y) % 8) * 50
    w = 55 + (abs(y) % 4) * 15
    d = 65 + (abs(y) % 3) * 20
    # Atmospheric perspective: slightly less saturated, slightly darker colors
    r = 0.45 + (abs(y) % 4) * 0.05
    g = 0.50 + (abs(y) % 3) * 0.06
    b = 0.58 + (abs(y) % 5) * 0.04
    buildings.append({
        'x': -340 - w/2,
        'y': y + 40,  # stagger them to peek through gaps
        'z': h/2,
        'w': w,
        'd': d,
        'h': h,
        'color': (r, g, b)
    })

# Far Right background buildings (placed behind the right buildings, further out at X ≈ 360)
for y in range(-20000, 20100, 320):
    h = 140 + (abs(y) % 6) * 60
    w = 65 + (abs(y) % 3) * 20
    d = 75 + (abs(y) % 4) * 15
    r = 0.42 + (abs(y) % 5) * 0.04
    g = 0.48 + (abs(y) % 4) * 0.05
    b = 0.56 + (abs(y) % 6) * 0.03
    buildings.append({
        'x': 360 + w/2,
        'y': y + 60,  # stagger them
        'z': h/2,
        'w': w,
        'd': d,
        'h': h,
        'color': (r, g, b)
    })


# Setup procedural trees
trees = []
random.seed(99)  # For consistent placement
for y in range(-20000, 20000, 200):  # Slightly spaced for performance over 40k units
    # Left side tree
    lx = -75.0 + random.uniform(-8.0, 8.0)
    ly = y + random.uniform(-10.0, 10.0)
    lh = random.uniform(25.0, 35.0)  # trunk height
    trees.append((lx, ly, lh))

    # Right side tree
    rx = 85.0 + random.uniform(-8.0, 8.0)
    ry = y + random.uniform(-10.0, 10.0)
    rh = random.uniform(25.0, 35.0)
    trees.append((rx, ry, rh))


def draw_shaded_cube(x, y, z, sx, sy, sz, color):
    """
    Draws a custom 3D cube with manually shaded faces to look 
    premium without complex lighting shaders.
    """
    r, g, b = color
    c_top = (min(1.0, r * 1.3), min(1.0, g * 1.3), min(1.0, b * 1.3))
    c_bottom = (r * 0.4, g * 0.4, b * 0.4)
    c_sides_y = (r * 0.75, g * 0.75, b * 0.75)
    c_sides_x = (r * 0.95, g * 0.95, b * 0.95)

    glPushMatrix()
    glTranslatef(x, y, z)
    glScalef(sx, sy, sz)

    glBegin(GL_QUADS)
    # Top (+Z)
    glColor3f(*c_top)
    glVertex3f(-0.5, -0.5, 0.5)
    glVertex3f(0.5, -0.5, 0.5)
    glVertex3f(0.5, 0.5, 0.5)
    glVertex3f(-0.5, 0.5, 0.5)

    # Bottom (-Z)
    glColor3f(*c_bottom)
    glVertex3f(-0.5, -0.5, -0.5)
    glVertex3f(0.5, -0.5, -0.5)
    glVertex3f(0.5, 0.5, -0.5)
    glVertex3f(-0.5, 0.5, -0.5)

    # Front (+Y)
    glColor3f(*c_sides_y)
    glVertex3f(-0.5, 0.5, -0.5)
    glVertex3f(0.5, 0.5, -0.5)
    glVertex3f(0.5, 0.5, 0.5)
    glVertex3f(-0.5, 0.5, 0.5)

    # Back (-Y)
    glColor3f(*c_sides_y)
    glVertex3f(-0.5, -0.5, -0.5)
    glVertex3f(0.5, -0.5, -0.5)
    glVertex3f(0.5, -0.5, 0.5)
    glVertex3f(-0.5, -0.5, 0.5)

    # Right (+X)
    glColor3f(*c_sides_x)
    glVertex3f(0.5, -0.5, -0.5)
    glVertex3f(0.5, 0.5, -0.5)
    glVertex3f(0.5, 0.5, 0.5)
    glVertex3f(0.5, -0.5, 0.5)

    # Left (-X)
    glColor3f(*c_sides_x)
    glVertex3f(-0.5, -0.5, -0.5)
    glVertex3f(-0.5, 0.5, -0.5)
    glVertex3f(-0.5, 0.5, 0.5)
    glVertex3f(-0.5, -0.5, 0.5)
    glEnd()

    glPopMatrix()


def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    """
    Renders 2D text overlay using orthographic projection.
    """
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_pillars():
    # Track pillars (every 150 units along Y, extending up to Y=16500)
    for y in range(-1650, 16500, 150):
        if abs(y - train_position) > 3000:
            continue
        # Concrete column (X=0, Z=0 to 40, height=40, width=12, depth=12)
        draw_shaded_cube(0, y, 20.0, 12, 12, 40, (0.65, 0.65, 0.68))
        
        # Pillar cap (slightly wider top, Z=38 to 40, height=2, width=16, depth=16)
        draw_shaded_cube(0, y, 39.0, 16, 16, 2, (0.7, 0.7, 0.73))

    # Platform pillars (supporting the elevated destination station platforms)
    # Loop over all 9 destination stations
    for i in range(9):
        y_pos = 650.0 + i * 1850.0
        if abs(y_pos - train_position) > 3500:
            continue
        for y in range(int(y_pos) - 400, int(y_pos) + 450, 150):
            # Pillar column (X=34, Z=0 to 36, height=36, width=10, depth=10)
            draw_shaded_cube(34, y, 18.0, 10, 10, 36, (0.65, 0.65, 0.68))

    # Starting platform pillars (supporting the starting station platform at Y=-1200)
    if abs(-1200 - train_position) < 3500:
        for y in [-1350, -1200, -1050]:
            draw_shaded_cube(34, y, 18.0, 10, 10, 36, (0.65, 0.65, 0.68))


def draw_tracks():
    # Elevated Concrete Viaduct base (X=0, Z=40 to 42, width=32, height=2, Y center at 7375, length 18050)
    draw_shaded_cube(0, 7375, 41.0, 32, 18050, 2, (0.6, 0.6, 0.63))

    # Left Rail (Z=42 to 45, center Z=43.5, height=3)
    draw_shaded_cube(-12, 7375, 43.5, 2, 18050, 3, (0.1, 0.1, 0.1))
    # Right Rail
    draw_shaded_cube(12, 7375, 43.5, 2, 18050, 3, (0.1, 0.1, 0.1))

    # Sleepers (Wooden ties, Z=42.5, height=1)
    for y in range(-1600, 16450, 45):
        draw_shaded_cube(0, y, 42.5, 30, 8, 1, (0.35, 0.22, 0.15))


def draw_staircase(platform_x, start_y, direction_y, platform_z=52.0):
    num_steps = 13
    step_height_inc = platform_z / num_steps  # 52.0 / 13 = 4.0
    step_length = 8.0
    stair_width = 10.0
    stair_color = (0.68, 0.68, 0.72)  # slightly darker grey than platform to stand out
    railing_color = (0.15, 0.15, 0.18)  # dark steel/iron railing

    # Draw the steps
    for i in range(num_steps):
        # Steps step down as we move away from start_y along direction_y
        h = platform_z - (i * step_height_inc)
        y = start_y + direction_y * (i * step_length + step_length / 2.0)
        x = platform_x + stair_width / 2.0
        z = h / 2.0
        
        # Step block
        draw_shaded_cube(x, y, z, stair_width, step_length, h, stair_color)

        # Railing post (on the outer edge: X = platform_x + stair_width - 0.5)
        rx = platform_x + stair_width - 0.5
        ry = y
        rz_base = h
        rz_height = 12.0
        draw_shaded_cube(rx, ry, rz_base + rz_height / 2.0, 0.6, 0.6, rz_height, railing_color)

    # Slanted handrail connecting the tops of the posts
    total_length_y = num_steps * step_length
    total_height_z = platform_z
    rail_len = math.sqrt(total_length_y**2 + total_height_z**2)
    angle_rad = math.atan2(total_height_z, total_length_y)
    angle_deg = math.degrees(angle_rad)

    center_y = start_y + direction_y * (total_length_y / 2.0)
    center_z = platform_z / 2.0 + 12.0
    rx = platform_x + stair_width - 0.5

    glPushMatrix()
    glTranslatef(rx, center_y, center_z)
    glRotatef(-direction_y * angle_deg, 1.0, 0.0, 0.0)
    # Handrail bar
    draw_shaded_cube(0.0, 0.0, 0.0, 0.8, rail_len, 0.8, railing_color)
    glPopMatrix()


def draw_platform():
    # ================= STARTING STATION =================
    if abs(-1200 - train_position) < 3500:
        # Platform main structure (elevated deck: Z=36 to 52, height=16, center Z=44)
        # Positioned closer to track at X=34.0, Y=-1200, length 400 (from -1400 to -1000)
        draw_shaded_cube(34, -1200, 44.0, 40, 400, 16, (0.7, 0.7, 0.74))

        # Yellow safety border line on platform edge for starting station
        glColor3f(1.0, 0.8, 0.0)
        glBegin(GL_QUADS)
        glVertex3f(14.2, -1400, 52.05)
        glVertex3f(15.2, -1400, 52.05)
        glVertex3f(15.2, -1000, 52.05)
        glVertex3f(14.2, -1000, 52.05)
        glEnd()

        # Roof Canopy (Navy Blue metal sheet) at Z=83.0
        draw_shaded_cube(33.0, -1200, 83.0, 46, 400, 2, (0.22, 0.3, 0.38))

        # Roof Support Pillars (back of the platform at X=48)
        for y in [-1350, -1200, -1050]:
            # Thin steel support pillar (Z=52 to 82, height=30, center Z=67.0)
            draw_shaded_cube(48.0, y, 67.0, 2, 2, 30, (0.4, 0.42, 0.45))

        # Starting platform stairs (at the back X=44.0, from Y=-1000.0 going down in +Y direction)
        draw_staircase(44.0, -1000.0, 1)

    # ================= DESTINATION STATIONS (9 Stations) =================
    for i in range(9):
        y_pos = 650.0 + i * 1850.0
        if abs(y_pos - train_position) > 3500:
            continue
        
        # Platform main structure (elevated deck: Z=36 to 52, height=16, center Z=44)
        draw_shaded_cube(34, y_pos, 44.0, 40, 900, 16, (0.7, 0.7, 0.74))

        # Yellow safety border line on platform edge
        # Edge is at X=14.0, platform top is Z=52
        glColor3f(1.0, 0.8, 0.0)
        glBegin(GL_QUADS)
        glVertex3f(14.2, y_pos - 450, 52.05)
        glVertex3f(15.2, y_pos - 450, 52.05)
        glVertex3f(15.2, y_pos + 450, 52.05)
        glVertex3f(14.2, y_pos + 450, 52.05)
        glEnd()

        # Bright green Stop Zone patch on the platform surface
        # From Y = y_pos - 50 to y_pos + 50
        glColor3f(0.1, 0.85, 0.25)
        glBegin(GL_QUADS)
        glVertex3f(15.2, y_pos - 50, 52.1)
        glVertex3f(53.0, y_pos - 50, 52.1)
        glVertex3f(53.0, y_pos + 50, 52.1)
        glVertex3f(15.2, y_pos + 50, 52.1)
        glEnd()

        # Safety border outline for the Stop Zone
        glColor3f(1.0, 1.0, 1.0)
        glLineWidth(2)
        glBegin(GL_LINE_LOOP)
        glVertex3f(15.2, y_pos - 50, 52.15)
        glVertex3f(53.0, y_pos - 50, 52.15)
        glVertex3f(53.0, y_pos + 50, 52.15)
        glVertex3f(15.2, y_pos + 50, 52.15)
        glEnd()
        glLineWidth(1)

        # 3D Visual Stop Zone Alignment Poles (for Third Person camera assistance)
        # Start of Stop Zone (Orange-red pole)
        draw_shaded_cube(14.8, y_pos - tolerance, 62.0, 1.2, 1.2, 20.0, (1.0, 0.3, 0.1))
        
        # Center of Stop Zone (Bright Green pole)
        draw_shaded_cube(14.8, y_pos, 63.0, 1.2, 1.2, 22.0, (0.1, 0.9, 0.3))
        
        # End of Stop Zone (Orange-red pole)
        draw_shaded_cube(14.8, y_pos + tolerance, 62.0, 1.2, 1.2, 20.0, (1.0, 0.3, 0.1))

        # Roof Canopy (Navy Blue metal sheet) at Z=83.0
        draw_shaded_cube(33.0, y_pos, 83.0, 46, 900, 2, (0.22, 0.3, 0.38))

        # Roof Support Pillars (back of the platform at X=48)
        for y in range(int(y_pos) - 400, int(y_pos) + 450, 150):
            draw_shaded_cube(48.0, y, 67.0, 2, 2, 30, (0.4, 0.42, 0.45))

        # Destination platform stairs (at both ends, X=44.0)
        draw_staircase(44.0, y_pos - 450, -1)   # going down in -Y direction
        draw_staircase(44.0, y_pos + 450, 1)    # going down in +Y direction


def draw_yellow_cross_board():
    # === BOARD AT THE END OF THE TRACK (Y = 16400, facing -Y) ===
    # 1. Vertical support post (from Z=42 to Z=66, height=24, centered at Z=54)
    # Placed in the center of the track (X=0) at Y=16400.
    draw_shaded_cube(0.0, 16400.0, 54.0, 2.0, 2.0, 24.0, (0.25, 0.25, 0.25))

    # 2. Yellow circular/square board (centered at Z=66, Y=16399 to face incoming train)
    # Size: X=14, Y=0.8, Z=14
    draw_shaded_cube(0.0, 16399.0, 66.0, 14.0, 0.8, 14.0, (1.0, 0.85, 0.0))

    # 3. Black cross 'X' on the front face of the board (Y=16398.5 to prevent Z-fighting)
    glPushMatrix()
    glTranslatef(0.0, 16398.5, 66.0)
    glRotatef(45.0, 0.0, 1.0, 0.0)
    draw_shaded_cube(0.0, 0.0, 0.0, 16.0, 0.4, 2.5, (0.05, 0.05, 0.05))
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0.0, 16398.5, 66.0)
    glRotatef(-45.0, 0.0, 1.0, 0.0)
    draw_shaded_cube(0.0, 0.0, 0.0, 16.0, 0.4, 2.5, (0.05, 0.05, 0.05))
    glPopMatrix()

    # === BOARD AT THE START OF THE TRACK (Y = -1640, facing +Y) ===
    # 1. Vertical support post
    draw_shaded_cube(0.0, -1640.0, 54.0, 2.0, 2.0, 24.0, (0.25, 0.25, 0.25))

    # 2. Yellow circular/square board (facing incoming train from +Y, so Y = -1639.0)
    draw_shaded_cube(0.0, -1639.0, 66.0, 14.0, 0.8, 14.0, (1.0, 0.85, 0.0))

    # 3. Black cross 'X' on the front face of the board (Y = -1638.5 to prevent Z-fighting)
    glPushMatrix()
    glTranslatef(0.0, -1638.5, 66.0)
    glRotatef(45.0, 0.0, 1.0, 0.0)
    draw_shaded_cube(0.0, 0.0, 0.0, 16.0, 0.4, 2.5, (0.05, 0.05, 0.05))
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0.0, -1638.5, 66.0)
    glRotatef(-45.0, 0.0, 1.0, 0.0)
    draw_shaded_cube(0.0, 0.0, 0.0, 16.0, 0.4, 2.5, (0.05, 0.05, 0.05))
    glPopMatrix()


def draw_train():
    if camera_mode == CAMERA_FIRST_PERSON:
        # Draw the locomaster's cabin console, windshield frame, and console lights from inside
        # 1. Dashboard Console (Y from Y_center+101.5 to Y_center+105.5)
        draw_shaded_cube(0.0, train_position + 103.5, 58.0, 22, 4, 8, (0.2, 0.22, 0.25))

        # Central Glowing Blue Screen (Digital Speed HUD)
        glColor3f(0.05, 0.1, 0.2)  # Dark screen background
        glBegin(GL_QUADS)
        glVertex3f(-2.5, train_position + 101.4, 56.5)
        glVertex3f(2.5, train_position + 101.4, 56.5)
        glVertex3f(2.5, train_position + 101.4, 59.5)
        glVertex3f(-2.5, train_position + 101.4, 59.5)
        glEnd()

        # Digital HUD Speed Bar on dashboard screen
        # Background track
        glColor3f(0.0, 0.2, 0.25)
        glBegin(GL_QUADS)
        glVertex3f(-2.0, train_position + 101.35, 57.5)
        glVertex3f(2.0, train_position + 101.35, 57.5)
        glVertex3f(2.0, train_position + 101.35, 58.5)
        glVertex3f(-2.0, train_position + 101.35, 58.5)
        glEnd()
        # Glowing active speed bar
        speed_ratio = min(1.0, max(0.0, velocity / max_speed))
        fill_w = 4.0 * speed_ratio
        glColor3f(0.0, 0.95, 0.8)
        glBegin(GL_QUADS)
        glVertex3f(-2.0, train_position + 101.32, 57.5)
        glVertex3f(-2.0 + fill_w, train_position + 101.32, 57.5)
        glVertex3f(-2.0 + fill_w, train_position + 101.32, 58.5)
        glVertex3f(-2.0, train_position + 101.32, 58.5)
        glEnd()

        # Left Analog Dial (Speedometer background)
        glColor3f(0.95, 0.95, 0.95)
        glBegin(GL_QUADS)
        glVertex3f(-5.5, train_position + 101.4, 56.5)
        glVertex3f(-4.0, train_position + 101.4, 56.5)
        glVertex3f(-4.0, train_position + 101.4, 58.0)
        glVertex3f(-5.5, train_position + 101.4, 58.0)
        glEnd()
        # Dynamic Speedometer Needle
        speed_angle = -90.0 + 180.0 * speed_ratio
        speed_rad = math.radians(speed_angle)
        needle_dx = 0.6 * math.sin(speed_rad)
        needle_dz = 0.6 * math.cos(speed_rad)
        glColor3f(0.9, 0.1, 0.1)
        glLineWidth(3)
        glBegin(GL_LINES)
        glVertex3f(-4.75, train_position + 101.35, 57.25)
        glVertex3f(-4.75 + needle_dx, train_position + 101.35, 57.25 + needle_dz)
        glEnd()
        glLineWidth(1)

        # Right Analog Dial (White background)
        glColor3f(0.95, 0.95, 0.95)
        glBegin(GL_QUADS)
        glVertex3f(4.0, train_position + 101.4, 56.5)
        glVertex3f(5.5, train_position + 101.4, 56.5)
        glVertex3f(5.5, train_position + 101.4, 58.0)
        glVertex3f(4.0, train_position + 101.4, 58.0)
        glEnd()
        # Red needle on right dial
        glColor3f(0.9, 0.1, 0.1)
        glLineWidth(2)
        glBegin(GL_LINES)
        glVertex3f(4.75, train_position + 101.35, 57.25)
        glVertex3f(5.2, train_position + 101.35, 57.7)
        glEnd()
        glLineWidth(1)

        # Status lights on console
        # Green status light
        glColor3f(0.1, 1.0, 0.1)
        glPushMatrix()
        glTranslatef(-8.0, train_position + 101.4, 57.5)
        glutSolidCube(0.8)
        glPopMatrix()

        # Red warning light
        glColor3f(1.0, 0.1, 0.1)
        glPushMatrix()
        glTranslatef(-6.7, train_position + 101.4, 57.5)
        glutSolidCube(0.8)
        glPopMatrix()

        # Yellow indicator light
        glColor3f(1.0, 0.8, 0.1)
        glPushMatrix()
        glTranslatef(6.7, train_position + 101.4, 57.5)
        glutSolidCube(0.8)
        glPopMatrix()

        # Blue indicator light
        glColor3f(0.1, 0.5, 1.0)
        glPushMatrix()
        glTranslatef(8.0, train_position + 101.4, 57.5)
        glutSolidCube(0.8)
        glPopMatrix()

        # 2. Windshield Wipers resting at the bottom of the window glass
        glColor3f(0.08, 0.08, 0.1)
        glLineWidth(4)
        glBegin(GL_LINES)
        # Left wiper
        glVertex3f(-8.5, train_position + 104.3, 62.5)
        glVertex3f(-3.5, train_position + 104.3, 64.0)
        # Right wiper
        glVertex3f(1.5, train_position + 104.3, 62.5)
        glVertex3f(6.5, train_position + 104.3, 64.0)
        glEnd()
        glLineWidth(1)

        # 3. Throttle and Brake Levers sticking up from dashboard top (Z=62)
        # Left throttle lever (Red handle)
        draw_shaded_cube(-5.0, train_position + 102.5, 63.5, 0.4, 0.4, 3.0, (0.6, 0.6, 0.6))
        glColor3f(0.9, 0.1, 0.1)
        glPushMatrix()
        glTranslatef(-5.0, train_position + 102.5, 65.2)
        glutSolidSphere(0.6, 8, 8)
        glPopMatrix()

        # Right brake lever (Blue handle)
        draw_shaded_cube(5.0, train_position + 102.5, 63.5, 0.4, 0.4, 3.0, (0.6, 0.6, 0.6))
        glColor3f(0.1, 0.2, 0.9)
        glPushMatrix()
        glTranslatef(5.0, train_position + 102.5, 65.2)
        glutSolidSphere(0.6, 8, 8)
        glPopMatrix()

        # 4. Window Frame / Windshield Border
        # Top frame
        draw_shaded_cube(0.0, train_position + 104.5, 76.0, 24, 2, 3, (0.12, 0.12, 0.14))
        # Left pillar
        draw_shaded_cube(-11.5, train_position + 104.5, 67.0, 1, 2, 16, (0.12, 0.12, 0.14))
        # Right pillar
        draw_shaded_cube(11.5, train_position + 104.5, 67.0, 1, 2, 16, (0.12, 0.12, 0.14))
        return

    # Draw the 3 separate coaches
    # Coach coordinates (Y centers relative to train_position)
    coach_centers = [73.0, 0.0, -73.0]

    for dy in coach_centers:
        # 1. Main Body of Coach (Length 66, Width 28, Height 28, Center Z=62)
        draw_shaded_cube(0, train_position + dy, 62.0, 28, 66, 28, (0.8, 0.83, 0.88))

        # Roof of Coach (Dark grey)
        draw_shaded_cube(0, train_position + dy, 76.5, 28, 66, 1, (0.2, 0.22, 0.25))

        # Undercarriage base of Coach
        draw_shaded_cube(0, train_position + dy, 46.5, 26, 62, 3, (0.1, 0.1, 0.1))

        # Wheels (Front and back bogies of the coach)
        for w_offset in [-22, 22]:
            # Left wheel bogie
            draw_shaded_cube(-12, train_position + dy + w_offset, 44.25, 3.5, 10, 1.5, (0.15, 0.15, 0.15))
            # Right wheel bogie
            draw_shaded_cube(12, train_position + dy + w_offset, 44.25, 3.5, 10, 1.5, (0.15, 0.15, 0.15))

        # Cabin Windows (two windows per side of each coach)
        glColor3f(0.3, 0.6, 0.8)  # Cyan glass glow
        for win_dy in [-20, 20]:
            # Left side windows (pushed further out to X = -14.1 to prevent Z-fighting)
            glBegin(GL_QUADS)
            glVertex3f(-14.1, train_position + dy + win_dy - 7, 58)
            glVertex3f(-14.1, train_position + dy + win_dy + 7, 58)
            glVertex3f(-14.1, train_position + dy + win_dy + 7, 69)
            glVertex3f(-14.1, train_position + dy + win_dy - 7, 69)
            glEnd()

            # Right side windows (pushed further out to X = 14.1 to prevent Z-fighting)
            glBegin(GL_QUADS)
            glVertex3f(14.1, train_position + dy + win_dy - 7, 58)
            glVertex3f(14.1, train_position + dy + win_dy + 7, 58)
            glVertex3f(14.1, train_position + dy + win_dy + 7, 69)
            glVertex3f(14.1, train_position + dy + win_dy - 7, 69)
            glEnd()

    # Draw Bellows/Gangway Connectors (between Coach 1-2, and Coach 2-3)
    # Connector 1
    draw_shaded_cube(0, train_position + 36.5, 59.0, 20, 8, 22, (0.12, 0.12, 0.15))
    # Connector 2
    draw_shaded_cube(0, train_position - 36.5, 59.0, 20, 8, 22, (0.12, 0.12, 0.15))

    # Front Windshield & Headlights on the Front Coach (Coach 1, dy = 73.0)
    glColor3f(0.1, 0.12, 0.16)
    glBegin(GL_QUADS)
    glVertex3f(-11, train_position + 106.15, 60)
    glVertex3f(11, train_position + 106.15, 60)
    glVertex3f(11, train_position + 106.15, 72)
    glVertex3f(-11, train_position + 106.15, 72)
    glEnd()

    # Headlights (Yellow/Golden glow, pushed slightly to 106.2)
    glColor3f(1.0, 0.9, 0.4)
    glPushMatrix()
    glTranslatef(-8, train_position + 106.2, 52)
    glutSolidCube(4.0)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(8, train_position + 106.2, 52)
    glutSolidCube(4.0)
    glPopMatrix()

    # Rear Window on Coach 3 (dy = -73.0)
    glColor3f(0.1, 0.12, 0.16)
    glBegin(GL_QUADS)
    glVertex3f(-11, train_position - 106.15, 60)
    glVertex3f(11, train_position - 106.15, 60)
    glVertex3f(11, train_position - 106.15, 72)
    glVertex3f(-11, train_position - 106.15, 72)
    glEnd()

    # Draw smaller orange doors on both sides (left and right) for all 3 coaches
    for dy in coach_centers:
        for side in [-1, 1]:  # -1 for left side, 1 for right side
            x_pos = side * 14.12
            offset = 5.0 * door_open_ratio

            # --- Leaf 1 (Left leaf of the double door, Y goes from dy-6 to dy) ---
            # Body
            glColor3f(1.0, 0.45, 0.0)
            glBegin(GL_QUADS)
            glVertex3f(x_pos, train_position + dy - 6 - offset, 48)
            glVertex3f(x_pos, train_position + dy - offset, 48)
            glVertex3f(x_pos, train_position + dy - offset, 70)
            glVertex3f(x_pos, train_position + dy - 6 - offset, 70)
            glEnd()

            # Glass window
            glColor3f(0.15, 0.25, 0.35)
            glBegin(GL_QUADS)
            glVertex3f(x_pos + side * 0.05, train_position + dy - 5.0 - offset, 58)
            glVertex3f(x_pos + side * 0.05, train_position + dy - 1.0 - offset, 58)
            glVertex3f(x_pos + side * 0.05, train_position + dy - 1.0 - offset, 67)
            glVertex3f(x_pos + side * 0.05, train_position + dy - 5.0 - offset, 67)
            glEnd()

            # Red alignment indicator line on the edge
            glColor3f(1.0, 0.1, 0.1)
            glLineWidth(3)
            glBegin(GL_LINES)
            glVertex3f(x_pos + side * 0.1, train_position + dy - offset, 48)
            glVertex3f(x_pos + side * 0.1, train_position + dy - offset, 70)
            glEnd()
            glLineWidth(1)

            # --- Leaf 2 (Right leaf of the double door, Y goes from dy to dy+6) ---
            # Body
            glColor3f(1.0, 0.45, 0.0)
            glBegin(GL_QUADS)
            glVertex3f(x_pos, train_position + dy + offset, 48)
            glVertex3f(x_pos, train_position + dy + 6 + offset, 48)
            glVertex3f(x_pos, train_position + dy + 6 + offset, 70)
            glVertex3f(x_pos, train_position + dy + offset, 70)
            glEnd()

            # Glass window
            glColor3f(0.15, 0.25, 0.35)
            glBegin(GL_QUADS)
            glVertex3f(x_pos + side * 0.05, train_position + dy + 1.0 + offset, 58)
            glVertex3f(x_pos + side * 0.05, train_position + dy + 5.0 + offset, 58)
            glVertex3f(x_pos + side * 0.05, train_position + dy + 5.0 + offset, 67)
            glVertex3f(x_pos + side * 0.05, train_position + dy + 1.0 + offset, 67)
            glEnd()

            # Red alignment indicator line on the edge
            glColor3f(1.0, 0.1, 0.1)
            glLineWidth(3)
            glBegin(GL_LINES)
            glVertex3f(x_pos + side * 0.1, train_position + dy + offset, 48)
            glVertex3f(x_pos + side * 0.1, train_position + dy + offset, 70)
            glEnd()
            glLineWidth(1)


def draw_scenery():
    # 1. Draw the Sun FIRST in the background with depth testing disabled!
    # This guarantees the sun is always behind all buildings, trees, and scenery.
    glDisable(GL_DEPTH_TEST)
    glPushMatrix()
    glTranslatef(180.0, train_position + 400.0, 320.0)
    glColor3f(1.0, 0.85, 0.2)
    glutSolidSphere(25.0, 16, 16)
    glPopMatrix()
    glEnable(GL_DEPTH_TEST)

    # 2. Massive Green Grass Ground
    glColor3f(0.22, 0.55, 0.2)  # Natural green grass
    glBegin(GL_QUADS)
    glVertex3f(-20000.0, -20000.0, 0.0)
    glVertex3f(20000.0, -20000.0, 0.0)
    glVertex3f(20000.0, 20000.0, 0.0)
    glVertex3f(-20000.0, 20000.0, 0.0)
    glEnd()

    # 3. Grey Asphalt Highway (Left side)
    glColor3f(0.28, 0.3, 0.32)
    glBegin(GL_QUADS)
    glVertex3f(-160.0, -20000.0, 0.8)
    glVertex3f(-120.0, -20000.0, 0.8)
    glVertex3f(-120.0, 20000.0, 0.8)
    glVertex3f(-160.0, 20000.0, 0.8)
    glEnd()

    # Highway Yellow Dashed Lane Markers
    glColor3f(0.9, 0.8, 0.2)
    glBegin(GL_QUADS)
    for y in range(-20000, 20000, 80):
        glVertex3f(-140.8, y, 1.2)
        glVertex3f(-139.2, y, 1.2)
        glVertex3f(-139.2, y + 40, 1.2)
        glVertex3f(-140.8, y + 40, 1.2)
    glEnd()

    # 4. Blue River (Right side, beyond the platform)
    glColor3f(0.18, 0.48, 0.75)
    glBegin(GL_QUADS)
    glVertex3f(130.0, -20000.0, 0.5)
    glVertex3f(175.0, -20000.0, 0.5)
    glVertex3f(175.0, 20000.0, 0.5)
    glVertex3f(130.0, 20000.0, 0.5)
    glEnd()

    # 3. Buildings on left and right sides (placed at ground level Z=0)
    for b in buildings:
        if abs(b['y'] - train_position) > 3000:
            continue
        draw_shaded_cube(b['x'], b['y'], b['z'], b['w'], b['d'], b['h'], b['color'])

        # Add window grids on building faces facing the track
        bx, by, bz, bw, bd, bh = b['x'], b['y'], b['z'], b['w'], b['d'], b['h']
        glColor3f(0.35, 0.55, 0.7)  # Reflective blue glass windows
        glBegin(GL_QUADS)
        if bx < 0:  # Left side building (face is at bx + bw/2)
            face_x = bx + bw/2 + 0.5
            for wy in range(int(by - bd/2 + 8), int(by + bd/2 - 8), 20):
                for wz in range(20, int(bh - 15), 30):
                    glVertex3f(face_x, wy - 4, wz - 6)
                    glVertex3f(face_x, wy + 4, wz - 6)
                    glVertex3f(face_x, wy + 4, wz + 6)
                    glVertex3f(face_x, wy - 4, wz + 6)
        else:  # Right side building (face is at bx - bw/2)
            face_x = bx - bw/2 - 0.5
            for wy in range(int(by - bd/2 + 8), int(by + bd/2 - 8), 20):
                for wz in range(20, int(bh - 15), 30):
                    glVertex3f(face_x, wy - 4, wz - 6)
                    glVertex3f(face_x, wy + 4, wz - 6)
                    glVertex3f(face_x, wy + 4, wz + 6)
                    glVertex3f(face_x, wy - 4, wz + 6)
        glEnd()

    # 4. Draw trees on the sides
    for tx, ty, th in trees:
        if abs(ty - train_position) > 2500:
            continue
        # Trunk (Brown, center Z = th/2)
        draw_shaded_cube(tx, ty, th/2, 3.5, 3.5, th, (0.42, 0.26, 0.15))

        # Bottom foliage layer (Dark green, center Z = th + 5.0)
        draw_shaded_cube(tx, ty, th + 5.0, 16.0, 16.0, 10.0, (0.08, 0.42, 0.12))

        # Middle foliage layer (Medium green, center Z = th + 12.0)
        draw_shaded_cube(tx, ty, th + 12.0, 12.0, 12.0, 8.0, (0.12, 0.52, 0.18))

        # Top foliage layer (Light/Bright green, center Z = th + 17.5)
        draw_shaded_cube(tx, ty, th + 17.5, 8.0, 8.0, 6.0, (0.18, 0.62, 0.22))


def draw_hud():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glDisable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    # 1. Semi-transparent black background panel at the top (dashboard)
    glColor4f(0.05, 0.05, 0.1, 0.8)
    glBegin(GL_QUADS)
    glVertex2f(0, 680)
    glVertex2f(1000, 680)
    glVertex2f(1000, 800)
    glVertex2f(0, 800)
    glEnd()

    # Blue dashboard boundary line
    glColor4f(0.1, 0.5, 0.9, 0.6)
    glLineWidth(2)
    glBegin(GL_LINES)
    glVertex2f(0, 680)
    glVertex2f(1000, 680)
    glEnd()
    glLineWidth(1)

    # 2. Visual Progress Bar of the Track
    # Map train position (-1200 to 16400) to HUD slider coordinates (450 to 950)
    t_min, t_max = -1200.0, 16400.0
    hud_bar_start, hud_bar_end = 450.0, 950.0

    # Base track line on the slider
    glColor4f(0.2, 0.2, 0.25, 0.8)
    glBegin(GL_QUADS)
    glVertex2f(hud_bar_start, 707)
    glVertex2f(hud_bar_end, 707)
    glVertex2f(hud_bar_end, 713)
    glVertex2f(hud_bar_start, 713)
    glEnd()

    # Draw all 9 station platforms and stop zones on the HUD slider
    for i in range(9):
        y_pos = 650.0 + i * 1850.0
        
        # Platform segment on slider
        p_start = y_pos - 450.0
        p_end = y_pos + 450.0
        x_plat_start = hud_bar_start + (p_start - t_min) / (t_max - t_min) * (hud_bar_end - hud_bar_start)
        x_plat_end = hud_bar_start + (p_end - t_min) / (t_max - t_min) * (hud_bar_end - hud_bar_start)
        
        glColor4f(0.4, 0.4, 0.45, 0.8)
        glBegin(GL_QUADS)
        glVertex2f(x_plat_start, 704)
        glVertex2f(x_plat_end, 704)
        glVertex2f(x_plat_end, 716)
        glVertex2f(x_plat_start, 716)
        glEnd()

        # Stop Zone (Green segment) on slider
        sz_start = y_pos - 50.0
        sz_end = y_pos + 50.0
        x_sz_start = hud_bar_start + (sz_start - t_min) / (t_max - t_min) * (hud_bar_end - hud_bar_start)
        x_sz_end = hud_bar_start + (sz_end - t_min) / (t_max - t_min) * (hud_bar_end - hud_bar_start)
        
        glColor4f(0.1, 0.8, 0.2, 1.0)
        glBegin(GL_QUADS)
        glVertex2f(x_sz_start, 701)
        glVertex2f(x_sz_end, 701)
        glVertex2f(x_sz_end, 719)
        glVertex2f(x_sz_start, 719)
        glEnd()

    # Train Pointer (Red rectangle)
    clamped_pos = max(t_min, min(t_max, train_position))
    x_train = hud_bar_start + (clamped_pos - t_min) / (t_max - t_min) * (hud_bar_end - hud_bar_start)
    glColor4f(1.0, 0.2, 0.2, 1.0)
    glBegin(GL_QUADS)
    glVertex2f(x_train - 7, 696)
    glVertex2f(x_train + 7, 696)
    glVertex2f(x_train + 7, 724)
    glVertex2f(x_train - 7, 724)
    glEnd()

    # 3. Game State Overlays (Win / Lose / Station Stop popups)
    if game_state == STATE_WIN:
        glColor4f(0.02, 0.15, 0.05, 0.95)
        glBegin(GL_QUADS)
        glVertex2f(280, 300)
        glVertex2f(720, 300)
        glVertex2f(720, 480)
        glVertex2f(280, 480)
        glEnd()
        glColor4f(0.2, 0.9, 0.3, 0.9)
        glLineWidth(3)
        glBegin(GL_LINE_LOOP)
        glVertex2f(280, 300)
        glVertex2f(720, 300)
        glVertex2f(720, 480)
        glVertex2f(280, 480)
        glEnd()
        glLineWidth(1)

    elif game_state == STATE_LOSE:
        glColor4f(0.15, 0.02, 0.02, 0.95)
        glBegin(GL_QUADS)
        glVertex2f(280, 300)
        glVertex2f(720, 300)
        glVertex2f(720, 480)
        glVertex2f(280, 480)
        glEnd()
        glColor4f(0.9, 0.2, 0.2, 0.9)
        glLineWidth(3)
        glBegin(GL_LINE_LOOP)
        glVertex2f(280, 300)
        glVertex2f(720, 300)
        glVertex2f(720, 480)
        glVertex2f(280, 480)
        glEnd()
        glLineWidth(1)

    elif game_state == STATE_STATION_STOP:
        glColor4f(0.05, 0.1, 0.15, 0.95)
        glBegin(GL_QUADS)
        glVertex2f(280, 300)
        glVertex2f(720, 300)
        glVertex2f(720, 480)
        glVertex2f(280, 480)
        glEnd()
        glColor4f(0.3, 0.6, 0.9, 0.9)
        glLineWidth(3)
        glBegin(GL_LINE_LOOP)
        glVertex2f(280, 300)
        glVertex2f(720, 300)
        glVertex2f(720, 480)
        glVertex2f(280, 480)
        glEnd()
        glLineWidth(1)

    glDisable(GL_BLEND)
    glEnable(GL_DEPTH_TEST)

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

    # 4. Text Content Rendering

    # Speedometer (Scaled velocity to represent realistic kph)
    speed_kph = abs(velocity) * 8.0
    speed_limit_kph = speed_limit * 8.0
    draw_text(20, 765, f"Speed: {speed_kph:.1f} km/h (Limit: {speed_limit_kph:.0f} km/h)")

    # Overspeed Warning alert
    if velocity > speed_limit:
        if (int(overspeed_timer) // 10) % 2 == 0:
            glColor3f(1.0, 0.1, 0.1)
            draw_text(220, 760, "OVERSPEED WARNING! SLOW DOWN!", GLUT_BITMAP_HELVETICA_18)
            glColor3f(1, 1, 1)

    # Distance helper & Progress details
    target_idx = min(8, current_station_idx)
    target_y = dest_centers[target_idx]
    dist_to_sz = target_y - train_position
    if game_state == STATE_STATION_STOP and stop_message == "PERFECT":
        dist_to_sz = 0.0

    draw_text(20, 740, f"Next Station: {station_names[target_idx]} ({target_idx + 1}/9)")
    draw_text(20, 715, f"Score: {score} PTS")

    if game_state == STATE_START:
        draw_text(20, 690, f"Next Stop: {dist_to_sz:.1f} m ahead")
    elif game_state in (STATE_RUNNING, STATE_STATION_STOP):
        if dist_to_sz >= -tolerance:
            draw_text(20, 690, f"Distance to Stop Zone: {dist_to_sz:.1f} m")
        else:
            draw_text(20, 690, f"OVERSHOT STATION BY: {-dist_to_sz:.1f} m")

    # Game state descriptions
    if game_state == STATE_START:
        draw_text(550, 745, "READY TO DEPART - PRESS [W] TO ACCELERATE", GLUT_BITMAP_HELVETICA_12)
    elif game_state == STATE_RUNNING and not has_departed:
        target_idx = min(8, current_station_idx)
        target_y = dest_centers[target_idx]
        if train_position > target_y - 800.0:
            draw_text(500, 745, "STOPPED EARLY - PRESS [W] TO CREEP FORWARD TO PLATFORM", GLUT_BITMAP_HELVETICA_12)
        else:
            draw_text(550, 745, "READY TO DEPART - PRESS [W] TO ACCELERATE", GLUT_BITMAP_HELVETICA_12)
    elif game_state == STATE_RUNNING:
        if velocity > 0.01:
            draw_text(570, 745, "DRIVING... PRESS [SPACE] TO BRAKE!", GLUT_BITMAP_HELVETICA_12)
        else:
            draw_text(605, 745, "DECELERATING TO A HALT...", GLUT_BITMAP_HELVETICA_12)
    elif game_state == STATE_STATION_STOP:
        if station_stop_timer > 120:
            msg = "Doors Opening..."
        elif station_stop_timer > 60:
            msg = "Passenger Boarding..."
        else:
            msg = "Doors Closing..."
        draw_text(530, 745, f"ARRIVED AT {station_names[current_station_idx].upper()}: {msg}", GLUT_BITMAP_HELVETICA_12)


    # Autopilot indicator
    if cheat_mode:
        glColor3f(0.0, 1.0, 1.0)
        draw_text(590, 770, "AUTOPILOT (CHEAT MODE) ACTIVE", GLUT_BITMAP_HELVETICA_12)
        glColor3f(1.0, 1.0, 1.0)

    # Outcome messages
    if game_state == STATE_STATION_STOP:
        glColor3f(0.1, 0.9, 0.3)
        msg_str = f"{stop_message} STOP!"
        msg_x = int(500 - (len(msg_str) * 12.0) / 2)
        draw_text(msg_x, 420, msg_str, GLUT_BITMAP_TIMES_ROMAN_24)
        glColor3f(1.0, 1.0, 1.0)

    elif game_state == STATE_WIN:
        glColor3f(0.1, 0.9, 0.3)
        win_str = "LINE COMPLETED! YOU WIN!"
        win_x = int(500 - (len(win_str) * 12.0) / 2)
        draw_text(win_x, 430, win_str, GLUT_BITMAP_TIMES_ROMAN_24)
        
        glColor3f(1.0, 1.0, 1.0)
        score_str = f"Final Score: {score} PTS"
        score_x = int(500 - (len(score_str) * 9.5) / 2)
        draw_text(score_x, 395, score_str, GLUT_BITMAP_HELVETICA_18)
        
        desc_str = "Perfect stop at all stations!"
        desc_x = int(500 - (len(desc_str) * 9.5) / 2)
        draw_text(desc_x, 360, desc_str, GLUT_BITMAP_HELVETICA_18)
        
        restart_str = "Press [R] to Play Again"
        restart_x = int(500 - (len(restart_str) * 9.5) / 2)
        draw_text(restart_x, 320, restart_str, GLUT_BITMAP_HELVETICA_18)

    elif game_state == STATE_LOSE:
        glColor3f(1.0, 0.2, 0.2)
        lose_str = "MISSED! GAME OVER"
        lose_x = int(500 - (len(lose_str) * 12.0) / 2)
        draw_text(lose_x, 430, lose_str, GLUT_BITMAP_TIMES_ROMAN_24)
        
        glColor3f(1.0, 1.0, 1.0)
        reason_str = f"Reason: {lose_reason}"
        reason_x = int(500 - (len(reason_str) * 6.5) / 2)
        draw_text(reason_x, 395, reason_str, GLUT_BITMAP_HELVETICA_12)
        
        score_str = f"Final Score: {score} PTS"
        score_x = int(500 - (len(score_str) * 9.5) / 2)
        draw_text(score_x, 360, score_str, GLUT_BITMAP_HELVETICA_18)
        
        retry_str = "Press [R] to Try Again"
        retry_x = int(500 - (len(retry_str) * 9.5) / 2)
        draw_text(retry_x, 320, retry_str, GLUT_BITMAP_HELVETICA_18)


def keyboardListener(key, x, y):
    global velocity, game_state, train_position, camera_angle, camera_height, camera_mode
    global current_station_idx, station_stop_timer, door_open_ratio, score, overspeed_timer, stop_message, lose_reason, has_departed, cheat_mode

    key_lower = key.lower()

    if key_lower in key_states:
        key_states[key_lower] = True
        if key_lower == b'w' and game_state == STATE_START:
            game_state = STATE_RUNNING

    elif key_lower == b'c':
        # Toggle cheat mode (autopilot)
        cheat_mode = not cheat_mode
        if cheat_mode:
            key_states[b'w'] = False
            key_states[b' '] = False
            if game_state == STATE_START:
                game_state = STATE_RUNNING

    elif key_lower == b'r':
        train_position = -1200.0
        velocity = 0.0
        game_state = STATE_START
        camera_angle = 4.712
        camera_height = 160.0
        camera_mode = CAMERA_THIRD_PERSON
        current_station_idx = 0
        station_stop_timer = 0
        door_open_ratio = 0.0
        score = 0
        overspeed_timer = 0
        stop_message = ""
        lose_reason = ""
        has_departed = False
        key_states[b'w'] = False
        key_states[b' '] = False
        cheat_mode = False


def keyboardUpListener(key, x, y):
    key_lower = key.lower()
    if key_lower in key_states:
        key_states[key_lower] = False


def specialKeyListener(key, x, y):
    global camera_height, camera_angle

    if key == GLUT_KEY_UP:
        camera_height = min(400.0, camera_height + 5.0)

    elif key == GLUT_KEY_DOWN:
        camera_height = max(50.0, camera_height - 5.0)

    elif key == GLUT_KEY_LEFT:
        camera_angle -= 0.05

    elif key == GLUT_KEY_RIGHT:
        camera_angle += 0.05


def mouseListener(button, state, x, y):
    global camera_mode
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        if camera_mode == CAMERA_THIRD_PERSON:
            camera_mode = CAMERA_FIRST_PERSON
        else:
            camera_mode = CAMERA_THIRD_PERSON
        glutPostRedisplay()


def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(100, 1.25, 2.0, 25000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if camera_mode == CAMERA_FIRST_PERSON:
        # First-person view: inside the driver's cab at the front of the train
        cam_x = 0.0
        cam_y = train_position + 98.0  # Front cabin position inside front coach
        cam_z = 66.0  # Driver's eye level
        
        # Look ahead of the train along the track axis (+Y)
        gluLookAt(cam_x, cam_y, cam_z,
                  0.0, train_position + 300.0, 58.0,
                  0, 0, 1)
    else:
        # Third-person orbital view
        cam_x = camera_radius * math.cos(camera_angle)
        cam_y = train_position + camera_radius * math.sin(camera_angle)
        cam_z = camera_height

        # Camera looks directly at the train center (0, train_position, 60.0)
        gluLookAt(cam_x, cam_y, cam_z,
                  0, train_position, 60.0,
                  0, 0, 1)


def idle():
    global train_position, velocity, game_state, current_station_idx, station_stop_timer
    global door_open_ratio, score, overspeed_timer, speed_limit, stop_message, stop_points, lose_reason, has_departed, cheat_mode

    if game_state == STATE_RUNNING:
        if cheat_mode:
            target_y = dest_centers[current_station_idx]
            dist = target_y - train_position
            if dist > 0.0:
                target_speed = min(speed_limit, dist / 15.0)
                if velocity < target_speed:
                    velocity = min(velocity + acceleration, target_speed)
                elif velocity > target_speed:
                    velocity = max(target_speed, velocity - brake_power)
            else:
                velocity = 0.0
        else:
            # Continuous acceleration and braking
            if key_states[b'w']:
                velocity = min(velocity + acceleration, max_speed)
            elif key_states[b' ']:
                velocity = max(0.0, velocity - brake_power)

        train_position += velocity

        # Apply passive resistance (if not accelerating or braking in manual mode)
        if not cheat_mode and not key_states[b'w'] and not key_states[b' '] and velocity > 0.0:
            velocity = max(0.0, velocity - friction)

        # Train has departed when velocity is positive
        if velocity > 0.05:
            has_departed = True

        # Check Speed Limit & warning timer
        if velocity > speed_limit:
            overspeed_timer += 1
            if overspeed_timer > 120:  # 2 seconds at 60 FPS
                velocity = 0.0
                game_state = STATE_LOSE
                lose_reason = "Emergency Brake: Speed Limit Exceeded!"
        else:
            overspeed_timer = max(0, overspeed_timer - 1)

        # Check halt condition
        if velocity <= 0.0:
            velocity = 0.0
            
            # Check stopping distance at the current target station
            if has_departed:
                target_y = dest_centers[current_station_idx]
                
                # If they overshot the stop zone (too late)
                if train_position > target_y + tolerance:
                    game_state = STATE_LOSE
                    lose_reason = f"Stopped late (Overshot {station_names[current_station_idx]} by {train_position - target_y:.1f} m)"
                # If they stopped too early
                elif train_position < target_y - tolerance:
                    # Let them creep forward safely
                    has_departed = False
                # Inside the stop zone!
                else:
                    # Stop successful! Trigger station stop boarding sequence
                    game_state = STATE_STATION_STOP
                    station_stop_timer = 180  # 3 seconds at 60 FPS
                    
                    # Award points based on deviation
                    dist = abs(train_position - target_y)
                    if dist <= 12.0:
                        stop_message = "PERFECT"
                        stop_points = 100
                    elif dist <= 25.0:
                        stop_message = "GOOD"
                        stop_points = 50
                    else:
                        stop_message = "DECENT"
                        stop_points = 20
                    score += stop_points

        # Check overshoot/missed station
        else:
            if has_departed:
                target_y = dest_centers[current_station_idx]
                if train_position > target_y + tolerance:
                    velocity = 0.0
                    game_state = STATE_LOSE
                    lose_reason = f"Missed {station_names[current_station_idx]} Stop Zone!"

                # Check track end boundary (runaway train)
                elif train_position > 16300.0:
                    velocity = 0.0
                    game_state = STATE_LOSE
                    lose_reason = "Runaway train crashed at the end of the line!"

    elif game_state == STATE_STATION_STOP:
        # Animate passenger doors opening, boarding, and closing
        station_stop_timer -= 1
        
        # Phase 1 (180 to 120): Doors open
        if station_stop_timer > 120:
            door_open_ratio = (180 - station_stop_timer) / 60.0
        # Phase 2 (120 to 60): Doors stay fully open
        elif station_stop_timer > 60:
            door_open_ratio = 1.0
        # Phase 3 (60 to 0): Doors close
        else:
            door_open_ratio = station_stop_timer / 60.0

        if station_stop_timer == 0:
            door_open_ratio = 0.0
            # Advance to the next station
            if current_station_idx < 8:
                current_station_idx += 1
                game_state = STATE_RUNNING
                has_departed = False
            else:
                # All 9 stations completed! Win!
                game_state = STATE_WIN

    glutPostRedisplay()


def showScreen():
    glClearColor(0.6, 0.85, 1.0, 1.0)  # Bright day-light sky blue background
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)

    # Apply tracking camera position
    setupCamera()

    # Draw elements
    draw_scenery()
    draw_pillars()      # Draw support pillars under tracks & platform
    draw_tracks()
    draw_platform()
    draw_yellow_cross_board()
    draw_train()

    # Draw overlay HUD
    draw_hud()

    glutSwapBuffers()


def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Metro Perfect Stop")

    glEnable(GL_DEPTH_TEST)

    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutKeyboardUpFunc(keyboardUpListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)

    glutMainLoop()


if __name__ == "__main__":
    main()
