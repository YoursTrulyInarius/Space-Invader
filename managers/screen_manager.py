"""game/screens.py
Screens for profile selection, leaderboards, and standalone audio settings.
"""
import sys
import math
import random
import pygame

import constants
from constants import (
    NAVY, YELLOW, LIGHT_GRAY, GREEN, RED, WHITE, CYAN, GRAY, PURPLE,
    draw_text_center, draw_glow_rect, format_display_date
)
from managers.asset_manager import get_alien_surf
from managers.ui_manager import InputBox, _draw_slider_bar


def _make_star_icon(color):
    surf = pygame.Surface((18, 18), pygame.SRCALPHA)
    pts = [(9, 0), (12, 7), (18, 7), (13, 11), (15, 18), (9, 14), (3, 18), (5, 11), (0, 7), (6, 7)]
    pygame.draw.polygon(surf, color, pts)
    return surf


def _make_speaker_icon(color):
    surf = pygame.Surface((18, 18), pygame.SRCALPHA)
    pygame.draw.polygon(surf, color, [(2, 4), (8, 4), (12, 0), (12, 18), (8, 14), (2, 14)])
    pygame.draw.circle(surf, color, (13, 9), 4, 2)
    pygame.draw.circle(surf, color, (13, 9), 6, 1)
    return surf


def _make_music_icon(color):
    surf = pygame.Surface((20, 18), pygame.SRCALPHA)
    pygame.draw.rect(surf, color, (2, 5, 4, 8), border_radius=2)
    pygame.draw.circle(surf, color, (6, 6), 4)
    pygame.draw.circle(surf, color, (6, 14), 4)
    pygame.draw.line(surf, color, (8, 6), (16, 2), 3)
    pygame.draw.line(surf, color, (8, 14), (16, 10), 3)
    pygame.draw.circle(surf, color, (17, 3), 2)
    pygame.draw.circle(surf, color, (17, 11), 2)
    return surf


def _make_user_icon(color):
    surf = pygame.Surface((18, 18), pygame.SRCALPHA)
    pygame.draw.circle(surf, color, (9, 6), 5)
    pygame.draw.rect(surf, color, (4, 11, 10, 6), border_radius=3)
    return surf


def _make_score_icon(color):
    surf = pygame.Surface((18, 18), pygame.SRCALPHA)
    pygame.draw.polygon(surf, color, [(9, 2), (14, 7), (11, 16), (7, 16), (4, 7)])
    pygame.draw.circle(surf, color, (9, 10), 2)
    return surf


def _make_kill_icon(color):
    surf = pygame.Surface((18, 18), pygame.SRCALPHA)
    pygame.draw.line(surf, color, (4, 4), (14, 14), 3)
    pygame.draw.line(surf, color, (14, 4), (4, 14), 3)
    pygame.draw.circle(surf, color, (9, 9), 6, 2)
    return surf


def _make_acc_icon(color):
    surf = pygame.Surface((18, 18), pygame.SRCALPHA)
    pygame.draw.circle(surf, color, (9, 9), 8, 2)
    pygame.draw.line(surf, color, (9, 9), (14, 6), 3)
    pygame.draw.line(surf, color, (9, 9), (13, 12), 3)
    return surf


def _make_date_icon(color):
    surf = pygame.Surface((18, 18), pygame.SRCALPHA)
    pygame.draw.rect(surf, color, (2, 4, 14, 12), 2, border_radius=3)
    pygame.draw.line(surf, color, (5, 4), (5, 2), 3)
    pygame.draw.line(surf, color, (13, 4), (13, 2), 3)
    pygame.draw.line(surf, color, (4, 8), (14, 8), 2)
    return surf


def _make_leaderboard_icon(color):
    surf = pygame.Surface((18, 18), pygame.SRCALPHA)
    pygame.draw.rect(surf, color, (2, 6, 14, 10), 2, border_radius=3)
    pygame.draw.line(surf, color, (5, 9), (5, 13), 2)
    pygame.draw.line(surf, color, (9, 9), (9, 13), 2)
    pygame.draw.line(surf, color, (13, 9), (13, 13), 2)
    pygame.draw.line(surf, color, (6, 6), (12, 6), 2)
    return surf


