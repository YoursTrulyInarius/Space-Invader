# Space Invaders: Classic Arcade Edition

A retro-style arcade shooter built in Python with Pygame, procedural audio, and a MySQL-backed leaderboard system.

## Overview
Space Invaders: Classic Arcade Edition is a desktop game that combines classic arcade gameplay with a modern structure. The project uses object-oriented design for the game logic, a dedicated database layer for persistence, and procedural audio to keep the package self-contained.

## Latest Update
### Version 1.7 — Polished UI, Solar System Title Screen, and Button Icons
- Added a pixel-style orbiting solar system to the main profile screen while preserving the original starfield background.
- Reworked the title screen UI with larger central presentation, improved spacing, and cleaner menu button styling.
- Added icon-enhanced `LEADERBOARD F1` and `SETTINGS F2` buttons for better navigation affordance.
- Preserved modular game object structure and compatibility shim for `game/entities.py`.
- Kept the refined enemy destruction audio and boss rendering fixes from the prior refactor.

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
- `game/`: game loop, audio, UI, screens, and object modules
  - `player.py`: player ship state, movement, and shooting
  - `bullet.py`: player and enemy projectile classes
  - `enemy.py`: enemy and boss behavior
  - `powerup.py`: power-up object logic and rendering
  - `entities.py`: legacy compatibility shim for imports
  - `assets.py`: image loading and avatar textures
  - `audio.py`: procedural sound and music generation
  - `constants.py`: game-wide settings and helper functions
  - `screens.py`: menu, leaderboard, and audio settings screens
  - `ui.py`: pause menu and UI widgets
- `schema.sql`: SQL schema reference
- `tests/`: regression tests for the database layer

## Requirements
Install the following dependencies:

```bash
pip install pygame numpy mysql-connector-python
```

## Configuration
Update the connection settings in `config.py` before running the game.

## Running the Game
From the project root, run:

```bash
python main.py
```

On first launch, the database tables and leaderboard view are created automatically if needed.

## Database Schema
The project uses the following persistent structures:
- `players`: stores usernames and cumulative player stats
- `game_sessions`: stores per-session score, accuracy, duration, and power-up usage
- `leaderboard`: a view that returns the top scores for display

## Testing
A basic regression test is included for schema initialization:

```bash
python -m unittest discover -s tests -p "test_database.py" -v
```

## Version History
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