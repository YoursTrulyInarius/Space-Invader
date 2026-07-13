"""game/entities.py
Game-object classes: Player, Enemy, Bullet, EnemyBullet, Boss, PowerUp.
Each class is fully self-contained; dependencies flow only downward into
game.constants and game.assets.
"""
import random
import math
import pygame
import config

import game.constants as constants
from game.constants import (
    PLAYER_W, PLAYER_H,
    ENEMY_W, ENEMY_H,
    BULLET_W, BULLET_H,
    POWERUP_SIZE,
    WHITE, GREEN, LIME, DARK_GREEN,
    RED, YELLOW, CYAN, PURPLE, ORANGE,
    LIGHT_GRAY, DARK_GRAY,
    clamp_color, draw_glow_rect,
)
from game.assets import get_alien_surf, get_player_ship, get_boss_img, get_powerup_icon


# ── Player ────────────────────────────────────────────────────────────────────
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
            return [Bullet(cx - BULLET_W // 2,      self.y - 4),
                    Bullet(cx - BULLET_W // 2 - 18, self.y + 4),
                    Bullet(cx - BULLET_W // 2 + 18, self.y + 4)]
        return [Bullet(cx - BULLET_W // 2, self.y - 4)]

    def update(self):
        self.anim = (self.anim + 1) % 20
        if self.cooldown  > 0: self.cooldown  -= 1
        if self.sh_timer  > 0:
            self.sh_timer -= 1
            if self.sh_timer  == 0: self.shield = False
        if self.mu_timer  > 0:
            self.mu_timer -= 1
            if self.mu_timer  == 0: self.multi  = False
        if self.inv_timer > 0:
            self.inv_timer -= 1
            if self.inv_timer == 0: self.invincible = False

    def take_damage(self):
        """Returns True if damage was applied, False if blocked by shield/invincibility."""
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

        # Shield bubble
        if self.shield:
            for i in range(3):
                alpha_surf = pygame.Surface((self.W * 2 + i * 14, self.W * 2 + i * 14), pygame.SRCALPHA)
                pygame.draw.ellipse(alpha_surf, (*CYAN, max(0, 80 - i * 25)), alpha_surf.get_rect(), 2)
                screen.blit(alpha_surf, (cx - alpha_surf.get_width() // 2,
                                         self.y + self.H // 2 - alpha_surf.get_height() // 2))

        # Engine flame
        fh           = 8 + (self.anim % 10) // 2
        flame_colors = [ORANGE, YELLOW, WHITE]
        for fi, fc in enumerate(flame_colors):
            offset = fi * 1
            pygame.draw.polygon(screen, fc, [
                (self.x + 14 + offset, self.y + self.H - 2),
                (self.x + 20 - offset, self.y + self.H + fh - fi * 2),
                (self.x + 26 + offset, self.y + self.H - 2)])
            pygame.draw.polygon(screen, fc, [
                (self.x + self.W - 26 - offset, self.y + self.H - 2),
                (self.x + self.W - 20 + offset, self.y + self.H + fh - fi * 2),
                (self.x + self.W - 14 - offset, self.y + self.H - 2)])

        # Ship sprite or fallback polygon
        img = get_player_ship()
        if img:
            screen.blit(img, (self.x - 10, self.y - 10))
        else:
            body = [(cx, self.y),
                    (self.x, self.y + self.H),
                    (self.x + self.W, self.y + self.H)]
            pygame.draw.polygon(screen, GREEN, body)
            pygame.draw.polygon(screen, LIME,  body, 2)
            pygame.draw.line(screen, DARK_GREEN,
                             (self.x + 4, self.y + self.H - 4), (cx - 4, self.y + 8), 2)
            pygame.draw.line(screen, DARK_GREEN,
                             (self.x + self.W - 4, self.y + self.H - 4), (cx + 4, self.y + 8), 2)
            pygame.draw.circle(screen, CYAN,           (cx, self.y + 14), 7)
            pygame.draw.circle(screen, (10, 130, 200), (cx, self.y + 14), 5)
            pygame.draw.rect(screen, LIGHT_GRAY, (cx - 2, self.y - 8, 4, 10))


# ── Enemy ─────────────────────────────────────────────────────────────────────
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
        # Balanced firing: 60-160 frames between checks, 30% chance
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


# ── Player Bullet ─────────────────────────────────────────────────────────────
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
        # Fading trail
        trail_len = len(self.trail)
        for i, (tx, ty) in enumerate(self.trail):
            if trail_len == 0:
                continue
            w = BULLET_W * (i / float(trail_len))
            c = clamp_color(0, 150 + i * 20, 255)
            pygame.draw.rect(screen, c, (tx + (BULLET_W - w) / 2, ty, w, BULLET_H))

        # Glowing laser core
        rect = pygame.Rect(self.x - 2, self.y - 2, BULLET_W + 4, BULLET_H + 4)
        draw_glow_rect(screen, CYAN, rect, radius=6, layers=3)
        pygame.draw.rect(screen, WHITE, (self.x, self.y, BULLET_W, BULLET_H), border_radius=2)


# ── Enemy Bullet ──────────────────────────────────────────────────────────────
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


# ── Boss ──────────────────────────────────────────────────────────────────────
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
        cy  = self.y + self.H // 2
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
            # Fallback drawn boss
            pygame.draw.ellipse(screen, (30, 30, 45), (self.x, self.y + bob, self.W, self.H))
            pygame.draw.ellipse(screen, PURPLE,       (self.x, self.y + bob, self.W, self.H), 3)
            pygame.draw.ellipse(screen, CYAN,         (self.x + 10, self.y + bob + 10,
                                                        self.W - 20, self.H - 20), 2)
            core_color = RED if self.hp < self.max_hp // 3 else \
                         (ORANGE if self.hp < self.max_hp * 0.6 else LIME)
            draw_glow_rect(screen, core_color,
                           pygame.Rect(cx - 18, cy - 18 + bob, 36, 36), radius=18, layers=4)
            pygame.draw.circle(screen, WHITE, (cx, cy + bob), 12)

        # Health bar (always visible once boss has entered)
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


# ── PowerUp ───────────────────────────────────────────────────────────────────
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
        s    = POWERUP_SIZE
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
