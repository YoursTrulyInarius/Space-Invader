"""game/assets.py
Image and pixel-art asset loading.

Call `load_game_images()` once AFTER pygame.display.set_mode() so that
convert_alpha() works correctly.  All other surfaces (alien grids, power-up
icons) are built at import time from pure pygame drawing and do not require a
display to be active.
"""
import os
import pygame

from game.constants import (
    PLAYER_W, PLAYER_H, CELL,
    CYAN, GREEN, PURPLE,
    WHITE,
    clamp_color,
)

# ── Asset directory ───────────────────────────────────────────────────────────
_ASSET_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')

# ── Runtime image handles (populated by load_game_images) ─────────────────────
_IMG_PLAYER_SHIP   = None
_IMG_BOSS_CAPYBARA = None
_IMG_BOSS_ANIMAL   = None


# ── Low-level image loader ────────────────────────────────────────────────────
def _load_img(fname, size, colorkey=None, threshold=50):
    """Load and scale an image.  If *colorkey* is given, pixels close to that
    colour (within *threshold* distance) are made fully transparent using
    per-pixel alpha so anti-aliased edges are also removed cleanly.

    Uses numpy for vectorised colorkey removal when available, with a working
    pure-pygame fallback so the behaviour never silently differs.
    """
    path = os.path.join(_ASSET_DIR, fname)
    try:
        raw = pygame.image.load(path).convert_alpha()
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
    _IMG_PLAYER_SHIP   = _load_img('player_ship.png',   (PLAYER_W + 20, PLAYER_H + 20), colorkey=(0, 0, 0))
    _IMG_BOSS_CAPYBARA = _load_img('capybara_boss.png', (160, 130),                      colorkey=(255, 0, 255))
    _IMG_BOSS_ANIMAL   = _load_img('animal_boss.png',   (160, 130),                      colorkey=(255, 0, 255))
    if _IMG_PLAYER_SHIP:   print("[OK] player_ship.png loaded")
    if _IMG_BOSS_CAPYBARA: print("[OK] capybara_boss.png loaded")
    if _IMG_BOSS_ANIMAL:   print("[OK] animal_boss.png loaded")


# ── Public accessors ──────────────────────────────────────────────────────────
def get_player_ship():
    return _IMG_PLAYER_SHIP


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
