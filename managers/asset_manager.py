"""game/assets.py
Image and pixel-art asset loading.

Call `load_game_images()` once AFTER pygame.display.set_mode() so that
convert_alpha() works correctly.  All other surfaces (alien grids, power-up
icons) are built at import time from pure pygame drawing and do not require a
display to be active.
"""
import os
import pygame

from constants import (
    PLAYER_W, PLAYER_H, ENEMY_W, ENEMY_H, BULLET_W, BULLET_H, CELL,
    CYAN, GREEN, PURPLE,
    WHITE,
    clamp_color,
)

# ── Asset directory ───────────────────────────────────────────────────────────
_ASSET_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'images')

# ── Runtime image handles (populated by load_game_images) ─────────────────────
_IMG_PLAYER_SHIP   = None
_IMG_BOSS_CAPYBARA = None
_IMG_BOSS_ANIMAL   = None
_IMG_ENEMY_SHIP    = None   # regular enemy sprite
_IMG_ENEMY_BULLET  = None   # enemy projectile sprite
_IMG_PLAYER_BULLET = None   # player projectile sprite (mblutter)


# ── Low-level image loader ────────────────────────────────────────────────────
def _crop_to_content(surf, bg=(255, 255, 255), tolerance=30):
    """Return a sub-surface cropped to the bounding box of non-background pixels.
    Pixels within *tolerance* distance of *bg* are considered background."""
    w, h = surf.get_size()
    br, bg_g, bg_b = bg
    min_x, min_y, max_x, max_y = w, h, 0, 0
    try:
        import numpy as np
        arr = pygame.surfarray.array3d(surf)          # shape (w, h, 3)
        dist = ((arr[:,:,0].astype(np.int32) - br)**2 +
                (arr[:,:,1].astype(np.int32) - bg_g)**2 +
                (arr[:,:,2].astype(np.int32) - bg_b)**2)
        mask = dist > tolerance**2 * 3               # True where NOT background
        cols = np.any(mask, axis=1)                  # per-column flag
        rows = np.any(mask, axis=0)                  # per-row flag
        if not cols.any():
            return surf
        min_x = int(np.argmax(cols))
        max_x = int(w - 1 - np.argmax(cols[::-1]))
        min_y = int(np.argmax(rows))
        max_y = int(h - 1 - np.argmax(rows[::-1]))
    except ImportError:
        thr_sq = tolerance**2 * 3
        for x in range(w):
            for y in range(h):
                r, g, b, _ = surf.get_at((x, y))
                if (r-br)**2+(g-bg_g)**2+(b-bg_b)**2 > thr_sq:
                    min_x = min(min_x, x); max_x = max(max_x, x)
                    min_y = min(min_y, y); max_y = max(max_y, y)
    if max_x <= min_x or max_y <= min_y:
        return surf
    return surf.subsurface(pygame.Rect(min_x, min_y,
                                       max_x - min_x + 1,
                                       max_y - min_y + 1))


def _load_img(fname, size, colorkey=None, threshold=30, crop_bg=None):
    """Load, optionally auto-crop, and scale an image.

    *crop_bg* – if given (an RGB tuple), the image is first cropped to the
    bounding box of pixels that differ from that colour before scaling.
    *colorkey* – pixels close to this colour are made fully transparent after
    scaling, handling anti-aliased edges.
    """
    path = os.path.join(_ASSET_DIR, fname)
    try:
        raw = pygame.image.load(path).convert_alpha()
        if crop_bg is not None:
            raw = _crop_to_content(raw, bg=crop_bg, tolerance=threshold)
        img = pygame.transform.smoothscale(raw, size)
        if colorkey is not None:
            kr, kg, kb = colorkey
            try:
                import numpy as np
                arr   = pygame.surfarray.pixels3d(img)
                alpha = pygame.surfarray.pixels_alpha(img)
                dist  = (arr[:, :, 0].astype(np.int32) - kr) ** 2 + \
                        (arr[:, :, 1].astype(np.int32) - kg) ** 2 + \
                        (arr[:, :, 2].astype(np.int32) - kb) ** 2
                alpha[dist < threshold ** 2 * 3] = 0
                del arr, alpha
            except ImportError:
                # Pure-pygame fallback (small sprites, so speed is acceptable)
                w, h   = img.get_size()
                thr_sq = threshold ** 2 * 3
                for x in range(w):
                    for y in range(h):
                        r, g, b, a = img.get_at((x, y))
                        if a == 0:
                            continue
                        dist = (r - kr) ** 2 + (g - kg) ** 2 + (b - kb) ** 2
                        if dist < thr_sq:
                            img.set_at((x, y), (r, g, b, 0))
        return img
    except Exception as e:
        print(f"[WARN] Could not load {fname}: {e}")
        return None


