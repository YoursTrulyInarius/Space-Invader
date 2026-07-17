"""game/enemy.py
Enemy, boss, and enemy behavior classes.
"""
import random
import math
import pygame
import config
import game.constants as constants
from game.constants import ENEMY_W, ENEMY_H, GREEN, YELLOW, RED, PURPLE, LIGHT_GRAY, DARK_GRAY, LIME, WHITE
from game.assets import get_alien_surf, get_boss_img
from game.bullet import EnemyBullet


class Enemy:
    W, H = ENEMY_W, ENEMY_H

    def __init__(self, x, y, etype=0):
        self.x        = x
        self.y        = y
        self.target_y = y
        self.etype    = etype % 3
        self.dir      = 1
        self.speed    = config.GAME_CONFIG['enemy_speed']
        self.dn_timer = 0
        self.sh_timer = random.randint(60, 160)
        self.sh_cd    = 0
        self.anim     = 0
        self.surf     = get_alien_surf(self.etype)

    def update(self, _enemies):
        if self.y < self.target_y:
            self.y += 2
            return

        self.x       += self.speed * self.dir
        self.dn_timer = max(0, self.dn_timer - 1)
        self.sh_cd    = max(0, self.sh_cd - 1)
        self.anim     = (self.anim + 1) % 30

        if self.x <= 0 or self.x >= constants.SCREEN_WIDTH - self.W:
            self.dir      *= -1
            self.dn_timer  = 14

        if self.dn_timer > 0:
            self.y += 2

    def shoot(self):
        self.sh_timer -= 1
        if self.sh_timer <= 0 and self.sh_cd == 0:
            self.sh_timer = random.randint(60, 160)
            if random.random() < 0.30:
                self.sh_cd = 55
                return EnemyBullet(self.x + self.W // 2, self.y + self.H)
        return None

    def draw(self, screen):
        bob = 0 if self.anim < 15 else 2
        sw, sh = self.surf.get_width(), self.surf.get_height()
        screen.blit(self.surf, (self.x + (self.W - sw) // 2,
                                 self.y + (self.H - sh) // 2 + bob))


class Boss:
    W, H = 140, 90

    def __init__(self, max_hp=30, level=1):
        self.x        = constants.SCREEN_WIDTH // 2 - self.W // 2
        self.y        = -120
        self.target_y = 78
        self.hp       = max_hp
        self.max_hp   = max_hp
        self.speed    = 2.5
        self.dir      = 1
        self.sh_timer = 60
        self.anim     = 0
        self.level    = level
        self.img      = get_boss_img(level)

    def update(self):
        self.anim += 1
        if self.y < self.target_y:
            self.y += 2
            return

        self.x += self.speed * self.dir
        if self.x <= 20 or self.x >= constants.SCREEN_WIDTH - self.W - 20:
            self.dir *= -1

        self.y = self.target_y + math.sin(self.anim * 0.05) * 15

    def shoot(self):
        if self.y < self.target_y:
            return []
        self.sh_timer -= 1
        if self.sh_timer <= 0:
            self.sh_timer = max(25, 60 - (self.max_hp - self.hp))
            cx = self.x + self.W // 2
            return [
                EnemyBullet(cx - 40, self.y + self.H),
                EnemyBullet(cx,      self.y + self.H + 10),
                EnemyBullet(cx + 40, self.y + self.H),
            ]
        return []

    def draw(self, screen):
        cx  = self.x + self.W // 2
        bob = int(math.sin(self.anim * 0.1) * 3)

        if self.img:
            screen.blit(self.img, (self.x, self.y + bob))
            iw, ih = 160, 130
            aura   = pygame.Surface((iw, ih), pygame.SRCALPHA)
            glow_col = (255, 50, 50)  if self.hp < self.max_hp // 3 else \
                       (255, 140, 0)  if self.hp < self.max_hp * 0.6 else \
                       (180, 60, 230)
            radius = 55 + int(math.sin(self.anim * 0.2) * 5)
            center = (iw // 2, ih // 2)
            pygame.draw.circle(aura, (*glow_col, 150), center, radius, 4)
            pygame.draw.circle(aura, (*glow_col, 80),  center, radius - 4, 2)
            screen.blit(aura, (self.x, self.y + bob))
        else:
            pygame.draw.ellipse(screen, (30, 30, 45), (self.x, self.y + bob, self.W, self.H))
            pygame.draw.ellipse(screen, PURPLE,       (self.x, self.y + bob, self.W, self.H), 3)
            pygame.draw.ellipse(screen, CYAN,         (self.x + 10, self.y + bob + 10,
                                                        self.W - 20, self.H - 20), 2)
            core_color = RED if self.hp < self.max_hp // 3 else \
                         (ORANGE if self.hp < self.max_hp * 0.6 else LIME)
            draw_glow_rect(screen, core_color,
                           pygame.Rect(cx - 18, self.y + bob + 18, 36, 36), radius=18, layers=4)
            pygame.draw.circle(screen, WHITE, (cx, self.y + bob + 18), 12)

        if self.y >= self.target_y - 5:
            hb_w     = self.W
            hp_ratio = max(0, self.hp / self.max_hp)
            c        = GREEN if hp_ratio > 0.5 else (YELLOW if hp_ratio > 0.25 else RED)
            pygame.draw.rect(screen, DARK_GRAY, (self.x, self.y - 15 + bob, hb_w, 8), border_radius=4)
            pygame.draw.rect(screen, c,         (self.x, self.y - 15 + bob,
                                                   int(hb_w * hp_ratio), 8), border_radius=4)
            fnt   = pygame.font.SysFont('consolas', 12, bold=True)
            label = fnt.render(f"BOSS  {self.hp}/{self.max_hp}", True, WHITE)
            screen.blit(label, (cx - label.get_width() // 2, self.y - 28 + bob))