def _make_settings_icon(color):
    surf = pygame.Surface((18, 18), pygame.SRCALPHA)
    pygame.draw.circle(surf, color, (9, 9), 7, 2)
    pygame.draw.circle(surf, color, (9, 5), 1)
    pygame.draw.circle(surf, color, (12, 9), 1)
    pygame.draw.circle(surf, color, (9, 13), 1)
    pygame.draw.circle(surf, color, (6, 9), 1)
    return surf


# ── Standalone Leaderboard screen (accessible from the main menu) ─────────────
class LeaderboardScreen:
    """Full-screen top-10 leaderboard, reachable from the main menu without
    needing to start (or finish) a game."""

    def __init__(self, screen, db):
        self.screen  = screen
        self.db      = db
        self.clock   = pygame.time.Clock()
        self.tick    = 0
        self.stars   = [[random.randint(0, constants.SCREEN_WIDTH),
                         random.randint(0, constants.SCREEN_HEIGHT),
                         random.uniform(0.3, 1.4),
                         random.randint(1, 2)] for _ in range(90)]
        self.fnt_ttl = pygame.font.SysFont("consolas", 40, bold=True)
        self.fnt_hd  = pygame.font.SysFont("consolas", 16, bold=True)
        self.fnt_row = pygame.font.SysFont("consolas", 17)
        self.fnt_sm  = pygame.font.SysFont("consolas", 15)
        self.rank_icons = [
            _make_star_icon((255, 215, 60)),
            _make_star_icon((200, 205, 215)),
            _make_star_icon((200, 140, 80)),
        ]
        self.header_icons = [
            _make_star_icon(CYAN),
            _make_user_icon(CYAN),
            _make_score_icon(CYAN),
            _make_kill_icon(CYAN),
            _make_acc_icon(CYAN),
            _make_date_icon(CYAN),
        ]

    def _draw_bg(self):
        self.screen.fill(NAVY)
        for s in self.stars:
            s[1] += s[2]
            if s[1] > constants.SCREEN_HEIGHT:
                s[1] = 0
                s[0] = random.randint(0, constants.SCREEN_WIDTH)
            b = random.randint(140, 240)
            pygame.draw.circle(self.screen, (b, b, b), (int(s[0]), int(s[1])), s[3])

    def run(self):
        online = bool(self.db and self.db.connected)
        rows   = self.db.get_leaderboard() if online else []

        while True:
            self.tick += 1
            self._draw_bg()
            draw_text_center(self.screen, "LEADERBOARD", self.fnt_ttl, YELLOW, 36)
            pygame.draw.line(self.screen, (50, 70, 130),
                             (constants.SCREEN_WIDTH // 2 - 230, 92),
                             (constants.SCREEN_WIDTH // 2 + 230, 92), 1)

            box_w = min(720, constants.SCREEN_WIDTH - 60)
            n_rows   = min(10, len(rows)) if online and rows else 1
            content_h = 54 + n_rows * 30 + 20
            box_h = max(140, min(content_h, constants.SCREEN_HEIGHT - 200))
            box   = pygame.Rect(constants.SCREEN_WIDTH // 2 - box_w // 2, 116, box_w, box_h)
            glow_box = box.inflate(14, 14)
            draw_glow_rect(self.screen, (30, 120, 220), glow_box, radius=18, layers=2)
            shadow = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
            shadow.fill((14, 18, 33, 220))
            pygame.draw.rect(shadow, (70, 75, 140, 80), shadow.get_rect(), 1, border_radius=12)
            self.screen.blit(shadow, box.topleft)
            pygame.draw.rect(self.screen, (85, 100, 165), box, 2, border_radius=12)

            if not online:
                msg = self.fnt_row.render("Offline — no database connection.", True, GRAY)
                self.screen.blit(msg, (box.centerx - msg.get_width() // 2, box.centery - 10))
            elif not rows:
                msg = self.fnt_row.render("No scores yet. Be the first to set one!", True, GRAY)
                self.screen.blit(msg, (box.centerx - msg.get_width() // 2, box.centery - 10))
            else:
                cols = ["#", "CALLSIGN", "SCORE", "KILLS", "ACC", "DATE"]
                offs = [0.025, 0.075, 0.34, 0.47, 0.575, 0.67]
                hy   = box.y + 18
                for idx, (h, off) in enumerate(zip(cols, offs)):
                    icon = self.header_icons[idx]
                    icon_x = box.x + int(box.width * off) - icon.get_width() // 2
                    self.screen.blit(icon, (icon_x, hy - 18))
                    ht = self.fnt_hd.render(h, True, CYAN)
                    self.screen.blit(ht, (box.x + int(box.width * off), hy))
                pygame.draw.line(self.screen, (55, 60, 120),
                                 (box.x + 14, hy + 26), (box.right - 14, hy + 26), 1)

                ry = hy + 36
                RANK_COLORS = {0: (255, 215, 60), 1: (200, 205, 215), 2: (200, 140, 80)}
                for i, entry in enumerate(rows[:10]):
                    un = str(entry.get('username', '???'))[:14]
                    sc = entry.get('score', 0)
                    ek = entry.get('enemies_killed', 0)
                    ac = entry.get('accuracy', 0) or 0
                    dt = format_display_date(entry.get('game_date', ''))
                    col = RANK_COLORS.get(i, WHITE)

                    if i % 2 == 1:
                        stripe = pygame.Rect(box.x + 8, ry - 4, box.width - 16, 28)
                        s = pygame.Surface(stripe.size, pygame.SRCALPHA)
                        s.fill((255, 255, 255, 10))
                        self.screen.blit(s, stripe.topleft)

                    icon_x = box.x + 12
                    if i < len(self.rank_icons):
                        self.screen.blit(self.rank_icons[i], (icon_x, ry + 1))
                        rank_x = icon_x + 24
                    else:
                        rank_x = box.x + int(box.width * offs[0])

                    vals = [f"{i+1}.", un, str(sc), str(ek), f"{float(ac):.0f}%", dt]
                    for j, (v, off) in enumerate(zip(vals, offs)):
                        x_pos = rank_x if j == 0 and i < len(self.rank_icons) else box.x + int(box.width * off)
                        vs = self.fnt_row.render(v, True, col)
                        self.screen.blit(vs, (x_pos, ry))
                    ry += 30
                    if ry > box.bottom - 24:
                        break

            back_rect = pygame.Rect(constants.SCREEN_WIDTH // 2 - 75, constants.SCREEN_HEIGHT - 62, 150, 38)
            hov = back_rect.collidepoint(pygame.mouse.get_pos())
            pygame.draw.rect(self.screen, (38, 96, 200) if hov else (20, 22, 40), back_rect, border_radius=8)
            pygame.draw.rect(self.screen, CYAN if hov else (55, 60, 120), back_rect, 2, border_radius=8)
            bt = self.fnt_row.render("< BACK", True, WHITE)
            self.screen.blit(bt, (back_rect.centerx - bt.get_width() // 2,
                                  back_rect.centery - bt.get_height() // 2))

            hint = self.fnt_sm.render("ESC / click BACK to return to the main menu", True, GRAY)
            self.screen.blit(hint, (constants.SCREEN_WIDTH // 2 - hint.get_width() // 2, constants.SCREEN_HEIGHT - 22))

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                elif ev.type == pygame.VIDEORESIZE:
                    w, h = ev.dict.get('size', (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
                    constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT = w, h
                    self.screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
                elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    return
                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if back_rect.collidepoint(ev.pos):
                        return

            pygame.display.flip()
            self.clock.tick(60)


# ── Standalone Audio Settings screen (accessible from the main menu) ──────────
class AudioSettingsScreen:
    """Lets the player adjust SFX / music volume from the main menu, without
    needing to be in a paused game first."""

    def __init__(self, screen, audio):
        self.screen    = screen
        self.audio     = audio
        self.clock     = pygame.time.Clock()
        self.sfx_drag  = False
        self.music_drag = False
        self.stars     = [[random.randint(0, constants.SCREEN_WIDTH),
                           random.randint(0, constants.SCREEN_HEIGHT),
                           random.uniform(0.3, 1.4),
                           random.randint(1, 2)] for _ in range(90)]
        self.fnt_ttl = pygame.font.SysFont("consolas", 40, bold=True)
        self.fnt_lbl = pygame.font.SysFont("consolas", 19)
        self.fnt_sm  = pygame.font.SysFont("consolas", 15)
        self.icon_sfx   = _make_speaker_icon(CYAN)
        self.icon_music = _make_music_icon(PURPLE)
        self.icon_test  = _make_speaker_icon(WHITE)

    def _draw_bg(self):
        self.screen.fill(NAVY)
        for s in self.stars:
            s[1] += s[2]
            if s[1] > constants.SCREEN_HEIGHT:
                s[1] = 0
                s[0] = random.randint(0, constants.SCREEN_WIDTH)
            b = random.randint(140, 240)
            pygame.draw.circle(self.screen, (b, b, b), (int(s[0]), int(s[1])), s[3])

    def _rects(self):
        cx, cy = constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2
        bw = 320
        return {
            'sfx_bar':   pygame.Rect(cx - bw // 2, cy - 30, bw, 18),
            'music_bar': pygame.Rect(cx - bw // 2, cy + 50, bw, 18),
            'test_btn':  pygame.Rect(cx - 95, cy + 108, 190, 40),
            'back_btn':  pygame.Rect(cx - 95, cy + 160, 190, 40),
        }

    def _update_vol(self, kind, mx, bar):
        v = max(0.0, min(1.0, (mx - bar.x) / bar.width))
        if not self.audio:
            return
        if kind == 'sfx':
            self.audio.set_sfx_vol(v)
        else:
            self.audio.set_music_vol(v)

    def run(self):
        while True:
            self._draw_bg()
            draw_text_center(self.screen, "AUDIO SETTINGS", self.fnt_ttl, YELLOW, 60)
            pygame.draw.line(self.screen, (50, 70, 130),
                             (constants.SCREEN_WIDTH // 2 - 200, 116),
                             (constants.SCREEN_WIDTH // 2 + 200, 116), 1)

            r = self._rects()

            if not self.audio or not self.audio.sounds:
                msg = self.fnt_lbl.render("Audio is unavailable (numpy not installed).",
                                          True, RED)
                self.screen.blit(msg, (constants.SCREEN_WIDTH // 2 - msg.get_width() // 2,
                                       constants.SCREEN_HEIGHT // 2 - 60))
            else:
                sfx_v   = self.audio.sfx_vol
                music_v = self.audio.music_vol
                sl = self.fnt_lbl.render(f"SFX VOLUME    {int(sfx_v * 100):>3}%", True, CYAN)
                self.screen.blit(self.icon_sfx, (r['sfx_bar'].x - 32, r['sfx_bar'].y - 4))
                self.screen.blit(sl, (r['sfx_bar'].x + 28, r['sfx_bar'].y - 30))
                _draw_slider_bar(self.screen, r['sfx_bar'], sfx_v, CYAN)

                ml = self.fnt_lbl.render(f"MUSIC VOLUME  {int(music_v * 100):>3}%", True, PURPLE)
                self.screen.blit(self.icon_music, (r['music_bar'].x - 32, r['music_bar'].y - 4))
                self.screen.blit(ml, (r['music_bar'].x + 28, r['music_bar'].y - 30))
                _draw_slider_bar(self.screen, r['music_bar'], music_v, PURPLE)

                mpos = pygame.mouse.get_pos()
                hov  = r['test_btn'].collidepoint(mpos)
                pygame.draw.rect(self.screen, (38, 96, 200) if hov else (20, 22, 40),
                                 r['test_btn'], border_radius=8)
                pygame.draw.rect(self.screen, CYAN if hov else (55, 60, 120), r['test_btn'], 2, border_radius=8)
                self.screen.blit(self.icon_test, (r['test_btn'].x + 14, r['test_btn'].centery - 9))
                tb = self.fnt_lbl.render("TEST SFX", True, WHITE)
                self.screen.blit(tb, (r['test_btn'].x + 38, r['test_btn'].centery - tb.get_height() // 2))

            mpos = pygame.mouse.get_pos()
            hov  = r['back_btn'].collidepoint(mpos)
            pygame.draw.rect(self.screen, (38, 96, 200) if hov else (20, 22, 40),
                             r['back_btn'], border_radius=8)
            pygame.draw.rect(self.screen, CYAN if hov else (55, 60, 120), r['back_btn'], 2, border_radius=8)
            bb = self.fnt_lbl.render("< BACK", True, WHITE)
            self.screen.blit(bb, (r['back_btn'].centerx - bb.get_width() // 2,
                                  r['back_btn'].centery - bb.get_height() // 2))

            hint = self.fnt_sm.render("Drag sliders to adjust   |   ESC = Back", True, GRAY)
            self.screen.blit(hint, (constants.SCREEN_WIDTH // 2 - hint.get_width() // 2, constants.SCREEN_HEIGHT - 30))

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                elif ev.type == pygame.VIDEORESIZE:
                    w, h = ev.dict.get('size', (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
                    constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT = w, h
                    self.screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
                elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    return
                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    r = self._rects()
                    if self.audio and self.audio.sounds:
                        if r['sfx_bar'].collidepoint(ev.pos):
                            self.sfx_drag = True
                            self._update_vol('sfx', ev.pos[0], r['sfx_bar'])
                        elif r['music_bar'].collidepoint(ev.pos):
                            self.music_drag = True
                            self._update_vol('music', ev.pos[0], r['music_bar'])
                        elif r['test_btn'].collidepoint(ev.pos):
                            self.audio.play('shoot')
                    if r['back_btn'].collidepoint(ev.pos):
                        return
                elif ev.type == pygame.MOUSEBUTTONUP:
                    self.sfx_drag = self.music_drag = False
                elif ev.type == pygame.MOUSEMOTION:
                    r = self._rects()
                    if self.sfx_drag:
                        self._update_vol('sfx', ev.pos[0], r['sfx_bar'])
                    if self.music_drag:
                        self._update_vol('music', ev.pos[0], r['music_bar'])

            pygame.display.flip()
            self.clock.tick(60)


# ── Profile Screen ────────────────────────────────────────────────────────────
class ProfileScreen:
    def __init__(self, screen, db, audio=None):
        self.screen  = pygame.display.get_surface()
        self.db      = db
        self.audio   = audio
        self.input   = InputBox(constants.SCREEN_WIDTH // 2 - 210, constants.SCREEN_HEIGHT // 2 + 20, 420, 46)
        self.error   = ""
        self.etimer  = 0
        self.clock   = pygame.time.Clock()
        self.tick    = 0
        self.stars   = [[random.randint(0, constants.SCREEN_WIDTH),
                         random.randint(0, constants.SCREEN_HEIGHT),
                         random.uniform(0.3, 1.4),
                         random.randint(1, 2)] for _ in range(130)]
        self.players = self._load_players()
        self.solar_planets = [
            {'orbit': 84,  'size': 6, 'speed': 0.012, 'phase': 0.0, 'color': (160, 210, 255)},
            {'orbit': 118, 'size': 7, 'speed': 0.008, 'phase': 1.8, 'color': (120, 180, 240)},
            {'orbit': 152, 'size': 8, 'speed': 0.005, 'phase': 3.7, 'color': (255, 180, 100), 'ring': True, 'ring_color': (255, 205, 130, 120)},
            {'orbit': 186, 'size': 6, 'speed': 0.003, 'phase': 5.1, 'color': (193, 255, 160)},
        ]
        self.icon_leaderboard = _make_leaderboard_icon(LIGHT_GRAY)
        self.icon_settings    = _make_settings_icon(LIGHT_GRAY)

    def _load_players(self):
        if self.db and self.db.connected:
            try:
                self.db.cursor.execute("SELECT username FROM players ORDER BY username")
                return [r['username'] for r in self.db.cursor.fetchall()]
            except:
                pass
        return []

    def _draw_bg(self):
        self.screen.fill(NAVY)
        for s in self.stars:
            s[1] += s[2]
            if s[1] > constants.SCREEN_HEIGHT:
                s[1] = 0
                s[0] = random.randint(0, constants.SCREEN_WIDTH)
            b = random.randint(140, 240)
            pygame.draw.circle(self.screen, (b, b, b), (int(s[0]), int(s[1])), s[3])

    def _draw_alien_parade(self):
        col_w = constants.SCREEN_WIDTH // 4
        for i in range(4):
            surf  = get_alien_surf(i % 3)
            wave  = int(6 * abs(pygame.math.Vector2(0, 1).rotate(self.tick * 3 + i * 90).y))
            x     = i * col_w + col_w // 2 - surf.get_width() // 2
            s2    = surf.copy()
            s2.set_alpha(90 + int(55 * abs(pygame.math.Vector2(1, 0).rotate(self.tick * 2 + i * 60).x)))
            self.screen.blit(s2, (x, 178 + wave))

    def _draw_solar_system(self):
        cx = constants.SCREEN_WIDTH // 2
        cy = constants.SCREEN_HEIGHT // 2 - 40
        pygame.draw.circle(self.screen, (252, 212, 112), (cx, cy), 11)
        sun_glow = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(sun_glow, (252, 212, 112, 48), (20, 20), 18)
        self.screen.blit(sun_glow, (cx - 20, cy - 20))

        for planet in self.solar_planets:
            orbit = planet['orbit']
            ring = pygame.Surface((orbit * 2 + 4, orbit * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(ring, (100, 160, 220, 20), (orbit + 2, orbit + 2), orbit, 1)
            self.screen.blit(ring, (cx - orbit - 2, cy - orbit - 2))
            angle = self.tick * planet['speed'] + planet['phase']
            px = cx + int(math.cos(angle) * orbit)
            py = cy + int(math.sin(angle) * orbit * 0.65)
            planet_rect = pygame.Rect(px - planet['size'] // 2, py - planet['size'] // 2,
                                      planet['size'], planet['size'])
            pygame.draw.rect(self.screen, planet['color'], planet_rect, border_radius=3)
            if planet.get('ring'):
                ring_size = planet['size'] * 3
                ring_surf = pygame.Surface((ring_size, ring_size), pygame.SRCALPHA)
                pygame.draw.ellipse(ring_surf, planet['ring_color'], ring_surf.get_rect(), 2)
                self.screen.blit(ring_surf, (px - ring_size // 2, py - ring_size // 2 + 2))

    def run(self):
        if self.audio:
            self.audio.play_bgm()
        fnt_title = pygame.font.SysFont("consolas", 64, bold=True)
        fnt_sub   = pygame.font.SysFont("consolas", 20)
        fnt_inst  = pygame.font.SysFont("consolas", 18)
        fnt_list  = pygame.font.SysFont("consolas", 19)
        fnt_cred  = pygame.font.SysFont("consolas", 15)

        while True:
            self.tick += 1
            self._draw_bg()
            self._draw_solar_system()
            self._draw_alien_parade()

            pulse = abs((self.tick % 120) - 60) / 60
            tc    = (255, int(192 + 63 * pulse), int(20 * pulse))
            draw_text_center(self.screen, "SPACE INVADERS", fnt_title, tc, 64)
            draw_text_center(self.screen, "-- CLASSIC ARCADE EDITION --",
                             fnt_sub, (100, 155, 255), 136)
            pygame.draw.line(self.screen, (50, 70, 130),
                             (constants.SCREEN_WIDTH // 2 - 230, 164),
                             (constants.SCREEN_WIDTH // 2 + 230, 164), 1)

            lbl = fnt_inst.render("ENTER CALLSIGN:", True, LIGHT_GRAY)
            self.screen.blit(lbl, (constants.SCREEN_WIDTH // 2 - lbl.get_width() // 2,
                                   constants.SCREEN_HEIGHT // 2 - 14))
            self.input.draw(self.screen)

            for i, n in enumerate(["New callsign  ->  creates a pilot profile",
                                    "Known callsign ->  loads your history"]):
                ns = fnt_inst.render(n, True, (115, 125, 155))
                self.screen.blit(ns, (constants.SCREEN_WIDTH // 2 - ns.get_width() // 2,
                                     constants.SCREEN_HEIGHT // 2 + 80 + i * 24))

            if self.players:
                list_w = min(500, constants.SCREEN_WIDTH - 120)
                list_h = 24 + min(5, len(self.players)) * 22 + 16
                list_box = pygame.Rect(constants.SCREEN_WIDTH // 2 - list_w // 2,
                                       constants.SCREEN_HEIGHT // 2 + 132,
                                       list_w, list_h)
                list_surf = pygame.Surface((list_box.width, list_box.height), pygame.SRCALPHA)
                list_surf.fill((18, 28, 58, 200))
                pygame.draw.rect(list_surf, (80, 110, 170, 80), list_surf.get_rect(), 1, border_radius=14)
                self.screen.blit(list_surf, list_box.topleft)

                ty = list_box.y + 12
                ht = fnt_list.render("KNOWN PILOTS:", True, YELLOW)
                self.screen.blit(ht, (list_box.centerx - ht.get_width() // 2, ty))
                for j, p in enumerate(self.players[:5]):
                    match = self.input.text and p.lower().startswith(self.input.text.lower())
                    ps = fnt_list.render(f"  {p}", True, GREEN if match else LIGHT_GRAY)
                    self.screen.blit(ps, (list_box.x + 16, ty + 22 + j * 21))

            if self.etimer > 0:
                es = fnt_inst.render(self.error, True, RED)
                self.screen.blit(es, (constants.SCREEN_WIDTH // 2 - es.get_width() // 2,
                                       constants.SCREEN_HEIGHT // 2 + 72))
                self.etimer -= 1

            cs = fnt_cred.render("DEVELOPED BY: CABARDO, SONJEEV C.", True, (60, 65, 90))
            self.screen.blit(cs, (constants.SCREEN_WIDTH // 2 - cs.get_width() // 2, constants.SCREEN_HEIGHT - 26))

            # ── Leaderboard / Settings buttons (slim row, above the title) ───
            btn_w, btn_h, gap = 150, 30, 10
            set_rect = pygame.Rect(constants.SCREEN_WIDTH - 12 - btn_w, 10, btn_w, btn_h)
            lb_rect  = pygame.Rect(set_rect.x - gap - btn_w, 10, btn_w, btn_h)
            mpos = pygame.mouse.get_pos()
            for rect, label, icon in (
                (lb_rect, "LEADERBOARD F1", self.icon_leaderboard),
                (set_rect, "SETTINGS F2", self.icon_settings)
            ):
                hov = rect.collidepoint(mpos)
                base = (30, 40, 70) if hov else (14, 18, 32)
                pygame.draw.rect(self.screen, base, rect, border_radius=8)
                pygame.draw.rect(self.screen, CYAN if hov else (55, 60, 120), rect, 1, border_radius=8)
                if hov:
                    glow = pygame.Surface((rect.width + 12, rect.height + 12), pygame.SRCALPHA)
                    pygame.draw.rect(glow, (40, 180, 255, 30), glow.get_rect(), border_radius=10)
                    self.screen.blit(glow, (rect.x - 6, rect.y - 6))
                color = WHITE if hov else LIGHT_GRAY
                text = fnt_cred.render(label, True, color)
                icon_colored = _make_leaderboard_icon(color) if icon is self.icon_leaderboard else _make_settings_icon(color)
                total_width = icon_colored.get_width() + 8 + text.get_width()
                x = rect.centerx - total_width // 2
                self.screen.blit(icon_colored, (x, rect.centery - icon_colored.get_height() // 2))
                self.screen.blit(text, (x + icon_colored.get_width() + 8,
                                        rect.centery - text.get_height() // 2))

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    return None
                elif ev.type == pygame.VIDEORESIZE:
                    w, h = ev.dict.get('size', (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
                    constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT = w, h
                    self.screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
                elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_F1:
                    LeaderboardScreen(self.screen, self.db).run()
                    self.screen = pygame.display.get_surface()
                    constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT = self.screen.get_size()
                    continue
                elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_F2:
                    AudioSettingsScreen(self.screen, self.audio).run()
                    self.screen = pygame.display.get_surface()
                    constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT = self.screen.get_size()
                    continue
                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if lb_rect.collidepoint(ev.pos):
                        LeaderboardScreen(self.screen, self.db).run()
                        self.screen = pygame.display.get_surface()
                        constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT = self.screen.get_size()
                        continue
                    elif set_rect.collidepoint(ev.pos):
                        AudioSettingsScreen(self.screen, self.audio).run()
                        self.screen = pygame.display.get_surface()
                        constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT = self.screen.get_size()
                        continue
                res = self.input.handle_event(ev)
                if res is not None:
                    name = res.strip()
                    if not name:
                        self.error, self.etimer = "Please enter a callsign!", 90
                    elif len(name) > 30:
                        self.error, self.etimer = "Too long! (max 30 chars)", 90
                    else:
                        return name

            pygame.display.flip()
            self.clock.tick(60)
