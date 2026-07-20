"""game/bullet.py
Player and enemy projectile classes.
"""
import pygame
import math
import config
import constants
from constants import BULLET_W, BULLET_H, WHITE, CYAN, YELLOW, ORANGE, RED, clamp_color, draw_glow_rect


# ── Player bullet ─────────────────────────────────────────────────────────────
class Bullet:
    """Cyan energy bolt – sharp metallic tip, glowing layered body, fading plasma trail."""

    BW = 5   # bullet width
    BH = 20  # bullet height

    def __init__(self, x, y):
        self.x     = x
        self.y     = y
        self.speed = config.GAME_CONFIG['bullet_speed']
        self.trail = []

    def update(self):
        self.trail.append((self.x, self.y))
        if len(self.trail) > 10:
            self.trail.pop(0)
        self.y -= self.speed

    def draw(self, screen):
        bw, bh = self.BW, self.BH
        cx = int(self.x + BULLET_W // 2)
        by = int(self.y)

        # ── Plasma trail (fading streaks below bullet) ──
        trail_len = len(self.trail)
        for i, (tx, ty) in enumerate(self.trail):
            frac    = i / max(trail_len, 1)
            alpha   = int(180 * frac)
            tw      = max(1, int(bw * frac * 0.7))
            th      = max(2, int(3 + 8 * frac))
            col     = clamp_color(0, int(120 + 110 * frac), 255)
            ts      = pygame.Surface((tw, th), pygame.SRCALPHA)
            ts.fill((*col, alpha))
            screen.blit(ts, (int(tx) + BULLET_W // 2 - tw // 2, int(ty) + bh))

        # ── Multi-layer outer glow (large soft halo) ──
        for layer in range(6, 0, -1):
            g_pad = layer * 2
            g_w   = bw + g_pad * 2
            g_h   = bh + g_pad * 2
            gs    = pygame.Surface((g_w, g_h), pygame.SRCALPHA)
            a     = max(0, 38 - layer * 6)
            r_val = max(0, 60 - layer * 8)
            pygame.draw.rect(gs, (r_val, 220, 255, a), (0, 0, g_w, g_h), border_radius=g_pad + 4)
            screen.blit(gs, (cx - bw // 2 - g_pad, by - g_pad))

        # ── Body – layered metallic casing ──
        # Outer dark-teal shell
        pygame.draw.rect(screen, (0, 100, 130),
                         (cx - bw // 2, by + 6, bw, bh - 6), border_radius=2)
        # Inner lighter band
        pygame.draw.rect(screen, (20, 170, 200),
                         (cx - bw // 2 + 1, by + 7, bw - 2, bh - 9), border_radius=1)
        # Bright highlight on left edge (3D feel)
        pygame.draw.line(screen, (120, 240, 255),
                         (cx - bw // 2 + 1, by + 7),
                         (cx - bw // 2 + 1, by + bh - 3), 1)

        # ── Bright energy spine (centre) ──
        pygame.draw.rect(screen, (220, 255, 255), (cx, by + 7, 1, bh - 9), border_radius=1)

        # ── Nose tip – pointed triangle ──
        tip_pts = [(cx, by), (cx - bw // 2, by + 7), (cx + bw // 2 + bw % 2, by + 7)]
        pygame.draw.polygon(screen, (180, 248, 255), tip_pts)
        # Bright centre stripe on nose
        pygame.draw.line(screen, WHITE, (cx, by + 1), (cx, by + 6), 1)
        # Rim where nose meets body
        pygame.draw.rect(screen, (60, 210, 230),
                         (cx - bw // 2, by + 6, bw, 2))

        # ── Spark at tip apex ──
        pygame.draw.circle(screen, WHITE, (cx, by), 1)

        # ── Base cap ──
        pygame.draw.rect(screen, (0, 80, 100),
                         (cx - bw // 2, by + bh - 2, bw, 2), border_radius=1)


# ── Enemy bullet ──────────────────────────────────────────────────────────────
class EnemyBullet:
    """Red plasma shell – glowing cap, layered body, blazing tapered tip, pulsing halo."""

    BW = 6   # bullet width
    BH = 22  # bullet height

    def __init__(self, x, y):
        self.x     = x
        self.y     = y
        self.speed = 3
        self.anim  = 0

    def update(self):
        self.y    += self.speed
        self.anim  = (self.anim + 1) % 30

    def draw(self, screen):
        bw, bh = self.BW, self.BH
        cx = int(self.x)
        by = int(self.y)

        # Animated pulse (0 → 1 → 0 cycle)
        t     = self.anim / 30.0
        pulse = math.sin(t * math.pi * 2)          # -1 … +1
        glow_r = 255
        glow_g = int(max(0, 60 + 60 * pulse))       # orange ↔ red
        glow_col = (glow_r, glow_g, 0)

        # ── Multi-layer outer glow (large halo) ──
        for layer in range(6, 0, -1):
            g_pad = layer * 2
            g_w   = bw + g_pad * 2
            g_h   = bh + g_pad * 2
            gs    = pygame.Surface((g_w, g_h), pygame.SRCALPHA)
            a     = max(0, 40 - layer * 6)
            pygame.draw.rect(gs, (*glow_col, a), (0, 0, g_w, g_h), border_radius=g_pad + 4)
            screen.blit(gs, (cx - bw // 2 - g_pad, by - g_pad))

        # ── Top cap ──
        cap_h = 5
        pygame.draw.rect(screen, (200, 40, 40),
                         (cx - bw // 2, by, bw, cap_h), border_radius=2)
        # Cap highlight
        pygame.draw.rect(screen, (255, 130, 130),
                         (cx - bw // 2 + 1, by + 1, bw - 2, 1))
        # Cap dark edge
        pygame.draw.rect(screen, (120, 10, 10),
                         (cx - bw // 2, by + cap_h - 1, bw, 1))

        # ── Body – layered red casing ──
        body_y = by + cap_h
        body_h = bh - cap_h - 7
        # Outer shell
        pygame.draw.rect(screen, (160, 20, 20),
                         (cx - bw // 2, body_y, bw, body_h), border_radius=1)
        # Inner lighter band
        pygame.draw.rect(screen, (210, 50, 30),
                         (cx - bw // 2 + 1, body_y + 1, bw - 2, body_h - 2), border_radius=1)

        # ── Hot orange / white energy core stripe ──
        core_bright = int(180 + 75 * pulse)
        pygame.draw.rect(screen, clamp_color(255, core_bright, 0),
                         (cx - 1, body_y + 1, 2, body_h - 2), border_radius=1)
        # Bright centre pixel row
        pygame.draw.line(screen, (255, 240, 180),
                         (cx, body_y + 2), (cx, body_y + body_h - 3), 1)

        # ── Mid rim band ──
        rim_y = body_y + body_h // 2 - 1
        pygame.draw.rect(screen, clamp_color(255, glow_g + 30, 10),
                         (cx - bw // 2, rim_y, bw, 2))

        # ── Left highlight (3D metallic edge) ──
        pygame.draw.line(screen, (255, 100, 80),
                         (cx - bw // 2 + 1, body_y + 1),
                         (cx - bw // 2 + 1, body_y + body_h - 2), 1)

        # ── Tapered tip pointing downward ──
        tip_y  = body_y + body_h
        tip_tl = (cx - bw // 2,         tip_y)
        tip_tr = (cx + bw // 2 + bw % 2, tip_y)
        tip_pt = (cx,                    by + bh)
        pygame.draw.polygon(screen, (230, 70, 20), [tip_tl, tip_tr, tip_pt])
        # Bright spine on tip
        pygame.draw.line(screen, clamp_color(255, 200 + int(55 * pulse), 80),
                         (cx, tip_y + 1), (cx, by + bh - 2), 1)

        # ── Glowing point at the very tip ──
        tip_glow = pygame.Surface((6, 6), pygame.SRCALPHA)
        tip_alpha = int(180 + 75 * pulse)
        pygame.draw.circle(tip_glow, (*glow_col, tip_alpha), (3, 3), 3)
        screen.blit(tip_glow, (cx - 3, by + bh - 3))
