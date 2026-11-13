import json
import math
import os
import random

import pygame

# ------------------------------------------------------------------
# SETTINGS
# ------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE_DIR, "assets")
SAVE_PATH = os.path.join(BASE_DIR, "save.json")

WIDTH, HEIGHT = 960, 540
FPS = 60
GROUND_Y = HEIGHT - 80
NUM_LEVELS = 3       # levels that exist right now: raise this by 1 each time you finish a level (max 5)
FINAL_LEVEL = 5      # the level that gets the final boss (THE BIG BOSS)

CHAR_SCALE = 0.45
PISTOL_SCALE = 0.2
BG_TOLERANCE = 40

MOVE_SPEED = 260
GRAVITY = 2200
JUMP_SPEED = -850
BULLET_SPEED = 900
MAG_SIZE = 12
MAX_HP = 100

HEAL_KEY = pygame.K_h          # change this to rebind heals
HEAL_AMOUNT = 40
HEAL_PRICE = 25
MAX_HEALS = 10

BASE_DAMAGE = 10
DAMAGE_PER_LEVEL = 4.5
MAX_DAMAGE_LEVEL = 5

# Platforms for each level: (left, top, width, height). Levels not listed have none.
PLATFORM_HEIGHT = 14
LEVEL_PLATFORMS = {
    1: [
        (80, GROUND_Y - 110, 200, PLATFORM_HEIGHT),     # low left
        (680, GROUND_Y - 110, 200, PLATFORM_HEIGHT),    # low right
        (370, GROUND_Y - 210, 220, PLATFORM_HEIGHT),    # high middle
    ],
    2: [   # level 2, phase 1 (the docks): three tiers of platforms
        (40, GROUND_Y - 110, 170, PLATFORM_HEIGHT),
        (395, GROUND_Y - 110, 170, PLATFORM_HEIGHT),
        (750, GROUND_Y - 110, 170, PLATFORM_HEIGHT),
        (160, GROUND_Y - 210, 190, PLATFORM_HEIGHT),
        (610, GROUND_Y - 210, 190, PLATFORM_HEIGHT),
        (385, GROUND_Y - 305, 190, PLATFORM_HEIGHT),
    ],
}

# ---- Level 2: docks -> climb the lighthouse -> Crate Captain ----
L2_GRUNTS = 20             # phase 1: grunts to beat (they arrive two at a time, one per side)
L2_SPAWN_DELAY = 2.2       # seconds between each pair of grunts
L2_MAX_ALIVE = 8           # most grunts alive at once
CLIMB_COUNT = 30           # phase 2: number of platforms to climb
CLIMB_STEP = 112           # height between platforms (a jump reaches about 160)
CLIMB_PLATFORM_W = 180
TIDE_SPEED = 42            # how fast the water rises (pixels/second) ...
TIDE_GROWTH = 0.35         # ... and how much faster it gets every second
TIDE_DAMAGE = 30           # HP per second while you are in the water
TIDE_START_BELOW = 140     # the tide starts this far below the docks
HORIZON_Y = 300            # where the sea meets the sky
LIGHTHOUSE_SHORT_TOP = 110 # how tall the lighthouse looks in phase 1
LEVEL2_ROOM_PLATFORMS = [  # phase 3: ledges inside the lamp room
    (80, GROUND_Y - 120, 200, PLATFORM_HEIGHT),
    (680, GROUND_Y - 120, 200, PLATFORM_HEIGHT),
    (380, GROUND_Y - 220, 200, PLATFORM_HEIGHT),
]


def make_climb_platforms():
    """The zig-zag of platforms up the lighthouse (same every time). The last one is the balcony."""
    rng = random.Random(2)
    plats = []
    left = 380
    for i in range(1, CLIMB_COUNT + 1):
        step = rng.choice([-240, -120, 120, 240])
        nxt = left + step
        if nxt < 40 or nxt > 740:
            nxt = left - step
        left = nxt
        plats.append(pygame.Rect(left, GROUND_Y - CLIMB_STEP * i, CLIMB_PLATFORM_W, PLATFORM_HEIGHT))
    balcony_top = GROUND_Y - CLIMB_STEP * (CLIMB_COUNT + 1)
    plats.append(pygame.Rect(300, balcony_top, 360, PLATFORM_HEIGHT))
    return plats


CLOUDS = [(80, 60, 140), (360, 140, 180), (700, 40, 160), (560, 230, 120), (180, 260, 150)]
STARS = [(37, 20), (120, 90), (210, 40), (330, 110), (450, 30), (520, 160), (640, 60),
         (730, 130), (820, 25), (900, 100), (60, 200), (280, 220), (600, 250), (860, 210)]
PLATFORM_BREAK_DELAY = 1.5     # seconds between the boss arriving and the platforms breaking

# Boss hazards
WAVE_SPEED = 320
WAVE_DAMAGE = 15
ROCK_DAMAGE = 20
ROCK_SPEED = 700
ROCK_WARNING = 0.9
BOSS_ATTACKS = ["shoot", "wave", "rocks"]
BOSS_ATTACK_LISTS = {1: ["wave", "rain"],      # Rusty: shockwave, then falling nuts and bolts
                     2: ["hook", "poison", "tsunami"],   # Crate Captain: hook, poison crate, tidal wave
                     3: ["trash", "can", "trash", "deluge"]}   # Sly Sam: trash spray, thrown can, sewage flood

IDLE_SHEET = os.path.join(ASSETS, "idle.jpg")
WALK_SHEET = os.path.join(ASSETS, "walk_right.jpg")
JUMP_SHEET = os.path.join(ASSETS, "jump.jpg")
PISTOL_SHEET = os.path.join(ASSETS, "golden_pistol.jpg")

CHAR_RECTS = [pygame.Rect(34 + i * 184, 282, 178, 370) for i in range(6)]
PISTOL_RECTS = [
    pygame.Rect(40, 292, 370, 250),
    pygame.Rect(420, 292, 182, 250),
    pygame.Rect(612, 292, 184, 250),
    pygame.Rect(803, 292, 385, 250),
    pygame.Rect(40, 556, 372, 290),
    pygame.Rect(422, 556, 372, 290),
    pygame.Rect(803, 556, 385, 290),
]
PISTOL_ICON = 0
PISTOL_HOLD = 5
SHOOT_SEQUENCE = [(2, 0.06), (3, 0.06), (4, 0.12)]
RELOAD_SEQUENCE = [(6, 0.5), (5, 0.1)]

HAND_OFFSET = (32, -20)
PISTOL_PIVOT = (0.28, 0.50)
MUZZLE_DISTANCE = 45

ENEMY_STRIP_FRAMES = 4

# ---- Papyrus grunt sprites (graph-paper sheets) ----
# Save the four sheets in the assets folder as:
#   papyrus_idle  papyrus_walk  papyrus_jump  papyrus_attack
# (.jpg, .png or .jfif all work)
GRUNT_HEIGHT = 130                 # on-screen height of a standing grunt (pixels)
GRUNTS_SHOOT = True                # grunts stop and shoot bone arrows with their bow
GRUNT_SHOOT_RANGE = 420            # how close you must be for them to start shooting
GRUNT_SHOOT_COOLDOWN = (2.5, 4.0)  # random wait between shots (seconds)
GRUNT_SHOT_SPEED = 380
GRUNT_SHOT_DAMAGE = 7

PAPER_COLOR = (216, 222, 228)      # graph paper colour
GRID_COLOR = (180, 186, 192)       # graph paper grid-line colour

_TOP_Y, _TOP_H = 95, 381
_BOT_Y, _BOT_H = 502, 367
_TOP_ROW = [pygame.Rect(x, _TOP_Y, w, _TOP_H)
            for x, w in [(36, 256), (319, 270), (610, 272), (907, 257)]]
_BOTTOM_3 = [pygame.Rect(36, _BOT_Y, 348, _BOT_H),
             pygame.Rect(424, _BOT_Y, 350, _BOT_H),
             pygame.Rect(815, _BOT_Y, 349, _BOT_H)]
# state -> (file name without extension, list of cell rectangles in the sheet)
PAPYRUS_SHEETS = {
    "idle": ("papyrus_idle", _TOP_ROW + _BOTTOM_3),
    "walk": ("papyrus_walk", _TOP_ROW + _BOTTOM_3),
    "jump": ("papyrus_jump", _TOP_ROW + _BOTTOM_3),
    "attack": ("papyrus_attack", _TOP_ROW + [pygame.Rect(36, _BOT_Y, 342, _BOT_H),
                                              pygame.Rect(815, _BOT_Y, 349, _BOT_H)]),
}
BONE_RECT = pygame.Rect(422, 621, 112, 34)   # the bone arrow picture on the attack sheet
WALK_FRAMES = [0, 1, 2, 3]                   # walk cycle uses cells 1-4
JUMP_UP_FRAME = 2                            # jump sheet cell used while rising
JUMP_DOWN_FRAME = 4                          # jump sheet cell used while falling
ATTACK_SEQUENCE = [(0, 0.25), (1, 0.20), (2, 0.35), (3, 0.12), (4, 0.20)]   # (cell, seconds)
ATTACK_FIRE_FRAME = 3                        # the bone is released when this cell shows

# ---- Rusty (level 1 boss) sprites ----
# Save the five sheets in the assets folder as:
#   rusty_idle  rusty_walk  rusty_jump  rusty_wave  rusty_rain
BOSS_SPRITES = {1: "rusty", 2: "crate_captain", 3: "sly_sam"}          # level number -> sheet name prefix
BOSS_SCALE = 0.72                    # size of boss sprites (1.0 = original sheet size)
BOSS_FEET_PAD = 12                   # empty pixels under the feet in each sheet cell
BOSS_SIZE_SPRITE = (110, 190)        # boss hitbox size (width, height)
BOSS_SIZES = {2: (110, 170), 3: (130, 190)}         # per-level override for the hitbox
_RUSTY_CELLS = [(30, 80, 220, 327), (271, 80, 232, 327), (520, 80, 232, 327), (774, 80, 220, 327),
                (30, 429, 298, 315), (362, 429, 299, 315), (695, 429, 298, 315)]
RUSTY_RECTS = [pygame.Rect(x, y, w, h - BOSS_FEET_PAD) for x, y, w, h in _RUSTY_CELLS]
# state -> (sheet, [cells used, in order]).  Cells are numbered 0-6 (left to right, top row first).
RUSTY_STATES = {
    "idle": ("idle", [0, 3, 4, 3]),
    "walk": ("walk", [0, 1, 2, 3, 4, 5]),
    "jump_up": ("jump", [2]),
    "jump_down": ("jump", [4]),
    "wave": ("wave", [0, 1, 2, 5, 6]),
    "rain": ("rain", [0, 1]),
}
WAVE_SEQUENCE = [(0, 0.35), (1, 0.35), (2, 0.20), (3, 0.20), (4, 0.30)]   # positions in the "wave" list
WAVE_RELEASE = 2                     # the shockwave starts when this position shows (the slam)
RAIN_SEQUENCE = [(0, 0.40), (1, 0.90)]

# ---- Crate Captain (level 2 boss) sprites ----
# The sheets were cleaned up and saved as transparent strips in the assets folder:
#   crate_captain_idle / walk / jump / hook / poison / tsunami / crate   (.png)
CAPTAIN_SCALE = 0.57                 # size of the Crate Captain (1.0 = original picture size)
CAPTAIN_FRAMES = {"idle": 7, "walk": 7, "jump": 7, "hook": 6, "poison": 6, "tsunami": 4}
TSUNAMI_SCALE = 0.65                 # size of the tidal wave picture
HOOK_SEQUENCE = [(0, 0.30), (1, 0.25), (2, 0.18), (3, 0.22), (4, 0.15), (5, 0.20)]
POISON_SEQUENCE = [(0, 0.35), (1, 0.30), (2, 0.15), (3, 0.40)]
TSUNAMI_SEQUENCE = [(0, 0.35), (1, 0.25), (2, 0.30), (3, 0.30)]   # crouch, jump, SLAM (wave starts), recover
HOOK_REACH_LONG = 222                # how far the hook flies when fully out (pixels)
HOOK_REACH_SHORT = 100               # and while it is being pulled back
HOOK_DAMAGE = 18
POISON_HIT = 14                      # thrown crate hits you
POISON_TICK = 6                      # standing in the puddle (once per second)
POISON_LIFE = 4.0                    # seconds a puddle stays
TSUNAMI_SPEED = 330
TSUNAMI_DAMAGE = 22
TSUNAMI_HEIGHT = 140                 # how tall the damaging part of the wave is (jump it or climb a high ledge)


# ---- Level 3: city -> sewer rats -> Sly Sam ----
# Sprites (transparent strips in the assets folder):
#   rat_idle / rat_walk / rat_jump / rat_spit / rat_spin
#   sly_sam_idle / sly_sam_jump / sly_sam_trash / sly_sam_can / sly_sam_deluge   (.png)
L3_RATS = 15                 # phase 2: giant rats, attacking from both sides
L3_SPAWN_DELAY = 2.6         # seconds between each pair of rats
L3_MAX_ALIVE = 6             # most rats alive at once in phase 2
L3_FIRST_WAVE = 8.0          # phase 3: seconds until the first rat wave
L3_WAVE_EVERY = 22.0         # ... and then a new wave this often (while Sly Sam is alive)
L3_WAVE_SIZE = 3             # rats per wave
RAT_HP = 70                  # base health of a giant rat (it is multiplied up a little per level)
RAT_SCALE = 0.34             # size of the rat pictures
RAT_SIZE = (110, 120)        # rat hitbox (width, height)
RAT_SPIT_SPEED = 340
RAT_SPIT_DAMAGE = 9
RAT_SPIN_SPEED = 380         # how fast a rat rolls forward when it spins
RAT_WHACK_DAMAGE = 14        # tail whack at the end of the spin
SLY_SAM_HP = 900             # Sly Sam's health
SLY_SCALE = 0.585            # size of the Sly Sam pictures
SLY_TRASH_DAMAGE = 10
SLY_CAN_DAMAGE = 16
SLUDGE_SPEED = 300           # the sewage flood (his ultimate) runs both ways along the floor
SLUDGE_HEIGHT = 110
SLUDGE_DAMAGE = 20
CITY_MANHOLE_X = 2800        # how far you walk through the city before the manhole
BOSS_HP = {3: SLY_SAM_HP}
LEVEL3_ROOM_PLATFORMS = [    # phase 3: platforms in the secret room
    (60, GROUND_Y - 130, 190, PLATFORM_HEIGHT),
    (710, GROUND_Y - 130, 190, PLATFORM_HEIGHT),
    (250, GROUND_Y - 230, 170, PLATFORM_HEIGHT),
    (540, GROUND_Y - 230, 170, PLATFORM_HEIGHT),
    (380, GROUND_Y - 330, 200, PLATFORM_HEIGHT),
]
RAT_SPIT_SEQUENCE = [(0, 0.30), (1, 0.20), (2, 0.12), (3, 0.20), (4, 0.15), (5, 0.15)]
RAT_SPIN_SEQUENCE = [(0, 0.25), (1, 0.15), (2, 0.55), (3, 0.15), (4, 0.25), (5, 0.20)]   # rolls at picture 2, tail whack at 4
TRASH_SEQUENCE = [(0, 0.35), (1, 0.25), (2, 0.18), (3, 0.22), (4, 0.20), (5, 0.25)]
CAN_SEQUENCE = [(0, 0.35), (1, 0.30), (2, 0.14), (3, 0.22), (4, 0.22), (5, 0.25)]
DELUGE_SEQUENCE = [(0, 0.45), (1, 0.35), (2, 0.45), (3, 0.45), (4, 0.35)]

ATTACK_SEQUENCES = {"attack": ATTACK_SEQUENCE, "wave": WAVE_SEQUENCE, "rain": RAIN_SEQUENCE,
                    "hook": HOOK_SEQUENCE, "poison": POISON_SEQUENCE, "tsunami": TSUNAMI_SEQUENCE,
                    "trash": TRASH_SEQUENCE, "can": CAN_SEQUENCE, "deluge": DELUGE_SEQUENCE,
                    "rat_spit": RAT_SPIT_SEQUENCE, "rat_spin": RAT_SPIN_SEQUENCE}
