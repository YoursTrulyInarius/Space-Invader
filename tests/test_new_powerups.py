import unittest
from unittest.mock import Mock, patch

from entities.bullet import Bullet
from managers.game_manager import GameManager


class FakePlayer:
    x = 200
    y = 500
    W = 40
    H = 24

    def __init__(self):
        self.shield = False
        self.sh_timer = 0
        self.sh_dur = 600
        self.multi = False
        self.mu_timer = 0
        self.mu_dur = 600

    def shoot(self):
        return [Bullet(217, 496)]


class NewPowerUpTests(unittest.TestCase):
    def setUp(self):
        self.game = GameManager.__new__(GameManager)
        self.game.player = FakePlayer()
        self.game.frame = 0
        self.game.side_drone_timer = 0
        self.game.side_drone_duration = 900
        self.game.score_multiplier_timer = 0
        self.game.score_multiplier_duration = 900
        self.game.score_multiplier = 2
        self.game.pw_side_drones = 0
        self.game.pw_score_multiplier = 0
        self.game.pw_shield = 0
        self.game.pw_multi = 0
        self.game.pw_heart = 0
        self.game.score = 10
        self.game.shots_fired = 0
        self.game.pending_shots_progress = 0
        self.game.bullets = []
        self.game.audio = None
        self.game.achievements = Mock()

    def test_drone_powerup_adds_two_bullets_per_player_shot(self):
        self.game.side_drone_timer = 300

        self.game._fire_player()

        self.assertEqual(len(self.game.bullets), 3)
        self.assertEqual(self.game.shots_fired, 3)
        self.assertTrue(all(isinstance(bullet, Bullet) for bullet in self.game.bullets))

    def test_random_drop_pool_makes_drones_uncommon(self):
        self.game.combo = 0
        self.game.powerups = []
        self.game.player.lives = 2
        self.game.player.max_lives = 3

        with patch("managers.game_manager.random.random", return_value=0):
            with patch(
                "managers.game_manager.random.choices", return_value=["side_drones"]
            ) as weighted_choice:
                self.game._drop_powerup(100, 200)

        self.assertEqual(self.game.powerups[0].kind, "side_drones")
        options, = weighted_choice.call_args.args
        weights = weighted_choice.call_args.kwargs["weights"]
        drone_weight = weights[options.index("side_drones")]
        self.assertIn("score_multiplier", options)
        self.assertLess(drone_weight, min(weights[:-1]))

    def test_score_multiplier_doubles_awarded_points(self):
        self.game._apply_powerup("score_multiplier")

        self.game._award_score(25)

        self.assertEqual(self.game.score, 60)
        self.assertEqual(self.game.pw_score_multiplier, 1)
        self.game.achievements.record_powerup_collected.assert_called_once_with(
            "score_multiplier"
        )

    def test_powerup_timers_expire(self):
        self.game.side_drone_timer = 1
        self.game.score_multiplier_timer = 1

        self.game._update_powerup_timers()

        self.assertEqual(self.game.side_drone_timer, 0)
        self.assertEqual(self.game.score_multiplier_timer, 0)
        self.assertEqual(self.game._drone_positions(), ())


if __name__ == "__main__":
    unittest.main()
