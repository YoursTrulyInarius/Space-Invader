import unittest

from managers.achievement_manager import AchievementManager


class FakeAchievementDatabase:
    connected = True

    def __init__(self):
        self.progress = {}
        self.unlocked = set()

    def increment_achievement_progress(self, _player_id, metric, amount=1):
        self.progress[metric] = self.progress.get(metric, 0) + amount
        return self.progress[metric]

    def set_achievement_progress(self, _player_id, metric, value):
        self.progress[metric] = max(self.progress.get(metric, 0), value)
        return self.progress[metric]

    def get_achievement_progress(self, _player_id):
        return self.progress.copy()

    def unlock_achievement(self, _player_id, key):
        if key in self.unlocked:
            return False
        self.unlocked.add(key)
        return True


class AchievementManagerTests(unittest.TestCase):
    def setUp(self):
        self.db = FakeAchievementDatabase()
        self.manager = AchievementManager(self.db, 1)

    def test_lifetime_kill_and_boss_achievements_unlock_once(self):
        first_contact = self.manager.record_progress("enemies_killed")
        first_boss = self.manager.record_boss_defeat(1)
        repeated_boss = self.manager.record_boss_defeat(1)

        self.assertEqual([item["key"] for item in first_contact], ["first_contact"])
        self.assertEqual([item["key"] for item in first_boss], ["boss_breaker"])
        self.assertEqual(repeated_boss, [])

    def test_four_distinct_boss_types_unlocks_after_all_have_been_defeated(self):
        unlocked = []
        for boss_number in (1, 2, 3):
            unlocked.extend(self.manager.record_boss_defeat(boss_number))
        self.assertNotIn("four_of_a_kind", [item["key"] for item in unlocked])

        unlocked.extend(self.manager.record_boss_defeat(4))

        self.assertIn("four_of_a_kind", [item["key"] for item in unlocked])

    def test_highest_level_uses_maximum_progress(self):
        self.manager.record_level_reached(8)
        self.manager.record_level_reached(4)

        unlocked = self.manager.record_level_reached(10)

        self.assertEqual([item["key"] for item in unlocked], ["unstoppable"])
        self.assertEqual(self.db.progress["highest_level"], 10)

    def test_run_challenges_unlock_on_expected_conditions(self):
        accuracy = self.manager.record_run_accuracy(20, 16)
        self.manager.record_run_accuracy(100, 79)
        self.manager.record_progress("clean_waves")
        self.manager.record_powerup_collected("shield")
        self.manager.record_powerup_collected("multishot")
        self.manager.record_powerup_collected("heart")
        self.manager.record_powerup_collected("side_drones")
        powerups = self.manager.record_powerup_collected("score_multiplier")
        for _ in range(7):
            powerups.extend(self.manager.record_powerup_collected("shield"))

        self.assertEqual([item["key"] for item in accuracy], ["sharpshooter"])
        self.assertIn("clean_sweep", self.db.unlocked)
        self.assertIn("fully_loaded", [item["key"] for item in powerups])
        self.assertIn("lifesaver", self.db.unlocked)
        self.assertIn("power_surge", self.db.unlocked)
        self.assertEqual(self.db.progress["best_run_powerup_types"], 5)

    def test_new_lifetime_and_skill_achievements_unlock(self):
        self.manager.record_progress("enemies_killed", 999)
        invasion = self.manager.record_progress("enemies_killed")
        self.manager.record_progress("games_played", 9)
        veteran = self.manager.record_progress("games_played")
        self.manager.record_progress("score_earned", 75_000)
        score = self.manager.record_progress("score_earned", 25_000)
        self.manager.record_progress("powerups_collected", 49)
        cache = self.manager.record_progress("powerups_collected")
        self.manager.record_progress("bosses_defeated", 9)
        titan = self.manager.record_progress("bosses_defeated")
        combo = self.manager.record_combo(25)
        untouchable = self.manager.record_boss_defeat_without_damage()
        accuracy = self.manager.record_run_accuracy(100, 95)

        self.assertIn("invasion_eraser", [item["key"] for item in invasion])
        self.assertIn("veteran_pilot", [item["key"] for item in veteran])
        self.assertIn("score_legend", [item["key"] for item in score])
        self.assertIn("cache_collector", [item["key"] for item in cache])
        self.assertIn("titan_slayer", [item["key"] for item in titan])
        self.assertIn("combo_master", [item["key"] for item in combo])
        self.assertIn("untouchable", [item["key"] for item in untouchable])
        self.assertIn("true_aim", [item["key"] for item in accuracy])

    def test_existing_player_totals_backfill_lifetime_achievement_progress(self):
        unlocked = self.manager.seed_existing_stats({
            "total_games_played": 12,
            "total_score": 120_000,
            "total_enemies_killed": 1_200,
            "total_powerups_collected": 60,
        })

        keys = {item["key"] for item in unlocked}
        self.assertTrue({
            "veteran_pilot",
            "score_legend",
            "first_contact",
            "invasion_eraser",
            "power_surge",
            "cache_collector",
        }.issubset(keys))


if __name__ == "__main__":
    unittest.main()
