-- Create database (if it doesn't exist)
CREATE DATABASE IF NOT EXISTS space_invaders;
USE space_invaders;

-- Drop tables if they exist (in correct order to avoid foreign key issues)
DROP TABLE IF EXISTS game_sessions;
DROP TABLE IF EXISTS players;

-- Create players table
CREATE TABLE players (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    total_score INT DEFAULT 0,
    total_games_played INT DEFAULT 0,
    total_enemies_killed INT DEFAULT 0,
    total_powerups_collected INT DEFAULT 0,
    highest_score INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create game_sessions table
CREATE TABLE game_sessions (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create view for leaderboard (using CREATE VIEW instead of CREATE OR REPLACE VIEW for compatibility)
CREATE VIEW leaderboard AS
SELECT 
    p.username,
    gs.score,
    gs.enemies_killed,
    gs.powerups_collected,
    gs.accuracy,
    DATE_FORMAT(gs.game_date, '%Y-%m-%d %H:%i') as game_date
FROM game_sessions gs
JOIN players p ON gs.player_id = p.id
ORDER BY gs.score DESC
LIMIT 10;

-- Optional: Create indexes for better performance
CREATE INDEX idx_username ON players(username);
CREATE INDEX idx_player_id ON game_sessions(player_id);
CREATE INDEX idx_score ON game_sessions(score);
CREATE INDEX idx_game_date ON game_sessions(game_date);