# Space Invaders: Classic Arcade Edition

A retro-style arcade shooter built in Python with Pygame, procedural audio, and a MySQL-backed leaderboard system.

## Overview
Space Invaders: Classic Arcade Edition is a desktop game that combines classic arcade gameplay with a modern structure. The project uses object-oriented design for the game logic, a dedicated database layer for persistence, and procedural audio to keep the package self-contained.

## Latest Changes
- Added MySQL connectivity through `mysql-connector-python`.
- Added automatic creation of the `space_invaders_db` database and its schema.
- Added `players` and `scores` tables plus the `leaderboard` view.
- Added player CRUD operations, score saving, leaderboard loading, player history, and profile updates in `database.py`.
- Added `settings.py` and `settings.json` for persistent sound volume and mobile-control preferences.
- Added `requirements.txt` and a project-local `.venv` workflow.
- Preserved offline-safe gameplay when MySQL is unavailable.
- Reorganized game entities and managers, with procedural visuals, audio, power-ups, and boss encounters.

## Features
- Wave-based gameplay with boss encounters
- Responsive window resizing and adaptive UI
- Power-ups including shield, multishot, and extra life
- Procedural sound effects and background music
- Persistent player profiles and match history
- Global leaderboard and audio settings screens
- Offline-safe gameplay when the database is unavailable

## Controls
- Arrow Keys / A and D: Move left and right
- Spacebar: Shoot
- Escape: Pause or return to the menu
- F1: Open leaderboard
- F2: Open audio settings
- R: Restart after game over
- D: Return to the profile screen
- Q: Quit

## Project Structure
- `main.py`: entry point for the game
- `database.py`: database wrapper and schema management
- `config.py`: database and gameplay configuration
- `constants.py`: game-wide settings and helper functions
- `entities/`: game entity classes
  - `player.py`: player ship state, movement, and shooting
  - `enemy.py`: enemy and boss behavior
  - `bullet.py`: player and enemy projectile classes
  - `powerup.py`: power-up object logic and rendering
- `managers/`: system manager modules
  - `game_manager.py`: core game manager and event loop
  - `asset_manager.py`: image loading and asset management
  - `audio_manager.py`: procedural sound and music generation
  - `screen_manager.py`: profile, leaderboard, and settings screens
  - `ui_manager.py`: pause menu and UI widgets
- `assets/`: game assets
  - `images/`: game textures, sprites, and background assets
  - `sounds/`: placeholder for sound resources
- `schema.sql`: SQL schema reference
- `tests/`: regression tests for the database layer

## Requirements

- Windows, macOS, or Linux
- Python 3.11 or newer
- MySQL Server 8.x or compatible MySQL installation
- Git

The game can open without MySQL, but profiles, scores, and leaderboards require a running MySQL server.

## Clone the Project

```bash
git clone https://github.com/YoursTrulyInarius/Space-Invader.git
cd Space-Invader
```

Open the cloned folder in VS Code, then create the virtual environment from the project root.

## Virtual Environment Setup

PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks script activation, run the project without activation:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

The `.venv/` directory is ignored by Git and should not be committed.

## Database Setup

1. Start MySQL Server.
2. Open [config.py](config.py) and set the MySQL host, username, password, and database if needed:

   ```python
   DB_CONFIG = {
     'host': 'localhost',
     'user': 'root',
     'password': 'your_mysql_password',
     'database': 'space_invaders_db'
   }
   ```

3. Run the setup script from the project root. It creates `space_invaders_db`, `players`, `scores`, indexes, and `leaderboard` automatically when the configured MySQL user has database-creation permission:

  ```powershell
  python database_setup.py
  ```

  When using the environment without activation, run `.\.venv\Scripts\python.exe database_setup.py`.

For advanced/manual SQL setup, run [schema.sql](schema.sql) in MySQL:

```bash
mysql -u root -p < schema.sql
```

`schema.sql` is intended as a clean rebuild script and drops the existing `scores`, `players`, and `leaderboard` objects. Back up production data before using it.

### Test the Connection and Insert a Player

With `.venv` active, run:

```powershell
python -c "from database import Database; db = Database(); player_id = db.create_player('test_player'); print('inserted player:', player_id); db.close()"
```

The command should print the inserted player ID. Because usernames are unique, remove `test_player` or use another username before repeating the command.

## Local Settings

`settings.json` stores local preferences:

- `sfx_volume`: sound-effect volume from `0.0` to `1.0`
- `music_volume`: music volume from `0.0` to `1.0`
- `mobile_controls`: reserved toggle for mobile input support

The audio settings screen saves volume changes automatically. The file contains no database credentials.

## Run the Game

From the project root, with `.venv` active:

```bash
python main.py
```

On first launch, the database and tables are created automatically when MySQL is available. If MySQL is unavailable, the game remains playable without persistent data.

## Database Schema
The project uses the following persistent structures:
- `players`: stores usernames and cumulative player stats
- `scores`: stores per-session score, accuracy, duration, and power-up usage
- `leaderboard`: a view that returns the top scores for display

## Testing

Run the database regression tests with the virtual-environment interpreter:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

The tests use lightweight fakes for schema initialization and do not require a live MySQL server.

## Version History
### Version 2.0
- Restructured workspace codebase directory layout to separate entities and managers
- Applied dynamic elliptical masking to hide dark border corners on enemy ship sprites
- Designed new procedural metallic cyan energy bolts for the player (with trailing plasma and sparks)
- Designed glowing red plasma artillery shells for the enemy (with pulsing halo and hot core)
- Relocated PNG game sprites to `assets/images/` and updated loader references

### Version 1.7
- Added a pixelated solar system animation to the profile menu screen
- Polished main menu and button visuals with stronger scene presentation
- Added icons for leaderboard/settings menu buttons
- Preserved earlier modular refactor and audio improvements

### Version 1.6
- Modular game object refactor
- Refined enemy destruction audio
- Fixed boss rendering import issue

### Version 1.5
- OOP refactor for cleaner code
- Improved database initialization and startup reliability
- Added regression test coverage

### Version 1.4
- Leaderboard screen and audio settings screen
- UI and HUD fixes
- Improved sprite transparency and audio handling

### Version 1.3
- Boss fights and wave progression
- New visual assets and audio improvements
- Offline-safe database behavior

### Version 1.2
- Responsive window resizing
- New power-up icons and improved UI

### Version 1.0
- Core gameplay, audio synthesis, and MySQL integration
