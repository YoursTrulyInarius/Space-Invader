"""game/constants.py
All colours, sprite-size constants, and pure-drawing helper functions.
Nothing here imports from other game sub-modules, so any module can safely
import from here without risking circular imports.
"""
import pygame
from datetime import datetime
import config

# ── Screen dimensions (read once from config) ─────────────────────────────────
SCREEN_WIDTH  = config.GAME_CONFIG['screen_width']
SCREEN_HEIGHT = config.GAME_CONFIG['screen_height']

# ── Sprite sizes ──────────────────────────────────────────────────────────────
PLAYER_W, PLAYER_H = 64, 52
ENEMY_W,  ENEMY_H  = 36, 28
BULLET_W, BULLET_H = 4,  14
POWERUP_SIZE        = 24

# Pixel-art cell size (used for alien grid rendering)
CELL = 3

# ── Colour palette ────────────────────────────────────────────────────────────
BLACK      = (  0,   0,   0)
WHITE      = (255, 255, 255)
GREEN      = ( 80, 255,  80)
LIME       = ( 50, 220,  50)
DARK_GREEN = (  0,  80,   0)
RED        = (220,  40,  40)
YELLOW     = (255, 220,  40)
CYAN       = ( 40, 230, 230)
PURPLE     = (180,  60, 230)
ORANGE     = (255, 140,  30)
GRAY       = ( 80,  80,  80)
LIGHT_GRAY = (180, 180, 180)
DARK_GRAY  = ( 28,  28,  40)
NAVY       = (  6,   6,  20)

# ── Pure helper functions ─────────────────────────────────────────────────────

def clamp_color(r, g, b):
    """Clamp each RGB component to [0, 255]."""
    return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))


def draw_text_center(surface, text, font, color, y, shadow=True):
    """Render *text* horizontally centred on *surface* at vertical position *y*."""
    if shadow:
        sh = font.render(text, True, BLACK)
        surface.blit(sh, (SCREEN_WIDTH // 2 - sh.get_width() // 2 + 2, y + 2))
    surf = font.render(text, True, color)
    surface.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2, y))


def draw_glow_rect(surface, color, rect, radius=8, layers=3):
    """Draw a glowing rounded rectangle on *surface*."""
    for i in range(layers, 0, -1):
        gs = pygame.Surface((rect.width + i * 4, rect.height + i * 4), pygame.SRCALPHA)
        a  = max(0, 55 - i * 16)
        pygame.draw.rect(gs, (*color, a), gs.get_rect(), border_radius=radius + i)
        surface.blit(gs, (rect.x - i * 2, rect.y - i * 2))
    pygame.draw.rect(surface, color, rect, border_radius=radius)


def format_display_date(raw):
    """Turn a DB timestamp like '2026-07-01 16:10' into 'July 1, 2026'.
    Falls back to the raw string if it cannot be parsed."""
    if not raw:
        return ""
    s = str(raw).strip()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt_obj = datetime.strptime(s, fmt)
            return f"{dt_obj.strftime('%B')} {dt_obj.day}, {dt_obj.year}"
        except ValueError:
            continue
    return s
