# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Update with your MySQL password
    'database': 'space_invaders'
}

# Game Settings
GAME_CONFIG = {
    'screen_width': 800,
    'screen_height': 600,
    'fps': 60,
    'player_speed': 8,
    'enemy_speed': 2,
    'bullet_speed': 10,
    'powerup_drop_chance': 0.25,
    'heart_drop_chance': 0.3,
    'max_lives': 3,
    'shield_duration': 300,  # 5 seconds at 60 FPS
    'multi_shot_duration': 300
}