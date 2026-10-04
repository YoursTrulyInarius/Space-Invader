import unittest
from unittest.mock import patch

from managers.game_manager import GameManager


class FakePlayer:
    lives = 3
    max_lives = 3


class BossPowerUpTests(unittest.TestCase):
    def test_guaranteed_drop_ignores_probability_roll(self):
        game = GameManager.__new__(GameManager)
        game.player = FakePlayer()
        game.combo = 0
        game.powerups = []
        game.pw_shield = 0
        game.pw_multi = 0
        game.pw_heart = 0

        with patch('managers.game_manager.random.random', return_value=1.0):
            with patch('managers.game_manager.random.choices', return_value=['shield']):
                game._drop_powerup(100, 200, guaranteed=True)

        self.assertEqual(len(game.powerups), 1)
        self.assertEqual(game.powerups[0].kind, 'shield')
        self.assertEqual(game.powerups[0].x, 100)
        self.assertEqual(game.powerups[0].y, 200)
        self.assertEqual(game.pw_shield, 0)

    def test_boss_fight_drops_powerups_periodically(self):
        game = GameManager.__new__(GameManager)
        game.player = FakePlayer()
        game.combo = 0
        game.powerups = []
        game.pw_shield = 0
        game.pw_multi = 0
        game.pw_heart = 0
        game.boss_powerup_timer = 0

        with patch('managers.game_manager.random.random', return_value=1.0):
            with patch('managers.game_manager.random.choices', return_value=['multishot']):
                with patch('managers.game_manager.random.randint', side_effect=[120, 2]):
                    game._update_boss_powerups()

        self.assertEqual(len(game.powerups), 1)
        self.assertEqual(game.powerups[0].kind, 'multishot')
        self.assertEqual(game.powerups[0].x, 120)
        self.assertEqual(game.powerups[0].y, 0)
        self.assertEqual(game.pw_multi, 0)
        self.assertEqual(game.boss_powerup_timer, 2)

        game._update_boss_powerups()
        self.assertEqual(len(game.powerups), 1)

        with patch('managers.game_manager.random.random', return_value=1.0):
            with patch('managers.game_manager.random.choices', return_value=['shield']):
                with patch('managers.game_manager.random.randint', side_effect=[240, 3]):
                    game._update_boss_powerups()

        self.assertEqual(len(game.powerups), 2)
        self.assertEqual(game.powerups[1].kind, 'shield')
        self.assertEqual(game.boss_powerup_timer, 3)


if __name__ == "__main__":
    unittest.main()
