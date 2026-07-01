import pygame
import random
import sys
import math
from datetime import datetime
from database import Database
import config

# Audio must be pre-initialised before pygame.init()
pygame.mixer.pre_init(44100, -16, 2, 1024)
pygame.init()

# ── Constants ─────────────────────────────────────────────────────────────────
SCREEN_WIDTH  = config.GAME_CONFIG['screen_width']
SCREEN_HEIGHT = config.GAME_CONFIG['screen_height']
PLAYER_W, PLAYER_H = 64, 52
ENEMY_W,  ENEMY_H  = 36, 28
BULLET_W, BULLET_H = 4,  14
POWERUP_SIZE        = 24

import os as _os
_ASSET_DIR = _os.path.join(_os.path.dirname(__file__), 'assets')

def _load_img(fname, size, colorkey=None, threshold=50):
    """Load and scale an image.  If colorkey is given, pixels close to that
    colour (within `threshold` distance) are made fully transparent using
    per-pixel alpha so anti-aliased edges are also removed cleanly."""
    path = _os.path.join(_ASSET_DIR, fname)
    try:
        raw  = pygame.image.load(path).convert_alpha()
        img  = pygame.transform.smoothscale(raw, size)
        if colorkey is not None:
            try:
                import numpy as np
                arr   = pygame.surfarray.pixels3d(img)   # shape (w,h,3)
                alpha = pygame.surfarray.pixels_alpha(img)  # shape (w,h)
                kr, kg, kb = colorkey
                dist = ( arr[:,:,0].astype(np.int32) - kr )**2 + \
                       ( arr[:,:,1].astype(np.int32) - kg )**2 + \
                       ( arr[:,:,2].astype(np.int32) - kb )**2
                alpha[ dist < threshold**2 * 3 ] = 0
                del arr, alpha           # unlock the surface
            except ImportError:
                # numpy not available – fall back to simple colorkey
                img.set_colorkey(colorkey, pygame.RLEACCEL)
        return img
    except Exception as e:
        print(f"[WARN] Could not load {fname}: {e}")
        return None



# Palette
BLACK      = (  0,   0,   0)
WHITE      = (255, 255, 255)
GREEN      = ( 80, 255,  80)
LIME       = ( 50, 220,  50)
DARK_GREEN = (  0,  80,   0)
RED        = (220,  40,  40)
YELLOW     = (255, 220,  40)
CYAN       = ( 40, 230, 230)
PURPLE     = (180,  60, 230)
ORANGE     = (255, 140,  30)
GRAY       = ( 80,  80,  80)
LIGHT_GRAY = (180, 180, 180)
DARK_GRAY  = ( 28,  28,  40)
NAVY       = (  6,   6,  20)

# ── Helpers ───────────────────────────────────────────────────────────────────
def clamp_color(r, g, b):
    return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))

def draw_text_center(surface, text, font, color, y, shadow=True):
    if shadow:
        sh = font.render(text, True, BLACK)
        surface.blit(sh, (SCREEN_WIDTH // 2 - sh.get_width() // 2 + 2, y + 2))
    surf = font.render(text, True, color)
    surface.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2, y))

def draw_glow_rect(surface, color, rect, radius=8, layers=3):
    for i in range(layers, 0, -1):
        gs = pygame.Surface((rect.width + i * 4, rect.height + i * 4), pygame.SRCALPHA)
        a  = max(0, 55 - i * 16)
        pygame.draw.rect(gs, (*color, a), gs.get_rect(), border_radius=radius + i)
        surface.blit(gs, (rect.x - i * 2, rect.y - i * 2))
    pygame.draw.rect(surface, color, rect, border_radius=radius)

# ── Audio Manager ─────────────────────────────────────────────────────────────
class AudioManager:
    """Generates retro SFX with numpy (graceful no-op if numpy missing)."""

    def __init__(self):
        self.sfx_vol   = 0.65
        self.music_vol = 0.35
        self.sounds    = {}
        self._init()

    def _init(self):
        try:
            import numpy as np
            SR = 44100

            def sine(freq, dur, vol=1.0, decay=0.0):
                n = int(SR * dur)
                t = np.linspace(0, dur, n, endpoint=False)
                w = np.sin(2 * np.pi * freq * t)
                if decay:
                    w *= np.exp(-decay * np.linspace(0, 1, n))
                w = np.clip(w * vol * 32767, -32767, 32767).astype(np.int16)
                return np.column_stack([w, w])

            def noise(dur, vol=0.5):
                n = int(SR * dur)
                w = np.random.uniform(-1, 1, n)
                w *= np.exp(-np.linspace(0, 6, n))
                w = np.clip(w * vol * 32767, -32767, 32767).astype(np.int16)
                return np.column_stack([w, w])

            def cat(*arrs):
                return np.concatenate(arrs)

            def boom(dur, vol=0.6):
                n = int(SR * dur)
                t = np.linspace(0, dur, n, endpoint=False)
                w = np.random.uniform(-1, 1, n)  # white noise
                freqs = np.linspace(150, 40, n)  # low rumble dropping in pitch
                rumble = np.sin(2 * np.pi * freqs * t)
                env = np.exp(-np.linspace(0, 6, n))  # fade out
                mix = (w * 0.6 + rumble * 0.6) * env
                mix = np.clip(mix * vol * 32767, -32767, 32767).astype(np.int16)
                return np.column_stack([mix, mix])

            def make(arr):
                return pygame.sndarray.make_sound(arr)

            self.sounds['shoot']   = make(sine(900, 0.06, 0.35, decay=10))
            self.sounds['explode'] = make(boom(0.4, 0.7))
            self.sounds['powerup'] = make(cat(sine(380, 0.06, 0.4), sine(570, 0.06, 0.4), sine(860, 0.10, 0.4)))
            self.sounds['hit']     = make(cat(sine(130, 0.07, 0.5, decay=12), noise(0.08, 0.3)))
            self.sounds['gameover']= make(cat(sine(380, 0.15, 0.4), sine(280, 0.15, 0.4), sine(190, 0.28, 0.4)))
            self.sounds['victory'] = make(cat(sine(400, 0.09, 0.4), sine(500, 0.09, 0.4),
                                             sine(640, 0.09, 0.4), sine(800, 0.18, 0.4)))

            # Simple looping BGM melody
            dur = 0.22
            scale = [220, 247, 262, 294, 330, 370, 392, 440]
            pattern = [0, 2, 4, 7, 4, 2, 0, 0, 3, 5, 7, 5, 3, 0, 2, 4]
            beats   = []
            for idx in pattern:
                note = scale[idx % len(scale)]
                b    = sine(note, dur * 0.65, 0.18, decay=4)
                pad  = np.zeros((int(SR * dur * 0.35), 2), dtype=np.int16)
                beats.append(cat(b, pad))
            self.sounds['bgm'] = make(cat(*beats))

            self._apply_vols()
            self.play_bgm()
            print("[OK] Audio initialised.")

        except Exception as e:
            print(f"[AUDIO] Skipping audio: {e}")
            self.sounds = {}

    def _apply_vols(self):
        for name, snd in self.sounds.items():
            snd.set_volume(self.music_vol if name == 'bgm' else self.sfx_vol)

    def play(self, name):
        if name in self.sounds:
            self.sounds[name].play()

    def set_sfx_vol(self, v):
        self.sfx_vol = max(0.0, min(1.0, v))
        for name, snd in self.sounds.items():
            if name != 'bgm':
                snd.set_volume(self.sfx_vol)

    def set_music_vol(self, v):
        self.music_vol = max(0.0, min(1.0, v))
        if 'bgm' in self.sounds:
            self.sounds['bgm'].set_volume(self.music_vol)

    def stop_bgm(self):
        if 'bgm' in self.sounds:
            self.sounds['bgm'].stop()

    def play_bgm(self):
        if 'bgm' in self.sounds:
            self.sounds['bgm'].stop()
            self.sounds['bgm'].play(loops=-1)

