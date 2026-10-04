# Space Invaders: Classic Arcade Edition
adadsaada
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
- Redesigned the login and registration screen with a responsive foreground panel and compact-window layout.
- Added complete keyboard focus navigation across callsign, password, login/register, and account-mode controls.
- Added Enter-key activation for the currently focused authentication action.
- Added four rotating boss sprites and periodic power-up drops during boss fights.
- Added a post-login pilot dashboard for gameplay, profile editing, statistics, match history, titles, leaderboard, and settings.
- Added 19 persistent achievements with lifetime and per-run progress on a keyboard-scrollable Titles page.
- Added Side Drones and a temporary 2x Score Multiplier power-up; drone drops use a lower random weight.
- Added persistent counters and safe startup migration for the new power-up session statistics.

## Features
- Wave-based gameplay with four rotating boss encounters
- Boss health is shown with a generic **BOSS** label; boss sprite names are not displayed
- Boss fights periodically spawn random power-ups during combat
- Responsive window resizing and adaptive UI
- Power-ups: shield, multishot, extra life, Side Drones, and a temporary 2x Score Multiplier
- Side Drones add two bullets to each player shot for 15 seconds and are less common than other power-ups
- Power-up effects and their remaining duration are shown in the gameplay HUD
- Procedural sound effects and background music
- Persistent player profiles and match history
- Login and registration with salted password hashes
- Post-login dashboard with profile editing, match history, statistics, and a titles page
- 19 persistent achievements covering lifetime milestones and per-run challenges
- Titles page shows locked/unlocked status and progress; browse with Up/Down, Page Up/Page Down, Home/End, or the mouse wheel
- Password visibility eye toggle on the login form
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
- Tab / Shift+Tab: Move through profile-screen controls
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
  - `achievement_manager.py`: achievement definitions, progress tracking, and unlock persistence
- `assets/`: game assets
  - `images/`: game textures, sprites, and background assets
  - `sounds/`: placeholder for sound resources
- `schema.sql`: SQL schema reference
- `tests/`: regression tests for database, dashboard, bosses, achievements, and power-ups

## Requirements

- Windows, macOS, or Linux
- Python 3.11 or newer
- MySQL Server 8.x or compatible MySQL installation
- Git

The game can open without MySQL, but login, profiles, saved scores, achievement persistence, and leaderboards require a running MySQL server.

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

3. Run the setup script from the project root. It creates `space_invaders_db`, the player, score, and achievement tables, indexes, and `leaderboard` automatically when the configured MySQL user has database-creation permission:

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
- `players`: stores usernames, password hashes, and cumulative player stats
- `scores`: stores per-session score, accuracy, duration, and counts for each power-up type
- `player_achievements`: stores each player's unlocked achievements
- `player_achievement_progress`: stores lifetime and per-run achievement metrics
- `leaderboard`: a view that returns the top scores for display

When upgrading an existing database, application startup adds missing password and power-up statistic columns. Existing player accounts created before login support must register a password before they can log in. Achievement tables are created automatically. `schema.sql` is a clean rebuild script that drops existing game tables and should only be used after backing up data.

## Login and Registration

The profile screen opens in **Login** mode. Enter a callsign and password, then press `Enter` or select **LOGIN**. Select **CREATE ACCOUNT** to register a new player; passwords must contain at least six characters. Select the eye icon inside the password field to show or hide the password while typing. Successful login opens the pilot dashboard rather than starting gameplay immediately. Choose **PLAY** to begin a run; use **PROFILE** to update your callsign, **STATS** to view lifetime totals and recent runs, or **TITLES** to browse all 19 achievements and their progress. The dashboard also provides the leaderboard, settings, and log-out actions.

## Testing

Run all automated regression tests with the virtual-environment interpreter:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

The tests use lightweight fakes for database behavior and do not require a live MySQL server. They cover the dashboard and achievements, boss sprite selection and fallback drawing, boss-fight power-up drops, power-up effects and statistics, and database schema/session behavior.

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