# the picture (position in the sequence) when the attack actually goes off
ATTACK_RELEASE = {"wave": WAVE_RELEASE, "hook": 2, "poison": 2, "tsunami": 2,
                  "trash": 2, "can": 2, "deluge": 2}

ENEMY_TYPES = {
    "grunt": {"hp": 30, "speed": 90, "size": (44, 70), "color": (190, 60, 60),
              "touch": 10, "coins": 5, "range": 0, "jumps": True},
    "runner": {"hp": 18, "speed": 200, "size": (38, 60), "color": (225, 140, 40),
               "touch": 8, "coins": 6, "range": 0, "jumps": True},
    "shooter": {"hp": 24, "speed": 70, "size": (44, 70), "color": (130, 70, 190),
                "touch": 6, "coins": 8, "range": 380, "delay": 1.8, "shot": 8},
    "boss": {"hp": 250, "speed": 85, "size": (100, 140), "color": (200, 80, 30),
             "touch": 18, "coins": 60, "range": 260, "delay": 2.0, "shot": 10, "jumps": True},
    "final_boss": {"hp": 1200, "speed": 100, "size": (160, 220), "color": (60, 20, 90),
                   "touch": 25, "coins": 300, "range": 300, "delay": 1.2, "shot": 14},
}

ENEMY_TYPES["rat"] = {"hp": RAT_HP, "speed": 115, "size": RAT_SIZE, "color": (110, 110, 120),
                      "touch": 10, "coins": 10, "range": 0, "jumps": True}

# Typed dialogue. Each line is (speaker, text). Click the mouse to continue.
TYPE_SPEED = 40          # characters per second (lower = slower typing)
LEVEL_INTRO = {
    1: [
        ("MISSION", "A gang of grunts has taken over the alley. All you need is your golden pistol."),
        ("MISSION", "Jump onto the platforms to get the high ground. Careful, the grunts can climb them too."),
        ("MISSION", "Take out every grunt. Once they are gone, their boss will come for you."),
    ],
    2: [
        ("MISSION", "The docks. Grunts are coming from BOTH sides at once, and the lighthouse watches from behind you."),
        ("MISSION", "More platforms here. Use them for the high ground, but the grunts can follow you up."),
        ("MISSION", "Take down all 20 grunts."),
    ],
    3: [
        ("MISSION", "Night in the city. The trail ends at an open manhole, and Sly Sam's gang is hiding somewhere below."),
        ("MISSION", "Walk right to find the manhole. Watch your step."),
    ],
}
LEVEL_BOSS_TALK = {
    1: [
        ("RUSTY", "So you're the one who has been scrapping my crew."),
        ("RUSTY", "This alley is MINE. Nobody walks out of here with a golden gun."),
        ("RUSTY", "Let's see how well you dance without those platforms!"),
    ],
    2: [
        ("CRATE CAPTAIN", "You climbed all the way up here for nothing, pal."),
        ("CRATE CAPTAIN", "Every crate in this harbour is mine. And I've got plenty to throw at you!"),
    ],
    3: [
        ("SLY SAM", "Well, well... you actually made it past my rats."),
        ("SLY SAM", "Nobody finds my hideout. And nobody leaves it."),
        ("SLY SAM", "Rats! Dinner time!"),
    ],
}

BOSS_NAMES = ["Rusty", "Crate Captain", "Sly Sam", "Big Bolt", "THE BIG BOSS"]

# Level 2 phase-change dialogue
L2_TIDE_TALK = [
    ("MISSION", "That's the last grunt... but the sea is angry. The TIDE is rising fast!"),
    ("MISSION", "Climb the platforms up the lighthouse before the water catches you!"),
]
L3_FALL_TALK = [
    ("MISSION", "You plunge down the manhole and splash into the sewer. Giant rats are closing in from BOTH sides!"),
]
L3_RATS_DONE = [
    ("MISSION", "That's all 15 rats. A hidden door has slid open at the end of the tunnel..."),
    ("MISSION", "Walk right to find Sly Sam."),
]
L3_SECRET_TALK = [
    ("MISSION", "A secret room deep in the sewer: Sly Sam's hideout. He will keep calling in more rats, so watch both sides."),
]
L2_TOP_TALK = [
    ("MISSION", "You made it to the lamp room at the top. Someone is waiting for you inside..."),
]


# ------------------------------------------------------------------
# SAVE / LOAD
# ------------------------------------------------------------------
def load_save():
    data = {"unlocked": 1, "coins": 0, "damage_level": 0, "heals": 2, "beaten": []}
    try:
        with open(SAVE_PATH) as f:
            data.update(json.load(f))
    except (OSError, ValueError):
        pass
    return data


def write_save(data):
    try:
        with open(SAVE_PATH, "w") as f:
            json.dump(data, f)
    except OSError:
        pass


# ------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------
def load_frames(path, rects, scale):
    sheet = pygame.image.load(path).convert()
    frames = []
    for rect in rects:
        raw = sheet.subsurface(rect).copy()
        bg_color = raw.get_at((2, 2))
        tol = (BG_TOLERANCE, BG_TOLERANCE, BG_TOLERANCE, 255)
        mask = pygame.mask.from_threshold(raw, bg_color, tol)
        mask.invert()
        raw_alpha = raw.convert_alpha()
        frame = mask.to_surface(setsurface=raw_alpha, unsetcolor=(0, 0, 0, 0))
        size = (int(rect.w * scale), int(rect.h * scale))
        frames.append(pygame.transform.scale(frame, size))
    return frames


def flipped(frames):
    return [pygame.transform.flip(f, True, False) for f in frames]


def frame_at(sequence, t):
    elapsed = 0.0
    result = sequence[-1][0]
    found = False
    for index, duration in sequence:
        elapsed += duration
        if not found and t < elapsed:
            result = index
            found = True
    return result


def lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def floor_under(prev_y, y, x, vy, platforms):
    """Where a falling thing lands this frame (platform top or the ground).
    Returns None if it is still in the air. Platforms only count when you
    fall onto them from above, so you can jump up through them."""
    result = None
    if vy >= 0:
        for p in platforms:
            if p.left <= x <= p.right and prev_y <= p.top + 1 and y >= p.top and result is None:
                result = float(p.top)
    if y >= GROUND_Y:
        result = float(GROUND_Y)
    return result


def make_placeholder_frames(color, size):
    """Simple drawn enemy (4 walk frames) used until real sprites exist."""
    w, h = size
    dark = lerp_color(color, (0, 0, 0), 0.4)
    head_h = h // 3
    body_h = h // 2
    leg_h = h - head_h - body_h
    frames = []
    for swing in (-4, 0, 4, 0):
        s = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(s, dark, (int(w * 0.2) + swing, head_h + body_h, int(w * 0.25), leg_h))
        pygame.draw.rect(s, dark, (int(w * 0.55) - swing, head_h + body_h, int(w * 0.25), leg_h))
        pygame.draw.rect(s, color, (int(w * 0.15), head_h, int(w * 0.7), body_h))
        pygame.draw.rect(s, color, (int(w * 0.2), 0, int(w * 0.6), head_h))
        pygame.draw.rect(s, (255, 255, 255), (int(w * 0.55), int(head_h * 0.3), int(w * 0.22), int(head_h * 0.35)))
        pygame.draw.rect(s, (0, 0, 0), (int(w * 0.68), int(head_h * 0.4), int(w * 0.09), int(head_h * 0.2)))
        pygame.draw.rect(s, dark, (int(w * 0.2), 0, int(w * 0.6), head_h), 2)
        frames.append(s)
    return frames


# Enemy art is a dict: state -> list of (surface, anchor_x).
# anchor_x is the pixel column that sits on the enemy's x position (middle of the feet).
# States: idle, walk, jump_up, jump_down, and (optional) attack + bone.
def frames_to_art(frames):
    tuples = [(f, f.get_width() / 2) for f in frames]
    return {"idle": tuples, "walk": tuples, "jump_up": [tuples[1]], "jump_down": [tuples[1]]}


def flip_art(art):
    out = {}
    for key, value in art.items():
        if key in ("bone", "crate", "orb", "glob", "can_img"):
            out[key] = pygame.transform.flip(value, True, False)
        else:
            out[key] = [(pygame.transform.flip(s, True, False), s.get_width() - ax) for s, ax in value]
    return out


ENEMY_ART_CACHE = {}


def get_enemy_art(names, size, color):
    """(right_facing_art, left_facing_art) for a drawn or PNG-strip enemy."""
    key = (tuple(names), size, color)
    if key not in ENEMY_ART_CACHE:
        found_path = ""
        for name in names:
            path = os.path.join(ASSETS, name + ".png")
            if found_path == "" and os.path.exists(path):
                found_path = path
        if found_path != "":
            sheet = pygame.image.load(found_path).convert_alpha()
            fw = sheet.get_width() // ENEMY_STRIP_FRAMES
            frames = []
            for i in range(ENEMY_STRIP_FRAMES):
                part = sheet.subsurface((i * fw, 0, fw, sheet.get_height()))
                frames.append(pygame.transform.scale(part, size))
        else:
            frames = make_placeholder_frames(color, size)
        right = frames_to_art(frames)
        ENEMY_ART_CACHE[key] = (right, flip_art(right))
    return ENEMY_ART_CACHE[key]


def find_asset(base):
    result = ""
    for ext in (".jpg", ".jpeg", ".png", ".jfif"):
        path = os.path.join(ASSETS, base + ext)
        if result == "" and os.path.exists(path):
            result = path
    return result


def cut_out(sheet, rect):
    """Cut one cell out of a graph-paper sheet and make the paper transparent."""
    raw = sheet.subsurface(rect).copy()
    raw.fill(PAPER_COLOR, (0, 0, 62, 56))                   # erase the frame number
    paper = pygame.mask.from_threshold(raw, PAPER_COLOR, (22, 22, 22, 255))
    grid = pygame.mask.from_threshold(raw, GRID_COLOR, (28, 28, 28, 255))
    paper.draw(grid, (0, 0))
    w, h = raw.get_size()
    remove = pygame.mask.Mask((w, h))
    for part in paper.connected_components(20):
        r = part.get_bounding_rects()[0]
        touches_edge = r.left <= 0 or r.top <= 0 or r.right >= w or r.bottom >= h
        if touches_edge or part.count() > 1200:
            remove.draw(part, (0, 0))
    remove.invert()
    return remove.to_surface(setsurface=raw.convert_alpha(), unsetcolor=(0, 0, 0, 0))


