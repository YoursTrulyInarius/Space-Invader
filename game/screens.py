"""game/screens.py
Screens for profile selection, leaderboards, and standalone audio settings.
"""
import sys
import random
import pygame

import game.constants as constants
from game.constants import (
    NAVY, YELLOW, LIGHT_GRAY, GREEN, RED, WHITE, CYAN, GRAY, PURPLE,
    draw_text_center, format_display_date
)
from game.assets import get_alien_surf
from game.ui import InputBox, _draw_slider_bar

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
            pygame.draw.rect(self.screen, (12, 12, 26), box, border_radius=12)
            pygame.draw.rect(self.screen, (70, 75, 140), box, 2, border_radius=12)

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
                for h, off in zip(cols, offs):
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

                    vals = [f"{i+1}.", un, str(sc), str(ek), f"{float(ac):.0f}%", dt]
                    for v, off in zip(vals, offs):
                        vs = self.fnt_row.render(v, True, col)
                        self.screen.blit(vs, (box.x + int(box.width * off), ry))
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
                self.screen.blit(sl, (constants.SCREEN_WIDTH // 2 - sl.get_width() // 2, r['sfx_bar'].y - 30))
                _draw_slider_bar(self.screen, r['sfx_bar'], sfx_v, CYAN)

                ml = self.fnt_lbl.render(f"MUSIC VOLUME  {int(music_v * 100):>3}%", True, PURPLE)
                self.screen.blit(ml, (constants.SCREEN_WIDTH // 2 - ml.get_width() // 2, r['music_bar'].y - 30))
                _draw_slider_bar(self.screen, r['music_bar'], music_v, PURPLE)

                mpos = pygame.mouse.get_pos()
                hov  = r['test_btn'].collidepoint(mpos)
                pygame.draw.rect(self.screen, (38, 96, 200) if hov else (20, 22, 40),
                                 r['test_btn'], border_radius=8)
                pygame.draw.rect(self.screen, CYAN if hov else (55, 60, 120), r['test_btn'], 2, border_radius=8)
                tb = self.fnt_lbl.render("TEST SFX", True, WHITE)
                self.screen.blit(tb, (r['test_btn'].centerx - tb.get_width() // 2,
                                      r['test_btn'].centery - tb.get_height() // 2))

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
            self._draw_alien_parade()

            pulse = abs((self.tick % 120) - 60) / 60
            tc    = (255, int(192 + 63 * pulse), int(20 * pulse))
            draw_text_center(self.screen, "SPACE INVADERS", fnt_title, tc, 52)
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
                ty = constants.SCREEN_HEIGHT // 2 + 140
                ht = fnt_list.render("KNOWN PILOTS:", True, YELLOW)
                self.screen.blit(ht, (constants.SCREEN_WIDTH // 2 - ht.get_width() // 2, ty))
                for j, p in enumerate(self.players[:5]):
                    match = self.input.text and p.lower().startswith(self.input.text.lower())
                    ps = fnt_list.render(f"  {p}", True, GREEN if match else LIGHT_GRAY)
                    self.screen.blit(ps, (constants.SCREEN_WIDTH // 2 - ps.get_width() // 2,
                                         ty + 22 + j * 21))

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
            for rect, label in ((lb_rect, "LEADERBOARD F1"), (set_rect, "SETTINGS F2")):
                hov = rect.collidepoint(mpos)
                pygame.draw.rect(self.screen, (30, 34, 60) if hov else (16, 17, 32), rect, border_radius=6)
                pygame.draw.rect(self.screen, CYAN if hov else (55, 60, 120), rect, 1, border_radius=6)
                lt = fnt_cred.render(label, True, WHITE if hov else LIGHT_GRAY)
                self.screen.blit(lt, (rect.centerx - lt.get_width() // 2,
                                       rect.centery - lt.get_height() // 2))

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
