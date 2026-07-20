"""game/ui.py
UI widgets and overlays: InputBox, PauseMenu, and drawing helpers.
"""
import pygame
import constants
from constants import (
    CYAN, WHITE, GRAY, LIGHT_GRAY, DARK_GRAY, YELLOW, PURPLE,
    draw_glow_rect, draw_text_center
)

# ── Standalone Audio Slider Renderer ──────────────────────────────────────────
def _draw_slider_bar(surface, bar, val, color):
    """Module-level slider renderer, shared by PauseMenu's settings tab and
    the standalone AudioSettingsScreen so the visuals stay in sync."""
    pygame.draw.rect(surface, DARK_GRAY, bar, border_radius=4)
    fill = pygame.Rect(bar.x, bar.y, int(bar.width * val), bar.height)
    if fill.width > 0:
        pygame.draw.rect(surface, color, fill, border_radius=4)
    hx = bar.x + int(bar.width * val)
    pygame.draw.circle(surface, WHITE, (hx, bar.centery), 9)
    pygame.draw.circle(surface, color, (hx, bar.centery), 7)


# ── InputBox ──────────────────────────────────────────────────────────────────
class InputBox:
    def __init__(self, x, y, w, h, placeholder="Enter callsign..."):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = ""
        self.ph   = placeholder
        self.font = pygame.font.SysFont("consolas", 26)
        self.tick = 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                return self.text
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif len(self.text) < 30 and event.unicode.isprintable():
                self.text += event.unicode
        return None

    def draw(self, surface):
        self.tick += 1
        draw_glow_rect(surface, (30, 100, 255), self.rect, radius=8, layers=4)
        pygame.draw.rect(surface, CYAN, self.rect, 2, border_radius=8)
        disp = self.text if self.text else self.ph
        col  = WHITE if self.text else GRAY
        ts   = self.font.render(disp, True, col)
        ty   = self.rect.centery - ts.get_height() // 2
        surface.blit(ts, (self.rect.x + 12, ty))
        if self.text and self.tick % 60 < 30:
            cx = self.rect.x + 12 + self.font.size(self.text)[0] + 2
            pygame.draw.line(surface, WHITE, (cx, ty + 2), (cx, ty + ts.get_height() - 2), 2)


