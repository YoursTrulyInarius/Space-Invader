import unittest
from datetime import datetime

import pygame

import constants
from constants import format_display_date
from managers.achievement_manager import ACHIEVEMENTS
from managers.screen_manager import DashboardScreen


class FakeDatabase:
    connected = True

    def __init__(self):
        self.player = {"id": 7, "username": "Pilot", "created_at": "2026-10-04"}
        self.updated = None

    def get_player(self, username):
        return self.player if username == self.player["username"] else None

    def get_player_stats(self, _username):
        return {
            "total_score": 100,
            "total_games_played": 2,
            "total_enemies_killed": 5,
            "total_powerups_collected": 1,
            "highest_score": 80,
        }

    def get_game_history(self, _username, limit=10):
        return []

    def get_player_rank(self, _username):
        return 1

    def get_player_achievements(self, _player_id):
        return []

    def get_achievement_progress(self, _player_id):
        return {"enemies_killed": 3}

    def update_player_profile(self, player_id, username):
        self.updated = (player_id, username)
        self.player["username"] = username
        return True


class DashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.font.init()

    def test_callsign_edit_updates_authenticated_dashboard_username(self):
        db = FakeDatabase()
        dashboard = DashboardScreen(None, db, None, "Pilot")
        dashboard.name_input.text = "NewPilot"

        dashboard._save_callsign()

        self.assertEqual(db.updated, (7, "NewPilot"))
        self.assertEqual(dashboard.username, "NewPilot")
        self.assertEqual(dashboard.name_input.text, "NewPilot")
        self.assertEqual(dashboard.message, "Callsign updated.")

    def test_empty_callsign_is_rejected(self):
        db = FakeDatabase()
        dashboard = DashboardScreen(None, db, None, "Pilot")
        dashboard.name_input.text = "   "

        dashboard._save_callsign()

        self.assertIsNone(db.updated)
        self.assertEqual(dashboard.username, "Pilot")
        self.assertEqual(dashboard.message, "Callsign cannot be empty.")

    def test_history_datetime_displays_as_readable_date(self):
        raw_date = datetime(2026, 10, 4, 16, 10)

        self.assertEqual(format_display_date(raw_date), "Oct 4, 2026")

    def test_titles_description_wraps_within_content_width(self):
        dashboard = DashboardScreen(None, FakeDatabase(), None, "Pilot")
        dashboard.screen = pygame.Surface((400, 240))
        font = pygame.font.SysFont("consolas", 18)
        text = "Your titles will appear here as you complete achievements."

        final_y = dashboard._draw_wrapped_text(text, font, (255, 255, 255),
                                               10, 10, 180, 24)

        self.assertGreater(final_y, 34)
        self.assertLessEqual(final_y, 10 + 24 * 5)

    def test_titles_page_draws_all_achievement_definitions(self):
        dashboard = DashboardScreen(None, FakeDatabase(), None, "Pilot")
        dashboard.screen = pygame.Surface((900, 700))
        dashboard.page = "titles"
        dashboard._draw_content(pygame.Rect(220, 100, 650, 570))

        self.assertEqual(len(dashboard.unlocked_achievements), 0)
        self.assertEqual(dashboard.achievement_progress["enemies_killed"], 3)

    def test_titles_can_be_browsed_using_keyboard_page_keys(self):
        dashboard = DashboardScreen(None, FakeDatabase(), None, "Pilot")
        visible = dashboard._titles_visible_count()
        max_scroll = len(ACHIEVEMENTS) - visible

        dashboard._scroll_titles(1, by_page=True)

        self.assertGreater(dashboard.titles_scroll, 0)
        self.assertLess(dashboard.titles_scroll, max_scroll)

        dashboard.titles_scroll = max_scroll
        dashboard._scroll_titles(1, by_page=True)
        self.assertEqual(dashboard.titles_scroll, max_scroll)

        dashboard._scroll_titles(-1, by_page=True)
        self.assertLess(dashboard.titles_scroll, max_scroll)

        dashboard.titles_scroll = 0
        dashboard._scroll_titles(-1, by_page=True)
        self.assertEqual(dashboard.titles_scroll, 0)

    def test_titles_up_down_scroll_one_achievement_per_press(self):
        dashboard = DashboardScreen(None, FakeDatabase(), None, "Pilot")

        dashboard._scroll_titles(1)
        self.assertEqual(dashboard.titles_scroll, 1)

        dashboard._scroll_titles(-1)
        self.assertEqual(dashboard.titles_scroll, 0)

    def test_titles_scroll_can_jump_to_last_achievement(self):
        dashboard = DashboardScreen(None, FakeDatabase(), None, "Pilot")
        dashboard.screen = pygame.Surface(
            (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT)
        )
        dashboard.page = "titles"
        dashboard.titles_scroll = len(ACHIEVEMENTS)
        dashboard._draw_content(dashboard._content_rect())

        self.assertEqual(dashboard.titles_scroll,
                         len(ACHIEVEMENTS) - dashboard._titles_visible_count())


if __name__ == "__main__":
    unittest.main()
