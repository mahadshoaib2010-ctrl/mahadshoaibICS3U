import json
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
NUM_LEVELS = 1       # levels that exist right now: raise this as you add levels
FINAL_LEVEL = 10     # the level that gets the final boss

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
MAX_HEALS = 9

BASE_DAMAGE = 10
DAMAGE_PER_LEVEL = 6
MAX_DAMAGE_LEVEL = 10

# Platforms for each level: (left, top, width, height). Levels not listed have none.
PLATFORM_HEIGHT = 14
LEVEL_PLATFORMS = {
    1: [
        (80, GROUND_Y - 110, 200, PLATFORM_HEIGHT),     # low left
        (680, GROUND_Y - 110, 200, PLATFORM_HEIGHT),    # low right
        (370, GROUND_Y - 210, 220, PLATFORM_HEIGHT),    # high middle
    ],
}
PLATFORM_BREAK_DELAY = 1.5     # seconds between the boss arriving and the platforms breaking

# Boss hazards
WAVE_SPEED = 320
WAVE_DAMAGE = 15
ROCK_DAMAGE = 20
ROCK_SPEED = 700
ROCK_WARNING = 0.9
BOSS_ATTACKS = ["shoot", "wave", "rocks"]
BOSS_ATTACK_LISTS = {1: ["wave", "rain"]}      # Rusty: shockwave, then falling nuts and bolts

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
BOSS_SPRITES = {1: "rusty"}          # level number -> sheet name prefix
BOSS_SCALE = 0.72                    # size of boss sprites (1.0 = original sheet size)
BOSS_FEET_PAD = 12                   # empty pixels under the feet in each sheet cell
BOSS_SIZE_SPRITE = (110, 190)        # boss hitbox size (width, height)
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
ATTACK_SEQUENCES = {"attack": ATTACK_SEQUENCE, "wave": WAVE_SEQUENCE, "rain": RAIN_SEQUENCE}

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

# Typed dialogue. Each line is (speaker, text). Click the mouse to continue.
TYPE_SPEED = 40          # characters per second (lower = slower typing)
LEVEL_INTRO = {
    1: [
        ("MISSION", "A gang of grunts has taken over the alley. All you need is your golden pistol."),
        ("MISSION", "Jump onto the platforms to get the high ground. Careful, the grunts can climb them too."),
        ("MISSION", "Take out every grunt. Once they are gone, their boss will come for you."),
    ],
}
LEVEL_BOSS_TALK = {
    1: [
        ("RUSTY", "So you're the one who has been scrapping my crew."),
        ("RUSTY", "This alley is MINE. Nobody walks out of here with a golden gun."),
        ("RUSTY", "Let's see how well you dance without those platforms!"),
    ],
}

BOSS_NAMES = [
    "Rusty", "Crate Captain", "Sly Sam", "Iron Hat", "Shadow Suit",
    "Madam Mayhem", "Big Bolt", "Night Owl", "The Collector", "THE BIG BOSS",
]


# ------------------------------------------------------------------
# SAVE / LOAD
# ------------------------------------------------------------------
def load_save():
    data = {"unlocked": 1, "coins": 0, "damage_level": 0, "heals": 2}
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
        if key == "bone":
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


def get_boss_art(level_no):
    """(right, left) art for this level's boss, or None if it has no sprite sheets."""
    if level_no not in BOSS_SPRITES:
        return None
    prefix = BOSS_SPRITES[level_no]
    if prefix not in BOSS_ART:
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

    def draw(self, screen):
        blink_off = self.invuln > 0 and int(self.invuln * 12) % 2 == 0
        if not blink_off:
            image = self.current_image()
            screen.blit(image, image.get_rect(midbottom=(self.x, self.y)))
            self.pistol.draw(screen, self.hand_pos(), self.facing)
        for b in self.bullets:
            pygame.draw.rect(screen, (255, 215, 0), (b["x"] - 6, b["y"] - 2, 12, 5))


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
        self.sprite_boss = boss_art is not None
        if papyrus is not None:
            self.art_right, self.art_left = papyrus
            self.size = (56, GRUNT_HEIGHT)
        elif boss_art is not None:
            self.art_right, self.art_left = boss_art
            self.size = BOSS_SIZE_SPRITE
        else:
            paint = color if color is not None else cfg["color"]
            if kind == "boss":
                names = ["boss_" + str(level_no), "enemy_boss"]
            else:
                names = ["enemy_" + kind]
            self.art_right, self.art_left = get_enemy_art(names, self.size, paint)
        self.can_bow = GRUNTS_SHOOT and kind == "grunt" and "attack" in self.art_right

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
            if self.attack_name == "wave" and position >= WAVE_RELEASE and not self.attack_fired:
                self.attack_fired = True
                self.boss_attack("wave", player_x, bullets, hazards)
            if self.attack_time >= sum(d for _, d in sequence):
                self.attack_time = None
                self.attack_name = ""
                self.shot_timer = self.cfg["delay"] * (0.6 if self.phase_two() else 1.0)

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
                color = lerp_color((200, 80, 30), (150, 0, 30), (self.number - 1) / 9)
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
                self.progress["coins"] += e.coins
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
            else:
                x = int(h["x"])
                if h["timer"] > 0:
                    grow = 1.0 - h["timer"] / ROCK_WARNING
                    w = int(20 + 40 * grow)
                    pygame.draw.ellipse(screen, (230, 50, 50), (x - w // 2, GROUND_Y - 6, w, 12), 3)
                else:
                    y = int(h["y"])
                    if x % 2 == 0:
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
        self.level = Level(number, self.player, self.progress)
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

        if result == "won":
            n = self.level.number
            self.last_reward = 20 * n
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
            self.text("+" + str(self.last_reward) + " bonus coins   (total " + str(p["coins"]) + ")",
                      self.font_mid, white, (WIDTH // 2, 220))
        elif s == "gameover":
            self.text("YOU DIED", self.font_big, (230, 70, 70), (WIDTH // 2, 170))
        elif s == "victory":
            self.text("YOU BEAT THE GAME!", self.font_big, gold, (WIDTH // 2, 160))
            self.text("The Big Boss is down.", self.font_mid, white, (WIDTH // 2, 240))

    def draw_play(self):
        lv = self.level
        t = (lv.number - 1) / (FINAL_LEVEL - 1)
        self.screen.fill(lerp_color((92, 150, 200), (90, 40, 55), t))
        ground = lerp_color((60, 120, 60), (50, 40, 40), t)
        pygame.draw.rect(self.screen, ground, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))

        lv.draw(self.screen)
        self.player.draw(self.screen)
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
        self.text("Coins: " + str(self.progress["coins"]), self.font_small, (255, 215, 0), (70, 125))

        self.text("LEVEL " + str(lv.number), self.font_mid, white, (WIDTH // 2, 24))
        if not lv.boss_spawned:
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


Game().run()