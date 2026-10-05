"""game/ui.py
UI widgets and overlays: InputBox, PauseMenu, and drawing helpers.
"""
import pygame
import constants
from settings import Settings
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
    def __init__(self, x, y, w, h, placeholder="Enter callsign...", password=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = ""
        self.ph   = placeholder
        self.password = password
        self.show_password = False
        self.focused = False
        self.select_all = False
        self.font = pygame.font.SysFont("consolas", 26)
        self.tick = 0

    @property
    def eye_rect(self):
        return pygame.Rect(self.rect.right - 42, self.rect.y + 7, 34, self.rect.height - 14)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.password and self.eye_rect.collidepoint(event.pos):
                self.show_password = not self.show_password
                self.focused = True
                self.select_all = False
                return None
            self.focused = self.rect.collidepoint(event.pos)
            self.select_all = False
            return None

        if not self.focused:
            return None

        if event.type == pygame.KEYDOWN:
            if event.mod & pygame.KMOD_CTRL and event.key == pygame.K_a:
                self.select_all = True
                return None
            if event.key == pygame.K_RETURN:
                return self.text
            elif event.key == pygame.K_BACKSPACE:
                if self.select_all:
                    self.text = ""
                    self.select_all = False
                else:
                    self.text = self.text[:-1]
            elif len(self.text) < 30 and event.unicode.isprintable():
                if self.select_all:
                    self.text = ""
                    self.select_all = False
                self.text += event.unicode
            return None
        return None

    def draw(self, surface):
        self.tick += 1
        draw_glow_rect(surface, (30, 100, 255), self.rect, radius=8, layers=4 if self.focused else 2)
        pygame.draw.rect(surface, CYAN if self.focused else (55, 60, 120), self.rect, 2, border_radius=8)
        disp = self.text if self.text else self.ph
        if self.password and self.text and not self.show_password:
            disp = "*" * len(self.text)
        col  = WHITE if self.text else GRAY
        ts   = self.font.render(disp, True, col)
        ty   = self.rect.centery - ts.get_height() // 2
        text_x = self.rect.x + 12
        if self.select_all and self.text:
            selection = pygame.Rect(text_x - 3, ty - 2, ts.get_width() + 6, ts.get_height() + 4)
            pygame.draw.rect(surface, (74, 154, 255), selection, border_radius=3)
        surface.blit(ts, (self.rect.x + 12, ty))
        if self.password:
            eye = self.eye_rect
            pygame.draw.ellipse(surface, LIGHT_GRAY, eye.inflate(-12, -12), 2)
            pygame.draw.circle(surface, CYAN if self.show_password else LIGHT_GRAY, eye.center, 4)
        if self.text and not self.select_all and self.tick % 60 < 30:
            cx = self.rect.x + 12 + self.font.size(disp)[0] + 2
            pygame.draw.line(surface, WHITE, (cx, ty + 2), (cx, ty + ts.get_height() - 2), 2)


# ── Pause Menu ────────────────────────────────────────────────────────────────
class PauseMenu:
    _OPTIONS = ['CONTINUE', 'LEADERBOARD', 'DASHBOARD', 'SETTINGS']

    def __init__(self, screen, audio, db=None):
        self.screen       = screen
        self.audio        = audio
        self.db           = db
        self.settings     = Settings()
        self.settings.load()
        self.state        = 'main'   # 'main' | 'settings'
        self.sel          = 0
        self.sfx_drag     = False
        self.music_drag   = False
        self.mobile_controls = bool(self.settings.get('mobile_controls', True))

        self.fnt_ttl = pygame.font.SysFont("consolas", 38, bold=True)
        self.fnt_btn = pygame.font.SysFont("consolas", 23, bold=True)
        self.fnt_lbl = pygame.font.SysFont("consolas", 19)
        self.fnt_sm  = pygame.font.SysFont("consolas", 15)

    # ── Button / slider geometry ──────────────────────────────────────────────
    def _btn_rects(self):
        cx, cy = constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2
        return [pygame.Rect(cx - 125, cy - 48 + i * 56, 250, 44)
                for i in range(len(self._OPTIONS))]

    def _settings_panel_rect(self):
        width = min(452, constants.SCREEN_WIDTH - 12)
        height = min(464, constants.SCREEN_HEIGHT - 12)
        return pygame.Rect(
            (constants.SCREEN_WIDTH - width) // 2,
            (constants.SCREEN_HEIGHT - height) // 2,
            width,
            height,
        )

    def _slider_rects(self):
        panel = self._settings_panel_rect()
        scale = min(panel.width / 452, panel.height / 464)
        cx = panel.centerx
        bar_width = min(int(338 * scale), panel.width - int(48 * scale))
        bar_height = max(8, int(16 * scale))
        def scaled(value):
            return int(value * scale)

        return {
            'sfx_bar': pygame.Rect(cx - bar_width // 2, panel.y + scaled(134),
                                   bar_width, bar_height),
            'music_bar': pygame.Rect(cx - bar_width // 2, panel.y + scaled(226),
                                     bar_width, bar_height),
            'mobile_toggle': pygame.Rect(
                panel.right - scaled(102), panel.y + scaled(275),
                scaled(66), scaled(34),
            ),
            'back': pygame.Rect(
                cx - scaled(106), panel.y + scaled(340), scaled(212), scaled(48),
            ),
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
            elif sliders['mobile_toggle'].collidepoint(event.pos):
                self._toggle_mobile_controls()
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

    def _toggle_mobile_controls(self):
        self.settings.load()
        self.mobile_controls = not self.settings.get('mobile_controls', True)
        self.settings.set('mobile_controls', self.mobile_controls)
        self.settings.save()

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
        panel = self._settings_panel_rect()
        scale = min(panel.width / 452, panel.height / 464)
        def scaled(value):
            return int(value * scale)

        pygame.draw.rect(self.screen, (12, 12, 26), panel, border_radius=12)
        pygame.draw.rect(self.screen, (70, 75, 140), panel, max(1, scaled(2)), border_radius=12)

        title_font = pygame.font.SysFont("consolas", max(24, scaled(40)), bold=True)
        title = title_font.render("SETTINGS", True, YELLOW)
        self.screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + scaled(14)))
        pygame.draw.line(self.screen, (55, 60, 120),
                         (panel.x + scaled(20), panel.y + scaled(74)),
                         (panel.right - scaled(20), panel.y + scaled(74)), 1)

        sliders = self._slider_rects()

        # Keep labels and values on one line while leaving the sliders full width.
        label_font = pygame.font.SysFont("consolas", max(13, scaled(20)))
        sfx_label = label_font.render("SFX VOLUME", True, CYAN)
        sfx_value = label_font.render(f"{int(self.audio.sfx_vol * 100)}%", True, CYAN)
        self.screen.blit(sfx_label, (panel.x + scaled(106), panel.y + scaled(96)))
        self.screen.blit(sfx_value, (panel.right - scaled(158), panel.y + scaled(96)))
        _draw_slider_bar(self.screen, sliders['sfx_bar'], self.audio.sfx_vol, CYAN)

        music_label = label_font.render("MUSIC VOLUME", True, PURPLE)
        music_value = label_font.render(f"{int(self.audio.music_vol * 100)}%", True, PURPLE)
        self.screen.blit(music_label, (panel.x + scaled(106), panel.y + scaled(188)))
        self.screen.blit(music_value, (panel.right - scaled(158), panel.y + scaled(188)))
        _draw_slider_bar(self.screen, sliders['music_bar'], self.audio.music_vol, PURPLE)

        # Keep the setting label separate from its switch.
        toggle = sliders['mobile_toggle']
        toggle_font = pygame.font.SysFont("consolas", max(11, scaled(16)))
        label = toggle_font.render("MOBILE CONTROLS", True, WHITE)
        label_x = max(panel.x + scaled(20), toggle.x - label.get_width() - scaled(20))
        self.screen.blit(label, (label_x, toggle.centery - label.get_height() // 2))
        toggle_bg = (30, 190, 115) if self.mobile_controls else (58, 62, 82)
        toggle_border = (100, 255, 170) if self.mobile_controls else (120, 130, 160)
        pygame.draw.rect(self.screen, toggle_bg, toggle, border_radius=toggle.height // 2)
        pygame.draw.rect(self.screen, toggle_border, toggle, max(1, scaled(2)),
                         border_radius=toggle.height // 2)
        knob_size = max(16, scaled(26))
        knob = pygame.Rect(toggle.x + scaled(4), toggle.centery - knob_size // 2,
                           knob_size, knob_size)
        if self.mobile_controls:
            knob.x = toggle.right - knob.width - scaled(4)
        pygame.draw.ellipse(self.screen, WHITE, knob)

        br = sliders['back']
        pygame.draw.rect(self.screen, (20, 22, 40), br, border_radius=scaled(9))
        pygame.draw.rect(self.screen, (55, 60, 120), br, max(1, scaled(2)),
                         border_radius=scaled(9))
        back_font = pygame.font.SysFont("consolas", max(13, scaled(20)))
        bt = back_font.render("<  BACK", True, LIGHT_GRAY)
        self.screen.blit(bt, (br.centerx - bt.get_width() // 2,
                              br.centery - bt.get_height() // 2))

        hint = pygame.font.SysFont("consolas", max(10, scaled(15))).render(
            "Drag sliders to adjust   |   ESC = Back", True, GRAY
        )
        self.screen.blit(hint, (panel.centerx - hint.get_width() // 2,
                                panel.y + scaled(414)))
