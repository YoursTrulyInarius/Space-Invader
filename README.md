# Space Invaders: Classic Arcade Edition

A retro-style arcade shooter built in Python with Pygame, procedural audio, and a MySQL-backed leaderboard system.

## Overview
Space Invaders: Classic Arcade Edition is a desktop game that combines classic arcade gameplay with a modern structure. The project uses object-oriented programming for the game logic and a dedicated database layer for persistence, player stats, and leaderboard tracking.

## Latest Update
### Version 1.5 — OOP Refactor and Database Reliability
- Refactored the persistence layer into a cleaner object-oriented database class.
- Added explicit schema initialization so tables and the leaderboard view are created automatically on startup.
- Improved fresh-setup handling by creating the target database when it does not exist.
- Hardened connection-state handling for smoother online/offline behavior.
- Added a regression test covering schema initialization.

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
- [main.py](main.py): entry point for the game
- [database.py](database.py): database wrapper and schema management
- [config.py](config.py): database and gameplay configuration
- [game/](game/): game loop, entities, UI, and screens
- [schema.sql](schema.sql): SQL schema reference
- [tests/](tests/): regression tests for the database layer

## Requirements
Install the following dependencies:

```bash
pip install pygame
pip install numpy
pip install mysql-connector-python
```

If you prefer, you can also install them together:

```bash
pip install pygame numpy mysql-connector-python
```

## Configuration
Update the connection settings in [config.py](config.py) before running the game.

## Running the Game
From the project root, run:

```bash
python main.py
```

On first launch, the database tables and leaderboard view are created automatically if needed.

## Database Schema
The project uses the following persistent structures:
- players: stores usernames and cumulative player stats
- game_sessions: stores per-session score, accuracy, duration, and power-up usage
- leaderboard: a view that returns the top scores for display

## Testing
A basic regression test is included for schema initialization:

```bash
python -m unittest discover -s tests -p "test_database.py" -v
```

## Version History
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