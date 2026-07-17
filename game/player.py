"""game/player.py
Player ship state, movement, shooting, and rendering.
"""
import pygame
import config
import game.constants as constants
from game.constants import (
    PLAYER_W, PLAYER_H, GREEN, LIME, DARK_GREEN,
    CYAN, WHITE, ORANGE, YELLOW, LIGHT_GRAY,
    BULLET_W, BULLET_H,
)
from game.assets import get_player_ship
from game.bullet import Bullet


class Player:
    W, H = PLAYER_W, PLAYER_H

    def __init__(self):
        self.x          = constants.SCREEN_WIDTH // 2 - self.W // 2
        self.y          = constants.SCREEN_HEIGHT - 72
        self.speed      = config.GAME_CONFIG['player_speed']
        self.lives      = config.GAME_CONFIG['max_lives']
        self.max_lives  = config.GAME_CONFIG['max_lives']
        self.cooldown   = 0
        self.cd_max     = 12
        self.shield     = False
        self.sh_timer   = 0
        self.sh_dur     = config.GAME_CONFIG['shield_duration']
        self.multi      = False
        self.mu_timer   = 0
        self.mu_dur     = config.GAME_CONFIG['multi_shot_duration']
        self.invincible = False
        self.inv_timer  = 0
        self.anim       = 0

    def move(self, dx):
        self.x = max(0, min(constants.SCREEN_WIDTH - self.W, self.x + dx * self.speed))

    def shoot(self):
        if self.cooldown > 0:
            return []
        self.cooldown = self.cd_max
        cx = self.x + self.W // 2
        if self.multi:
            return [
                Bullet(cx - BULLET_W // 2,      self.y - 4),
                Bullet(cx - BULLET_W // 2 - 18, self.y + 4),
                Bullet(cx - BULLET_W // 2 + 18, self.y + 4),
            ]
        return [Bullet(cx - BULLET_W // 2, self.y - 4)]

    def update(self):
        self.anim = (self.anim + 1) % 20
        if self.cooldown  > 0:
            self.cooldown  -= 1
        if self.sh_timer  > 0:
            self.sh_timer -= 1
            if self.sh_timer == 0:
                self.shield = False
        if self.mu_timer  > 0:
            self.mu_timer -= 1
            if self.mu_timer == 0:
                self.multi  = False
        if self.inv_timer > 0:
            self.inv_timer -= 1
            if self.inv_timer == 0:
                self.invincible = False

    def take_damage(self):
        if self.shield or self.invincible:
            return False
        self.lives     -= 1
        self.invincible = True
        self.inv_timer  = 90
        return True

    def draw(self, screen):
        if self.invincible and self.inv_timer % 8 < 4:
            return
        cx = self.x + self.W // 2

        if self.shield:
            for i in range(3):
                alpha_surf = pygame.Surface((self.W * 2 + i * 14, self.W * 2 + i * 14), pygame.SRCALPHA)
                pygame.draw.ellipse(alpha_surf, (*CYAN, max(0, 80 - i * 25)), alpha_surf.get_rect(), 2)
                screen.blit(alpha_surf, (cx - alpha_surf.get_width() // 2,
                                         self.y + self.H // 2 - alpha_surf.get_height() // 2))

        fh           = 8 + (self.anim % 10) // 2
        flame_colors = [ORANGE, YELLOW, WHITE]
        for fi, fc in enumerate(flame_colors):
            offset = fi * 1
            pygame.draw.polygon(screen, fc, [
                (self.x + 14 + offset, self.y + self.H - 2),
                (self.x + 20 - offset, self.y + self.H + fh - fi * 2),
                (self.x + 26 + offset, self.y + self.H - 2),
            ])
            pygame.draw.polygon(screen, fc, [
                (self.x + self.W - 26 - offset, self.y + self.H - 2),
                (self.x + self.W - 20 + offset, self.y + self.H + fh - fi * 2),
                (self.x + self.W - 14 - offset, self.y + self.H - 2),
            ])

        img = get_player_ship()
        if img:
            screen.blit(img, (self.x - 10, self.y - 10))
        else:
            body = [(cx, self.y), (self.x, self.y + self.H), (self.x + self.W, self.y + self.H)]
            pygame.draw.polygon(screen, GREEN, body)
            pygame.draw.polygon(screen, LIME, body, 2)
            pygame.draw.line(screen, DARK_GREEN,
                             (self.x + 4, self.y + self.H - 4), (cx - 4, self.y + 8), 2)
            pygame.draw.line(screen, DARK_GREEN,
                             (self.x + self.W - 4, self.y + self.H - 4), (cx + 4, self.y + 8), 2)
            pygame.draw.circle(screen, CYAN, (cx, self.y + 14), 7)
            pygame.draw.circle(screen, (10, 130, 200), (cx, self.y + 14), 5)
            pygame.draw.rect(screen, LIGHT_GRAY, (cx - 2, self.y - 8, 4, 10))
