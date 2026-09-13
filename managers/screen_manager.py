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
        self.fnt_sub = pygame.font.SysFont("consolas", 15)
        self.fnt_hd  = pygame.font.SysFont("consolas", 16, bold=True)
        self.fnt_row = pygame.font.SysFont("consolas", 17)
        self.fnt_row_compact = pygame.font.SysFont("consolas", 15)
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

    def _table_layout(self, row_count):
        compact = constants.SCREEN_WIDTH < 760 or constants.SCREEN_HEIGHT < 560
        box_w = min(900, constants.SCREEN_WIDTH - 40)
        box_y = 112 if not compact else 86
        row_h = 30 if not compact else 27
        header_h = 66 if not compact else 58
        visible = max(1, min(10, row_count))
        max_box_h = max(150, constants.SCREEN_HEIGHT - box_y - 92)
        box_h = min(header_h + visible * row_h + 18, max_box_h)
        row_h = max(22, (box_h - header_h - 18) // visible)
        box_h = header_h + visible * row_h + 18
        box = pygame.Rect(constants.SCREEN_WIDTH // 2 - box_w // 2, box_y, box_w, box_h)
        return box, row_h, header_h, compact

    def _draw_table_header(self, box, header_h, compact):
        centers = [0.055, 0.20, 0.50, 0.64, 0.75, 0.88]
        labels = ["#", "CALLSIGN", "SCORE", "KILLS", "ACC", "DATE"]
        font = self.fnt_sm if compact else self.fnt_hd
        header_y = box.y + 38 if not compact else box.y + 34
        for icon, label, center in zip(self.header_icons, labels, centers):
            x = box.x + int(box.width * center)
            self.screen.blit(icon, (x - icon.get_width() // 2, header_y - 25))
            text = font.render(label, True, CYAN)
            self.screen.blit(text, (x - text.get_width() // 2, header_y))
        pygame.draw.line(self.screen, (55, 82, 145),
                         (box.x + 18, box.y + header_h),
                         (box.right - 18, box.y + header_h), 1)

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
        rows = list(self.db.get_leaderboard()[:10]) if online else []

        while True:
            self.tick += 1
            self._draw_bg()
            compact = constants.SCREEN_WIDTH < 760 or constants.SCREEN_HEIGHT < 560
            title_font = pygame.font.SysFont("consolas", 32, bold=True) if compact else self.fnt_ttl
            draw_text_center(self.screen, "LEADERBOARD", title_font, YELLOW, 22 if compact else 36)
            subtitle = self.fnt_sub.render("TOP 10 PILOTS BY SCORE", True, (100, 170, 255))
            self.screen.blit(subtitle, (constants.SCREEN_WIDTH // 2 - subtitle.get_width() // 2,
                                        66 if compact else 84))
            pygame.draw.line(self.screen, (50, 70, 130),
                             (constants.SCREEN_WIDTH // 2 - 290, 98 if compact else 108),
                             (constants.SCREEN_WIDTH // 2 + 290, 98 if compact else 108), 1)

            box, row_h, header_h, compact = self._table_layout(len(rows) if rows else 1)
            draw_glow_rect(self.screen, (30, 120, 220), box.inflate(12, 12), radius=16, layers=2)
            pygame.draw.rect(self.screen, (10, 18, 40), box, border_radius=12)
            pygame.draw.rect(self.screen, (62, 108, 190), box, 2, border_radius=12)
            header_band = pygame.Rect(box.x + 2, box.y + 2, box.width - 4, header_h)
            pygame.draw.rect(self.screen, (19, 37, 70), header_band, border_radius=9)

            if not online:
                msg = self.fnt_row.render("OFFLINE - NO DATABASE CONNECTION", True, GRAY)
                self.screen.blit(msg, (box.centerx - msg.get_width() // 2, box.centery - 10))
            elif not rows:
                msg = self.fnt_row.render("NO SCORES YET - BE THE FIRST TO SET ONE", True, GRAY)
                self.screen.blit(msg, (box.centerx - msg.get_width() // 2, box.centery - 10))
            else:
                self._draw_table_header(box, header_h, compact)
                starts = [0.04, 0.12, 0.43, 0.58, 0.69, 0.80]
                ry = box.y + header_h + 8
                rank_colors = {0: (255, 215, 60), 1: (200, 205, 215), 2: (200, 140, 80)}
                for i, entry in enumerate(rows[:10]):
                    un = str(entry.get('username', '???'))[:14]
                    sc = entry.get('score', 0)
                    ek = entry.get('enemies_killed', 0)
                    ac = entry.get('accuracy', 0) or 0
                    dt = format_display_date(entry.get('game_date', '')) or "--"
                    col = rank_colors.get(i, WHITE)

                    if i % 2 == 1:
                        stripe = pygame.Rect(box.x + 10, ry - 4, box.width - 20, row_h)
                        pygame.draw.rect(self.screen, (24, 42, 76), stripe, border_radius=4)

                    icon_x = box.x + 12
                    if i < len(self.rank_icons):
                        self.screen.blit(self.rank_icons[i], (icon_x, ry + max(0, (row_h - 18) // 2)))
                        rank_x = icon_x + 24
                    else:
                        rank_x = box.x + int(box.width * starts[0])

                    vals = [f"{i+1}.", un, str(sc), str(ek), f"{float(ac):.0f}%", dt]
                    row_font = self.fnt_row_compact if compact else self.fnt_row
                    for j, (v, off) in enumerate(zip(vals, starts)):
                        x_pos = rank_x if j == 0 and i < len(self.rank_icons) else box.x + int(box.width * off)
                        vs = row_font.render(v, True, col)
                        self.screen.blit(vs, (x_pos, ry))
                    ry += row_h

            back_rect = pygame.Rect(constants.SCREEN_WIDTH // 2 - 82,
                                    constants.SCREEN_HEIGHT - 62, 164, 38)
            hov = back_rect.collidepoint(pygame.mouse.get_pos())
            pygame.draw.rect(self.screen, (38, 96, 200) if hov else (20, 22, 40), back_rect, border_radius=8)
            pygame.draw.rect(self.screen, CYAN if hov else (55, 60, 120), back_rect, 2, border_radius=8)
            bt = self.fnt_row.render("BACK TO MENU", True, WHITE)
            self.screen.blit(bt, (back_rect.centerx - bt.get_width() // 2,
                                  back_rect.centery - bt.get_height() // 2))

            hint = self.fnt_sm.render("ESC / click BACK to return", True, GRAY)
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
        self.input = InputBox(0, 0, 420, 46, "Enter callsign...")
        self.password_input = InputBox(0, 0, 420, 46, "Enter password...", password=True)
        self.focus_index = 0
        self._layout_auth()
        self.mode = 'login'
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

    def _layout_auth(self):
        compact = constants.SCREEN_HEIGHT < 500
        width = min(500, constants.SCREEN_WIDTH - 40)
        field_width = width - 48
        field_height = 40 if compact else 46
        panel_top = 58 if compact else 188
        field_y = panel_top + (38 if compact else 56)
        field_gap = 52 if compact else 72
        field_x = constants.SCREEN_WIDTH // 2 - field_width // 2
        self.input.rect = pygame.Rect(field_x, field_y, field_width, field_height)
        self.password_input.rect = pygame.Rect(field_x, field_y + field_gap, field_width, field_height)
        self._set_focus(self.focus_index)

    def _set_focus(self, index):
        self.focus_index = index % 4
        self.input.focused = self.focus_index == 0
        self.password_input.focused = self.focus_index == 1

    def _load_players(self):
        if self.db and self.db.connected:
            try:
                self.db.cursor.execute("SELECT username FROM players ORDER BY username")
                return [r['username'] for r in self.db.cursor.fetchall()]
            except:
                pass
        return []

    def _action_rects(self):
        compact = constants.SCREEN_HEIGHT < 500
        y = self.password_input.rect.bottom + (12 if compact else 28)
        cx = constants.SCREEN_WIDTH // 2
        button_width = min(220, (constants.SCREEN_WIDTH - 60) // 2)
        button_height = 38 if compact else 46
        gap = 12
        return {
            'submit': pygame.Rect(cx - button_width - gap // 2, y, button_width, button_height),
            'mode': pygame.Rect(cx + gap // 2, y, button_width, button_height),
        }

    def _submit(self):
        username = self.input.text.strip()
        password = self.password_input.text
        if not username or not password:
            self.error, self.etimer = "Enter both callsign and password.", 120
            return None
        if len(username) > 30:
            self.error, self.etimer = "Callsign too long! (max 30 chars)", 120
            return None

        if not self.db or not self.db.connected:
            self.error, self.etimer = "Database unavailable. Try again later.", 120
            return None

        if self.mode == 'register':
            if len(password) < 6:
                self.error, self.etimer = "Password must be at least 6 characters.", 120
                return None
            player_id = self.db.register_player(username, password)
            if not player_id:
                self.error, self.etimer = "Registration failed. Callsign may already exist.", 120
                return None
            return username

        if self.db.authenticate_player(username, password):
            return username
        self.error, self.etimer = "Invalid callsign or password.", 120
        return None

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
            self._layout_auth()
            self._draw_bg()
            self._draw_solar_system()
            self._draw_alien_parade()

            pulse = abs((self.tick % 120) - 60) / 60
            tc    = (255, int(192 + 63 * pulse), int(20 * pulse))
            compact = constants.SCREEN_HEIGHT < 500
            title_font = fnt_title if not compact else pygame.font.SysFont("consolas", 34, bold=True)
            draw_text_center(self.screen, "SPACE INVADERS", title_font, tc, 12 if compact else 64)
            draw_text_center(self.screen, "-- CLASSIC ARCADE EDITION --",
                             fnt_sub if not compact else pygame.font.SysFont("consolas", 14),
                             (100, 155, 255), 56 if compact else 136)
            pygame.draw.line(self.screen, (50, 70, 130),
                             (constants.SCREEN_WIDTH // 2 - 230, 82 if compact else 164),
                             (constants.SCREEN_WIDTH // 2 + 230, 82 if compact else 164), 1)

            rects = self._action_rects()
            panel_top = 48 if compact else 180
            panel_bottom = rects['mode'].bottom + (38 if compact else 60)
            panel_width = min(500, constants.SCREEN_WIDTH - 40)
            panel = pygame.Rect(constants.SCREEN_WIDTH // 2 - panel_width // 2,
                                panel_top, panel_width, panel_bottom - panel_top)
            pygame.draw.rect(self.screen, (10, 14, 32), panel, border_radius=14)
            pygame.draw.rect(self.screen, (48, 76, 145), panel, 2, border_radius=14)

            mode_title = "LOGIN" if self.mode == 'login' else "REGISTER"
            lbl = fnt_inst.render(mode_title, True, YELLOW)
            self.screen.blit(lbl, (constants.SCREEN_WIDTH // 2 - lbl.get_width() // 2,
                                   panel_top + 12 if compact else panel_top + 16))
            user_lbl = fnt_inst.render("CALLSIGN", True, LIGHT_GRAY)
            pass_lbl = fnt_inst.render("PASSWORD", True, LIGHT_GRAY)
            self.screen.blit(user_lbl, (self.input.rect.x, self.input.rect.y - 24))
            self.screen.blit(pass_lbl, (self.password_input.rect.x, self.password_input.rect.y - 24))
            self.input.draw(self.screen)
            self.password_input.draw(self.screen)

            if not compact:
                hint = fnt_cred.render("Click the eye to show or hide your password.", True, (115, 125, 155))
                self.screen.blit(hint, (constants.SCREEN_WIDTH // 2 - hint.get_width() // 2,
                                        self.password_input.rect.bottom + 10))

            for key, label in (('submit', mode_title),
                               ('mode', "CREATE ACCOUNT" if self.mode == 'login' else "BACK TO LOGIN")):
                rect = rects[key]
                hov = rect.collidepoint(pygame.mouse.get_pos())
                focused = (key == 'submit' and self.focus_index == 2) or (key == 'mode' and self.focus_index == 3)
                active = hov or focused
                pygame.draw.rect(self.screen, (38, 96, 200) if active else (20, 22, 40), rect, border_radius=8)
                pygame.draw.rect(self.screen, CYAN if active else (55, 60, 120), rect, 2, border_radius=8)
                text = fnt_inst.render(label, True, WHITE)
                self.screen.blit(text, (rect.centerx - text.get_width() // 2,
                                        rect.centery - text.get_height() // 2))

            if self.etimer > 0:
                es = fnt_inst.render(self.error, True, RED)
                self.screen.blit(es, (constants.SCREEN_WIDTH // 2 - es.get_width() // 2,
                                       rects['mode'].bottom + 8))
                self.etimer -= 1

            if not compact:
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
                    rects = self._action_rects()
                    if rects['submit'].collidepoint(ev.pos):
                        self._set_focus(2)
                        result = self._submit()
                        if result:
                            return result
                        continue
                    if rects['mode'].collidepoint(ev.pos):
                        self._set_focus(3)
                        self.mode = 'register' if self.mode == 'login' else 'login'
                        self.error = ""
                        self.password_input.text = ""
                        continue
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_TAB:
                    backwards = bool(ev.mod & pygame.KMOD_SHIFT)
                    self._set_focus(self.focus_index - 1 if backwards else self.focus_index + 1)
                    self.input.select_all = False
                    self.password_input.select_all = False
                    continue
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_RETURN:
                    if self.focus_index == 3:
                        self.mode = 'register' if self.mode == 'login' else 'login'
                        self.error = ""
                        self.password_input.text = ""
                        continue
                    result = self._submit()
                    if result:
                        return result
                    continue
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if self.input.rect.collidepoint(ev.pos):
                        self._set_focus(0)
                    elif self.password_input.rect.collidepoint(ev.pos):
                        self._set_focus(1)
                self.input.handle_event(ev)
                self.password_input.handle_event(ev)

            pygame.display.flip()
            self.clock.tick(60)