# ── Pause Menu ────────────────────────────────────────────────────────────────
class PauseMenu:
    _OPTIONS = ['CONTINUE', 'DASHBOARD', 'SETTINGS']

    def __init__(self, screen, audio):
        self.screen       = screen
        self.audio        = audio
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
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        return [pygame.Rect(cx - 125, cy - 48 + i * 56, 250, 44)
                for i in range(len(self._OPTIONS))]

    def _slider_rects(self):
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
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
        if opt == 'CONTINUE':   return 'continue'
        if opt == 'DASHBOARD':  return 'dashboard'
        if opt == 'SETTINGS':   self.state = 'settings'
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
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 162))
        self.screen.blit(ov, (0, 0))
        if self.state == 'main':
            self._draw_main()
        else:
            self._draw_settings()

    def _draw_main(self):
        panel = pygame.Rect(SCREEN_WIDTH // 2 - 165, SCREEN_HEIGHT // 2 - 128, 330, 270)
        pygame.draw.rect(self.screen, (12, 12, 26), panel, border_radius=12)
        pygame.draw.rect(self.screen, (70, 75, 140), panel, 2, border_radius=12)

        draw_text_center(self.screen, "PAUSED", self.fnt_ttl, YELLOW,
                         SCREEN_HEIGHT // 2 - 118)
        pygame.draw.line(self.screen, (55, 60, 120),
                         (SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT // 2 - 70),
                         (SCREEN_WIDTH // 2 + 140, SCREEN_HEIGHT // 2 - 70), 1)

        for i, (rect, opt) in enumerate(zip(self._btn_rects(), self._OPTIONS)):
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
        self.screen.blit(ht, (SCREEN_WIDTH // 2 - ht.get_width() // 2,
                              SCREEN_HEIGHT // 2 + 148))

    def _draw_settings(self):
        panel = pygame.Rect(SCREEN_WIDTH // 2 - 185, SCREEN_HEIGHT // 2 - 158, 370, 320)
        pygame.draw.rect(self.screen, (12, 12, 26), panel, border_radius=12)
        pygame.draw.rect(self.screen, (70, 75, 140), panel, 2, border_radius=12)

        draw_text_center(self.screen, "SETTINGS", self.fnt_ttl, YELLOW,
                         SCREEN_HEIGHT // 2 - 148)
        pygame.draw.line(self.screen, (55, 60, 120),
                         (SCREEN_WIDTH // 2 - 160, SCREEN_HEIGHT // 2 - 104),
                         (SCREEN_WIDTH // 2 + 160, SCREEN_HEIGHT // 2 - 104), 1)

        sliders = self._slider_rects()

        # SFX
        sl = self.fnt_lbl.render(f"SFX VOLUME    {int(self.audio.sfx_vol * 100):>3}%", True, CYAN)
        self.screen.blit(sl, (SCREEN_WIDTH // 2 - sl.get_width() // 2,
                              SCREEN_HEIGHT // 2 - 56))
        self._draw_slider(sliders['sfx_bar'], self.audio.sfx_vol, CYAN)

        # Music
        ml = self.fnt_lbl.render(f"MUSIC VOLUME  {int(self.audio.music_vol * 100):>3}%", True, PURPLE)
        self.screen.blit(ml, (SCREEN_WIDTH // 2 - ml.get_width() // 2,
                              SCREEN_HEIGHT // 2 + 6))
        self._draw_slider(sliders['music_bar'], self.audio.music_vol, PURPLE)

        br = sliders['back']
        pygame.draw.rect(self.screen, (20, 22, 40), br, border_radius=8)
        pygame.draw.rect(self.screen, (55, 60, 120), br, 2, border_radius=8)
        bt = self.fnt_lbl.render("< BACK", True, LIGHT_GRAY)
        self.screen.blit(bt, (br.centerx - bt.get_width() // 2,
                              br.centery - bt.get_height() // 2))

        hint = self.fnt_sm.render("Drag sliders to adjust   |   ESC = Back", True, GRAY)
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2,
                                SCREEN_HEIGHT // 2 + 148))

    def _draw_slider(self, bar, val, color):
        pygame.draw.rect(self.screen, DARK_GRAY, bar, border_radius=4)
        fill = pygame.Rect(bar.x, bar.y, int(bar.width * val), bar.height)
        if fill.width > 0:
            pygame.draw.rect(self.screen, color, fill, border_radius=4)
        hx = bar.x + int(bar.width * val)
        pygame.draw.circle(self.screen, WHITE, (hx, bar.centery), 9)
        pygame.draw.circle(self.screen, color, (hx, bar.centery), 7)

# ── Classic pixel-art alien grids ─────────────────────────────────────────────
_GRIDS = [
    # Crab (bottom rows) – cyan
    ["  X     X  ", "   X   X   ", "  XXXXXXX  ",
     " XX XXX XX ", "XXXXXXXXXXX", "X XXXXXXX X",
     "X X     X X", "   XX XX   "],
    # Squid (middle rows) – green
    ["    XXX    ", "  XXXXXXX  ", " XXXXXXXXX ",
     "XXX XXX XXX","XXXXXXXXXXX", "  XX   XX  ",
     " X  X X  X ", "X         X"],
    # UFO (top rows) – purple
    ["   XXXXX   ", " XXXXXXXXX ", "XXXXXXXXXXX",
     "XX X X X XX","XXXXXXXXXXX", "  XX   XX  ",
     " X       X ", "           "],
]
_ALIEN_PALETTES = [
    (CYAN,   clamp_color( 0, 150, 150)),
    (GREEN,  clamp_color( 0, 155,   0)),
    (PURPLE, clamp_color(95,   0, 155)),
]
CELL = 3

def _make_alien(grid, col, dark):
    cols = max(len(r) for r in grid)
    surf = pygame.Surface((cols * CELL, len(grid) * CELL), pygame.SRCALPHA)
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch == 'X':
                c2 = col if (r + c) % 2 == 0 else dark
                pygame.draw.rect(surf, c2, (c * CELL, r * CELL, CELL, CELL))
    return surf

_ALIEN_SURFS = [_make_alien(g, col, dark) for g, (col, dark) in zip(_GRIDS, _ALIEN_PALETTES)]

# ── Game images (loaded lazily after display init) ────────────────────────────
_IMG_PLAYER_SHIP   = None
_IMG_BOSS_CAPYBARA = None
_IMG_BOSS_ANIMAL   = None

def _load_game_images():
    """Call this AFTER pygame.display.set_mode() so convert_alpha() works."""
    global _IMG_PLAYER_SHIP, _IMG_BOSS_CAPYBARA, _IMG_BOSS_ANIMAL
    # Player ship has black background; boss images use magenta chroma-key
    _IMG_PLAYER_SHIP   = _load_img('player_ship.png',   (PLAYER_W + 20, PLAYER_H + 20), colorkey=(0, 0, 0))
    _IMG_BOSS_CAPYBARA = _load_img('capybara_boss.png', (160, 130),                      colorkey=(255, 0, 255))
    _IMG_BOSS_ANIMAL   = _load_img('animal_boss.png',   (160, 130),                      colorkey=(255, 0, 255))
    if _IMG_PLAYER_SHIP:   print("[OK] player_ship.png loaded")
    if _IMG_BOSS_CAPYBARA: print("[OK] capybara_boss.png loaded")
    if _IMG_BOSS_ANIMAL:   print("[OK] animal_boss.png loaded")

# ── PowerUp Pixel-Art Icons ──────────────────────────────────────────────────
def _make_icon(grid, color):
    rows = len(grid)
    cols = max(len(r) for r in grid)
    cell_sz = 2
    surf = pygame.Surface((cols * cell_sz, rows * cell_sz), pygame.SRCALPHA)
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch == 'X':
                pygame.draw.rect(surf, color, (c * cell_sz, r * cell_sz, cell_sz, cell_sz))
    return surf

_ICON_SHIELD = _make_icon([
    "  XXXX  ",
    " XXXXXX ",
    "XX    XX",
    "XX    XX",
    "XX    XX",
    " XX  XX ",
    "  XXXX  ",
    "   XX   "
], WHITE)

_ICON_MULTI = _make_icon([
    "  X X X  ",
    "  X X X  ",
    "  X X X  ",
    "  X X X  ",
    "  X X X  ",
    "  X X X  ",
    "   X X   ",
    "    X    "
], WHITE)

_ICON_HEART = _make_icon([
    " XX  XX ",
    "XXXXXXXX",
    "XXXXXXXX",
    "XXXXXXXX",
    " XXXXXX ",
    "  XXXX  ",
    "   XX   ",
    "        "
], WHITE)

_POWERUP_ICONS = {
    'shield':    _ICON_SHIELD,
    'multishot': _ICON_MULTI,
    'heart':     _ICON_HEART
}

# ─────────────────────────────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────────────────────────────
class ProfileScreen:
    def __init__(self, screen, db, audio=None):
        self.screen  = pygame.display.get_surface()
        self.db      = db
        self.audio   = audio
        self.input   = InputBox(SCREEN_WIDTH // 2 - 210, SCREEN_HEIGHT // 2 + 20, 420, 46)
        self.error   = ""
        self.etimer  = 0
        self.clock   = pygame.time.Clock()
        self.tick    = 0
        self.stars   = [[random.randint(0, SCREEN_WIDTH),
                         random.randint(0, SCREEN_HEIGHT),
                         random.uniform(0.3, 1.4),
                         random.randint(1, 2)] for _ in range(130)]
        self.players = self._load_players()

    def _load_players(self):
        if self.db and self.db.connection:
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
            if s[1] > SCREEN_HEIGHT:
                s[1] = 0
                s[0] = random.randint(0, SCREEN_WIDTH)
            b = random.randint(140, 240)
            pygame.draw.circle(self.screen, (b, b, b), (int(s[0]), int(s[1])), s[3])

    def _draw_alien_parade(self):
        col_w = SCREEN_WIDTH // 4
        for i in range(4):
            surf  = _ALIEN_SURFS[i % 3]
            wave  = int(6 * abs(pygame.math.Vector2(0, 1).rotate(self.tick * 3 + i * 90).y))
            x     = i * col_w + col_w // 2 - surf.get_width() // 2
            s2    = surf.copy()
            s2.set_alpha(90 + int(55 * abs(pygame.math.Vector2(1, 0).rotate(self.tick * 2 + i * 60).x)))
            self.screen.blit(s2, (x, 178 + wave))

    def run(self):
        global SCREEN_WIDTH, SCREEN_HEIGHT
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
                             (SCREEN_WIDTH // 2 - 230, 164),
                             (SCREEN_WIDTH // 2 + 230, 164), 1)

            lbl = fnt_inst.render("ENTER CALLSIGN:", True, LIGHT_GRAY)
            self.screen.blit(lbl, (SCREEN_WIDTH // 2 - lbl.get_width() // 2,
                                   SCREEN_HEIGHT // 2 - 14))
            self.input.draw(self.screen)

            for i, n in enumerate(["New callsign  ->  creates a pilot profile",
                                    "Known callsign ->  loads your history"]):
                ns = fnt_inst.render(n, True, (115, 125, 155))
                self.screen.blit(ns, (SCREEN_WIDTH // 2 - ns.get_width() // 2,
                                     SCREEN_HEIGHT // 2 + 80 + i * 24))

            if self.players:
                ty = SCREEN_HEIGHT // 2 + 140
                ht = fnt_list.render("KNOWN PILOTS:", True, YELLOW)
                self.screen.blit(ht, (SCREEN_WIDTH // 2 - ht.get_width() // 2, ty))
                for j, p in enumerate(self.players[:5]):
                    match = self.input.text and p.lower().startswith(self.input.text.lower())
                    ps = fnt_list.render(f"  {p}", True, GREEN if match else LIGHT_GRAY)
                    self.screen.blit(ps, (SCREEN_WIDTH // 2 - ps.get_width() // 2,
                                         ty + 22 + j * 21))

            if self.etimer > 0:
                es = fnt_inst.render(self.error, True, RED)
                self.screen.blit(es, (SCREEN_WIDTH // 2 - es.get_width() // 2,
                                      SCREEN_HEIGHT // 2 + 72))
                self.etimer -= 1

            cs = fnt_cred.render("DEVELOPED BY: CABARDO, SONJEEV C.", True, (60, 65, 90))
            self.screen.blit(cs, (SCREEN_WIDTH // 2 - cs.get_width() // 2, SCREEN_HEIGHT - 26))

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    return None
                elif ev.type == pygame.VIDEORESIZE:
                    SCREEN_WIDTH, SCREEN_HEIGHT = ev.w, ev.h
                    self.screen = pygame.display.set_mode((ev.w, ev.h), pygame.RESIZABLE)
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

# ─────────────────────────────────────────────────────────────────────────────
class Player:
    W, H = PLAYER_W, PLAYER_H

    def __init__(self):
        self.x          = SCREEN_WIDTH // 2 - self.W // 2
        self.y          = SCREEN_HEIGHT - 72
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
        self.x = max(0, min(SCREEN_WIDTH - self.W, self.x + dx * self.speed))

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
        if self.shield or self.invincible:
            return False
        self.lives    -= 1
        self.invincible = True
        self.inv_timer  = 90
        return True

    def draw(self, screen):
        if self.invincible and self.inv_timer % 8 < 4:
            return
        cx = self.x + self.W // 2

        if self.shield:
            for i in range(3):
                alpha_surf = pygame.Surface((self.W * 2 + i*14, self.W * 2 + i*14), pygame.SRCALPHA)
                pygame.draw.ellipse(alpha_surf, (*CYAN, max(0, 80 - i * 25)), alpha_surf.get_rect(), 2)
                screen.blit(alpha_surf, (cx - alpha_surf.get_width()//2, self.y + self.H//2 - alpha_surf.get_height()//2))

        # Engine flame
        fh = 8 + (self.anim % 10) // 2
        flame_colors = [ORANGE, YELLOW, WHITE]
        for fi, fc in enumerate(flame_colors):
            fw = max(2, 10 - fi * 3)
            offset = fi * 1
            pygame.draw.polygon(screen, fc, [
                (self.x + 14 + offset, self.y + self.H - 2),
                (self.x + 20 - offset, self.y + self.H + fh - fi * 2),
                (self.x + 26 + offset, self.y + self.H - 2)])
            pygame.draw.polygon(screen, fc, [
                (self.x + self.W - 26 - offset, self.y + self.H - 2),
                (self.x + self.W - 20 + offset, self.y + self.H + fh - fi * 2),
                (self.x + self.W - 14 - offset, self.y + self.H - 2)])

        # Draw ship image or fallback polygon
        if _IMG_PLAYER_SHIP:
            img = _IMG_PLAYER_SHIP
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

# ─────────────────────────────────────────────────────────────────────────────
class Enemy:
    W, H = ENEMY_W, ENEMY_H

    def __init__(self, x, y, etype=0):
        self.x     = x
        self.y     = y
        self.target_y = y
        self.etype = etype % 3
        self.dir   = 1
        self.speed = config.GAME_CONFIG['enemy_speed']
        self.dn_timer = 0
        # Balanced firing: 60-160 frames between checks, 30% chance
        self.sh_timer = random.randint(60, 160)
        self.sh_cd    = 0
        self.anim     = 0
        self.surf     = _ALIEN_SURFS[self.etype]

    def update(self, _enemies):
        if self.y < self.target_y:
            self.y += 2
            return

        self.x        += self.speed * self.dir
        self.dn_timer  = max(0, self.dn_timer - 1)
        self.sh_cd     = max(0, self.sh_cd - 1)
        self.anim      = (self.anim + 1) % 30

        if self.x <= 0 or self.x >= SCREEN_WIDTH - self.W:
            self.dir      *= -1
            self.dn_timer  = 14

        if self.dn_timer > 0:
            self.y += 2

    def shoot(self):
        self.sh_timer -= 1
        if self.sh_timer <= 0 and self.sh_cd == 0:
            self.sh_timer = random.randint(60, 160)
            if random.random() < 0.30:      # 30% chance – feels active without being unfair
                self.sh_cd = 55
                return EnemyBullet(self.x + self.W // 2, self.y + self.H)
        return None

    def draw(self, screen):
        bob = 0 if self.anim < 15 else 2
        sw, sh = self.surf.get_width(), self.surf.get_height()
        screen.blit(self.surf,
                    (self.x + (self.W - sw) // 2,
                     self.y + (self.H - sh) // 2 + bob))

# ─────────────────────────────────────────────────────────────────────────────
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
            if trail_len == 0: continue
            w = BULLET_W * (i / float(trail_len))
            c = clamp_color(0, 150 + i * 20, 255)
            pygame.draw.rect(screen, c, (tx + (BULLET_W - w) / 2, ty, w, BULLET_H))
        
        # Glowing core laser
        rect = pygame.Rect(self.x - 2, self.y - 2, BULLET_W + 4, BULLET_H + 4)
        draw_glow_rect(screen, CYAN, rect, radius=6, layers=3)
        pygame.draw.rect(screen, WHITE, (self.x, self.y, BULLET_W, BULLET_H), border_radius=2)

# ─────────────────────────────────────────────────────────────────────────────
class EnemyBullet:
    def __init__(self, x, y):
        self.x    = x
        self.y    = y
        self.speed = 3      # visible, dangerous but dodgeable
        self.anim  = 0

    def update(self):
        self.y   += self.speed
        self.anim = (self.anim + 1) % 6

    def draw(self, screen):
        self.anim = (self.anim + 1) % 10
        r, g, b = (255, 100, 0) if self.anim >= 5 else (255, 30, 30)
        
        # Rocket/Laser capsule shape
        rect = pygame.Rect(self.x, self.y, 6, 18)
        draw_glow_rect(screen, (r, g, b), rect, radius=6, layers=3)
        pygame.draw.rect(screen, YELLOW, (self.x + 1, self.y + 2, 4, 14), border_radius=3)
        
        # Bright flare at the back of the rocket
        pygame.draw.circle(screen, WHITE, (self.x + 3, self.y + 2), 3)

# ─────────────────────────────────────────────────────────────────────────────
class Boss:
    W, H = 140, 90

    def __init__(self, max_hp=30, level=1):
        self.x = SCREEN_WIDTH // 2 - self.W // 2
        self.y = -120
        self.target_y = 60
        self.hp = max_hp
        self.max_hp = max_hp
        self.speed = 2.5
        self.dir = 1
        self.sh_timer = 60
        self.anim = 0
        self.level = level
        # Pick boss image based on level parity
        self.img = _IMG_BOSS_CAPYBARA if (level % 2 == 1) else _IMG_BOSS_ANIMAL

    def update(self):
        self.anim += 1
        if self.y < self.target_y:
            self.y += 2
            return
            
        self.x += self.speed * self.dir
        if self.x <= 20 or self.x >= SCREEN_WIDTH - self.W - 20:
            self.dir *= -1
            
        self.y = self.target_y + math.sin(self.anim * 0.05) * 15

    def shoot(self):
        if self.y < self.target_y: return []
        self.sh_timer -= 1
        if self.sh_timer <= 0:
            self.sh_timer = max(25, 60 - (self.max_hp - self.hp)) 
            cx = self.x + self.W // 2
            return [
                EnemyBullet(cx - 40, self.y + self.H),
                EnemyBullet(cx,      self.y + self.H + 10),
                EnemyBullet(cx + 40, self.y + self.H)
            ]
        return []

    def draw(self, screen):
        cx = self.x + self.W // 2
        cy = self.y + self.H // 2
        bob = int(math.sin(self.anim * 0.1) * 3)

        if self.img:
            # Draw boss image with bob effect
            screen.blit(self.img, (self.x, self.y + bob))
            # Perfectly centered circular aura
            iw, ih = 160, 130
            aura = pygame.Surface((iw, ih), pygame.SRCALPHA)
            glow_col = (255, 50, 50) if self.hp < self.max_hp // 3 else \
                       (255, 140, 0) if self.hp < self.max_hp * 0.6 else (180, 60, 230)
            
            radius = 55 + int(math.sin(self.anim * 0.2) * 5)
            center = (iw // 2, ih // 2)
            pygame.draw.circle(aura, (*glow_col, 150), center, radius, 4)
            pygame.draw.circle(aura, (*glow_col, 80), center, radius - 4, 2)
            screen.blit(aura, (self.x, self.y + bob))
        else:
            # Fallback drawn boss
            pygame.draw.ellipse(screen, (30, 30, 45), (self.x, self.y + bob, self.W, self.H))
            pygame.draw.ellipse(screen, PURPLE, (self.x, self.y + bob, self.W, self.H), 3)
            pygame.draw.ellipse(screen, CYAN, (self.x + 10, self.y + bob + 10, self.W - 20, self.H - 20), 2)
            core_color = RED if self.hp < self.max_hp // 3 else (ORANGE if self.hp < self.max_hp * 0.6 else LIME)
            draw_glow_rect(screen, core_color, pygame.Rect(cx - 18, cy - 18 + bob, 36, 36), radius=18, layers=4)
            pygame.draw.circle(screen, WHITE, (cx, cy + bob), 12)

        # Health bar (always shown)
        if self.y >= self.target_y - 5:
            hb_w = self.W
            pygame.draw.rect(screen, DARK_GRAY, (self.x, self.y - 15 + bob, hb_w, 8), border_radius=4)
            hp_ratio = max(0, self.hp / self.max_hp)
            c = GREEN if hp_ratio > 0.5 else (YELLOW if hp_ratio > 0.25 else RED)
            pygame.draw.rect(screen, c, (self.x, self.y - 15 + bob, int(hb_w * hp_ratio), 8), border_radius=4)
            # HP label
            fnt = pygame.font.SysFont('consolas', 12, bold=True)
            label = fnt.render(f"BOSS  {self.hp}/{self.max_hp}", True, WHITE)
            screen.blit(label, (cx - label.get_width()//2, self.y - 28 + bob))

# ─────────────────────────────────────────────────────────────────────────────
class PowerUp:
    _COLORS = {'shield': CYAN, 'multishot': PURPLE, 'heart': RED}

    def __init__(self, x, y, kind):
        self.x    = x
        self.y    = float(y)
        self.kind = kind
        self.speed = 1.4    # gentle fall – easy to intercept
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
        icon_surf = _POWERUP_ICONS[self.kind]
        screen.blit(icon_surf, (rect.centerx - icon_surf.get_width() // 2,
                                 rect.centery - icon_surf.get_height() // 2))

# ─────────────────────────────────────────────────────────────────────────────
class Game:
    def __init__(self, username="Player", db=None, audio=None):
        self.screen   = pygame.display.get_surface()
        pygame.display.set_caption(f"Space Invaders  |  {username}")
        self.clock    = pygame.time.Clock()
        self.username = username
        self.db       = db if db else Database()
        self.audio    = audio

        self.player        = Player()
        self.enemies       = []
        self.bullets       = []
        self.enemy_bullets = []
        self.powerups      = []

        self.score       = 0
        self.game_over   = False
        self.win         = False
        self.frame       = 0
        self.level       = 1
        self.wave_state  = 'spawning'
        self.state_timer = 0
        self.boss        = None
        self.paused      = False

        self.total_killed = 0
        self.shots_fired  = 0
        self.shots_hit    = 0
        self.combo        = 0
        self.combo_timer  = 0
        self.pw_shield    = 0
        self.pw_multi     = 0
        self.pw_heart     = 0

        self.game_id    = None
        self.player_id  = None
        self.sess_start = None
        self._setup_session()

        self.stars = [[random.randint(0, SCREEN_WIDTH),
                       random.randint(0, SCREEN_HEIGHT),
                       random.uniform(0.2, 1.2),
                       random.randint(1, 2)] for _ in range(130)]

        self.fnt_lg  = pygame.font.SysFont("consolas", 28, bold=True)
        self.fnt_md  = pygame.font.SysFont("consolas", 22, bold=True)
        self.fnt_sm  = pygame.font.SysFont("consolas", 17)
        self.fnt_ttl = pygame.font.SysFont("consolas", 56, bold=True)

        self.pause_menu = PauseMenu(self.screen, self.audio) if self.audio else None
        self._create_enemies()
        if self.audio:
            self.audio.play_bgm()

    # ── Session ───────────────────────────────────────────────────────────────
    def _setup_session(self):
        if self.db and self.db.connection:
            self.player_id = self.db.get_or_create_player(self.username)
            if self.player_id:
                self.game_id    = self.db.start_game_session(self.player_id)
                self.sess_start = datetime.now()
                print(f"[OK] Game session started (ID: {self.game_id})")

    def _save_stats(self):
        if not (self.db and self.db.connection and self.game_id and self.player_id):
            return
        dur = (datetime.now() - self.sess_start).seconds if self.sess_start else 0
        self.db.update_game_session(self.game_id, self.player_id, {
            'score': self.score, 'enemies_killed': self.total_killed,
            'shield_powerups': self.pw_shield, 'multishot_powerups': self.pw_multi,
            'heart_powerups': self.pw_heart, 'shots_fired': self.shots_fired,
            'shots_hit': self.shots_hit, 'duration': dur,
        })

    # ── Enemies ───────────────────────────────────────────────────────────────
    def _create_enemies(self):
        self.enemies.clear()
        cols = min(11, max(4, 4 + self.level))
        rows = min(5, max(2, 1 + self.level // 2))
        start_x = (SCREEN_WIDTH - (cols * 68)) // 2
        for row in range(rows):
            for col in range(cols):
                e = Enemy(start_x + col * 68, -100 - row * 48, row % 3)
                e.target_y = 38 + row * 48
                self.enemies.append(e)

    # ── Power-ups ─────────────────────────────────────────────────────────────
    def _drop_powerup(self, x, y):
        # 15% base drop – frequent enough to feel rewarding, not spammy
        if random.random() > (0.15 + 0.01 * min(self.combo, 5)):
            return
        pool = ['shield', 'multishot']
        if self.player.lives < self.player.max_lives:
            pool.append('heart')
        kind = random.choice(pool)
        if kind == 'shield':    self.pw_shield += 1
        elif kind == 'multishot': self.pw_multi += 1
        else:                   self.pw_heart  += 1
        self.powerups.append(PowerUp(x, y, kind))

    # ── Collisions ────────────────────────────────────────────────────────────
    @staticmethod
    def _hit(ax, ay, aw, ah, bx, by, bw, bh):
        return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by

    def _handle_collisions(self):
        p = self.player

        for b in self.bullets[:]:
            hit_enemy = False
            for e in self.enemies[:]:
                if self._hit(b.x, b.y, BULLET_W, BULLET_H, e.x, e.y, e.W, e.H):
                    if b in self.bullets: self.bullets.remove(b)
                    self.enemies.remove(e)
                    self.combo += 1; self.combo_timer = 90
                    self.score += 10 + (self.combo // 3) * 5
                    self.total_killed += 1; self.shots_hit += 1
                    self._drop_powerup(e.x, e.y)
                    if self.audio: self.audio.play('explode')
                    hit_enemy = True
                    break
            
            if not hit_enemy and self.boss and self.boss.hp > 0:
                if self._hit(b.x, b.y, BULLET_W, BULLET_H, self.boss.x, self.boss.y, self.boss.W, self.boss.H):
                    if b in self.bullets: self.bullets.remove(b)
                    self.boss.hp -= 1
                    self.score += 5
                    self.shots_hit += 1
                    if self.audio: self.audio.play('hit')
                    if self.boss.hp <= 0:
                        self.score += 500 * self.level
                        self.combo += 5; self.combo_timer = 120
                        self.total_killed += 1
                        for _ in range(3): self._drop_powerup(self.boss.x + random.randint(0, self.boss.W), self.boss.y + random.randint(0, self.boss.H))
                        if self.audio: self.audio.play('explode')

        for eb in self.enemy_bullets[:]:
            if self._hit(eb.x, eb.y, 6, 15, p.x, p.y, p.W, p.H):
                self.enemy_bullets.remove(eb)
                if p.take_damage():
                    self.combo = 0
                    if self.audio: self.audio.play('hit')
                    if p.lives <= 0:
                        self.game_over = True
                        if self.audio:
                            self.audio.stop_bgm()
                            self.audio.play('gameover')
                        self._save_stats()

        for e in self.enemies[:]:
            if self._hit(e.x, e.y, e.W, e.H, p.x, p.y, p.W, p.H):
                self.enemies.remove(e)
                if p.take_damage():
                    self.combo = 0
                    if self.audio: self.audio.play('hit')
                    if p.lives <= 0:
                        self.game_over = True
                        if self.audio:
                            self.audio.stop_bgm()
                            self.audio.play('gameover')
                        self._save_stats()
                        
        if self.boss and self.boss.hp > 0:
            if self._hit(self.boss.x, self.boss.y, self.boss.W, self.boss.H, p.x, p.y, p.W, p.H):
                if p.take_damage():
                    self.combo = 0
                    if self.audio: self.audio.play('hit')
                    if p.lives <= 0:
                        self.game_over = True
                        if self.audio:
                            self.audio.stop_bgm()
                            self.audio.play('gameover')
                        self._save_stats()

        for pu in self.powerups[:]:
            if self._hit(pu.x, int(pu.y), POWERUP_SIZE, POWERUP_SIZE, p.x, p.y, p.W, p.H):
                if pu.kind == 'shield':
                    p.shield = True; p.sh_timer = p.sh_dur
                elif pu.kind == 'multishot':
                    p.multi  = True; p.mu_timer = p.mu_dur
                elif pu.kind == 'heart' and p.lives < p.max_lives:
                    p.lives += 1
                self.powerups.remove(pu)
                if self.audio: self.audio.play('powerup')

        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer == 0: self.combo = 0

    # ── Drawing ───────────────────────────────────────────────────────────────
    def _draw_bg(self):
        self.screen.fill(NAVY)
        for s in self.stars:
            s[1] += s[2] * (1 + self.level * 0.04)
            if s[1] > SCREEN_HEIGHT:
                s[1] = 0; s[0] = random.randint(0, SCREEN_WIDTH)
            b = random.randint(110, 230)
            pygame.draw.circle(self.screen, (b, b, b), (int(s[0]), int(s[1])), s[3])

    def _draw_ui(self):
        p = self.player
        pygame.draw.line(self.screen, (40, 44, 70), (0, 58), (SCREEN_WIDTH, 58), 1)

        sc = self.fnt_lg.render(f"SCORE  {self.score:>6}", True, WHITE)
        self.screen.blit(sc, (12, 12))

        lv = self.fnt_md.render(f"LEVEL {self.level}", True, LIME)
        self.screen.blit(lv, (SCREEN_WIDTH // 2 - lv.get_width() // 2, 16))

        lbl = self.fnt_md.render("LIVES", True, WHITE)
        self.screen.blit(lbl, (SCREEN_WIDTH - 12 - lbl.get_width(), 12))
        hx = SCREEN_WIDTH - 12 - p.max_lives * 22
        for i in range(p.max_lives):
            col = RED if i < p.lives else DARK_GRAY
            cx, cy = hx + i * 22 + 8, 40
            pygame.draw.circle(self.screen, col, (cx - 4, cy - 3), 5)
            pygame.draw.circle(self.screen, col, (cx + 4, cy - 3), 5)
            pygame.draw.polygon(self.screen, col,
                                [(cx - 9, cy - 1), (cx, cy + 8), (cx + 9, cy - 1)])

        yo = 64
        if p.shield:
            self._draw_bar("SHIELD", CYAN,   p.sh_timer, p.sh_dur, yo); yo += 28
        if p.multi:
            self._draw_bar("MULTI ", PURPLE, p.mu_timer, p.mu_dur, yo)

        if not self.boss:
            ec = self.fnt_sm.render(f"ENEMIES: {len(self.enemies)}", True, LIGHT_GRAY)
            self.screen.blit(ec, (12, SCREEN_HEIGHT - 22))

        esc_hint = self.fnt_sm.render("ESC = Pause", True, GRAY)
        self.screen.blit(esc_hint, (SCREEN_WIDTH - 12 - esc_hint.get_width(), SCREEN_HEIGHT - 22))

        if self.combo > 2:
            pulse = abs((self.frame % 40) - 20) / 20
            cc = self.fnt_md.render(f"{self.combo}x COMBO!", True, YELLOW)
            cc.set_alpha(int(155 + 100 * pulse))
            self.screen.blit(cc, (SCREEN_WIDTH - 12 - cc.get_width(), 80))

        if self.wave_state == 'cleared':
            banner = self.fnt_lg.render("WAVE CLEARED!", True, LIME)
            shadow = self.fnt_lg.render("WAVE CLEARED!", True, BLACK)
            bx = SCREEN_WIDTH // 2 - banner.get_width() // 2
            by = SCREEN_HEIGHT // 2 - 40
            self.screen.blit(shadow, (bx + 4, by + 4))
            self.screen.blit(banner, (bx, by))

    def _draw_bar(self, label, color, timer, dur, y):
        ls = self.fnt_sm.render(label, True, color)
        self.screen.blit(ls, (12, y))
        bw = 86
        pygame.draw.rect(self.screen, DARK_GRAY, (12, y + 18, bw, 4))
        pygame.draw.rect(self.screen, color, (12, y + 18, int(bw * timer / dur), 4))

    def _draw_game_over(self):
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 175))
        self.screen.blit(ov, (0, 0))

        pulse = abs((self.frame % 80) - 40) / 40
        if self.win:
            tc = (int(80 + 175 * pulse), 255, int(80 * pulse))
            draw_text_center(self.screen, "VICTORY!", self.fnt_ttl, tc, 52)
        else:
            tc = (255, int(40 * pulse), int(40 * pulse))
            draw_text_center(self.screen, "GAME OVER", self.fnt_ttl, tc, 52)

        box = pygame.Rect(SCREEN_WIDTH // 2 - 215, 136, 430, 210)
        pygame.draw.rect(self.screen, (14, 14, 28), box, border_radius=10)
        pygame.draw.rect(self.screen, (70, 75, 140), box, 2, border_radius=10)

        acc = int((self.shots_hit / self.shots_fired * 100) if self.shots_fired > 0 else 0)
        stats = [("Final Score",       f"{self.score}"),
                 ("Enemies Destroyed", f"{self.total_killed}"),
                 ("Power-ups Picked",  f"{self.pw_shield + self.pw_multi + self.pw_heart}"),
                 ("Accuracy",          f"{acc}%")]
        yp = 154
        for lbl, val in stats:
            ls = self.fnt_md.render(f"{lbl}:", True, LIGHT_GRAY)
            vs = self.fnt_md.render(val, True, YELLOW)
            self.screen.blit(ls, (box.x + 20, yp))
            self.screen.blit(vs, (box.right - 20 - vs.get_width(), yp))
            yp += 38

        if self.db and self.db.connection:
            lb = self.db.get_leaderboard()
            if lb:
                yp = 370
                th = self.fnt_md.render("-- TOP SCORES --", True, YELLOW)
                self.screen.blit(th, (SCREEN_WIDTH // 2 - th.get_width() // 2, yp)); yp += 28
                for i, entry in enumerate(lb[:5]):
                    un  = entry.get('username', '???') if isinstance(entry, dict) else entry[0]
                    sc  = entry.get('score', 0)        if isinstance(entry, dict) else entry[1]
                    ac2 = entry.get('accuracy', 0)     if isinstance(entry, dict) else (entry[4] if len(entry) > 4 else 0)
                    col = YELLOW if i == 0 else (LIGHT_GRAY if i < 3 else GRAY)
                    es  = self.fnt_sm.render(
                        f"{i+1}. {un:<10} {sc:>5} pts  {float(ac2):.0f}%", True, col)
                    self.screen.blit(es, (SCREEN_WIDTH // 2 - es.get_width() // 2, yp + i * 22))

        hint = self.fnt_sm.render("R = Restart        Q = Quit        D = Dashboard",
                                  True, GRAY)
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 28))

    # ── Main loop ─────────────────────────────────────────────────────────────
    def run(self):
        """Returns: None (quit) | 'dashboard' (back to profile)"""
        global SCREEN_WIDTH, SCREEN_HEIGHT
        running = True
        result  = None

        while running:
            self.frame += 1

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False; self._save_stats()
                elif ev.type == pygame.VIDEORESIZE:
                    SCREEN_WIDTH, SCREEN_HEIGHT = ev.w, ev.h
                    self.screen = pygame.display.set_mode((ev.w, ev.h), pygame.RESIZABLE)

                elif ev.type == pygame.KEYDOWN:
                    # ── Pause toggle ──────────────────────────────────────────
                    if ev.key == pygame.K_ESCAPE and not self.game_over:
                        self.paused = not self.paused
                        continue

                    # ── Game-over keys ────────────────────────────────────────
                    elif self.game_over:
                        if ev.key == pygame.K_r:
                            self._save_stats()
                            self.__init__(self.username, self.db, self.audio)
                        elif ev.key == pygame.K_q:
                            running = False
                        elif ev.key == pygame.K_d:
                            result  = 'dashboard'; running = False

                # ── Pause menu events ─────────────────────────────────────────
                if self.paused and self.pause_menu:
                    pm_result = self.pause_menu.handle_event(ev)
                    if pm_result == 'continue':
                        self.paused = False
                    elif pm_result == 'dashboard':
                        result = 'dashboard'; running = False; self._save_stats()

            # ── Draw background (always) ───────────────────────────────────────
            self._draw_bg()

            if not self.game_over:
                if not self.paused:
                    # Input
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_LEFT]  or keys[pygame.K_a]: self.player.move(-1)
                    if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.player.move(1)
                    if keys[pygame.K_SPACE]:
                        bs = self.player.shoot()
                        if bs and self.audio: self.audio.play('shoot')
                        self.shots_fired += len(bs)
                        self.bullets.extend(bs)

                    # Update
                    self.player.update()

                    for b in self.bullets[:]:
                        b.update()
                        if b.y < 0: self.bullets.remove(b)

                    for eb in self.enemy_bullets[:]:
                        eb.update()
                        if eb.y > SCREEN_HEIGHT: self.enemy_bullets.remove(eb)

                    for e in self.enemies[:]:
                        e.update(self.enemies)
                        shot = e.shoot()
                        if shot: self.enemy_bullets.append(shot)
                        if e.y > SCREEN_HEIGHT: self.enemies.remove(e)

                    for pu in self.powerups[:]:
                        pu.update()
                        if pu.y > SCREEN_HEIGHT: self.powerups.remove(pu)

                    if self.wave_state == 'spawning':
                        if all(e.y >= e.target_y for e in self.enemies):
                            self.wave_state = 'fighting'
                    elif self.wave_state == 'fighting':
                        if not self.enemies:
                            self.wave_state = 'boss_spawning'
                            self.boss = Boss(max_hp=20 + self.level * 10, level=self.level)
                    elif self.wave_state == 'boss_spawning':
                        self.boss.update()
                        if self.boss.y >= self.boss.target_y:
                            self.wave_state = 'boss_fighting'
                    elif self.wave_state == 'boss_fighting':
                        self.boss.update()
                        shot = self.boss.shoot()
                        if shot: self.enemy_bullets.extend(shot)
                        if self.boss.hp <= 0:
                            self.wave_state = 'cleared'
                            self.state_timer = 90
                            self.boss = None
                    elif self.wave_state == 'cleared':
                        self.state_timer -= 1
                        if self.state_timer <= 0:
                            self.level += 1
                            self._create_enemies()
                            self.wave_state = 'spawning'

                    self._handle_collisions()

                # Draw game objects
                if self.boss: self.boss.draw(self.screen)
                for e  in self.enemies:       e.draw(self.screen)
                for b  in self.bullets:       b.draw(self.screen)
                for eb in self.enemy_bullets: eb.draw(self.screen)
                for pu in self.powerups:      pu.draw(self.screen)
                self.player.draw(self.screen)
                self._draw_ui()

                # Pause overlay
                if self.paused and self.pause_menu:
                    self.pause_menu.draw()

            else:
                for e in self.enemies: e.draw(self.screen)
                self.player.draw(self.screen)
                self._draw_game_over()

            # We now draw directly to the fluid screen.

            pygame.display.flip()
            self.clock.tick(config.GAME_CONFIG['fps'])

        # Keep pygame/db active on return to Dashboard
        return result


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    db    = Database(host=config.DB_CONFIG['host'], user=config.DB_CONFIG['user'],
                     password=config.DB_CONFIG['password'], database=config.DB_CONFIG['database'])
    audio = AudioManager()

    pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Space Invaders")
    _load_game_images()   # Must be called after display is up


    while True:
        username = ProfileScreen(pygame.display.get_surface(), db, audio).run()
        if not username:
            break
        print(f"\nStarting game for: {username}")
        result = Game(username, db, audio).run()
        if result != 'dashboard':
            break

    if db and db.connection:
        db.close()
    pygame.quit()
    sys.exit()