def load_game_images():
    """Populate the ship / boss image globals.
    Must be called AFTER pygame.display.set_mode()."""
    global _IMG_PLAYER_SHIP, _IMG_BOSS_CAPYBARA, _IMG_BOSS_ANIMAL
    global _IMG_ENEMY_SHIP, _IMG_ENEMY_BULLET, _IMG_PLAYER_BULLET
    # Boss / player ship – these have known colourkeys, no crop needed
    _IMG_PLAYER_SHIP   = _load_img('player_ship.png',   (PLAYER_W + 20, PLAYER_H + 20), colorkey=(0, 0, 0))
    _IMG_BOSS_CAPYBARA = _load_img('capybara_boss.png', (160, 130),                      colorkey=(255, 0, 255))
    _IMG_BOSS_ANIMAL   = _load_img('animal_boss.png',   (160, 130),                      colorkey=(255, 0, 255))
    # New sprites – white canvas, auto-crop then remove white fringe
    _IMG_ENEMY_SHIP    = _load_img('enemy ship.png',    (48, 38),          colorkey=(255, 255, 255), crop_bg=(255, 255, 255))
    _IMG_ENEMY_BULLET  = _load_img('enemy bullet.png',  (10,           24),               colorkey=(255, 255, 255), crop_bg=(255, 255, 255))
    _IMG_PLAYER_BULLET = _load_img('mblutter.png',      (BULLET_W + 6, BULLET_H + 14),   colorkey=(255, 255, 255), crop_bg=(255, 255, 255))
    if _IMG_PLAYER_SHIP:   print("[OK] player_ship.png loaded")
    if _IMG_BOSS_CAPYBARA: print("[OK] capybara_boss.png loaded")
    if _IMG_BOSS_ANIMAL:   print("[OK] animal_boss.png loaded")
    if _IMG_ENEMY_SHIP:    print("[OK] enemy ship.png loaded")
    if _IMG_ENEMY_BULLET:  print("[OK] enemy bullet.png loaded")
    if _IMG_PLAYER_BULLET: print("[OK] mblutter.png loaded")


# ── Public accessors ──────────────────────────────────────────────────────────
def get_player_ship():
    return _IMG_PLAYER_SHIP


def get_enemy_ship():
    return _IMG_ENEMY_SHIP


def get_enemy_bullet_img():
    return _IMG_ENEMY_BULLET


def get_player_bullet_img():
    return _IMG_PLAYER_BULLET


def get_boss_img(level):
    """Return the correct boss image based on level parity."""
    return _IMG_BOSS_CAPYBARA if (level % 2 == 1) else _IMG_BOSS_ANIMAL


# ── Classic pixel-art alien grids ─────────────────────────────────────────────
_GRIDS = [
    # Crab (bottom rows) – cyan
    ["  X     X  ", "   X   X   ", "  XXXXXXX  ",
     " XX XXX XX ", "XXXXXXXXXXX", "X XXXXXXX X",
     "X X     X X", "   XX XX   "],
    # Squid (middle rows) – green
    ["    XXX    ", "  XXXXXXX  ", " XXXXXXXXX ",
     "XXX XXX XXX", "XXXXXXXXXXX", "  XX   XX  ",
     " X  X X  X ", "X         X"],
    # UFO (top rows) – purple
    ["   XXXXX   ", " XXXXXXXXX ", "XXXXXXXXXXX",
     "XX X X X XX", "XXXXXXXXXXX", "  XX   XX  ",
     " X       X ", "           "],
]

_ALIEN_PALETTES = [
    (CYAN,   clamp_color(0,  150, 150)),
    (GREEN,  clamp_color(0,  155,   0)),
    (PURPLE, clamp_color(95,   0, 155)),
]


def _make_alien(grid, col, dark):
    cols = max(len(r) for r in grid)
    surf = pygame.Surface((cols * CELL, len(grid) * CELL), pygame.SRCALPHA)
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch == 'X':
                c2 = col if (r + c) % 2 == 0 else dark
                pygame.draw.rect(surf, c2, (c * CELL, r * CELL, CELL, CELL))
    return surf


# Built at import time (no display needed for SRCALPHA surfaces)
ALIEN_SURFS = [_make_alien(g, col, dark) for g, (col, dark) in zip(_GRIDS, _ALIEN_PALETTES)]


def get_alien_surf(index):
    return ALIEN_SURFS[index % 3]


# ── PowerUp pixel-art icons ───────────────────────────────────────────────────
def _make_icon(grid, color):
    rows    = len(grid)
    cols    = max(len(r) for r in grid)
    cell_sz = 2
    surf    = pygame.Surface((cols * cell_sz, rows * cell_sz), pygame.SRCALPHA)
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch == 'X':
                pygame.draw.rect(surf, color, (c * cell_sz, r * cell_sz, cell_sz, cell_sz))
    return surf


_ICON_SHIELD = _make_icon([
    "  XXXX  ",
    " XXXXXX ",
    "XX    XX",
    "XX    XX",
    "XX    XX",
    " XX  XX ",
    "  XXXX  ",
    "   XX   "
], WHITE)

_ICON_MULTI = _make_icon([
    "  X X X  ",
    "  X X X  ",
    "  X X X  ",
    "  X X X  ",
    "  X X X  ",
    "  X X X  ",
    "   X X   ",
    "    X    "
], WHITE)

_ICON_HEART = _make_icon([
    " XX  XX ",
    "XXXXXXXX",
    "XXXXXXXX",
    "XXXXXXXX",
    " XXXXXX ",
    "  XXXX  ",
    "   XX   ",
    "        "
], WHITE)

POWERUP_ICONS = {
    'shield':    _ICON_SHIELD,
    'multishot': _ICON_MULTI,
    'heart':     _ICON_HEART,
}


def get_powerup_icon(kind):
    return POWERUP_ICONS[kind]
