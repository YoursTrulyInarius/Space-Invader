import unittest

from database import Database


class FakeCursor:
    def __init__(self):
        self.queries = []
        self.rowcount = 1

    def execute(self, query, params=None):
        self.queries.append((query, params))

    def fetchone(self):
        return None

    def fetchall(self):
        return []

    def close(self):
        pass

    @property
    def lastrowid(self):
        return 1


class FakeConnection:
    def __init__(self, cursor):
        self.cursor_obj = cursor
        self.commits = 0
        self.closed = False
        self.database = None

    def cursor(self, dictionary=False):
        return self.cursor_obj

    def commit(self):
        self.commits += 1

    def close(self):
        self.closed = True


class DatabaseTests(unittest.TestCase):
    def test_initialize_schema_creates_required_tables_and_view(self):
        cursor = FakeCursor()
        connection = FakeConnection(cursor)
        db = Database.__new__(Database)
        db.connection = connection
        db.cursor = cursor
        db.database = "space_invaders_db"

        db.initialize_schema()

        queries = [query for query, _ in cursor.queries]
        self.assertTrue(any("CREATE TABLE IF NOT EXISTS players" in query for query in queries))
        self.assertTrue(any("CREATE TABLE IF NOT EXISTS scores" in query for query in queries))
        self.assertTrue(any("CREATE TABLE IF NOT EXISTS player_achievements" in query for query in queries))
        self.assertTrue(any("CREATE TABLE IF NOT EXISTS player_achievement_progress" in query for query in queries))
        self.assertTrue(any("CREATE VIEW leaderboard" in query for query in queries))
        self.assertTrue(any("ADD COLUMN `side_drone_powerups`" in query for query in queries))
        self.assertTrue(any("ADD COLUMN `score_multiplier_powerups`" in query for query in queries))
        self.assertGreaterEqual(connection.commits, 1)

    def test_game_session_saves_each_powerup_and_total_count(self):
        cursor = FakeCursor()
        connection = FakeConnection(cursor)
        db = Database.__new__(Database)
        db.connection = connection
        db.cursor = cursor

        result = db.update_game_session(10, 2, {
            "shield_powerups": 1,
            "multishot_powerups": 2,
            "heart_powerups": 3,
            "side_drone_powerups": 4,
            "score_multiplier_powerups": 5,
        })

        self.assertTrue(result)
        score_query, score_params = cursor.queries[0]
        self.assertIn("side_drone_powerups = %s", score_query)
        self.assertIn("score_multiplier_powerups = %s", score_query)
        self.assertEqual(score_params[2:8], (15, 1, 2, 3, 4, 5))
        self.assertEqual(connection.commits, 2)

    def test_game_history_returns_native_timestamp_for_ui_formatting(self):
        cursor = FakeCursor()
        connection = FakeConnection(cursor)
        db = Database.__new__(Database)
        db.connection = connection
        db.cursor = cursor

        self.assertEqual(db.get_game_history("Pilot", limit=5), [])

        query = cursor.queries[0][0]
        self.assertIn("game_date", query)
        self.assertNotIn("DATE_FORMAT", query)


if __name__ == "__main__":
    unittest.main()
