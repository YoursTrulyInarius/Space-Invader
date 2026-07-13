import unittest

from database import Database


class FakeCursor:
    def __init__(self):
        self.queries = []

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
        db.database = "space_invaders"

        db.initialize_schema()

        queries = [query for query, _ in cursor.queries]
        self.assertTrue(any("CREATE TABLE IF NOT EXISTS players" in query for query in queries))
        self.assertTrue(any("CREATE TABLE IF NOT EXISTS game_sessions" in query for query in queries))
        self.assertTrue(any("CREATE VIEW leaderboard" in query for query in queries))
        self.assertGreaterEqual(connection.commits, 1)


if __name__ == "__main__":
    unittest.main()