# ── Pause Menu ────────────────────────────────────────────────────────────────
class PauseMenu:
    _OPTIONS = ['CONTINUE', 'LEADERBOARD', 'DASHBOARD', 'SETTINGS']

    def __init__(self, screen, audio, db=None):
        self.screen       = screen
        self.audio        = audio
        self.db           = db
        self.state        = 'main'   # 'main' | 'settings'
        self.sel          = 0
        self.sfx_drag     = False
        self.music_drag   = False

        self.fnt_ttl = pygame.font.SysFont("consolas", 38, bold=True)
        self.fnt_btn = pygame.font.SysFont("consolas", 23, bold=True)
        self.fnt_lbl = pygame.font.SysFont("consolas", 19)
        self.fnt_sm  = pygame.font.SysFont("consolas", 15)

    # ── Button / slider geometry ──────────────────────────────────────────────
    def _btn_rects(self):
        cx, cy = constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2
        return [pygame.Rect(cx - 125, cy - 48 + i * 56, 250, 44)
                for i in range(len(self._OPTIONS))]

    def _slider_rects(self):
        cx, cy = constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2
        bw = 270
        return {
            'sfx_bar':   pygame.Rect(cx - bw // 2, cy - 18, bw, 16),
            'music_bar': pygame.Rect(cx - bw // 2, cy + 44, bw, 16),
            'back':      pygame.Rect(cx - 85,       cy + 96, 170, 40),
        }

    # ── Event handling ────────────────────────────────────────────────────────
    def handle_event(self, event):
        """Returns 'continue', 'dashboard', or None."""
        return self._main_event(event) if self.state == 'main' else self._settings_event(event)

    def _main_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return 'continue'
            elif event.key == pygame.K_UP:
                self.sel = (self.sel - 1) % len(self._OPTIONS)
            elif event.key == pygame.K_DOWN:
                self.sel = (self.sel + 1) % len(self._OPTIONS)
            elif event.key == pygame.K_RETURN:
                return self._activate(self.sel)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, r in enumerate(self._btn_rects()):
                if r.collidepoint(event.pos):
                    return self._activate(i)
        elif event.type == pygame.MOUSEMOTION:
            for i, r in enumerate(self._btn_rects()):
                if r.collidepoint(event.pos):
                    self.sel = i
        return None

    def _activate(self, idx):
        opt = self._OPTIONS[idx]
        if opt == 'CONTINUE':     return 'continue'
        if opt == 'LEADERBOARD':  return 'leaderboard'
        if opt == 'DASHBOARD':    return 'dashboard'
        if opt == 'SETTINGS':     self.state = 'settings'
        return None

    def _settings_event(self, event):
        sliders = self._slider_rects()
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.state = 'main'
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if sliders['sfx_bar'].collidepoint(event.pos):
                self.sfx_drag = True
                self._update_vol('sfx', event.pos[0], sliders['sfx_bar'])
            elif sliders['music_bar'].collidepoint(event.pos):
                self.music_drag = True
                self._update_vol('music', event.pos[0], sliders['music_bar'])
            elif sliders['back'].collidepoint(event.pos):
                self.state = 'main'
        elif event.type == pygame.MOUSEBUTTONUP:
            self.sfx_drag = self.music_drag = False
        elif event.type == pygame.MOUSEMOTION:
            if self.sfx_drag:
                self._update_vol('sfx',   event.pos[0], sliders['sfx_bar'])
            if self.music_drag:
                self._update_vol('music', event.pos[0], sliders['music_bar'])
        return None

    def _update_vol(self, kind, mx, bar):
        v = max(0.0, min(1.0, (mx - bar.x) / bar.width))
        if kind == 'sfx':   self.audio.set_sfx_vol(v)
        else:               self.audio.set_music_vol(v)

    # ── Drawing ───────────────────────────────────────────────────────────────
    def draw(self):
        ov = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 162))
        self.screen.blit(ov, (0, 0))
        if self.state == 'main':
            self._draw_main()
        else:
            self._draw_settings()

    def _draw_main(self):
        cy      = constants.SCREEN_HEIGHT // 2
        btns    = self._btn_rects()
        panel_top    = cy - 128
        panel_bottom = btns[-1].bottom + 34
        panel = pygame.Rect(constants.SCREEN_WIDTH // 2 - 165, panel_top, 330, panel_bottom - panel_top)
        pygame.draw.rect(self.screen, (12, 12, 26), panel, border_radius=12)
        pygame.draw.rect(self.screen, (70, 75, 140), panel, 2, border_radius=12)

        draw_text_center(self.screen, "PAUSED", self.fnt_ttl, YELLOW,
                         constants.SCREEN_HEIGHT // 2 - 118)
        pygame.draw.line(self.screen, (55, 60, 120),
                         (constants.SCREEN_WIDTH // 2 - 140, constants.SCREEN_HEIGHT // 2 - 70),
                         (constants.SCREEN_WIDTH // 2 + 140, constants.SCREEN_HEIGHT // 2 - 70), 1)

        for i, (rect, opt) in enumerate(zip(btns, self._OPTIONS)):
            sel    = (i == self.sel)
            bg     = (38, 96, 200) if sel else (20, 22, 40)
            border = CYAN if sel else (55, 60, 120)
            pygame.draw.rect(self.screen, bg,     rect, border_radius=8)
            pygame.draw.rect(self.screen, border, rect, 2, border_radius=8)
            ts = self.fnt_btn.render(opt, True, WHITE if sel else LIGHT_GRAY)
            self.screen.blit(ts, (rect.centerx - ts.get_width() // 2,
                                  rect.centery - ts.get_height() // 2))

        ht = self.fnt_sm.render("ESC = Resume   ENTER = Select   Arrow Keys = Navigate",
                                True, GRAY)
        self.screen.blit(ht, (constants.SCREEN_WIDTH // 2 - ht.get_width() // 2, panel_bottom + 14))

    def _draw_settings(self):
        panel = pygame.Rect(constants.SCREEN_WIDTH // 2 - 185, constants.SCREEN_HEIGHT // 2 - 158, 370, 320)
        pygame.draw.rect(self.screen, (12, 12, 26), panel, border_radius=12)
        pygame.draw.rect(self.screen, (70, 75, 140), panel, 2, border_radius=12)

        draw_text_center(self.screen, "SETTINGS", self.fnt_ttl, YELLOW,
                         constants.SCREEN_HEIGHT // 2 - 148)
        pygame.draw.line(self.screen, (55, 60, 120),
                         (constants.SCREEN_WIDTH // 2 - 160, constants.SCREEN_HEIGHT // 2 - 104),
                         (constants.SCREEN_WIDTH // 2 + 160, constants.SCREEN_HEIGHT // 2 - 104), 1)

        sliders = self._slider_rects()

        # SFX
        sl = self.fnt_lbl.render(f"SFX VOLUME    {int(self.audio.sfx_vol * 100):>3}%", True, CYAN)
        self.screen.blit(sl, (constants.SCREEN_WIDTH // 2 - sl.get_width() // 2,
                              constants.SCREEN_HEIGHT // 2 - 56))
        _draw_slider_bar(self.screen, sliders['sfx_bar'], self.audio.sfx_vol, CYAN)

        # Music
        ml = self.fnt_lbl.render(f"MUSIC VOLUME  {int(self.audio.music_vol * 100):>3}%", True, PURPLE)
        self.screen.blit(ml, (constants.SCREEN_WIDTH // 2 - ml.get_width() // 2,
                              constants.SCREEN_HEIGHT // 2 + 6))
        _draw_slider_bar(self.screen, sliders['music_bar'], self.audio.music_vol, PURPLE)

        br = sliders['back']
        pygame.draw.rect(self.screen, (20, 22, 40), br, border_radius=8)
        pygame.draw.rect(self.screen, (55, 60, 120), br, 2, border_radius=8)
        bt = self.fnt_lbl.render("< BACK", True, LIGHT_GRAY)
        self.screen.blit(bt, (br.centerx - bt.get_width() // 2,
                              br.centery - bt.get_height() // 2))

        hint = self.fnt_sm.render("Drag sliders to adjust   |   ESC = Back", True, GRAY)
        self.screen.blit(hint, (constants.SCREEN_WIDTH // 2 - hint.get_width() // 2,
                                constants.SCREEN_HEIGHT // 2 + 148))
