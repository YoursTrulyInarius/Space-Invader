"""game/powerup.py
Power-up object state and rendering.
"""
import pygame
import constants
from constants import CYAN, RED, PURPLE, WHITE, clamp_color
from managers.asset_manager import get_powerup_icon


class PowerUp:
    _COLORS = {'shield': CYAN, 'multishot': PURPLE, 'heart': RED}

    def __init__(self, x, y, kind):
        self.x     = x
        self.y     = float(y)
        self.kind  = kind
        self.speed = 1.4
        self.anim  = 0

    def update(self):
        self.y   += self.speed
        self.anim = (self.anim + 1) % 60

    def draw(self, screen):
        col  = self._COLORS[self.kind]
        s    = constants.POWERUP_SIZE
        rect = pygame.Rect(int(self.x), int(self.y), s, s)
        gs   = pygame.Surface((s + 8, s + 8), pygame.SRCALPHA)
        pygame.draw.rect(gs, (*col, 55), gs.get_rect(), border_radius=6)
        screen.blit(gs, (rect.x - 4, rect.y - 4))
        pygame.draw.rect(screen, clamp_color(col[0] // 4, col[1] // 4, col[2] // 4),
                         rect, border_radius=5)
        pygame.draw.rect(screen, col, rect, 2, border_radius=5)
        icon_surf = get_powerup_icon(self.kind)
        screen.blit(icon_surf, (rect.centerx - icon_surf.get_width() // 2,
                                 rect.centery - icon_surf.get_height() // 2))
