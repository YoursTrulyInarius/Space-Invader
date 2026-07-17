"""game/bullet.py
Player and enemy projectile classes.
"""
import pygame
import config
import game.constants as constants
from game.constants import BULLET_W, BULLET_H, WHITE, CYAN, YELLOW, clamp_color, draw_glow_rect


class Bullet:
    def __init__(self, x, y):
        self.x     = x
        self.y     = y
        self.speed = config.GAME_CONFIG['bullet_speed']
        self.trail = []

    def update(self):
        self.trail.append((self.x, self.y))
        if len(self.trail) > 5:
            self.trail.pop(0)
        self.y -= self.speed

    def draw(self, screen):
        trail_len = len(self.trail)
        for i, (tx, ty) in enumerate(self.trail):
            if trail_len == 0:
                continue
            w = BULLET_W * (i / float(trail_len))
            c = clamp_color(0, 150 + i * 20, 255)
            pygame.draw.rect(screen, c, (tx + (BULLET_W - w) / 2, ty, w, BULLET_H))

        rect = pygame.Rect(self.x - 2, self.y - 2, BULLET_W + 4, BULLET_H + 4)
        draw_glow_rect(screen, CYAN, rect, radius=6, layers=3)
        pygame.draw.rect(screen, WHITE, (self.x, self.y, BULLET_W, BULLET_H), border_radius=2)


class EnemyBullet:
    def __init__(self, x, y):
        self.x     = x
        self.y     = y
        self.speed = 3
        self.anim  = 0

    def update(self):
        self.y    += self.speed
        self.anim  = (self.anim + 1) % 6

    def draw(self, screen):
        self.anim  = (self.anim + 1) % 10
        r, g, b    = (255, 100, 0) if self.anim >= 5 else (255, 30, 30)

        rect = pygame.Rect(self.x, self.y, 6, 18)
        draw_glow_rect(screen, (r, g, b), rect, radius=6, layers=3)
        pygame.draw.rect(screen, YELLOW, (self.x + 1, self.y + 2, 4, 14), border_radius=3)
        pygame.draw.circle(screen, WHITE, (self.x + 3, self.y + 2), 3)
