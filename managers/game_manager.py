"""game/game.py
The core Game class containing the main game loop, level generation,
collision handling, and drawing logic.
"""
import random
import math
import pygame
from datetime import datetime

import config
from database import Database
import constants
from entities.player import Player
from entities.enemy import Enemy, Boss
from entities.powerup import PowerUp
from entities.bullet import Bullet
from managers.ui_manager import PauseMenu
from managers.screen_manager import LeaderboardScreen
from managers.achievement_manager import AchievementManager


class GameManager:
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
        self.boss_powerup_timer = 0
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
        self.pw_side_drones = 0
        self.pw_score_multiplier = 0
        self.side_drone_timer = 0
        self.side_drone_duration = 900
        self.score_multiplier_timer = 0
        self.score_multiplier_duration = 900
        self.score_multiplier = 2
        self.wave_hit     = False
        self.pending_shots_progress = 0
        self._achievement_run_checked = False
        self._achievement_run_progress_saved = False
        self.boss_damaged = False

        self.game_id    = None
        self.player_id  = None
        self.sess_start = None
        self._setup_session()
        self.achievements = AchievementManager(self.db, self.player_id)
        if self.db and self.db.connected and self.player_id:
            stats = self.db.get_player_stats(self.username)
            if stats:
                self.achievements.seed_existing_stats(stats)

        self.stars = [[random.randint(0, constants.SCREEN_WIDTH),
                       random.randint(0, constants.SCREEN_HEIGHT),
                       random.uniform(0.2, 1.2),
                       random.randint(1, 2)] for _ in range(130)]

        self.fnt_lg  = pygame.font.SysFont("consolas", 28, bold=True)
        self.fnt_md  = pygame.font.SysFont("consolas", 22, bold=True)
        self.fnt_sm  = pygame.font.SysFont("consolas", 17)
        self.fnt_ttl = pygame.font.SysFont("consolas", 56, bold=True)

        self.pause_menu = PauseMenu(self.screen, self.audio, self.db) if self.audio else None
        self._create_enemies()
        if self.audio:
            self.audio.play_bgm()

    # ── Session ───────────────────────────────────────────────────────────────
    def _setup_session(self):
        if self.db and self.db.connected:
            self.player_id = self.db.get_or_create_player(self.username)
            if self.player_id:
                self.game_id    = self.db.start_game_session(self.player_id)
                self.sess_start = datetime.now()
                print(f"[OK] Game session started (ID: {self.game_id})")

    def _save_stats(self):
        if not self._achievement_run_checked:
            self._achievement_run_checked = True
            self.achievements.record_run_accuracy(self.shots_fired, self.shots_hit)
        if not self._achievement_run_progress_saved:
            self._achievement_run_progress_saved = True
            self.achievements.record_progress("games_played")
            self.achievements.record_progress("score_earned", self.score)
        self._flush_shot_achievement_progress()
        if not (self.db and self.db.connected and self.game_id and self.player_id):
            return
        dur = (datetime.now() - self.sess_start).seconds if self.sess_start else 0
        self.db.update_game_session(self.game_id, self.player_id, {
            'score': self.score, 'enemies_killed': self.total_killed,
            'shield_powerups': self.pw_shield, 'multishot_powerups': self.pw_multi,
            'heart_powerups': self.pw_heart,
            'side_drone_powerups': self.pw_side_drones,
            'score_multiplier_powerups': self.pw_score_multiplier,
            'shots_fired': self.shots_fired,
            'shots_hit': self.shots_hit, 'duration': dur,
        })

    def _flush_shot_achievement_progress(self):
        if self.pending_shots_progress:
            self.achievements.record_progress("shots_fired", self.pending_shots_progress)
            self.pending_shots_progress = 0

    def _record_player_damage(self):
        self.wave_hit = True
        if self.wave_state == "boss_fighting":
            self.boss_damaged = True

    def _award_score(self, points):
        multiplier = self.score_multiplier if self.score_multiplier_timer > 0 else 1
        self.score += points * multiplier

    def _apply_powerup(self, kind):
        if kind == 'shield':
            self.player.shield = True
            self.player.sh_timer = self.player.sh_dur
            self.pw_shield += 1
        elif kind == 'multishot':
            self.player.multi = True
            self.player.mu_timer = self.player.mu_dur
            self.pw_multi += 1
        elif kind == 'heart':
            if self.player.lives < self.player.max_lives:
                self.player.lives += 1
                self.pw_heart += 1
        elif kind == 'side_drones':
            self.side_drone_timer = max(self.side_drone_timer, self.side_drone_duration)
            self.pw_side_drones += 1
        elif kind == 'score_multiplier':
            self.score_multiplier_timer = max(
                self.score_multiplier_timer, self.score_multiplier_duration
            )
            self.pw_score_multiplier += 1
        self.achievements.record_powerup_collected(kind)

    def _fire_player(self):
        shots = self.player.shoot()
        if shots and self.side_drone_timer > 0:
            for x, y in self._drone_positions():
                shots.append(Bullet(x - constants.BULLET_W // 2, y))
        if shots and self.audio:
            self.audio.play('shoot')
        self.shots_fired += len(shots)
        self.pending_shots_progress += len(shots)
        if self.pending_shots_progress >= 20:
            self._flush_shot_achievement_progress()
        self.bullets.extend(shots)

    def _update_powerup_timers(self):
        self.side_drone_timer = max(0, self.side_drone_timer - 1)
        self.score_multiplier_timer = max(0, self.score_multiplier_timer - 1)

    def _drone_positions(self):
        if self.side_drone_timer <= 0:
            return ()
        center_y = self.player.y + self.player.H // 2
        bob = int(math.sin(self.frame * 0.08) * 5)
        offset = self.player.W // 2 + 22
        return (
            (max(8, self.player.x + self.player.W // 2 - offset), center_y + bob),
            (min(constants.SCREEN_WIDTH - 24,
                 self.player.x + self.player.W // 2 + offset), center_y - bob),
        )

    def _draw_side_drones(self):
        for x, y in self._drone_positions():
            pygame.draw.ellipse(self.screen, (20, 70, 100),
                                (x - 10, y - 7, 20, 14))
            pygame.draw.ellipse(self.screen, constants.CYAN,
                                (x - 10, y - 7, 20, 14), 2)
            pygame.draw.circle(self.screen, constants.WHITE, (x, y), 3)

    # ── Enemies ───────────────────────────────────────────────────────────────
    def _create_enemies(self):
        self.enemies.clear()
        cols = min(11, max(4, 4 + self.level))
        rows = min(5, max(2, 1 + self.level // 2))
        start_x = (constants.SCREEN_WIDTH - (cols * 68)) // 2
        for row in range(rows):
            for col in range(cols):
                e = Enemy(start_x + col * 68, -100 - row * 48, row % 3)
                e.target_y = 84 + row * 48   # keep clear of the HUD bar (y ≤ 58)
                self.enemies.append(e)

    # ── Power-ups ─────────────────────────────────────────────────────────────
    def _drop_powerup(self, x, y, guaranteed=False):
        if not guaranteed and random.random() > (0.15 + 0.01 * min(self.combo, 5)):
            return
        pool = ['shield', 'multishot']
        if self.player.lives < self.player.max_lives:
            pool.append('heart')
        pool.append('score_multiplier')
        kind = random.choices(
            pool + ['side_drones'],
            weights=[1] * len(pool) + [0.2],
            k=1,
        )[0]
        self.powerups.append(PowerUp(x, y, kind))

    def _update_boss_powerups(self):
        if self.boss_powerup_timer > 0:
            self.boss_powerup_timer -= 1
        if self.boss_powerup_timer <= 0:
            x = random.randint(0, constants.SCREEN_WIDTH - constants.POWERUP_SIZE)
            self._drop_powerup(x, 0, guaranteed=True)
            self.boss_powerup_timer = random.randint(300, 600)

    # ── Collisions ────────────────────────────────────────────────────────────
    @staticmethod
    def _hit(ax, ay, aw, ah, bx, by, bw, bh):
        return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by

    def _handle_collisions(self):
        p = self.player

        for b in self.bullets[:]:
            hit_enemy = False
            for e in self.enemies[:]:
                if self._hit(b.x, b.y, constants.BULLET_W, constants.BULLET_H, e.x, e.y, e.W, e.H):
                    if b in self.bullets: self.bullets.remove(b)
                    self.enemies.remove(e)
                    self.combo += 1; self.combo_timer = 90
                    self._award_score(10 + (self.combo // 3) * 5)
                    self.total_killed += 1; self.shots_hit += 1
                    self.achievements.record_progress("enemies_killed")
                    self.achievements.record_combo(self.combo)
                    self._drop_powerup(e.x, e.y)
                    if self.audio: self.audio.play('explode')
                    hit_enemy = True
                    break
            
            if not hit_enemy and self.boss and self.boss.hp > 0:
                if self._hit(b.x, b.y, constants.BULLET_W, constants.BULLET_H, self.boss.x, self.boss.y, self.boss.W, self.boss.H):
                    if b in self.bullets: self.bullets.remove(b)
                    self.boss.hp -= 1
                    self._award_score(5)
                    self.shots_hit += 1
                    if self.audio: self.audio.play('hit')
                    if self.boss.hp <= 0:
                        self._award_score(500 * self.level)
                        self.combo += 5; self.combo_timer = 120
                        self.total_killed += 1
                        self.achievements.record_boss_defeat(self.boss.boss_number)
                        if not self.boss_damaged:
                            self.achievements.record_boss_defeat_without_damage()
                        if self.audio: self.audio.play('explode')

        for eb in self.enemy_bullets[:]:
            if self._hit(eb.x, eb.y, 6, 15, p.x, p.y, p.W, p.H):
                self.enemy_bullets.remove(eb)
                if p.take_damage():
                    self._record_player_damage()
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
                    self._record_player_damage()
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
                    self._record_player_damage()
                    self.combo = 0
                    if self.audio: self.audio.play('hit')
                    if p.lives <= 0:
                        self.game_over = True
                        if self.audio:
                            self.audio.stop_bgm()
                            self.audio.play('gameover')
                        self._save_stats()

        for pu in self.powerups[:]:
            if self._hit(pu.x, int(pu.y), constants.POWERUP_SIZE, constants.POWERUP_SIZE, p.x, p.y, p.W, p.H):
                self.powerups.remove(pu)
                self._apply_powerup(pu.kind)
                if self.audio: self.audio.play('powerup')

        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer == 0: self.combo = 0

    # ── Drawing ───────────────────────────────────────────────────────────────
    def _draw_bg(self):
        self.screen.fill(constants.NAVY)
        for s in self.stars:
            s[1] += s[2] * (1 + self.level * 0.04)
            if s[1] > constants.SCREEN_HEIGHT:
                s[1] = 0; s[0] = random.randint(0, constants.SCREEN_WIDTH)
            b = random.randint(110, 230)
            pygame.draw.circle(self.screen, (b, b, b), (int(s[0]), int(s[1])), s[3])

    def _draw_ui(self):
        p = self.player
        pygame.draw.line(self.screen, (40, 44, 70), (0, 58), (constants.SCREEN_WIDTH, 58), 1)

        sc = self.fnt_lg.render(f"SCORE  {self.score:>6}", True, constants.WHITE)
        self.screen.blit(sc, (12, 12))

        lv = self.fnt_md.render(f"LEVEL {self.level}", True, constants.LIME)
        self.screen.blit(lv, (constants.SCREEN_WIDTH // 2 - lv.get_width() // 2, 16))

        lbl = self.fnt_md.render("LIVES", True, constants.WHITE)
        self.screen.blit(lbl, (constants.SCREEN_WIDTH - 12 - lbl.get_width(), 12))
        hx = constants.SCREEN_WIDTH - 12 - p.max_lives * 22
        for i in range(p.max_lives):
            col = constants.RED if i < p.lives else constants.DARK_GRAY
            cx, cy = hx + i * 22 + 8, 40
            pygame.draw.circle(self.screen, col, (cx - 4, cy - 3), 5)
            pygame.draw.circle(self.screen, col, (cx + 4, cy - 3), 5)
            pygame.draw.polygon(self.screen, col,
                                [(cx - 9, cy - 1), (cx, cy + 8), (cx + 9, cy - 1)])

        yo = 64
        if p.shield:
            self._draw_bar("SHIELD", constants.CYAN,   p.sh_timer, p.sh_dur, yo); yo += 28
        if p.multi:
            self._draw_bar("MULTI ", constants.PURPLE, p.mu_timer, p.mu_dur, yo)
            yo += 28
        if self.side_drone_timer > 0:
            self._draw_bar("DRONES", constants.ORANGE, self.side_drone_timer,
                           self.side_drone_duration, yo)
            yo += 28
        if self.score_multiplier_timer > 0:
            self._draw_bar("SCORE x2", constants.YELLOW,
                           self.score_multiplier_timer,
                           self.score_multiplier_duration, yo)

        if not self.boss:
            ec = self.fnt_sm.render(f"ENEMIES: {len(self.enemies)}", True, constants.LIGHT_GRAY)
            self.screen.blit(ec, (12, constants.SCREEN_HEIGHT - 22))

        esc_hint = self.fnt_sm.render("ESC = Pause", True, constants.GRAY)
        self.screen.blit(esc_hint, (constants.SCREEN_WIDTH - 12 - esc_hint.get_width(), constants.SCREEN_HEIGHT - 22))

        if self.combo > 2:
            pulse = abs((self.frame % 40) - 20) / 20
            cc = self.fnt_md.render(f"{self.combo}x COMBO!", True, constants.YELLOW)
            cc.set_alpha(int(155 + 100 * pulse))
            self.screen.blit(cc, (constants.SCREEN_WIDTH - 12 - cc.get_width(), 80))

        if self.wave_state == 'cleared':
            banner = self.fnt_lg.render("WAVE CLEARED!", True, constants.LIME)
            shadow = self.fnt_lg.render("WAVE CLEARED!", True, constants.BLACK)
            bx = constants.SCREEN_WIDTH // 2 - banner.get_width() // 2
            by = constants.SCREEN_HEIGHT // 2 - 40
            self.screen.blit(shadow, (bx + 4, by + 4))
            self.screen.blit(banner, (bx, by))

    def _draw_bar(self, label, color, timer, dur, y):
        ls = self.fnt_sm.render(label, True, color)
        self.screen.blit(ls, (12, y))
        bw = 86
        pygame.draw.rect(self.screen, constants.DARK_GRAY, (12, y + 18, bw, 4))
        pygame.draw.rect(self.screen, color, (12, y + 18, int(bw * timer / dur), 4))

    def _draw_game_over(self):
        ov = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 175))
        self.screen.blit(ov, (0, 0))

        pulse = abs((self.frame % 80) - 40) / 40
        if self.win:
            tc = (int(80 + 175 * pulse), 255, int(80 * pulse))
            constants.draw_text_center(self.screen, "VICTORY!", self.fnt_ttl, tc, 52)
        else:
            tc = (255, int(40 * pulse), int(40 * pulse))
            constants.draw_text_center(self.screen, "GAME OVER", self.fnt_ttl, tc, 52)

        box = pygame.Rect(constants.SCREEN_WIDTH // 2 - 215, 136, 430, 210)
        pygame.draw.rect(self.screen, (14, 14, 28), box, border_radius=10)
        pygame.draw.rect(self.screen, (70, 75, 140), box, 2, border_radius=10)

        acc = int((self.shots_hit / self.shots_fired * 100) if self.shots_fired > 0 else 0)
        stats = [("Final Score",       f"{self.score}"),
                 ("Enemies Destroyed", f"{self.total_killed}"),
                 ("Power-ups Picked",  f"{self.pw_shield + self.pw_multi + self.pw_heart + self.pw_side_drones + self.pw_score_multiplier}"),
                 ("Accuracy",          f"{acc}%")]
        yp = 154
        for lbl, val in stats:
            ls = self.fnt_md.render(f"{lbl}:", True, constants.LIGHT_GRAY)
            vs = self.fnt_md.render(val, True, constants.YELLOW)
            self.screen.blit(ls, (box.x + 20, yp))
            self.screen.blit(vs, (box.right - 20 - vs.get_width(), yp))
            yp += 38

        if self.db and self.db.connected:
            lb = self.db.get_leaderboard()
            if lb:
                yp = 370
                th = self.fnt_md.render("-- TOP SCORES --", True, constants.YELLOW)
                self.screen.blit(th, (constants.SCREEN_WIDTH // 2 - th.get_width() // 2, yp)); yp += 28
                for i, entry in enumerate(lb[:5]):
                    un  = entry.get('username', '???') if isinstance(entry, dict) else entry[0]
                    sc  = entry.get('score', 0)        if isinstance(entry, dict) else entry[1]
                    ac2 = entry.get('accuracy', 0)     if isinstance(entry, dict) else (entry[4] if len(entry) > 4 else 0)
                    col = constants.YELLOW if i == 0 else (constants.LIGHT_GRAY if i < 3 else constants.GRAY)
                    es  = self.fnt_sm.render(
                        f"{i+1}. {un:<10} {sc:>5} pts  {float(ac2):.0f}%", True, col)
                    self.screen.blit(es, (constants.SCREEN_WIDTH // 2 - es.get_width() // 2, yp + i * 22))

        hint = self.fnt_sm.render("R = Restart        Q = Quit        D = Dashboard",
                                  True, constants.GRAY)
        self.screen.blit(hint, (constants.SCREEN_WIDTH // 2 - hint.get_width() // 2, constants.SCREEN_HEIGHT - 28))

    # ── Main loop ─────────────────────────────────────────────────────────────
    def run(self):
        """Returns: None (quit) | 'dashboard' (back to profile)"""
        running = True
        result  = None

        while running:
            self.frame += 1

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False; self._save_stats()
                elif ev.type == pygame.VIDEORESIZE:
                    w, h = ev.dict.get('size', (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
                    constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT = w, h
                    self.screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)

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
                            self._save_stats()
                            running = False
                        elif ev.key == pygame.K_d:
                            result  = 'dashboard'; running = False; self._save_stats()

                # ── Pause menu events ─────────────────────────────────────────
                if self.paused and self.pause_menu:
                    pm_result = self.pause_menu.handle_event(ev)
                    if pm_result == 'continue':
                        self.paused = False
                    elif pm_result == 'dashboard':
                        result = 'dashboard'; running = False; self._save_stats()
                    elif pm_result == 'leaderboard':
                        LeaderboardScreen(self.screen, self.db).run()
                        self.pause_menu.state = 'main'  # stay paused, back to pause menu

            # ── Draw background (always) ───────────────────────────────────────
            self._draw_bg()

            if not self.game_over:
                if not self.paused:
                    # Input
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_LEFT]  or keys[pygame.K_a]: self.player.move(-1)
                    if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.player.move(1)
                    if keys[pygame.K_SPACE]:
                        self._fire_player()

                    # Update
                    self.player.update()
                    self._update_powerup_timers()

                    for b in self.bullets[:]:
                        b.update()
                        if b.y < 0: self.bullets.remove(b)

                    for eb in self.enemy_bullets[:]:
                        eb.update()
                        if eb.y > constants.SCREEN_HEIGHT: self.enemy_bullets.remove(eb)

                    for e in self.enemies[:]:
                        e.update(self.enemies)
                        shot = e.shoot()
                        if shot: self.enemy_bullets.append(shot)
                        if e.y > constants.SCREEN_HEIGHT: self.enemies.remove(e)

                    for pu in self.powerups[:]:
                        pu.update()
                        if pu.y > constants.SCREEN_HEIGHT: self.powerups.remove(pu)

                    if self.wave_state == 'spawning':
                        if all(e.y >= e.target_y for e in self.enemies):
                            self.wave_state = 'fighting'
                    elif self.wave_state == 'fighting':
                        if not self.enemies:
                            if not self.wave_hit:
                                self.achievements.record_progress("clean_waves")
                            self.wave_state = 'boss_spawning'
                            self.boss = Boss(max_hp=20 + self.level * 10, level=self.level)
                    elif self.wave_state == 'boss_spawning':
                        self.boss.update()
                        if self.boss.y >= self.boss.target_y:
                            self.wave_state = 'boss_fighting'
                            self.boss_powerup_timer = 0
                            self.boss_damaged = False
                    elif self.wave_state == 'boss_fighting':
                        self.boss.update()
                        shot = self.boss.shoot()
                        if shot: self.enemy_bullets.extend(shot)
                        self._update_boss_powerups()
                        if self.boss.hp <= 0:
                            self.wave_state = 'cleared'
                            self.state_timer = 90
                            self.boss = None
                    elif self.wave_state == 'cleared':
                        self.state_timer -= 1
                        if self.state_timer <= 0:
                            self.level += 1
                            self.wave_hit = False
                            self.achievements.record_level_reached(self.level)
                            self._create_enemies()
                            self.wave_state = 'spawning'

                    self._handle_collisions()

                # Draw game objects
                if self.boss: self.boss.draw(self.screen)
                for e  in self.enemies:       e.draw(self.screen)
                for b  in self.bullets:       b.draw(self.screen)
                for eb in self.enemy_bullets: eb.draw(self.screen)
                for pu in self.powerups:      pu.draw(self.screen)
                self._draw_side_drones()
                self.player.draw(self.screen)
                self._draw_ui()

                # Pause overlay
                if self.paused and self.pause_menu:
                    self.pause_menu.draw()

            else:
                for e in self.enemies: e.draw(self.screen)
                self.player.draw(self.screen)
                self._draw_game_over()

            pygame.display.flip()
            self.clock.tick(config.GAME_CONFIG['fps'])

        return result
