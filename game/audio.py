"""game/audio.py
AudioManager – synthesises retro SFX and BGM at runtime using numpy.
Gracefully disables itself (no-op) when numpy is not installed.
"""
import pygame


class AudioManager:
    """Generates retro SFX with numpy (graceful no-op if numpy missing)."""

    def __init__(self):
        self.sfx_vol   = 0.65
        self.music_vol = 0.35
        self.sounds    = {}
        self._init()

    # ── Initialisation ────────────────────────────────────────────────────────
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
                n      = int(SR * dur)
                t      = np.linspace(0, dur, n, endpoint=False)
                w      = np.random.uniform(-1, 1, n)
                freqs  = np.linspace(150, 40, n)
                rumble = np.sin(2 * np.pi * freqs * t)
                env    = np.exp(-np.linspace(0, 6, n))
                mix    = (w * 0.6 + rumble * 0.6) * env
                mix    = np.clip(mix * vol * 32767, -32767, 32767).astype(np.int16)
                return np.column_stack([mix, mix])

            def make(arr):
                return pygame.sndarray.make_sound(arr)

            self.sounds['shoot']    = make(sine(900, 0.06, 0.35, decay=10))
            self.sounds['explode']  = make(boom(0.4, 0.7))
            self.sounds['powerup']  = make(cat(sine(380, 0.06, 0.4), sine(570, 0.06, 0.4), sine(860, 0.10, 0.4)))
            self.sounds['hit']      = make(cat(sine(130, 0.07, 0.5, decay=12), noise(0.08, 0.3)))
            self.sounds['gameover'] = make(cat(sine(380, 0.15, 0.4), sine(280, 0.15, 0.4), sine(190, 0.28, 0.4)))
            self.sounds['victory']  = make(cat(sine(400, 0.09, 0.4), sine(500, 0.09, 0.4),
                                               sine(640, 0.09, 0.4), sine(800, 0.18, 0.4)))

            # Simple looping BGM melody
            dur     = 0.22
            scale   = [220, 247, 262, 294, 330, 370, 392, 440]
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
            print("=" * 60)
            print(f"[AUDIO] DISABLED — could not initialise audio: {e}")
            if isinstance(e, ImportError):
                print("[AUDIO] This game's SFX/music are synthesized with "
                      "numpy at runtime. Install it with:")
                print("        pip install -r requirements.txt")
                print("        (or: pip install numpy)")
            print("=" * 60)
            self.sounds = {}

    # ── Volume helpers ────────────────────────────────────────────────────────
    def _apply_vols(self):
        for name, snd in self.sounds.items():
            snd.set_volume(self.music_vol if name == 'bgm' else self.sfx_vol)

    def set_sfx_vol(self, v):
        self.sfx_vol = max(0.0, min(1.0, v))
        for name, snd in self.sounds.items():
            if name != 'bgm':
                snd.set_volume(self.sfx_vol)

    def set_music_vol(self, v):
        self.music_vol = max(0.0, min(1.0, v))
        if 'bgm' in self.sounds:
            self.sounds['bgm'].set_volume(self.music_vol)

    # ── Playback ──────────────────────────────────────────────────────────────
    def play(self, name):
        if name in self.sounds:
            self.sounds[name].play()

    def stop_bgm(self):
        if 'bgm' in self.sounds:
            self.sounds['bgm'].stop()

    def play_bgm(self):
        if 'bgm' in self.sounds:
            self.sounds['bgm'].stop()
            self.sounds['bgm'].play(loops=-1)