def trim_with_anchor(frame):
    """Crop to the visible pixels. Returns (surface, anchor_x), where anchor_x is the
    middle of the feet so the character stands in the same spot in every frame."""
    rects = pygame.mask.from_surface(frame).get_bounding_rects()
    if len(rects) == 0:
        return frame, frame.get_width() / 2
    box = rects[0].unionall(rects[1:])
    band_h = max(8, box.height // 8)
    band = pygame.Rect(box.left, box.bottom - band_h, box.width, band_h)
    foot_rects = pygame.mask.from_surface(frame.subsurface(band)).get_bounding_rects()
    if len(foot_rects) > 0:
        foot_x = band.left + foot_rects[0].unionall(foot_rects[1:]).centerx
    else:
        foot_x = box.centerx
    return frame.subsurface(box).copy(), foot_x - box.left


PAPYRUS = {"loaded": False, "right": None, "left": None}


def build_papyrus_art():
    paths = {}
    all_found = True
    for state, (base, rects) in PAPYRUS_SHEETS.items():
        paths[state] = find_asset(base)
        if paths[state] == "":
            all_found = False
    if not all_found:
        return None

    raw = {}
    bone = None
    for state, (base, rects) in PAPYRUS_SHEETS.items():
        sheet = pygame.image.load(paths[state]).convert()
        raw[state] = [trim_with_anchor(cut_out(sheet, r)) for r in rects]
        if state == "attack":
            bone = trim_with_anchor(cut_out(sheet, BONE_RECT))[0]

    scale = GRUNT_HEIGHT / raw["idle"][0][0].get_height()

    def scaled(item):
        surf, anchor = item
        size = (max(1, int(surf.get_width() * scale)), max(1, int(surf.get_height() * scale)))
        return pygame.transform.smoothscale(surf, size), anchor * scale

    return {
        "idle": [scaled(f) for f in raw["idle"]],
        "walk": [scaled(raw["walk"][i]) for i in WALK_FRAMES],
        "jump_up": [scaled(raw["jump"][JUMP_UP_FRAME])],
        "jump_down": [scaled(raw["jump"][JUMP_DOWN_FRAME])],
        "attack": [scaled(f) for f in raw["attack"]],
        "bone": scaled((bone, 0))[0],
    }


def get_papyrus_art():
    """(right, left) art for the Papyrus grunt, or None if the sheets are missing."""
    if not PAPYRUS["loaded"]:
        PAPYRUS["loaded"] = True
        art = build_papyrus_art()
        if art is not None:
            PAPYRUS["right"] = art
            PAPYRUS["left"] = flip_art(art)
    if PAPYRUS["right"] is None:
        return None
    return PAPYRUS["right"], PAPYRUS["left"]


def border_anchors(raw):
    """Background colours of a sheet cell: the grey colours that fill its edge ring."""
    w, h = raw.get_size()
    ring = []
    for x in range(w):
        for y in (0, 1, h - 2, h - 1):
            ring.append((x, y))
    for y in range(h):
        for x in (0, 1, w - 2, w - 1):
            ring.append((x, y))
    groups = {}
    for pos in ring:
        r, g, b, _ = raw.get_at(pos)
        mx = max(r, g, b)
        mn = min(r, g, b)
        if mx - mn <= 30 and b >= r and mx <= 165:
            groups.setdefault((r // 6, g // 6, b // 6), []).append((r, g, b))
    anchors = []
    for values in groups.values():
        n = len(values)
        if n >= 6:
            anchors.append((sum(v[0] for v in values) // n,
                            sum(v[1] for v in values) // n,
                            sum(v[2] for v in values) // n))
    return anchors


def cut_out_adaptive(sheet, rect, erase_ground_line=False):
    """Cut one cell from a dark gridded sheet and make the background transparent."""
    raw = sheet.subsurface(rect).copy()
    w, h = raw.get_size()
    near = pygame.mask.Mask((w, h))
    for color in border_anchors(raw):
        near.draw(pygame.mask.from_threshold(raw, color, (9, 9, 9, 255)), (0, 0))
    remove = pygame.mask.Mask((w, h))
    for part in near.connected_components(40):
        r = part.get_bounding_rects()[0]
        touches_edge = r.left <= 0 or r.top <= 0 or r.right >= w or r.bottom >= h
        if touches_edge or part.count() > 150:
            remove.draw(part, (0, 0))
    remove.draw(pygame.mask.Mask((52, 46), fill=True), (0, 0))    # the frame number
    # drop thin leftover grid-line pieces (long and skinny, not solid)
    keep = remove.copy()
    keep.invert()
    for part in keep.connected_components(40):
        r = part.get_bounding_rects()[0]
        if max(r.w, r.h) >= 40 and part.count() / float(r.w * r.h) < 0.12:
            remove.draw(part, (0, 0))
    remove.invert()
    frame = remove.to_surface(setsurface=raw.convert_alpha(), unsetcolor=(0, 0, 0, 0))
    if erase_ground_line:
        for y in range(h - 50, h):
            dark = []
            for x in range(w):
                r, g, b, a = frame.get_at((x, y))
                if a > 0 and max(r, g, b) < 45:
                    dark.append(x)
            if len(dark) >= 100:
                for x in dark:
                    frame.set_at((x, y), (0, 0, 0, 0))
    return frame


BOSS_ART = {}


def build_boss_art(prefix):
    sheets = {}
    for sheet_name in ("idle", "walk", "jump", "wave", "rain"):
        path = find_asset(prefix + "_" + sheet_name)
        if path == "":
            return None
        sheets[sheet_name] = pygame.image.load(path).convert()

    cells = {}
    art = {}
    for state, (sheet_name, indexes) in RUSTY_STATES.items():
        frames = []
        for i in indexes:
            key = (sheet_name, i)
            if key not in cells:
                cut = cut_out_adaptive(sheets[sheet_name], RUSTY_RECTS[i], sheet_name == "walk")
                size = (max(1, int(cut.get_width() * BOSS_SCALE)), max(1, int(cut.get_height() * BOSS_SCALE)))
                cells[key] = (pygame.transform.smoothscale(cut, size), size[0] / 2)
            frames.append(cells[key])
        art[state] = frames
    return art


def load_strip(path, count, scale):
    """A strip of equal-sized frames (already transparent) -> list of (surface, anchor_x)."""
    sheet = pygame.image.load(path).convert_alpha()
    fw = sheet.get_width() // count
    frames = []
    for i in range(count):
        part = sheet.subsurface((i * fw, 0, fw, sheet.get_height())).copy()
        size = (max(1, int(fw * scale)), max(1, int(part.get_height() * scale)))
        frames.append((pygame.transform.smoothscale(part, size), size[0] / 2))
    return frames


def build_captain_art():
    strips = {}
    for name, count in CAPTAIN_FRAMES.items():
        path = find_asset("crate_captain_" + name)
        if path == "":
            return None
        scale = TSUNAMI_SCALE if name == "tsunami" else CAPTAIN_SCALE
        strips[name] = load_strip(path, count, scale)
    crate_path = find_asset("crate_captain_crate")
    if crate_path == "":
        return None
    crate = pygame.image.load(crate_path).convert_alpha()
    crate = pygame.transform.smoothscale(crate, (int(crate.get_width() * CAPTAIN_SCALE),
                                                 int(crate.get_height() * CAPTAIN_SCALE)))
    jump = strips["jump"]
    return {
        "idle": strips["idle"],
        "walk": strips["walk"],
        "jump_up": [jump[2]],
        "jump_down": [jump[4]],
        "hook": strips["hook"],
        "poison": strips["poison"][:4],
        "tsunami": [jump[1], jump[2], jump[6], jump[5]],     # stomp pose that calls the wave
        "tsunami_wave": strips["tsunami"],
        "crate": crate,
    }


def make_glob(color, radius):
    """A round blob of slime (used for the rat spit and Sly Sam's trash spray)."""
    surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    dark = lerp_color(color, (0, 0, 0), 0.55)
    pygame.draw.circle(surf, dark, (radius, radius), radius)
    pygame.draw.circle(surf, color, (radius, radius), max(1, radius - 3))
    pygame.draw.circle(surf, lerp_color(color, (255, 255, 255), 0.6), (radius - radius // 3, radius - radius // 3),
                       max(1, radius // 4))
    return surf


def make_trash_can_surface():
    surf = pygame.Surface((38, 52), pygame.SRCALPHA)
    pygame.draw.rect(surf, (120, 126, 130), (4, 8, 30, 42))
    for x in (11, 19, 27):
        pygame.draw.line(surf, (80, 86, 92), (x, 12), (x, 48), 2)
    pygame.draw.rect(surf, (40, 44, 50), (4, 8, 30, 42), 2)
    pygame.draw.rect(surf, (160, 166, 170), (1, 2, 36, 7))
    pygame.draw.rect(surf, (40, 44, 50), (1, 2, 36, 7), 2)
    return surf


def build_sly_art():
    strips = {}
    for name in ("idle", "jump", "trash", "can", "deluge"):
        path = find_asset("sly_sam_" + name)
        if path == "":
            return None
        count = 5 if name == "deluge" else 6
        strips[name] = load_strip(path, count, SLY_SCALE)
    idle = strips["idle"]
    jump = strips["jump"]
    return {
        "idle": idle,
        "walk": [idle[0], idle[1], idle[3], idle[4]],
        "jump_up": [jump[2]],
        "jump_down": [jump[4]],
        "trash": strips["trash"],
        "can": strips["can"],
        "deluge": strips["deluge"],
        "glob": make_glob((120, 230, 50), 15),
        "can_img": make_trash_can_surface(),
    }


RAT = {"loaded": False, "right": None, "left": None}


def build_rat_art():
    strips = {}
    for name in ("idle", "walk", "jump", "spit", "spin"):
        path = find_asset("rat_" + name)
        if path == "":
            return None
        strips[name] = load_strip(path, 6, RAT_SCALE)
    return {
        "idle": strips["idle"],
        "walk": strips["walk"],
        "jump_up": [strips["jump"][2]],
        "jump_down": [strips["jump"][4]],
        "rat_spit": strips["spit"],
        "rat_spin": strips["spin"],
        "orb": make_glob((90, 210, 70), 14),
    }


def get_rat_art():
    """(right, left) art for the giant sewer rat, or None if its sheets are missing."""
    if not RAT["loaded"]:
        RAT["loaded"] = True
        art = build_rat_art()
        if art is not None:
            RAT["right"] = art
            RAT["left"] = flip_art(art)
    if RAT["right"] is None:
        return None
    return RAT["right"], RAT["left"]


def get_boss_art(level_no):
    """(right, left) art for this level's boss, or None if it has no sprite sheets."""
    if level_no not in BOSS_SPRITES:
        return None
    prefix = BOSS_SPRITES[level_no]
    if prefix not in BOSS_ART:
        if prefix == "crate_captain":
            art = build_captain_art()
        elif prefix == "sly_sam":
            art = build_sly_art()
        else:
            art = build_boss_art(prefix)
        BOSS_ART[prefix] = None if art is None else (art, flip_art(art))
    return BOSS_ART[prefix]


# ------------------------------------------------------------------
# PLAYER
# ------------------------------------------------------------------
class Pistol:
    def __init__(self):
        self.right = load_frames(PISTOL_SHEET, PISTOL_RECTS, PISTOL_SCALE)
        self.left = flipped(self.right)
        self.sequence = None
        self.time = 0.0
        self.ammo = MAG_SIZE

    def busy(self):
        return self.sequence is not None

    def play(self, sequence):
        self.sequence = sequence
        self.time = 0.0

    def update(self, dt):
        if self.sequence is not None:
            self.time += dt
            total = sum(d for _, d in self.sequence)
            if self.time >= total:
                finished = self.sequence
                self.sequence = None
                if finished is RELOAD_SEQUENCE:
                    self.ammo = MAG_SIZE
                if self.ammo <= 0:
                    self.play(RELOAD_SEQUENCE)

    def frame_index(self):
        if self.sequence is None:
            return PISTOL_HOLD
        return frame_at(self.sequence, self.time)

    def draw(self, screen, hand_pos, facing):
        frames = self.right if facing == 1 else self.left
        image = frames[self.frame_index()]
        px = PISTOL_PIVOT[0] if facing == 1 else 1 - PISTOL_PIVOT[0]
        pivot = (image.get_width() * px, image.get_height() * PISTOL_PIVOT[1])
        screen.blit(image, (hand_pos[0] - pivot[0], hand_pos[1] - pivot[1]))


class Player:
    def __init__(self, progress):
        self.progress = progress
        self.idle_r = load_frames(IDLE_SHEET, CHAR_RECTS, CHAR_SCALE)
        self.walk_r = load_frames(WALK_SHEET, CHAR_RECTS, CHAR_SCALE)
        self.jump_r = load_frames(JUMP_SHEET, CHAR_RECTS, CHAR_SCALE)
        self.idle_l = flipped(self.idle_r)
        self.walk_l = flipped(self.walk_r)
        self.jump_l = flipped(self.jump_r)
        self.pistol = Pistol()
        self.reset()

    def reset(self):
        self.x = 200.0
        self.y = float(GROUND_Y)
        self.vy = 0.0
        self.facing = 1
        self.on_ground = True
        self.moving = False
        self.land_timer = 0.0
        self.anim_time = 0.0
        self.hp = MAX_HP
        self.invuln = 0.0
        self.bullets = []
        self.pistol.sequence = None
        self.pistol.time = 0.0
        self.pistol.ammo = MAG_SIZE

    @property
    def damage(self):
        return BASE_DAMAGE + DAMAGE_PER_LEVEL * self.progress["damage_level"]

    @property
    def rect(self):
        r = pygame.Rect(0, 0, 36, 110)
        r.midbottom = (int(self.x), int(self.y))
        return r

    def hand_pos(self):
        return (self.x + HAND_OFFSET[0] * self.facing, self.y + HAND_OFFSET[1])

    def take_damage(self, amount):
        if self.invuln <= 0:
            self.hp -= amount
            self.invuln = 1.0

    def use_heal(self):
        if self.progress["heals"] > 0 and self.hp < MAX_HP:
            self.progress["heals"] -= 1
            self.hp = min(MAX_HP, self.hp + HEAL_AMOUNT)

    def shoot(self):
        if not self.pistol.busy() and self.pistol.ammo > 0:
            self.pistol.ammo -= 1
            self.pistol.play(SHOOT_SEQUENCE)
            hx, hy = self.hand_pos()
            self.bullets.append({"x": hx + MUZZLE_DISTANCE * self.facing, "y": hy - 6,
                                 "vx": BULLET_SPEED * self.facing, "alive": True})

    def reload(self):
        if not self.pistol.busy() and self.pistol.ammo < MAG_SIZE:
            self.pistol.play(RELOAD_SEQUENCE)

    def jump(self):
        if self.on_ground:
            self.vy = JUMP_SPEED
            self.on_ground = False

    def update(self, dt, direction, platforms):
        self.moving = direction != 0
        self.x += direction * MOVE_SPEED * dt
        self.x = max(30, min(WIDTH - 30, self.x))
        if direction != 0:
            self.facing = direction

        was_in_air = not self.on_ground
        self.on_ground = False
        prev_y = self.y
        self.vy += GRAVITY * dt
        self.y += self.vy * dt
        floor = floor_under(prev_y, self.y, self.x, self.vy, platforms)
        if floor is not None:
            self.y = floor
            self.vy = 0.0
            self.on_ground = True
            if was_in_air:
                self.land_timer = 0.2
        self.land_timer = max(0.0, self.land_timer - dt)
        self.invuln = max(0.0, self.invuln - dt)

        self.anim_time += dt
        self.pistol.update(dt)

        for b in self.bullets:
            b["x"] += b["vx"] * dt
            if b["x"] < -20 or b["x"] > WIDTH + 20:
                b["alive"] = False
        self.bullets = [b for b in self.bullets if b["alive"]]

    def current_image(self):
        right = self.facing == 1
        if not self.on_ground:
            frames = self.jump_r if right else self.jump_l
            return frames[2] if self.vy < 0 else frames[3]
        if self.land_timer > 0:
            frames = self.jump_r if right else self.jump_l
            return frames[4] if self.land_timer > 0.1 else frames[5]
        if self.moving:
            frames = self.walk_r if right else self.walk_l
            return frames[int(self.anim_time * 10) % 6]
        frames = self.idle_r if right else self.idle_l
        return frames[int(self.anim_time * 6) % 6]

    def draw(self, screen, scroll=0.0):
        blink_off = self.invuln > 0 and int(self.invuln * 12) % 2 == 0
        if not blink_off:
            image = self.current_image()
            screen.blit(image, image.get_rect(midbottom=(self.x, self.y + scroll)))
            hx, hy = self.hand_pos()
            self.pistol.draw(screen, (hx, hy + scroll), self.facing)
        for b in self.bullets:
            pygame.draw.rect(screen, (255, 215, 0), (b["x"] - 6, b["y"] + scroll - 2, 12, 5))


# ------------------------------------------------------------------
# ENEMIES
# ------------------------------------------------------------------
class Enemy:
    def __init__(self, kind, x, level_no, color=None):
        cfg = ENEMY_TYPES[kind]
        self.kind = kind
        self.cfg = cfg
        self.is_boss = kind in ("boss", "final_boss")
        self.level_no = level_no
        if kind == "final_boss":
            scale = 1.0
        elif self.is_boss:
            scale = 1 + 0.3 * (level_no - 1)
        else:
            scale = 1 + 0.15 * (level_no - 1)
        self.max_hp = cfg["hp"] * scale
        if kind == "boss" and level_no in BOSS_HP:
            self.max_hp = float(BOSS_HP[level_no])
        self.hp = self.max_hp
        self.speed = cfg["speed"] * (1 + 0.03 * (level_no - 1))
        self.touch = cfg["touch"] * (1 + 0.1 * (level_no - 1))
        self.coins = cfg["coins"] + (level_no if self.is_boss else 0)
        w, h = cfg["size"]
        if kind == "boss":
            w = int(w * (1 + 0.04 * level_no))
            h = int(h * (1 + 0.04 * level_no))
        self.size = (w, h)
        self.x = float(x)
        self.y = float(GROUND_Y)
        self.vy = 0.0
        self.on_ground = True
        self.moving = False
        self.jump_cooldown = random.uniform(0.0, 0.6)
        self.facing = 1
        self.anim_time = random.random()
        self.flash = 0.0
        self.shot_timer = random.uniform(0.8, 1.6)
        self.attack_index = 0
        self.attack_time = None
        self.attack_name = ""
        self.attack_fired = False
        self.attack_cooldown = random.uniform(1.0, GRUNT_SHOOT_COOLDOWN[1])

        papyrus = get_papyrus_art() if kind == "grunt" else None
        boss_art = get_boss_art(level_no) if kind == "boss" else None
        rat_art = get_rat_art() if kind == "rat" else None
        self.sprite_boss = boss_art is not None
        if papyrus is not None:
            self.art_right, self.art_left = papyrus
            self.size = (56, GRUNT_HEIGHT)
        elif boss_art is not None:
            self.art_right, self.art_left = boss_art
            self.size = BOSS_SIZES.get(level_no, BOSS_SIZE_SPRITE)
        elif rat_art is not None:
            self.art_right, self.art_left = rat_art
            self.size = RAT_SIZE
        else:
            paint = color if color is not None else cfg["color"]
            if kind == "boss":
                names = ["boss_" + str(level_no), "enemy_boss"]
            else:
                names = ["enemy_" + kind]
            self.art_right, self.art_left = get_enemy_art(names, self.size, paint)
        self.can_bow = GRUNTS_SHOOT and kind == "grunt" and "attack" in self.art_right
        self.can_rat = kind == "rat" and "rat_spit" in self.art_right

    @property
    def rect(self):
        r = pygame.Rect(0, 0, int(self.size[0] * 0.7), self.size[1])
        r.midbottom = (int(self.x), int(self.y))
        return r

    def phase_two(self):
        return self.is_boss and self.hp < self.max_hp * 0.5

    def update(self, dt, player_x, player_y, bullets, hazards, platforms):
        cfg = self.cfg
        dx = player_x - self.x
        dist = abs(dx)
        attacking = self.attack_time is not None
        if not attacking:
            self.facing = 1 if dx >= 0 else -1
        speed = self.speed * (1.25 if self.phase_two() else 1.0)

        # horizontal movement (a grunt stands still while it shoots)
        move = 0
        rng = cfg["range"]
        if attacking:
            move = 0
        elif rng == 0:
            move = self.facing
        elif dist > rng + 40:
            move = self.facing
        elif dist < rng - 80:
            move = -self.facing
        self.moving = move != 0
        self.x += move * speed * dt
        self.x = max(-60.0, min(WIDTH + 60.0, self.x))

        if self.can_bow:
            self.update_bow(dt, dist, player_y, bullets)
        if self.can_rat:
            self.update_rat(dt, dist, player_y, bullets, hazards)

        # jumping up to platforms when the player is above
        self.jump_cooldown = max(0.0, self.jump_cooldown - dt)
        wants_jump = (cfg.get("jumps", False) and self.on_ground and self.jump_cooldown <= 0
                      and self.attack_time is None and player_y < self.y - 60 and dist < 300)
        if wants_jump:
            self.vy = JUMP_SPEED
            self.jump_cooldown = 0.9

        # gravity and landing
        self.on_ground = False
        prev_y = self.y
        self.vy += GRAVITY * dt
        self.y += self.vy * dt
        floor = floor_under(prev_y, self.y, self.x, self.vy, platforms)
        if floor is not None:
            self.y = floor
            self.vy = 0.0
            self.on_ground = True

        self.anim_time += dt
        self.flash = max(0.0, self.flash - dt)

        # attacks for ranged enemies and bosses
        if self.sprite_boss:
            self.update_boss_attacks(dt, player_x, bullets, hazards)
        elif rng > 0 and -20 < self.x < WIDTH + 20:
            self.shot_timer -= dt
            if self.shot_timer <= 0:
                delay = cfg["delay"] * (0.6 if self.phase_two() else 1.0)
                self.shot_timer = delay
                if self.is_boss:
                    attack = BOSS_ATTACKS[self.attack_index % len(BOSS_ATTACKS)]
                    self.attack_index += 1
                    self.boss_attack(attack, player_x, bullets, hazards)
                else:
                    self.fire(bullets)

    def update_boss_attacks(self, dt, player_x, bullets, hazards):
        """Animated boss attacks: wind up, release the hazard, recover, wait."""
        if self.attack_time is None:
            self.shot_timer -= dt
            if self.shot_timer <= 0 and self.on_ground and 0 < self.x < WIDTH:
                names = BOSS_ATTACK_LISTS.get(self.level_no, BOSS_ATTACKS)
                self.attack_name = names[self.attack_index % len(names)]
                self.attack_index += 1
                self.attack_time = 0.0
                self.attack_fired = False
                if self.attack_name == "rain":
                    self.boss_attack("rain", player_x, bullets, hazards)
                    self.attack_fired = True
        else:
            self.attack_time += dt * (1.3 if self.phase_two() else 1.0)
            sequence = ATTACK_SEQUENCES[self.attack_name]
            position = frame_at(sequence, self.attack_time)
            release = ATTACK_RELEASE.get(self.attack_name)
            if release is not None and position >= release and not self.attack_fired:
                self.attack_fired = True
                self.boss_attack(self.attack_name, player_x, bullets, hazards)
            if self.attack_time >= sum(d for _, d in sequence):
                self.attack_time = None
                self.attack_name = ""
                self.shot_timer = self.cfg["delay"] * (0.6 if self.phase_two() else 1.0)

    def update_rat(self, dt, dist, player_y, bullets, hazards):
        """Giant rat: spits poison from a distance, rolls into a spin and whacks with its tail up close."""
        if self.attack_time is None:
            self.attack_cooldown = max(0.0, self.attack_cooldown - dt)
            ready = (self.attack_cooldown <= 0 and self.on_ground
                     and abs(player_y - self.y) < 90 and 0 < self.x < WIDTH)
            if ready and dist < 150:
                self.attack_name = "rat_spin"
            elif ready and 200 < dist < 420:
                self.attack_name = "rat_spit"
            if self.attack_name != "":
                self.attack_time = 0.0
                self.attack_fired = False
        else:
            self.attack_time += dt
            sequence = ATTACK_SEQUENCES[self.attack_name]
            position = frame_at(sequence, self.attack_time)
            if self.attack_name == "rat_spit":
                if position >= 2 and not self.attack_fired:
                    self.attack_fired = True
                    art = self.art_right if self.facing == 1 else self.art_left
                    bullets.append({"x": self.x + self.facing * 60, "y": self.y - self.size[1] * 0.55,
                                    "vx": self.facing * RAT_SPIT_SPEED, "vy": 0.0,
                                    "damage": RAT_SPIT_DAMAGE * (1 + 0.1 * (self.level_no - 1)),
                                    "alive": True, "img": art["orb"]})
            else:
                if position == 2:
                    self.x = max(-60.0, min(WIDTH + 60.0, self.x + self.facing * RAT_SPIN_SPEED * dt))
                if position >= 4 and not self.attack_fired:
                    self.attack_fired = True
                    hazards.append({"type": "melee", "x": self.x, "y": self.y, "dir": self.facing, "reach": 120,
                                    "dmg": RAT_WHACK_DAMAGE, "t": 0.0, "life": 0.25, "hit": False, "alive": True})
            if self.attack_time >= sum(d for _, d in sequence):
                self.attack_time = None
                self.attack_name = ""
                self.attack_cooldown = random.uniform(2.5, 4.5)

    def update_bow(self, dt, dist, player_y, bullets):
        """Grunt bow attack: aim, draw, release a bone arrow, then wait."""
        if self.attack_time is None:
            self.attack_cooldown = max(0.0, self.attack_cooldown - dt)
            ready = (self.attack_cooldown <= 0 and self.on_ground
                     and 120 < dist < GRUNT_SHOOT_RANGE
                     and abs(player_y - self.y) < 90
                     and 0 < self.x < WIDTH)
            if ready:
                self.attack_time = 0.0
                self.attack_name = "attack"
                self.attack_fired = False
        else:
            self.attack_time += dt
            cell = frame_at(ATTACK_SEQUENCE, self.attack_time)
            if cell == ATTACK_FIRE_FRAME and not self.attack_fired:
                self.attack_fired = True
                self.fire_bone(bullets)
            if self.attack_time >= sum(d for _, d in ATTACK_SEQUENCE):
                self.attack_time = None
                self.attack_cooldown = random.uniform(GRUNT_SHOOT_COOLDOWN[0], GRUNT_SHOOT_COOLDOWN[1])

    def fire_bone(self, bullets):
        art = self.art_right if self.facing == 1 else self.art_left
        damage = GRUNT_SHOT_DAMAGE * (1 + 0.1 * (self.level_no - 1))
        bullets.append({"x": self.x + self.facing * 45, "y": self.y - self.size[1] * 0.55,
                        "vx": self.facing * GRUNT_SHOT_SPEED, "vy": 0.0,
                        "damage": damage, "alive": True, "img": art["bone"]})

    def boss_attack(self, attack, player_x, bullets, hazards):
        if attack == "shoot":
            self.fire(bullets)
        elif attack == "wave":
            hazards.append({"type": "wave", "x": self.x, "vx": self.facing * WAVE_SPEED, "alive": True})
        elif attack == "hook":
            hazards.append({"type": "hook", "x": self.x, "y": self.y, "dir": self.facing,
                            "t": 0.0, "hit": False, "alive": True})
        elif attack == "poison":
            art = self.art_right if self.facing == 1 else self.art_left
            targets = [player_x]
            if self.phase_two():
                targets.append(player_x + random.choice([-1, 1]) * random.uniform(90, 180))
            x0 = self.x + self.facing * 40
            y0 = self.y - self.size[1] * 0.8
            flight, gravity = 0.9, 1500.0
            for tx in targets:
                tx = max(40.0, min(WIDTH - 40.0, tx))
                hazards.append({"type": "crate", "x": x0, "y": y0, "vx": (tx - x0) / flight,
                                "vy": (GROUND_Y - 16 - y0 - 0.5 * gravity * flight * flight) / flight,
                                "g": gravity, "rot": 0.0, "img": art["crate"], "alive": True})
        elif attack == "trash":
            art = self.art_right if self.facing == 1 else self.art_left
            count = 3 + (2 if self.phase_two() else 0)
            y = self.y - self.size[1] * 0.62
            for i in range(count):
                spread = (i - (count - 1) / 2) * 110
                bullets.append({"x": self.x + self.facing * 55, "y": y, "vx": self.facing * 400, "vy": spread,
                                "damage": SLY_TRASH_DAMAGE * (1 + 0.1 * (self.level_no - 1)),
                                "alive": True, "img": art["glob"]})
        elif attack == "can":
            art = self.art_right if self.facing == 1 else self.art_left
            targets = [player_x]
            if self.phase_two():
                targets.append(player_x + random.choice([-1, 1]) * random.uniform(90, 180))
            x0 = self.x + self.facing * 45
            y0 = self.y - self.size[1] * 0.8
            flight, gravity = 0.9, 1500.0
            for tx in targets:
                tx = max(40.0, min(WIDTH - 40.0, tx))
                hazards.append({"type": "crate", "x": x0, "y": y0, "vx": (tx - x0) / flight,
                                "vy": (GROUND_Y - 16 - y0 - 0.5 * gravity * flight * flight) / flight,
                                "g": gravity, "rot": 0.0, "img": art["can_img"], "dmg": SLY_CAN_DAMAGE,
                                "tint": "green", "alive": True})
        elif attack == "deluge":
            for direction in (-1, 1):
                hazards.append({"type": "sludge", "x": self.x, "dir": direction, "age": 0.0, "alive": True})
        elif attack == "tsunami":
            art = self.art_right if self.facing == 1 else self.art_left
            hazards.append({"type": "tsunami", "x": self.x, "dir": self.facing, "age": 0.0,
                            "frames": art["tsunami_wave"], "alive": True})
        else:
            count = 3 + (2 if self.phase_two() else 0)
            for i in range(count):
                offset = 0.0 if i == 0 else random.uniform(-220, 220)
                rx = max(40.0, min(WIDTH - 40.0, player_x + offset))
                hazards.append({"type": "rock", "x": rx, "y": -30.0,
                                "timer": ROCK_WARNING, "alive": True})

    def fire(self, bullets):
        if self.kind == "final_boss":
            count = 3
        elif self.is_boss:
            count = 1 + self.level_no // 4
        else:
            count = 1
        if self.phase_two():
            count += 2 if self.kind == "final_boss" else 1
        speed = min(650, 360 + 25 * self.level_no)
        damage = self.cfg["shot"] * (1 + 0.1 * (self.level_no - 1))
        y = self.y - self.size[1] * 0.6
        for i in range(count):
            spread = (i - (count - 1) / 2) * 90
            bullets.append({"x": self.x + self.facing * 30, "y": y,
                            "vx": self.facing * speed, "vy": spread,
                            "damage": damage, "alive": True})

    def current_frame(self):
        art = self.art_right if self.facing == 1 else self.art_left
        if self.attack_time is not None:
            sequence = ATTACK_SEQUENCES[self.attack_name]
            return art[self.attack_name][frame_at(sequence, self.attack_time)]
        if not self.on_ground:
            key = "jump_up" if self.vy < 0 else "jump_down"
            return art[key][0]
        if self.moving:
            frames = art["walk"]
            return frames[int(self.anim_time * 8) % len(frames)]
        frames = art["idle"]
        return frames[int(self.anim_time * 6) % len(frames)]

    def draw(self, screen):
        image, anchor = self.current_frame()
        if self.flash > 0:
            image = image.copy()
            image.fill((90, 90, 90), special_flags=pygame.BLEND_RGB_ADD)
        screen.blit(image, (self.x - anchor, self.y - image.get_height()))
        if not self.is_boss:
            bar_w = 40
            top = self.y - self.size[1] - 10
            pygame.draw.rect(screen, (60, 0, 0), (self.x - bar_w / 2, top, bar_w, 5))
            pygame.draw.rect(screen, (0, 220, 0),
                             (self.x - bar_w / 2, top, bar_w * max(0, self.hp) / self.max_hp, 5))


# ------------------------------------------------------------------
# LEVEL
# ------------------------------------------------------------------
class Level:
    def __init__(self, number, player, progress):
        self.number = number
        self.player = player
        self.progress = progress
        self.total = 4 + number * 2
        self.spawned = 0
        self.killed = 0
        self.spawn_timer = 1.0
        self.spawn_delay = max(0.6, 2.2 - 0.15 * number)
        self.max_alive = min(3 + number // 2, 8)
        self.kinds = ["grunt"]
        if number >= 2:
            self.kinds.append("runner")
        if number >= 4:
            self.kinds.append("shooter")
        if number >= 6:
            self.kinds.append("shooter")
        self.enemies = []
        self.enemy_bullets = []
        self.hazards = []
        self.platforms = [pygame.Rect(r) for r in LEVEL_PLATFORMS.get(number, [])]
        self.breaking = False
        self.break_timer = 0.0
        self.debris = []
        self.boss = None
        self.talk_pending = False
        self.boss_spawned = False
        self.boss_dead = False
        self.boss_name = BOSS_NAMES[number - 1]
        self.replay = number in progress["beaten"]     # already beaten once: no coins this time
        self.earned = 0                # coins collected this run: only kept if you beat the whole level
        self.scroll = 0.0              # how far the camera has moved up (only used by climbing levels)
        self.pending_dialogue = None   # a level can set this to show a dialogue (e.g. between phases)

    def status_text(self):
        """Text under the level number in the HUD, or None for the default."""
        return None

    def banner_text(self):
        """Big warning text in the HUD (or None)."""
        return None

    def phase_dialogue_done(self):
        """Called when a between-phase dialogue has been clicked through."""
        pass

    def draw_background(self, screen):
        t = (self.number - 1) / (FINAL_LEVEL - 1)
        screen.fill(lerp_color((92, 150, 200), (90, 40, 55), t))
        ground = lerp_color((60, 120, 60), (50, 40, 40), t)
        pygame.draw.rect(screen, ground, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))

    def draw_foreground(self, screen):
        pass

    def spawn_side(self):
        return random.choice([-40, WIDTH + 40])

    def spawn_logic(self, dt):
        alive = len(self.enemies)
        if self.spawned < self.total:
            self.spawn_timer -= dt
            if self.spawn_timer <= 0 and alive < self.max_alive:
                self.enemies.append(Enemy(random.choice(self.kinds), self.spawn_side(), self.number))
                self.spawned += 1
                self.spawn_timer = self.spawn_delay
        elif not self.boss_spawned and alive == 0:
            boss_x = WIDTH - 140 if self.player.x < WIDTH / 2 else 140
            if self.number == FINAL_LEVEL:
                self.boss = Enemy("final_boss", boss_x, self.number)
            else:
                color = lerp_color((200, 80, 30), (150, 0, 30), (self.number - 1) / (FINAL_LEVEL - 1))
                self.boss = Enemy("boss", boss_x, self.number, color)
            self.boss.facing = 1 if self.player.x > boss_x else -1
            self.enemies.append(self.boss)
            self.boss_spawned = True
            self.talk_pending = True

    def start_boss_fight(self):
        """Called once the boss has finished talking: the platforms start to break."""
        if len(self.platforms) > 0:
            self.breaking = True
            self.break_timer = PLATFORM_BREAK_DELAY

    def shatter_platforms(self):
        for p in self.platforms:
            for cx in range(p.left, p.right, 20):
                self.debris.append({"x": cx + 10.0, "y": float(p.top) + 7,
                                    "vx": random.uniform(-70, 70),
                                    "vy": random.uniform(-160, 0)})
        self.platforms = []
        self.breaking = False

    def update_platforms(self, dt):
        if self.breaking:
            self.break_timer -= dt
            if self.break_timer <= 0:
                self.shatter_platforms()
        for d in self.debris:
            d["vy"] += GRAVITY * dt
            d["x"] += d["vx"] * dt
            d["y"] += d["vy"] * dt
        self.debris = [d for d in self.debris if d["y"] < HEIGHT + 30]

    def update_hazards(self, dt):
        p = self.player
        scale = 1 + 0.1 * (self.number - 1)
        for h in self.hazards:
            if h["type"] == "wave":
                h["x"] += h["vx"] * dt
                r = pygame.Rect(0, 0, 40, 30)
                r.midbottom = (int(h["x"]), GROUND_Y)
                if r.colliderect(p.rect):
                    p.take_damage(WAVE_DAMAGE * scale)
                if h["x"] < -60 or h["x"] > WIDTH + 60:
                    h["alive"] = False
            elif h["type"] == "hook":
                h["t"] += dt
                reach = HOOK_REACH_LONG if h["t"] < 0.18 else HOOK_REACH_SHORT
                if h["dir"] == 1:
                    r = pygame.Rect(int(h["x"]) + 20, int(h["y"]) - 125, reach, 40)
                else:
                    r = pygame.Rect(int(h["x"]) - 20 - reach, int(h["y"]) - 125, reach, 40)
                if not h["hit"] and r.colliderect(p.rect):
                    p.take_damage(HOOK_DAMAGE * scale)
                    h["hit"] = True
                if h["t"] > 0.40:
                    h["alive"] = False
            elif h["type"] == "crate":
                h["vy"] += h["g"] * dt
                h["x"] += h["vx"] * dt
                h["y"] += h["vy"] * dt
                h["rot"] += 360 * dt
                r = pygame.Rect(0, 0, 44, 44)
                r.center = (int(h["x"]), int(h["y"]))
                hit = r.colliderect(p.rect)
                if hit:
                    p.take_damage(h.get("dmg", POISON_HIT) * scale)
                if hit or h["y"] >= GROUND_Y - 16:
                    h["alive"] = False
                    self.hazards.append({"type": "puddle", "x": h["x"], "life": POISON_LIFE,
                                         "tint": h.get("tint"), "alive": True})
            elif h["type"] == "melee":
                h["t"] += dt
                reach = h["reach"]
                left = h["x"] + 15 if h["dir"] == 1 else h["x"] - 15 - reach
                r = pygame.Rect(int(left), int(h["y"]) - 60, reach, 60)
                if not h["hit"] and r.colliderect(p.rect):
                    p.take_damage(h["dmg"] * scale)
                    h["hit"] = True
                if h["t"] > h["life"]:
                    h["alive"] = False
            elif h["type"] == "sludge":
                h["age"] += dt
                h["x"] += h["dir"] * SLUDGE_SPEED * dt
                r = pygame.Rect(0, 0, 150, SLUDGE_HEIGHT)
                r.midbottom = (int(h["x"]), GROUND_Y)
                if r.colliderect(p.rect):
                    p.take_damage(SLUDGE_DAMAGE * scale)
                if h["x"] < -200 or h["x"] > WIDTH + 200:
                    h["alive"] = False
            elif h["type"] == "puddle":
                h["life"] -= dt
                r = pygame.Rect(0, 0, 150, 24)
                r.midbottom = (int(h["x"]), GROUND_Y)
                if r.colliderect(p.rect):
                    p.take_damage(POISON_TICK * scale)
                if h["life"] <= 0:
                    h["alive"] = False
            elif h["type"] == "tsunami":
                h["age"] += dt
                h["x"] += h["dir"] * TSUNAMI_SPEED * dt
                r = pygame.Rect(0, 0, 120, TSUNAMI_HEIGHT)
                r.midbottom = (int(h["x"]), GROUND_Y)
                if r.colliderect(p.rect):
                    p.take_damage(TSUNAMI_DAMAGE * scale)
                if h["x"] < -200 or h["x"] > WIDTH + 200:
                    h["alive"] = False
            else:
                if h["timer"] > 0:
                    h["timer"] -= dt
                else:
                    h["y"] += ROCK_SPEED * dt
                    r = pygame.Rect(0, 0, 36, 36)
                    r.center = (int(h["x"]), int(h["y"]))
                    if r.colliderect(p.rect):
                        p.take_damage(ROCK_DAMAGE * scale)
                        h["alive"] = False
                    if h["y"] >= GROUND_Y - 18:
                        h["alive"] = False
        self.hazards = [h for h in self.hazards if h["alive"]]

    def update(self, dt):
        p = self.player
        self.spawn_logic(dt)
        self.update_platforms(dt)

        for e in self.enemies:
            e.update(dt, p.x, p.y, self.enemy_bullets, self.hazards, self.platforms)

        for b in p.bullets:
            brect = pygame.Rect(0, 0, 12, 6)
            brect.center = (int(b["x"]), int(b["y"]))
            for e in self.enemies:
                if b["alive"] and brect.colliderect(e.rect):
                    e.hp -= p.damage
                    e.flash = 0.1
                    b["alive"] = False
        p.bullets = [b for b in p.bullets if b["alive"]]

        for e in self.enemies:
            if e.hp <= 0:
                if not self.replay:
                    self.earned += e.coins
                if e.is_boss:
                    self.boss_dead = True
                else:
                    self.killed += 1
        self.enemies = [e for e in self.enemies if e.hp > 0]

        for e in self.enemies:
            if e.rect.colliderect(p.rect):
                p.take_damage(e.touch)

        for eb in self.enemy_bullets:
            eb["x"] += eb["vx"] * dt
            eb["y"] += eb["vy"] * dt
            if "img" in eb:
                r = pygame.Rect(0, 0, eb["img"].get_width(), 14)
            else:
                r = pygame.Rect(0, 0, 12, 12)
            r.center = (int(eb["x"]), int(eb["y"]))
            if r.colliderect(p.rect):
                p.take_damage(eb["damage"])
                eb["alive"] = False
            if eb["x"] < -30 or eb["x"] > WIDTH + 30 or eb["y"] < 0 or eb["y"] > HEIGHT:
                eb["alive"] = False
        self.enemy_bullets = [eb for eb in self.enemy_bullets if eb["alive"]]

        self.update_hazards(dt)

        result = ""
        if p.hp <= 0:
            result = "lost"
        elif self.boss_dead:
            result = "won"
        return result

    def draw_platforms(self, screen):
        for p in self.platforms:
            shake = random.randint(-2, 2) if self.breaking else 0
            body = (150, 70, 50) if self.breaking else (120, 85, 55)
            top = (200, 110, 80) if self.breaking else (165, 125, 85)
            r = p.move(shake, 0)
            pygame.draw.rect(screen, body, r)
            pygame.draw.rect(screen, top, (r.left, r.top, r.width, 4))
            pygame.draw.rect(screen, (60, 40, 25), r, 2)
            if self.breaking:
                for cx in range(r.left + 20, r.right - 10, 40):
                    pygame.draw.line(screen, (40, 25, 15), (cx, r.top), (cx + 6, r.bottom), 2)
        for d in self.debris:
            pygame.draw.rect(screen, (120, 85, 55), (d["x"] - 9, d["y"] - 7, 18, 14))
            pygame.draw.rect(screen, (60, 40, 25), (d["x"] - 9, d["y"] - 7, 18, 14), 2)

    def draw_hazards(self, screen):
        for h in self.hazards:
            if h["type"] == "wave":
                x = int(h["x"])
                points = [(x - 20, GROUND_Y), (x - 12, GROUND_Y - 30), (x - 4, GROUND_Y - 12),
                          (x + 4, GROUND_Y - 30), (x + 12, GROUND_Y - 12), (x + 20, GROUND_Y)]
                pygame.draw.polygon(screen, (255, 150, 30), points)
                pygame.draw.polygon(screen, (255, 230, 120), points, 2)
            elif h["type"] == "crate":
                img = pygame.transform.rotate(h["img"], h["rot"])
                screen.blit(img, img.get_rect(center=(int(h["x"]), int(h["y"]))))
            elif h["type"] == "puddle":
                fade = min(1.0, h["life"] / 0.8)
                x = int(h["x"])
                rim = lerp_color((20, 20, 30), (130, 220, 60), fade)
                fill = lerp_color((20, 20, 30), (70, 150, 40) if h.get("tint") == "green" else (110, 40, 160), fade)
                pygame.draw.ellipse(screen, rim, (x - 78, GROUND_Y - 16, 156, 24))
                pygame.draw.ellipse(screen, fill, (x - 70, GROUND_Y - 13, 140, 17))
                for i in range(3):
                    bx = x - 40 + i * 40 + int(8 * math.sin(h["life"] * 4 + i))
                    pygame.draw.circle(screen, rim, (bx, GROUND_Y - 18 - int((h["life"] * 20 + i * 7) % 12)), 3)
            elif h["type"] == "sludge":
                x = int(h["x"])
                d = h["dir"]
                grow = min(1.0, h["age"] / 0.35)
                top = int(SLUDGE_HEIGHT * (0.35 + 0.65 * grow))
                points = [(x - d * 75, GROUND_Y), (x - d * 75, GROUND_Y - 30)]
                for i in range(1, 7):
                    t = i / 6.0
                    px = x - d * 75 + d * 150 * t * 0.85
                    py = GROUND_Y - 30 - (top - 30) * t - int(6 * math.sin(h["age"] * 9 + i * 1.7))
                    points.append((px, py))
                points += [(x + d * 75, GROUND_Y - top * 0.55), (x + d * 75, GROUND_Y)]
                pygame.draw.polygon(screen, (84, 96, 46), points)
                pygame.draw.polygon(screen, (160, 180, 80), points, 3)
                for i in range(4):
                    bx = x - d * 50 + d * i * 32
                    by = GROUND_Y - 20 - int((h["age"] * 40 + i * 23) % (top - 25))
                    pygame.draw.circle(screen, (180, 210, 90), (bx, by), 4, 2)
            elif h["type"] == "melee":
                pass        # the tail whack is part of the rat's picture
            elif h["type"] == "tsunami":
                index = min(len(h["frames"]) - 1, int(h["age"] / 0.15))
                image, anchor = h["frames"][index]
                screen.blit(image, (h["x"] - anchor, GROUND_Y + 6 - image.get_height()))
            elif h["type"] == "hook":
                pass        # the hook is part of the Crate Captain's picture
            else:
                x = int(h["x"])
                if h["timer"] > 0:
                    grow = 1.0 - h["timer"] / ROCK_WARNING
                    w = int(20 + 40 * grow)
                    pygame.draw.ellipse(screen, (230, 50, 50), (x - w // 2, GROUND_Y - 6, w, 12), 3)
                else:
                    y = int(h["y"])
                    if self.number == 2:
                        crate = pygame.Rect(x - 17, y - 17, 34, 34)
                        pygame.draw.rect(screen, (175, 125, 70), crate)
                        pygame.draw.rect(screen, (70, 45, 25), crate, 3)
                        pygame.draw.line(screen, (70, 45, 25), crate.topleft, crate.bottomright, 3)
                        pygame.draw.line(screen, (70, 45, 25), crate.topright, crate.bottomleft, 3)
                    elif x % 2 == 0:
                        hexagon = [(x - 18, y), (x - 9, y - 16), (x + 9, y - 16),
                                   (x + 18, y), (x + 9, y + 16), (x - 9, y + 16)]
                        pygame.draw.polygon(screen, (150, 95, 55), hexagon)
                        pygame.draw.polygon(screen, (50, 30, 20), hexagon, 3)
                        pygame.draw.circle(screen, (45, 30, 25), (x, y), 7)
                    else:
                        pygame.draw.rect(screen, (130, 130, 135), (x - 5, y - 8, 10, 30))
                        pygame.draw.rect(screen, (60, 60, 70), (x - 5, y - 8, 10, 30), 2)
                        pygame.draw.rect(screen, (150, 95, 55), (x - 13, y - 20, 26, 14))
                        pygame.draw.rect(screen, (50, 30, 20), (x - 13, y - 20, 26, 14), 3)

    def draw(self, screen):
        self.draw_platforms(screen)
        self.draw_hazards(screen)
        for e in self.enemies:
            e.draw(screen)
        for eb in self.enemy_bullets:
            if "img" in eb:
                screen.blit(eb["img"], eb["img"].get_rect(center=(int(eb["x"]), int(eb["y"]))))
            else:
                pygame.draw.circle(screen, (255, 70, 70), (int(eb["x"]), int(eb["y"])), 6)
                pygame.draw.circle(screen, (255, 220, 220), (int(eb["x"]), int(eb["y"])), 3)


# ------------------------------------------------------------------
# LEVEL 2: three phases
#   docks      - 20 grunts arrive from both sides, platforms to fight on
#   climb      - the tide rises, climb the lighthouse (the camera follows you up)
#   boss       - the Crate Captain, inside the lamp room
# ------------------------------------------------------------------
class Level2(Level):
    def __init__(self, number, player, progress):
        Level.__init__(self, number, player, progress)
        self.total = L2_GRUNTS
        self.spawn_delay = L2_SPAWN_DELAY
        self.max_alive = L2_MAX_ALIVE
        self.kinds = ["grunt"]
        self.phase = "docks"          # docks, docks_done, climb, to_boss, boss
        self.climb_platforms = make_climb_platforms()
        self.balcony = self.climb_platforms[-1]
        self.top_world = self.balcony.top - 70          # roof of the lighthouse (world y)
        self.max_scroll = HEIGHT * 0.6 - self.balcony.top + 40
        self.tide_y = float(GROUND_Y + TIDE_START_BELOW)
        self.climb_time = 0.0
        self.tower_grow = 0.0
        self.anim_t = 0.0
        self.beam = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    # ---------- phase logic ----------
    def spawn_logic(self, dt):
        """Phase 1: grunts come in pairs, one from each side at the same moment."""
        if self.phase != "docks" or self.spawned >= self.total:
            return
        self.spawn_timer -= dt
        if self.spawn_timer <= 0 and len(self.enemies) + 2 <= self.max_alive:
            for side in (-40, WIDTH + 40):
                self.enemies.append(Enemy("grunt", side, self.number))
                self.spawned += 1
            self.spawn_timer = self.spawn_delay

    def start_boss_fight(self):
        pass        # the lamp room ledges do not break

    def status_text(self):
        if self.phase in ("docks", "docks_done"):
            return "PHASE 1 - Grunts left: " + str(self.total - self.killed)
        if self.phase in ("climb", "to_boss"):
            height = GROUND_Y - self.balcony.top
            pct = max(0, min(100, int(100 * (GROUND_Y - self.player.y) / height)))
            return "PHASE 2 - Climb the lighthouse!  " + str(pct) + "%"
        return None

    def phase_dialogue_done(self):
        if self.phase == "docks_done":
            self.begin_climb()
        elif self.phase == "to_boss":
            self.begin_boss_phase()

    def begin_climb(self):
        self.shatter_platforms()                 # the docks collapse into the sea
        self.platforms = self.climb_platforms
        self.enemy_bullets = []
        self.hazards = []
        self.tide_y = float(GROUND_Y + TIDE_START_BELOW)
        self.climb_time = 0.0
        self.phase = "climb"

    def begin_boss_phase(self):
        self.phase = "boss"
        self.platforms = [pygame.Rect(r) for r in LEVEL2_ROOM_PLATFORMS]
        self.debris = []
        self.scroll = 0.0
        p = self.player
        p.x = 200.0
        p.y = float(GROUND_Y)
        p.vy = 0.0
        p.on_ground = True
        p.bullets = []
        self.enemy_bullets = []
        self.hazards = []
        self.boss = Enemy("boss", WIDTH - 140, self.number, (175, 115, 55))
        self.boss.facing = -1
        self.enemies.append(self.boss)
        self.boss_spawned = True
        self.talk_pending = True

    def update(self, dt):
        self.anim_t += dt
        if self.phase == "docks" or self.phase == "boss":
            result = Level.update(self, dt)
            if (self.phase == "docks" and result == "" and self.spawned >= self.total
                    and len(self.enemies) == 0):
                self.phase = "docks_done"
                self.pending_dialogue = L2_TIDE_TALK
            return result
        if self.phase == "climb":
            return self.update_climb(dt)
        return "lost" if self.player.hp <= 0 else ""       # waiting for a dialogue to be clicked

    def update_climb(self, dt):
        p = self.player
        self.climb_time += dt
        self.tower_grow = min(1.0, self.tower_grow + dt / 2.5)
        self.update_platforms(dt)

        speed = TIDE_SPEED + TIDE_GROWTH * self.climb_time
        self.tide_y -= speed * dt
        if p.y > self.tide_y + 10:
            p.hp -= TIDE_DAMAGE * dt

        target = max(0.0, min(self.max_scroll, HEIGHT * 0.6 - p.y))
        self.scroll += (target - self.scroll) * min(1.0, 8 * dt)

        if p.hp <= 0:
            return "lost"
        b = self.balcony
        if p.on_ground and p.y <= b.top + 1 and b.left <= p.x <= b.right:
            self.phase = "to_boss"
            self.pending_dialogue = L2_TOP_TALK
        return ""

    # ---------- drawing ----------
    def draw_platforms(self, screen):
        sc = int(self.scroll)
        if self.phase == "boss":
            body, top, edge = (85, 85, 100), (140, 140, 158), (40, 40, 55)
        else:
            body, top, edge = (120, 85, 55), (165, 125, 85), (60, 40, 25)
        for p in self.platforms:
            r = p.move(0, sc)
            if r.bottom < 0 or r.top > HEIGHT:
                continue
            pygame.draw.rect(screen, body, r)
            pygame.draw.rect(screen, top, (r.left, r.top, r.width, 4))
            pygame.draw.rect(screen, edge, r, 2)
        for d in self.debris:
            pygame.draw.rect(screen, (120, 85, 55), (d["x"] - 9, d["y"] + sc - 7, 18, 14))
            pygame.draw.rect(screen, (60, 40, 25), (d["x"] - 9, d["y"] + sc - 7, 18, 14), 2)

    def climb_progress(self):
        if self.phase in ("climb", "to_boss"):
            return max(0.0, min(1.0, self.scroll / self.max_scroll))
        return 0.0

    def draw_background(self, screen):
        if self.phase == "boss":
            self.draw_interior(screen)
            return
        sc = self.scroll
        prog = self.climb_progress()
        screen.fill(lerp_color((110, 165, 215), (28, 32, 70), prog))

        if prog > 0.4:                                   # stars come out as you climb
            for sx, sy in STARS:
                pygame.draw.circle(screen, (230, 230, 255), (sx, int((sy + sc * 0.1) % HEIGHT)), 2)
        cloud = lerp_color((238, 242, 250), (75, 80, 115), prog)
        for cx, cy, cw in CLOUDS:
            y = int((cy + sc * 0.35) % (HEIGHT + 120)) - 60
            ch = int(cw * 0.3)
            pygame.draw.ellipse(screen, cloud, (cx, y, cw, ch))
            pygame.draw.ellipse(screen, cloud, (cx + cw // 5, y - ch // 2, cw // 2, ch))
            pygame.draw.ellipse(screen, cloud, (cx + cw // 2, y - ch // 3, cw // 2, ch))

        sea_top = int(HORIZON_Y + sc)                    # the ocean
        if sea_top < HEIGHT:
            top = max(0, sea_top)
            pygame.draw.rect(screen, lerp_color((40, 110, 165), (14, 38, 80), prog),
                             (0, top, WIDTH, HEIGHT - top))
            streak = lerp_color((90, 160, 205), (40, 70, 120), prog)
            for k in range(0, (HEIGHT - top) // 18 + 2):
                y = sea_top + 14 + k * 18
                if 0 <= y < HEIGHT:
                    for x in range(0, WIDTH, 70):
                        dx = int(x + (k * 23 + self.anim_t * 18) % 70)
                        pygame.draw.line(screen, streak, (dx, y), (dx + 26, y), 2)

        self.draw_lighthouse(screen)

        deck_top = int(GROUND_Y + sc)                    # the wooden docks
        if deck_top < HEIGHT:
            for x in (60, 300, 560, 820):
                pygame.draw.rect(screen, (70, 48, 30), (x, deck_top + 80, 16, HEIGHT))
            pygame.draw.rect(screen, (125, 88, 52), (0, deck_top, WIDTH, 80))
            pygame.draw.rect(screen, (165, 125, 85), (0, deck_top, WIDTH, 6))
            pygame.draw.line(screen, (80, 55, 33), (0, deck_top + 40), (WIDTH, deck_top + 40), 2)
            for x in range(0, WIDTH, 48):
                pygame.draw.line(screen, (80, 55, 33), (x, deck_top + 6), (x, deck_top + 80), 2)

    def draw_lighthouse(self, screen):
        cx = WIDTH // 2
        sc = self.scroll
        if self.phase in ("docks", "docks_done"):
            top_world = LIGHTHOUSE_SHORT_TOP
        else:
            e = self.tower_grow * self.tower_grow * (3 - 2 * self.tower_grow)
            top_world = LIGHTHOUSE_SHORT_TOP + (self.top_world - LIGHTHOUSE_SHORT_TOP) * e
        base_y = GROUND_Y - 30 + sc
        top_y = top_world + sc
        bw, tw, band = 130.0, 84.0, 70
        total = base_y - top_y

        def width_at(y):
            return tw + (bw - tw) * (y - top_y) / total

        bands = int(total // band) + 1
        for k in range(bands):
            y1 = base_y - k * band
            y0 = max(top_y, y1 - band)
            if y1 < 0 or y0 > HEIGHT:
                continue
            color = (200, 55, 55) if k % 2 == 0 else (235, 235, 238)
            w0, w1 = width_at(y0), width_at(y1)
            pygame.draw.polygon(screen, color, [(cx - w0 / 2, y0), (cx + w0 / 2, y0),
                                                (cx + w1 / 2, y1), (cx - w1 / 2, y1)])
            if k % 3 == 1:
                yc = (y0 + y1) / 2
                pygame.draw.rect(screen, (40, 50, 80), (cx - 7, yc - 14, 14, 28))
                pygame.draw.rect(screen, (30, 30, 40), (cx - 7, yc - 14, 14, 28), 2)
        if base_y > 0:
            pygame.draw.line(screen, (60, 60, 70), (cx - bw / 2, base_y), (cx - tw / 2, top_y), 3)
            pygame.draw.line(screen, (60, 60, 70), (cx + bw / 2, base_y), (cx + tw / 2, top_y), 3)

        if top_y > -90:                                  # lamp room, roof and the sweeping beam
            pygame.draw.rect(screen, (70, 70, 80), (cx - tw / 2 - 16, top_y, tw + 32, 8))
            pygame.draw.rect(screen, (255, 235, 140), (cx - 24, top_y - 46, 48, 46))
            pygame.draw.rect(screen, (60, 60, 70), (cx - 24, top_y - 46, 48, 46), 3)
            pygame.draw.polygon(screen, (190, 50, 50), [(cx - 34, top_y - 46), (cx + 34, top_y - 46),
                                                        (cx, top_y - 82)])
            self.beam.fill((0, 0, 0, 0))
            reach = math.sin(self.anim_t * 0.8) * 800
            ly = top_y - 23
            pygame.draw.polygon(self.beam, (255, 240, 150, 55),
                                [(cx, ly - 6), (cx + reach, ly - 60), (cx + reach, ly + 60), (cx, ly + 6)])
            screen.blit(self.beam, (0, 0))

        if base_y < HEIGHT + 80:                         # the rocks the lighthouse stands on
            pygame.draw.rect(screen, (60, 40, 30), (cx - 14, base_y - 44, 28, 44))
            pygame.draw.ellipse(screen, (90, 90, 98), (cx - 150, base_y - 25, 300, 70))
            pygame.draw.ellipse(screen, (120, 120, 128), (cx - 110, base_y - 28, 220, 40))

    def draw_interior(self, screen):
        cx = WIDTH // 2
        screen.fill((38, 36, 50))
        for y in range(0, GROUND_Y, 36):
            pygame.draw.line(screen, (52, 50, 66), (0, y), (WIDTH, y), 2)
            for x in range(((y // 36) % 2) * 40, WIDTH, 80):
                pygame.draw.line(screen, (52, 50, 66), (x, y), (x, y + 36), 2)
        for wx in (90, WIDTH - 230):                      # arched windows onto the night sea
            night = (18, 26, 62)
            pygame.draw.rect(screen, night, (wx, 90, 140, 210))
            pygame.draw.circle(screen, night, (wx + 70, 90), 70)
            pygame.draw.rect(screen, (18, 40, 80), (wx, 230, 140, 70))
            for sx, sy in ((20, 60), (100, 30), (60, 110), (120, 150), (30, 170)):
                pygame.draw.circle(screen, (230, 230, 255), (wx + sx, 60 + sy), 2)
            pygame.draw.rect(screen, (95, 92, 110), (wx - 6, 90, 152, 216), 6)
            pygame.draw.circle(screen, (95, 92, 110), (wx + 70, 90), 76, 6, True, True, False, False)
        pygame.draw.rect(screen, (75, 72, 90), (cx - 18, 190, 36, GROUND_Y - 190))   # lamp pillar
        pulse = 1 + 0.08 * math.sin(self.anim_t * 3)
        self.beam.fill((0, 0, 0, 0))
        pygame.draw.circle(self.beam, (255, 230, 120, 50), (cx, 150), int(130 * pulse))
        pygame.draw.circle(self.beam, (255, 230, 120, 90), (cx, 150), int(90 * pulse))
        screen.blit(self.beam, (0, 0))
        pygame.draw.circle(screen, (255, 240, 170), (cx, 150), 44)
        pygame.draw.circle(screen, (90, 85, 100), (cx, 150), 44, 5)
        pygame.draw.line(screen, (90, 85, 100), (cx - 44, 150), (cx + 44, 150), 3)
        pygame.draw.line(screen, (90, 85, 100), (cx, 106), (cx, 194), 3)
        pygame.draw.rect(screen, (70, 66, 82), (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        pygame.draw.rect(screen, (110, 106, 125), (0, GROUND_Y, WIDTH, 6))
        for x in range(0, WIDTH, 80):
            pygame.draw.line(screen, (50, 47, 62), (x, GROUND_Y + 6), (x, HEIGHT), 2)

    def draw_foreground(self, screen):
        """The rising tide is drawn over the player so you can see yourself wading in it."""
        if self.phase not in ("climb", "to_boss"):
            return
        water_top = self.tide_y + self.scroll
        if water_top >= HEIGHT:
            return
        top = int(max(water_top, -20))
        h = HEIGHT - top + 12
        surf = pygame.Surface((WIDTH, h), pygame.SRCALPHA)
        points = [(0, h)]
        for x in range(0, WIDTH + 20, 20):
            points.append((x, 12 + 6 * math.sin(x * 0.03 + self.anim_t * 3)))
        points.append((WIDTH, h))
        pygame.draw.polygon(surf, (25, 90, 170, 150), points)
        pygame.draw.lines(surf, (190, 225, 255), False, points[1:-1], 3)
        screen.blit(surf, (0, top - 12))


# ------------------------------------------------------------------
# LEVEL 3: three phases
#   city   - walk through the city at night to the open manhole, fall in
#   rats   - 15 giant sewer rats from both sides (sewer hall)
#   boss   - walk right into the secret room and fight Sly Sam (rat waves keep coming)
# ------------------------------------------------------------------
def make_buildings(rng, end, wmin, wmax, hmin, hmax):
    out = []
    x = 0
    while x < end:
        w = rng.randint(wmin, wmax)
        out.append((x, w, rng.randint(hmin, hmax)))
        x += w + rng.randint(0, 18)
    return out


def draw_poop(screen, x, y, s=1.0):
    base, dark, light = (112, 70, 34), (66, 38, 16), (160, 108, 60)
    for w, h, up in ((46, 16, 0), (34, 14, 11), (22, 12, 21), (9, 8, 30)):
        r = pygame.Rect(int(x - w * s / 2), int(y - up * s - h * s), int(w * s), int(h * s))
        pygame.draw.ellipse(screen, base, r)
        pygame.draw.ellipse(screen, dark, r, 2)
        pygame.draw.ellipse(screen, light, (r.left + r.width // 5, r.top + 2, max(2, r.width // 4), max(2, r.height // 4)))


def draw_bag(screen, x, y, s=1.0):
    body = pygame.Rect(int(x - 19 * s), int(y - 30 * s), int(38 * s), int(30 * s))
    pygame.draw.ellipse(screen, (34, 46, 36), body)
    pygame.draw.ellipse(screen, (12, 18, 14), body, 2)
    pygame.draw.polygon(screen, (34, 46, 36), [(x - 6 * s, y - 27 * s), (x - 11 * s, y - 40 * s),
                                               (x - 2 * s, y - 31 * s), (x + 8 * s, y - 41 * s),
                                               (x + 6 * s, y - 27 * s)])
    pygame.draw.line(screen, (90, 110, 90), (x - 10 * s, y - 22 * s), (x - 5 * s, y - 15 * s), 2)


def draw_can_prop(screen, x, y, s=1.0):
    body = pygame.Rect(int(x - 15 * s), int(y - 44 * s), int(30 * s), int(44 * s))
    pygame.draw.rect(screen, (112, 118, 122), body)
    for k in (-8, 0, 8):
        pygame.draw.line(screen, (74, 80, 86), (x + k * s, y - 40 * s), (x + k * s, y - 4 * s), 2)
    pygame.draw.rect(screen, (36, 40, 46), body, 2)
    lid = pygame.Rect(int(x - 17 * s), int(y - 50 * s), int(34 * s), int(7 * s))
    pygame.draw.rect(screen, (150, 156, 160), lid)
    pygame.draw.rect(screen, (36, 40, 46), lid, 2)


def draw_bottle(screen, x, y, s=1.0):
    pygame.draw.rect(screen, (70, 150, 120), (int(x - 5 * s), int(y - 22 * s), int(10 * s), int(22 * s)))
    pygame.draw.rect(screen, (70, 150, 120), (int(x - 2 * s), int(y - 30 * s), int(4 * s), int(9 * s)))
    pygame.draw.rect(screen, (20, 50, 40), (int(x - 5 * s), int(y - 22 * s), int(10 * s), int(22 * s)), 1)


JUNK_DRAW = {"poop": draw_poop, "bag": draw_bag, "can": draw_can_prop, "bottle": draw_bottle}
HALL_JUNK = [("poop", 90, 1.0), ("bag", 170, 1.1), ("can", 255, 1.0), ("poop", 340, 1.2), ("bottle", 415, 1.0),
             ("bag", 505, 1.0), ("poop", 600, 0.9), ("can", 690, 1.1), ("bag", 780, 1.2), ("poop", 870, 1.0),
             ("bottle", 935, 1.0)]
ROOM_JUNK = [("can", 70, 1.5), ("bag", 130, 1.2), ("poop", 205, 1.2), ("can", 330, 1.3), ("poop", 420, 1.0),
             ("bag", 540, 1.1), ("can", 625, 1.5), ("poop", 710, 1.3), ("bag", 800, 1.2), ("can", 890, 1.4)]


class Level3(Level):
    def __init__(self, number, player, progress):
        Level.__init__(self, number, player, progress)
        self.total = L3_RATS
        self.spawn_delay = L3_SPAWN_DELAY
        self.max_alive = L3_MAX_ALIVE
        self.kinds = ["rat"]
        self.phase = "city"       # city, falling, to_sewer, rats, rats_done, go_right, to_boss, boss
        self.scroll_x = 0.0       # how far you have walked through the city
        self.hole_x = 0.0
        self.fall_t = 0.0
        self.door_t = 0.0
        self.anim_t = 0.0
        self.wave_timer = L3_FIRST_WAVE
        self.wave_warning = 0.0
        self.far = make_buildings(random.Random(11), 3600, 70, 130, 130, 280)
        self.near = make_buildings(random.Random(12), 3800, 90, 170, 170, 340)
        self.glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.fade = pygame.Surface((WIDTH, HEIGHT))
        self.fade.fill((0, 0, 0))

    # ---------- phase logic ----------
    def start_boss_fight(self):
        pass        # the platforms in the secret room do not break

    def status_text(self):
        if self.phase in ("city", "falling", "to_sewer"):
            return "PHASE 1 - Find the manhole"
        if self.phase in ("rats", "rats_done"):
            return "PHASE 2 - Rats left: " + str(self.total - self.killed)
        if self.phase in ("go_right", "to_boss"):
            return "PHASE 3 - Find Sly Sam's hideout"
        if self.phase == "boss" and self.boss_dead:
            return "Finish off the rats!"
        return None

    def banner_text(self):
        if self.phase == "go_right" and int(self.anim_t * 2) % 2 == 0:
            return "GO RIGHT  >>>"
        if self.phase == "city" and self.scroll_x < 400 and int(self.anim_t * 2) % 2 == 0:
            return "WALK RIGHT  >>>"
        if self.phase == "boss" and self.wave_warning > 0:
            return str(L3_WAVE_SIZE) + " MORE RATS INCOMING!"
        return None

    def phase_dialogue_done(self):
        if self.phase == "to_sewer":
            self.begin_rats()
        elif self.phase == "rats_done":
            self.phase = "go_right"
        elif self.phase == "to_boss":
            self.begin_boss_phase()

    def put_player(self, x):
        p = self.player
        p.x = float(x)
        p.y = float(GROUND_Y)
        p.vy = 0.0
        p.on_ground = True
        p.bullets = []

    def begin_rats(self):
        self.phase = "rats"
        self.put_player(WIDTH / 2)
        self.scroll_x = 0.0
        self.enemies = []
        self.enemy_bullets = []
        self.hazards = []
        self.spawn_timer = 1.2

    def begin_boss_phase(self):
        self.phase = "boss"
        self.platforms = [pygame.Rect(r) for r in LEVEL3_ROOM_PLATFORMS]
        self.put_player(130)
        self.enemies = []
        self.enemy_bullets = []
        self.hazards = []
        self.boss = Enemy("boss", WIDTH - 170, self.number, (60, 90, 40))
        self.boss.facing = -1
        self.enemies.append(self.boss)
        self.boss_spawned = True
        self.talk_pending = True
        self.wave_timer = L3_FIRST_WAVE

    def spawn_wave(self):
        for i in range(L3_WAVE_SIZE):
            if i % 2 == 0:
                x = -50 - 45 * (i // 2)
            else:
                x = WIDTH + 50 + 45 * (i // 2)
            rat = Enemy("rat", x, self.number)
            rat.coins = 0                      # wave rats give no coins (no farming)
            self.enemies.append(rat)
        self.wave_warning = 2.5

    def spawn_logic(self, dt):
        if self.phase == "rats":
            if self.spawned >= self.total:
                return
            self.spawn_timer -= dt
            if self.spawn_timer <= 0 and len(self.enemies) + 2 <= self.max_alive:
                for side in (-50, WIDTH + 50):          # one from each side at the same moment
                    if self.spawned < self.total:
                        self.enemies.append(Enemy("rat", side, self.number))
                        self.spawned += 1
                self.spawn_timer = self.spawn_delay
        elif self.phase == "boss" and not self.boss_dead:
            self.wave_warning = max(0.0, self.wave_warning - dt)
            self.wave_timer -= dt
            if self.wave_timer <= 0:
                self.spawn_wave()
                self.wave_timer = L3_WAVE_EVERY

    def update(self, dt):
        self.anim_t += dt
        ph = self.phase
        if ph == "city":
            return self.update_city()
        if ph == "falling":
            return self.update_fall(dt)
        if ph in ("rats", "go_right", "boss"):
            result = Level.update(self, dt)
            if ph == "rats":
                if result == "" and self.spawned >= self.total and len(self.enemies) == 0:
                    self.phase = "rats_done"
                    self.pending_dialogue = L3_RATS_DONE
            elif ph == "go_right":
                self.door_t = min(1.0, self.door_t + dt)
                if self.player.x >= WIDTH - 50:
                    self.phase = "to_boss"
                    self.pending_dialogue = L3_SECRET_TALK
            elif result == "won" and len(self.enemies) > 0:
                result = ""                    # Sly Sam is down, but the rats must go too
            return result
        if ph == "rats_done":
            self.door_t = min(1.0, self.door_t + dt)
        return "lost" if self.player.hp <= 0 else ""

    def update_city(self):
        p = self.player
        max_scroll = CITY_MANHOLE_X - 640
        if p.x > 520 and self.scroll_x < max_scroll:
            d = min(p.x - 520, max_scroll - self.scroll_x)
            self.scroll_x += d
            p.x -= d
        elif p.x < 300 and self.scroll_x > 0:
            d = min(300 - p.x, self.scroll_x)
            self.scroll_x -= d
            p.x += d
        if p.x + self.scroll_x >= CITY_MANHOLE_X:
            self.phase = "falling"
            self.fall_t = 0.0
            self.hole_x = CITY_MANHOLE_X - self.scroll_x
        return ""

    def update_fall(self, dt):
        p = self.player
        self.fall_t += dt
        p.x = self.hole_x
        p.vy = 0.0
        p.on_ground = False
        p.y = GROUND_Y + 0.5 * 1800 * self.fall_t * self.fall_t
        if self.fall_t >= 1.2:
            self.phase = "to_sewer"
            self.pending_dialogue = L3_FALL_TALK
        return ""

    # ---------- drawing ----------
    def draw_platforms(self, screen):
        for p in self.platforms:
            pygame.draw.rect(screen, (70, 80, 70), p)
            pygame.draw.rect(screen, (125, 145, 110), (p.left, p.top, p.width, 4))
            pygame.draw.rect(screen, (30, 40, 30), p, 2)
            for x in range(p.left + 12, p.right - 6, 24):
                pygame.draw.line(screen, (40, 52, 40), (x, p.top + 4), (x, p.bottom - 2), 2)

    def draw_background(self, screen):
        if self.phase in ("city", "falling"):
            self.draw_city(screen)
        elif self.phase == "to_sewer":
            screen.fill((0, 0, 0))
        elif self.phase == "boss":
            self.draw_secret_room(screen)
        else:
            self.draw_sewer_hall(screen)

    def draw_city(self, screen):
        sx = self.scroll_x
        bands = 14
        for i in range(bands):
            c = lerp_color((6, 8, 24), (52, 36, 84), i / (bands - 1))
            top = i * GROUND_Y // bands
            pygame.draw.rect(screen, c, (0, top, WIDTH, GROUND_Y // bands + 2))
        for k, (stx, sty) in enumerate(STARS):
            pygame.draw.circle(screen, (225, 225, 250), (int((stx * 1.1 - sx * 0.03) % WIDTH), sty + 10), 1 + k % 2)
        mx = int(770 - sx * 0.02)
        pygame.draw.circle(screen, (238, 236, 205), (mx, 90), 34)
        pygame.draw.circle(screen, (10, 12, 32), (mx + 14, 82), 30)       # crescent
        for bx, bw, bh in self.far:                                         # far skyline
            x = int(bx - sx * 0.25)
            if -bw < x < WIDTH:
                pygame.draw.rect(screen, (16, 18, 42), (x, GROUND_Y - bh, bw, bh))
                for wy in range(GROUND_Y - bh + 14, GROUND_Y - 10, 28):
                    for wx in range(x + 8, x + bw - 10, 20):
                        if (bx // 5 + wx // 20 + wy // 28) % 5 == 0:
                            pygame.draw.rect(screen, (150, 130, 80), (wx, wy, 6, 9))
        for bx, bw, bh in self.near:                                        # near buildings
            x = int(bx - sx * 0.55)
            if -bw < x < WIDTH:
                pygame.draw.rect(screen, (26, 28, 60), (x, GROUND_Y - bh, bw, bh))
                pygame.draw.rect(screen, (14, 16, 38), (x, GROUND_Y - bh, bw, bh), 2)
                for wy in range(GROUND_Y - bh + 16, GROUND_Y - 30, 30):
                    for wx in range(x + 10, x + bw - 14, 24):
                        lit = (bx // 7 + wx // 24 + wy // 30) % 4 == 0
                        pygame.draw.rect(screen, (245, 215, 115) if lit else (14, 16, 36), (wx, wy, 11, 15))
        road = (40, 40, 50)                                                 # street
        pygame.draw.rect(screen, road, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        pygame.draw.rect(screen, (98, 98, 112), (0, GROUND_Y, WIDTH, 6))
        for k in range(-1, WIDTH // 120 + 2):
            pygame.draw.rect(screen, (190, 170, 60), (int(k * 120 - sx % 120), GROUND_Y + 40, 60, 6))
        self.glow.fill((0, 0, 0, 0))
        first = int(sx // 380)
        for k in range(first, first + WIDTH // 380 + 3):                  # street lamps
            x = int(k * 380 + 150 - sx)
            pygame.draw.rect(screen, (52, 52, 64), (x - 3, GROUND_Y - 175, 6, 175))
            pygame.draw.rect(screen, (52, 52, 64), (x, GROUND_Y - 177, 26, 5))
            pygame.draw.ellipse(screen, (255, 240, 170), (x + 14, GROUND_Y - 175, 24, 10))
            pygame.draw.polygon(self.glow, (255, 230, 140, 34), [(x + 24, GROUND_Y - 170), (x - 50, GROUND_Y),
                                                                  (x + 100, GROUND_Y)])
            pygame.draw.circle(self.glow, (255, 230, 140, 40), (x + 26, GROUND_Y - 170), 46)
        hx = int(CITY_MANHOLE_X - sx)
        if self.phase == "falling":
            hx = int(self.hole_x)
            pygame.draw.rect(screen, (6, 6, 10), (hx - 30, GROUND_Y, 60, HEIGHT - GROUND_Y))
        elif -80 < hx < WIDTH + 80:                                         # the manhole
            pygame.draw.ellipse(screen, (112, 112, 124), (hx - 38, GROUND_Y - 6, 76, 14))
            pygame.draw.ellipse(screen, (8, 8, 12), (hx - 30, GROUND_Y - 4, 60, 9))
            for i in range(4):                                              # steam
                t = (self.anim_t * 0.6 + i * 0.25) % 1.0
                pygame.draw.circle(self.glow, (200, 210, 220, int(90 * (1 - t))),
                                   (hx + int(10 * math.sin(i * 2 + self.anim_t)), int(GROUND_Y - 10 - 70 * t)),
                                   int(10 + 14 * t))
            bounce = int(5 * math.sin(self.anim_t * 4))
            pygame.draw.polygon(screen, (255, 210, 40), [(hx - 14, GROUND_Y - 64 + bounce),
                                                         (hx + 14, GROUND_Y - 64 + bounce),
                                                         (hx, GROUND_Y - 42 + bounce)])
        screen.blit(self.glow, (0, 0))

    def draw_sewer_hall(self, screen):
        screen.fill((20, 28, 26))
        for y in range(0, GROUND_Y, 30):
            pygame.draw.line(screen, (32, 44, 40), (0, y), (WIDTH, y), 2)
            for x in range((y // 30 % 2) * 30, WIDTH, 60):
                pygame.draw.line(screen, (32, 44, 40), (x, y), (x, y + 30), 2)
        for ax in range(80, WIDTH, 320):                                    # tunnel arches
            pygame.draw.rect(screen, (10, 16, 14), (ax - 70, 150, 140, GROUND_Y - 150))
            pygame.draw.circle(screen, (10, 16, 14), (ax, 150), 70)
            pygame.draw.rect(screen, (50, 64, 56), (ax - 76, 150, 152, GROUND_Y - 150), 5)
            pygame.draw.circle(screen, (50, 64, 56), (ax, 150), 76, 5, True, True, False, False)
        for py in (36, 66):                                                  # pipes with drips
            pygame.draw.rect(screen, (62, 80, 66), (0, py, WIDTH, 16))
            pygame.draw.line(screen, (110, 135, 110), (0, py + 3), (WIDTH, py + 3), 2)
            for jx in range(60, WIDTH, 160):
                pygame.draw.rect(screen, (40, 54, 44), (jx, py - 3, 12, 22))
        for jx in range(120, WIDTH, 160):
            t = (self.anim_t * 0.9 + jx * 0.013) % 1.0
            pygame.draw.circle(screen, (110, 220, 70), (jx, int(84 + (GROUND_Y - 100) * t * t)), 3)
        for mx in range(30, WIDTH, 97):                                      # hanging slime
            pygame.draw.line(screen, (60, 140, 50), (mx, 82), (mx, 82 + 14 + (mx * 7) % 40), 3)
        for lx in (200, 520, 840):                                           # lamps
            pygame.draw.rect(screen, (30, 36, 32), (lx - 10, 120, 20, 10))
            pygame.draw.circle(screen, (200, 230, 120), (lx, 136), 7)
        self.draw_door(screen)
        self.draw_liquid(screen)
        for kind, x, sc in HALL_JUNK:
            JUNK_DRAW[kind](screen, x, GROUND_Y - 4, sc)

    def draw_door(self, screen):
        """The hidden door at the right end of the sewer hall."""
        x = WIDTH - 64
        pygame.draw.rect(screen, (8, 14, 10), (x, GROUND_Y - 170, 64, 170))
        if self.door_t > 0:
            pygame.draw.rect(screen, (60, 200, 60), (x + 10, GROUND_Y - 160, 44, 150), 3)
        lift = int(165 * self.door_t)
        slab = pygame.Rect(x, GROUND_Y - 170 - lift, 64, 170)
        if lift < 165:
            pygame.draw.rect(screen, (46, 60, 52), slab)
            pygame.draw.rect(screen, (24, 34, 28), slab, 3)
            for yy in range(slab.top + 20, slab.bottom, 30):
                pygame.draw.line(screen, (30, 42, 34), (slab.left, yy), (slab.right, yy), 2)

    def draw_liquid(self, screen):
        top = GROUND_Y - 8
        pygame.draw.rect(screen, (46, 108, 40), (0, top, WIDTH, HEIGHT - top))
        pygame.draw.rect(screen, (30, 78, 28), (0, top + 30, WIDTH, HEIGHT - top - 30))
        points = [(0, HEIGHT)]
        for x in range(0, WIDTH + 20, 20):
            points.append((x, top + 3 * math.sin(x * 0.05 + self.anim_t * 2.2)))
        points.append((WIDTH, HEIGHT))
        pygame.draw.polygon(screen, (60, 135, 50), points)
        pygame.draw.lines(screen, (150, 230, 90), False, points[1:-1], 2)
        for i in range(9):
            bx = (i * 113 + int(self.anim_t * 14)) % WIDTH
            pygame.draw.circle(screen, (140, 220, 90), (bx, top + 12 + (i * 17) % 40), 3, 1)

    def draw_secret_room(self, screen):
        cx = WIDTH // 2
        screen.fill((14, 20, 22))
        for y in range(0, GROUND_Y, 32):
            pygame.draw.line(screen, (26, 38, 40), (0, y), (WIDTH, y), 2)
            for x in range((y // 32 % 2) * 36, WIDTH, 72):
                pygame.draw.line(screen, (26, 38, 40), (x, y), (x, y + 32), 2)
        pygame.draw.rect(screen, (46, 64, 56), (0, 44, WIDTH, 22))                  # big pipe
        pygame.draw.line(screen, (100, 130, 105), (0, 49), (WIDTH, 49), 3)
        for px in (140, 480, 820):
            pygame.draw.rect(screen, (30, 44, 38), (px, 38, 16, 34))
            t = (self.anim_t * 0.7 + px * 0.01) % 1.0
            pygame.draw.rect(screen, (110, 230, 70), (px + 6, 72, 4, int(10 + (GROUND_Y - 90) * t)))
        for chx in (180, 780):                                                       # hanging chains
            for k in range(8):
                pygame.draw.ellipse(screen, (80, 88, 90), (chx - 5, 70 + k * 16, 10, 16), 2)
        self.glow.fill((0, 0, 0, 0))
        pulse = 1 + 0.1 * math.sin(self.anim_t * 2.5)
        for gx in (150, 480, 810):                                                   # glowing slime pools
            pygame.draw.circle(self.glow, (90, 255, 70, 40), (gx, GROUND_Y - 6), int(110 * pulse))
        pygame.draw.circle(self.glow, (90, 255, 70, 30), (cx, 120), int(150 * pulse))
        screen.blit(self.glow, (0, 0))
        pygame.draw.rect(screen, (50, 58, 60), (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))   # stone floor
        pygame.draw.rect(screen, (92, 104, 100), (0, GROUND_Y, WIDTH, 6))
        for x in range(0, WIDTH, 90):
            pygame.draw.line(screen, (34, 40, 42), (x, GROUND_Y + 6), (x, HEIGHT), 2)
        for gx in (150, 480, 810):
            pygame.draw.ellipse(screen, (60, 190, 50), (gx - 70, GROUND_Y - 6, 140, 16))
            pygame.draw.ellipse(screen, (140, 255, 100), (gx - 50, GROUND_Y - 3, 100, 8))
        for kind, x, sc in ROOM_JUNK:
            JUNK_DRAW[kind](screen, x, GROUND_Y - 2, sc)

    def draw_foreground(self, screen):
        if self.phase == "falling":
            hx = int(self.hole_x)
            pygame.draw.rect(screen, (40, 40, 50), (0, GROUND_Y, hx - 30, HEIGHT - GROUND_Y))
            pygame.draw.rect(screen, (40, 40, 50), (hx + 30, GROUND_Y, WIDTH - hx - 30, HEIGHT - GROUND_Y))
            pygame.draw.rect(screen, (98, 98, 112), (0, GROUND_Y, hx - 30, 6))
            pygame.draw.rect(screen, (98, 98, 112), (hx + 30, GROUND_Y, WIDTH - hx - 30, 6))
            alpha = int(255 * max(0.0, min(1.0, (self.fall_t - 0.6) / 0.6)))
            if alpha > 0:
                self.fade.set_alpha(alpha)
                screen.blit(self.fade, (0, 0))
        elif self.phase in ("rats", "rats_done", "go_right", "to_boss"):
            band = pygame.Surface((WIDTH, 30), pygame.SRCALPHA)           # the sewage is up to your feet
            band.fill((70, 160, 50, 115))
            screen.blit(band, (0, GROUND_Y - 12))


def make_level(number, player, progress):
    if number == 3:
        return Level3(number, player, progress)
    if number == 2:
        return Level2(number, player, progress)
    return Level(number, player, progress)


# ------------------------------------------------------------------
# UI
# ------------------------------------------------------------------
def wrap_text(text, font, max_width):
    words = text.split(" ")
    lines = []
    current = ""
    for w in words:
        test = w if current == "" else current + " " + w
        if font.size(test)[0] <= max_width:
            current = test
        else:
            lines.append(current)
            current = w
    lines.append(current)
    return lines


class Dialogue:
    """Typed-out text box. update() types it, click() finishes the line or moves on."""

    def __init__(self, lines, kind):
        self.lines = lines
        self.kind = kind          # "intro" or "boss"
        self.index = 0
        self.chars = 0.0
        self.finished = False

    def current_text(self):
        return self.lines[self.index][1]

    def line_complete(self):
        return int(self.chars) >= len(self.current_text())

    def update(self, dt):
        if not self.line_complete():
            self.chars += TYPE_SPEED * dt

    def click(self):
        if not self.line_complete():
            self.chars = float(len(self.current_text()))
        else:
            self.index += 1
            self.chars = 0.0
            if self.index >= len(self.lines):
                self.finished = True

    def draw(self, screen, font_text, font_name, font_small):
        if self.finished:
            return
        speaker = self.lines[self.index][0]
        color = (255, 215, 0) if speaker == "MISSION" else (255, 110, 90)
        box = pygame.Rect(40, HEIGHT - 190, WIDTH - 80, 150)
        pygame.draw.rect(screen, (15, 18, 35), box, border_radius=12)
        pygame.draw.rect(screen, color, box, 3, border_radius=12)

        tag = font_name.render(speaker, True, color)
        tag_rect = pygame.Rect(box.left + 20, box.top - 18, tag.get_width() + 24, 34)
        pygame.draw.rect(screen, (15, 18, 35), tag_rect, border_radius=8)
        pygame.draw.rect(screen, color, tag_rect, 3, border_radius=8)
        screen.blit(tag, (tag_rect.left + 12, tag_rect.top + 7))

        wrapped = wrap_text(self.current_text(), font_text, box.width - 48)
        remaining = int(self.chars)
        y = box.top + 28
        for line in wrapped:
            shown = line[:remaining]
            if shown != "":
                screen.blit(font_text.render(shown, True, (240, 240, 250)), (box.left + 24, y))
            remaining = max(0, remaining - len(line) - 1)
            y += 32

        if self.line_complete() and (pygame.time.get_ticks() // 500) % 2 == 0:
            last = self.index == len(self.lines) - 1
            hint = "click to start" if last else "click to continue"
            label = font_small.render(hint, True, (170, 180, 210))
            screen.blit(label, (box.right - label.get_width() - 20, box.bottom - 30))


class Button:
    def __init__(self, rect, text, name, enabled=True):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.name = name
        self.enabled = enabled

    def draw(self, screen, font, mouse_pos):
        hover = self.enabled and self.rect.collidepoint(mouse_pos)
        if not self.enabled:
            fill, edge, color = (50, 50, 55), (80, 80, 85), (120, 120, 125)
        elif hover:
            fill, edge, color = (230, 190, 60), (255, 255, 255), (20, 20, 20)
        else:
            fill, edge, color = (40, 50, 80), (200, 200, 220), (255, 255, 255)
        pygame.draw.rect(screen, fill, self.rect, border_radius=10)
        pygame.draw.rect(screen, edge, self.rect, 3, border_radius=10)
        label = font.render(self.text, True, color)
        screen.blit(label, label.get_rect(center=self.rect.center))


def damage_price(level):
    return 40 + 30 * level


# ------------------------------------------------------------------
# GAME
# ------------------------------------------------------------------
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Adventure Game")
        self.clock = pygame.time.Clock()
        self.font_big = pygame.font.SysFont(None, 80)
        self.font_mid = pygame.font.SysFont(None, 40)
        self.font_small = pygame.font.SysFont(None, 28)
        self.font_text = pygame.font.SysFont(None, 34)
        self.dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.dim.fill((0, 0, 0, 90))
        self.dialogue = None

        self.progress = load_save()
        self.player = Player(self.progress)
        self.level = None
        self.running = True
        self.state = "menu"
        self.shop_from = "menu"
        self.buttons = []
        self.last_reward = 0
        self.set_state("menu")

    # ---------- states and buttons ----------
    def set_state(self, name):
        self.state = name
        self.buttons = self.build_buttons()

    def build_buttons(self):
        s = self.state
        p = self.progress
        buttons = []
        if s == "menu":
            buttons = [Button((380, 230, 200, 56), "PLAY", "play"),
                       Button((380, 300, 200, 56), "SHOP", "shop"),
                       Button((380, 370, 200, 56), "QUIT", "quit")]
        elif s == "levels":
            for i in range(NUM_LEVELS):
                n = i + 1
                start_x = (WIDTH - (min(NUM_LEVELS, 5) * 150 - 30)) // 2
                rect = (start_x + (i % 5) * 150, 150 + (i // 5) * 125, 120, 100)
                buttons.append(Button(rect, str(n), "level_" + str(n), n <= p["unlocked"]))
            buttons.append(Button((250, 430, 200, 56), "SHOP", "shop"))
            buttons.append(Button((510, 430, 200, 56), "BACK", "menu"))
        elif s == "shop":
            lvl = p["damage_level"]
            maxed = lvl >= MAX_DAMAGE_LEVEL
            dmg_text = "Damage booster: MAXED" if maxed else \
                "Damage +" + str(DAMAGE_PER_LEVEL) + "  (" + str(damage_price(lvl)) + " coins)"
            buttons.append(Button((230, 190, 500, 64), dmg_text, "buy_damage", not maxed))
            heal_text = "Heal potion  (" + str(HEAL_PRICE) + " coins)"
            buttons.append(Button((230, 275, 500, 64), heal_text, "buy_heal", p["heals"] < MAX_HEALS))
            buttons.append(Button((380, 400, 200, 56), "BACK", "back_shop"))
        elif s == "complete":
            if self.level.number < NUM_LEVELS:
                buttons.append(Button((380, 300, 200, 56), "NEXT LEVEL", "next"))
            buttons.append(Button((380, 370, 200, 56), "LEVELS", "levels"))
        elif s == "gameover":
            buttons = [Button((380, 300, 200, 56), "RETRY", "retry"),
                       Button((380, 370, 200, 56), "LEVELS", "levels")]
        elif s == "victory":
            buttons = [Button((380, 360, 200, 56), "MENU", "menu")]
        return buttons

    def start_level(self, number):
        self.player.reset()
        get_papyrus_art()          # load enemy sprites now so there is no pause mid-fight
        get_boss_art(number)
        get_rat_art()
        self.level = make_level(number, self.player, self.progress)
        self.dialogue = None
        if number in LEVEL_INTRO:
            self.dialogue = Dialogue(LEVEL_INTRO[number], "intro")
        self.set_state("playing")

    def advance_dialogue(self):
        self.dialogue.click()
        if self.dialogue.finished:
            kind = self.dialogue.kind
            self.dialogue = None
            if kind == "boss":
                self.level.start_boss_fight()
            elif kind == "phase":
                self.level.phase_dialogue_done()

    def press(self, name):
        p = self.progress
        if name == "play" or name == "levels":
            self.set_state("levels")
        elif name == "menu":
            self.set_state("menu")
        elif name == "shop":
            self.shop_from = self.state
            self.set_state("shop")
        elif name == "back_shop":
            self.set_state(self.shop_from)
        elif name == "quit":
            self.running = False
        elif name.startswith("level_"):
            self.start_level(int(name[6:]))
        elif name == "next":
            self.start_level(self.level.number + 1)
        elif name == "retry":
            self.start_level(self.level.number)
        elif name == "buy_damage":
            lvl = p["damage_level"]
            price = damage_price(lvl)
            if lvl < MAX_DAMAGE_LEVEL and p["coins"] >= price:
                p["coins"] -= price
                p["damage_level"] += 1
                write_save(p)
            self.set_state("shop")
        elif name == "buy_heal":
            if p["heals"] < MAX_HEALS and p["coins"] >= HEAL_PRICE:
                p["coins"] -= HEAL_PRICE
                p["heals"] += 1
                write_save(p)
            self.set_state("shop")

    # ---------- main loop ----------
    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(dt)
            self.draw()
            pygame.display.flip()
        write_save(self.progress)
        pygame.quit()

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        if self.state == "playing":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                write_save(self.progress)
                self.dialogue = None
                self.set_state("levels")
            elif self.dialogue is not None:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.advance_dialogue()
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                    self.player.jump()
                if event.key == pygame.K_r:
                    self.player.reload()
                if event.key == HEAL_KEY:
                    self.player.use_heal()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            clicked = ""
            for b in self.buttons:
                if b.enabled and b.rect.collidepoint(event.pos):
                    clicked = b.name
            if clicked != "":
                self.press(clicked)

    def update(self, dt):
        if self.state != "playing":
            return
        if self.dialogue is not None:
            self.dialogue.update(dt)
            for e in self.level.enemies:
                e.anim_time += dt
            return
        keys = pygame.key.get_pressed()
        direction = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            direction -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            direction += 1
        if keys[pygame.K_f] or pygame.mouse.get_pressed()[0]:
            self.player.shoot()

        self.player.update(dt, direction, self.level.platforms)
        result = self.level.update(dt)

        if self.level.talk_pending:
            self.level.talk_pending = False
            if self.level.number in LEVEL_BOSS_TALK:
                self.dialogue = Dialogue(LEVEL_BOSS_TALK[self.level.number], "boss")
            else:
                self.level.start_boss_fight()

        if self.level.pending_dialogue is not None:
            self.dialogue = Dialogue(self.level.pending_dialogue, "phase")
            self.level.pending_dialogue = None

        if result == "won":
            n = self.level.number
            if n in self.progress["beaten"]:
                self.last_reward = 0                           # coins are only paid the first time
            else:
                self.last_reward = 20 * n + self.level.earned  # level bonus + coins from this run
                self.progress["beaten"].append(n)
            self.progress["coins"] += self.last_reward
            self.progress["unlocked"] = max(self.progress["unlocked"], min(n + 1, NUM_LEVELS))
            write_save(self.progress)
            self.set_state("victory" if n == FINAL_LEVEL else "complete")
        elif result == "lost":
            write_save(self.progress)
            self.set_state("gameover")

    # ---------- drawing ----------
    def text(self, msg, font, color, center):
        surf = font.render(msg, True, color)
        self.screen.blit(surf, surf.get_rect(center=center))

    def draw_buttons(self):
        mouse = pygame.mouse.get_pos()
        for b in self.buttons:
            b.draw(self.screen, self.font_mid, mouse)

    def draw(self):
        s = self.state
        if s == "playing":
            self.draw_play()
        else:
            self.screen.fill((20, 24, 40))
            self.draw_menu_screens()
            self.draw_buttons()

    def draw_menu_screens(self):
        s = self.state
        p = self.progress
        gold = (255, 215, 0)
        white = (235, 235, 245)
        if s == "menu":
            self.text("ADVENTURE GAME", self.font_big, gold, (WIDTH // 2, 120))
            self.text("Coins: " + str(p["coins"]), self.font_small, white, (WIDTH // 2, 180))
            self.text("Move: A/D   Jump: Space   Shoot: F or click   Reload: R   Heal: H",
                      self.font_small, (150, 160, 190), (WIDTH // 2, 480))
        elif s == "levels":
            self.text("SELECT LEVEL", self.font_big, gold, (WIDTH // 2, 70))
            self.text("Coins: " + str(p["coins"]) + "    Heals: " + str(p["heals"]),
                      self.font_small, white, (WIDTH // 2, 115))
        elif s == "shop":
            self.text("SHOP", self.font_big, gold, (WIDTH // 2, 70))
            self.text("Coins: " + str(p["coins"]), self.font_mid, white, (WIDTH // 2, 125))
            self.text("Damage per shot: " + str(BASE_DAMAGE + DAMAGE_PER_LEVEL * p["damage_level"]),
                      self.font_small, white, (WIDTH // 2, 160))
            self.text("Heals owned: " + str(p["heals"]) + "   (press H in a level to use one)",
                      self.font_small, white, (WIDTH // 2, 355))
        elif s == "complete":
            self.text("LEVEL " + str(self.level.number) + " COMPLETE!", self.font_big, gold, (WIDTH // 2, 150))
            if self.last_reward == 0:
                msg = "Already beaten before: no coins   (total " + str(p["coins"]) + ")"
            else:
                msg = "+" + str(self.last_reward) + " coins earned   (total " + str(p["coins"]) + ")"
            self.text(msg, self.font_mid, white, (WIDTH // 2, 220))
        elif s == "gameover":
            self.text("YOU DIED", self.font_big, (230, 70, 70), (WIDTH // 2, 170))
        elif s == "victory":
            self.text("YOU BEAT THE GAME!", self.font_big, gold, (WIDTH // 2, 160))
            self.text("The Big Boss is down.", self.font_mid, white, (WIDTH // 2, 240))

    def draw_play(self):
        lv = self.level
        lv.draw_background(self.screen)
        lv.draw(self.screen)
        self.player.draw(self.screen, lv.scroll)
        lv.draw_foreground(self.screen)
        self.draw_hud()
        if self.dialogue is not None:
            self.screen.blit(self.dim, (0, 0))
            self.dialogue.draw(self.screen, self.font_text, self.font_mid, self.font_small)

    def draw_hud(self):
        p = self.player
        lv = self.level
        white = (255, 255, 255)
        pygame.draw.rect(self.screen, (80, 0, 0), (16, 16, 220, 20))
        pygame.draw.rect(self.screen, (0, 200, 60), (16, 16, 220 * max(0, p.hp) / MAX_HP, 20))
        pygame.draw.rect(self.screen, white, (16, 16, 220, 20), 2)
        self.text("HP " + str(int(max(0, p.hp))) + "/" + str(MAX_HP), self.font_small, white, (126, 26))

        icon = p.pistol.right[PISTOL_ICON]
        small = pygame.transform.scale(icon, (icon.get_width() // 3, icon.get_height() // 3))
        self.screen.blit(small, (16, 44))
        if p.pistol.ammo > 0 and p.pistol.sequence is not RELOAD_SEQUENCE:
            ammo_text = str(p.pistol.ammo) + "/" + str(MAG_SIZE)
        else:
            ammo_text = "RELOADING"
        self.text(ammo_text, self.font_small, white, (16 + small.get_width() + 55, 62))

        self.text("[H] Heals: " + str(self.progress["heals"]), self.font_small, white, (80, 100))
        if lv.replay:
            coin_text = "Coins: " + str(self.progress["coins"]) + "  (already beaten: no coins)"
        else:
            coin_text = "Coins: " + str(self.progress["coins"]) + "  (+" + str(lv.earned) + ")"
        self.text(coin_text, self.font_small, (255, 215, 0), (170, 125))

        self.text("LEVEL " + str(lv.number), self.font_mid, white, (WIDTH // 2, 24))
        status = lv.status_text()
        if status is not None:
            self.text(status, self.font_small, white, (WIDTH // 2, 52))
        elif not lv.boss_spawned:
            left = lv.total - lv.killed
            self.text("Enemies left: " + str(left), self.font_small, white, (WIDTH // 2, 52))
        elif lv.boss is not None and lv.boss.hp > 0:
            bw = 400
            bx = WIDTH // 2 - bw // 2
            pygame.draw.rect(self.screen, (60, 0, 0), (bx, 48, bw, 16))
            pygame.draw.rect(self.screen, (220, 40, 40), (bx, 48, bw * lv.boss.hp / lv.boss.max_hp, 16))
            pygame.draw.rect(self.screen, white, (bx, 48, bw, 16), 2)
            self.text(lv.boss_name, self.font_small, white, (WIDTH // 2, 80))
        if lv.breaking:
            self.text("THE PLATFORMS ARE BREAKING!", self.font_mid, (255, 120, 80), (WIDTH // 2, 120))
        banner = lv.banner_text()
        if banner is not None:
            self.text(banner, self.font_mid, (255, 120, 80), (WIDTH // 2, 120))


if __name__ == "__main__":
    Game().run()