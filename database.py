import mysql.connector
import config


class Database:
    def __init__(self, host=None, user=None, password=None, database=None):
        self.host = host or config.DB_CONFIG['host']
        self.user = user or config.DB_CONFIG['user']
        self.password = password or config.DB_CONFIG['password']
        self.database = database or config.DB_CONFIG['database']
        self.connection = None
        self.cursor = None
        self.connected = False
        self.connect()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def _is_ready(self):
        return self.connection is not None and self.cursor is not None

    def _ensure_connection(self):
        return self._is_ready()

    def connect(self):
        """Establish a database connection and initialize the schema."""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                charset='utf8mb4',
                use_unicode=True,
            )
            self._create_database_if_needed()
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                use_unicode=True,
            )
            self.cursor = self.connection.cursor(dictionary=True)
            self.connected = True
            self.initialize_schema()
            print("[OK] Database connected successfully!")
            return True
        except mysql.connector.Error as err:
            self.connected = False
            self.connection = None
            self.cursor = None
            print(f"[ERR] Database connection error: {err}")
            print("Please make sure:")
            print("  1. MySQL is running")
            print("  2. Credentials in config.py are correct")
            return False

    def _create_database_if_needed(self):
        if not self.connection:
            return False

        cursor = self.connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{self.database}`")
        cursor.close()
        self.connection.commit()
        return True

    def initialize_schema(self):
        """Create all required database objects if they don't exist."""
        if not self._ensure_connection():
            return False

        try:
            self._create_players_table()
            self._create_game_sessions_table()
            self._create_leaderboard_view()
            self._create_indexes()
            self.connection.commit()
            print("[OK] Database schema initialized successfully!")
            return True
        except mysql.connector.Error as err:
            print(f"[ERR] Error creating tables: {err}")
            return False

    def create_tables(self):
        """Backward-compatible alias for schema initialization."""
        return self.initialize_schema()

    def _create_players_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                total_score INT DEFAULT 0,
                total_games_played INT DEFAULT 0,
                total_enemies_killed INT DEFAULT 0,
                total_powerups_collected INT DEFAULT 0,
                highest_score INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

    def _create_game_sessions_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS game_sessions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                player_id INT NOT NULL,
                score INT DEFAULT 0,
                enemies_killed INT DEFAULT 0,
                powerups_collected INT DEFAULT 0,
                shield_powerups INT DEFAULT 0,
                multishot_powerups INT DEFAULT 0,
                heart_powerups INT DEFAULT 0,
                shots_fired INT DEFAULT 0,
                shots_hit INT DEFAULT 0,
                accuracy DECIMAL(5,2) DEFAULT 0,
                game_duration INT DEFAULT 0,
                game_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

    def _create_leaderboard_view(self):
        self.cursor.execute("DROP VIEW IF EXISTS leaderboard")
        self.cursor.execute("""
            CREATE VIEW leaderboard AS
            SELECT
                p.username,
                gs.score,
                gs.enemies_killed,
                gs.powerups_collected,
                gs.accuracy,
                DATE_FORMAT(gs.game_date, '%%Y-%%m-%%d %%H:%%i') as game_date
            FROM game_sessions gs
            JOIN players p ON gs.player_id = p.id
            ORDER BY gs.score DESC
            LIMIT 10
        """)

    def _create_indexes(self):
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_username ON players(username)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_player_id ON game_sessions(player_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_score ON game_sessions(score)")

    def get_or_create_player(self, username):
        """Get an existing player or create a new one."""
        if not self._ensure_connection():
            return None

        try:
            self.cursor.execute("SELECT id FROM players WHERE username = %s", (username,))
            result = self.cursor.fetchone()

            if result:
                return result['id']

            self.cursor.execute("INSERT INTO players (username) VALUES (%s)", (username,))
            self.connection.commit()
            return self.cursor.lastrowid

        except mysql.connector.Error as err:
            print(f"[ERR] Error getting/creating player: {err}")
            return None

    def start_game_session(self, player_id):
        """Create a new game session record."""
        if not self._ensure_connection():
            return None

        try:
            self.cursor.execute("""
                INSERT INTO game_sessions (player_id)
                VALUES (%s)
            """, (player_id,))
            self.connection.commit()
            return self.cursor.lastrowid
        except mysql.connector.Error as err:
            print(f"[ERR] Error starting game session: {err}")
            return None

    def update_game_session(self, game_id, player_id, stats):
        """Update a completed game session with final statistics."""
        if not self._ensure_connection():
            return None

        try:
            accuracy = 0
            if stats.get('shots_fired', 0) > 0:
                accuracy = (stats.get('shots_hit', 0) / stats['shots_fired']) * 100

            total_powerups = (
                stats.get('shield_powerups', 0)
                + stats.get('multishot_powerups', 0)
                + stats.get('heart_powerups', 0)
            )

            self.cursor.execute("""
                UPDATE game_sessions
                SET score = %s,
                    enemies_killed = %s,
                    powerups_collected = %s,
                    shield_powerups = %s,
                    multishot_powerups = %s,
                    heart_powerups = %s,
                    shots_fired = %s,
                    shots_hit = %s,
                    accuracy = %s,
                    game_duration = %s
                WHERE id = %s
            """, (
                stats.get('score', 0),
                stats.get('enemies_killed', 0),
                total_powerups,
                stats.get('shield_powerups', 0),
                stats.get('multishot_powerups', 0),
                stats.get('heart_powerups', 0),
                stats.get('shots_fired', 0),
                stats.get('shots_hit', 0),
                accuracy,
                stats.get('duration', 0),
                game_id,
            ))
            self.connection.commit()

            self.cursor.execute("""
                UPDATE players
                SET total_score = total_score + %s,
                    total_games_played = total_games_played + 1,
                    total_enemies_killed = total_enemies_killed + %s,
                    total_powerups_collected = total_powerups_collected + %s,
                    highest_score = GREATEST(highest_score, %s)
                WHERE id = %s
            """, (
                stats.get('score', 0),
                stats.get('enemies_killed', 0),
                total_powerups,
                stats.get('score', 0),
                player_id,
            ))
            self.connection.commit()
            print(f"[OK] Game session updated: Score={stats.get('score', 0)}, Enemies={stats.get('enemies_killed', 0)}")
            return True

        except mysql.connector.Error as err:
            print(f"[ERR] Error updating game session: {err}")
            return False

    def get_leaderboard(self):
        """Get the top 10 scores."""
        if not self._ensure_connection():
            return []

        try:
            self.cursor.execute("""
                SELECT
                    username,
                    score,
                    enemies_killed,
                    powerups_collected,
                    ROUND(accuracy, 2) as accuracy,
                    game_date
                FROM leaderboard
            """)
            return self.cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"[ERR] Error fetching leaderboard: {err}")
            return []

    def get_player_stats(self, username):
        """Get player statistics."""
        if not self._ensure_connection():
            return None

        try:
            self.cursor.execute("""
                SELECT
                    total_score,
                    total_games_played,
                    total_enemies_killed,
                    total_powerups_collected,
                    highest_score,
                    DATE_FORMAT(created_at, '%%Y-%%m-%%d') as created_at
                FROM players
                WHERE username = %s
            """, (username,))
            return self.cursor.fetchone()
        except mysql.connector.Error as err:
            print(f"[ERR] Error fetching player stats: {err}")
            return None

    def get_game_history(self, username, limit=10):
        """Get recent game history for a player."""
        if not self._ensure_connection():
            return []

        try:
            self.cursor.execute("""
                SELECT
                    score,
                    enemies_killed,
                    powerups_collected,
                    ROUND(accuracy, 2) as accuracy,
                    game_duration,
                    DATE_FORMAT(game_date, '%%Y-%%m-%%d %%H:%%i') as game_date
                FROM game_sessions gs
                JOIN players p ON gs.player_id = p.id
                WHERE p.username = %s
                ORDER BY gs.game_date DESC
                LIMIT %s
            """, (username, limit))
            return self.cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"[ERR] Error fetching game history: {err}")
            return []

    def get_player_rank(self, username):
        """Get a player's ranking based on highest score."""
        if not self._ensure_connection():
            return None

        try:
            self.cursor.execute("""
                SELECT COUNT(*) + 1 as rank
                FROM players
                WHERE highest_score > (
                    SELECT highest_score FROM players WHERE username = %s
                )
            """, (username,))
            result = self.cursor.fetchone()
            return result['rank'] if result else None
        except mysql.connector.Error as err:
            print(f"[ERR] Error getting player rank: {err}")
            return None

    def close(self):
        """Close the database connection safely."""
        if self.cursor is not None:
            try:
                self.cursor.close()
            except mysql.connector.Error:
                pass
            finally:
                self.cursor = None

        if self.connection is not None:
            try:
                self.connection.close()
            except mysql.connector.Error:
                pass
            finally:
                self.connection = None

        self.connected = False
        print("[OK] Database connection closed.")