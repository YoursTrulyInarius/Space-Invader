# Space Invaders: Classic Arcade Edition (V.1.4)
### A Project for **INTEGRATIVE PROGRAMMING TECHNOLOGY**

Welcome to **Space Invaders: Classic Arcade Edition (V.1.4)**—a premium, fully-featured retro space shooter built as a project for **Integrative Programming Technology**.

## 💻 System Overview
This system is a desktop-based 2D arcade shooter that seamlessly integrates a standalone Python/Pygame client with a persistent MySQL backend database. Its primary purpose is to demonstrate **Integrative Programming Technology** concepts by combining procedural audio generation, real-time graphics rendering, object-oriented game logic, and external database management into a single, unified software application. The system tracks individual player sessions, manages high scores, and generates real-time performance analytics (such as weapon accuracy and playtime).

---

## 📜 Version History & Changelog

### **Version 1.4 (Current Update) — Bug Fixes & Leaderboard/Audio UI**
- **Fixed broken sprite transparency:** Boss and player-ship sprites could render with a solid magenta/black background box instead of a transparent one on machines without `numpy` installed. Sprite colorkey removal now has a real, working pure-pygame fallback, so transparency works correctly regardless of whether `numpy` is present.
- **Fixed silent audio failures:** All SFX/music are synthesized at runtime with `numpy`; if it was missing, sound disabled itself with only a single easy-to-miss console line. Missing-audio errors are now surfaced clearly, and a `requirements.txt` (pygame, numpy, mysql-connector-python) has been added so a fresh clone installs everything needed with `pip install -r requirements.txt`.
- **Fixed enemies overlapping the HUD:** The top row of the alien formation (and the boss) could spawn high enough to visually collide with the SCORE / LEVEL / LIVES bar at the top of the screen. Spawn positions now keep clear of the HUD at all times.
- **New: Leaderboard screen.** View the top 10 global scores (callsign, score, kills, accuracy, date) from the main menu (`F1` or the LEADERBOARD button) or mid-game from the pause menu — no need to finish a run just to check standings. Dates are shown in a clean, readable format (e.g. `July 1, 2026`), rows are zebra-striped, and the top 3 ranks get gold/silver/bronze highlighting.
- **New: Standalone Audio Settings screen.** Adjust SFX and music volume — with a live "Test SFX" button — from the main menu (`F2` or the AUDIO SETTINGS button), not just from the in-game pause menu.
- **Fixed pause menu layout:** The options panel now sizes itself to however many options it holds, so buttons (including the new LEADERBOARD option) never get clipped off the bottom.
- **Fixed main menu overlap:** The LEADERBOARD/AUDIO SETTINGS buttons no longer collide with the "SPACE INVADERS" title; they now sit in a slim row above it at any window size.

### **Version 1.3**
- **Boss Fights & Level Progression:** Infinite survival mode has been replaced with a structured wave system. Clear the alien grid to face off against the Boss (Capybara or Raccoon UFO) at the end of every wave!
- **High-Quality Sprites:** Integrated photorealistic pixel art for the player's space fighter jet and vibrant magenta chroma-keyed boss UFO sprites.
- **Visual Effects Overhaul:** Upgraded player bullets to thick, glowing cyan laser beams with fading trails. Enemy rockets are now pulsating plasma capsules with engine flares. Bosses feature dynamic, pulsing health auras.
- **Audio Improvements:** The typewriter-style explosion sound was completely overhauled into a deep, bassy synthesized boom effect.
- **Offline / Standalone Mode:** Improved database resilience. The game will now gracefully handle MySQL connection failures and allow you to play offline without crashing.

### **Version 1.2**
- **Fluid Responsive Design:** Introduced fully dynamic and responsive fluid layout replacing standard letterboxed scaling. The game window can be resized to any resolution or aspect ratio in real-time, and the UI and gameplay adapt automatically.
- **Power-up Icons:** Upgraded power-ups from flat text to customized pixel-art drop icons (Shield 🛡️, Multi-shot ⚡, Heart ♥).

### **Version 1.0 (Base Release)**
- **Core Gameplay:** Classic retro arcade layout with three distinct pre-rendered pixel-art alien types (Crab, Squid, UFO).
- **Programmatic Audio:** Real-time wave-synthesized sound effects (shooting, hits, power-ups) and a looping retro background music track powered by NumPy.
- **Database Integration:** Setup persistent MySQL connection for tracking player profiles, high scores, accuracy, and playtime metrics.
- **Interactive UI:** Dynamic menus, floating damage text, and an interactive pause menu with working volume sliders.

---

## 🛠️ Tech Stack

- **Language:** Python 3.8+
- **Graphics & Game Loop:** Pygame 2.6+
- **Audio Synthesis:** NumPy (used for procedural sine-wave & noise audio synthesis)
- **Database Connection:** MySQL Server (using `mysql-connector-python` adapter)

---

## 🎮 Key Features

- **🏆 Leaderboard & Audio Settings Screens (NEW in v1.4):** Check the top-10 global leaderboard or adjust SFX/music volume straight from the main menu (`F1` / `F2`) or mid-game from the pause menu — no need to finish a run first.
- **🛸 Wave Progression & Epic Boss Fights:** Clear the grid of alien invaders to face off against powerful end-of-wave Bosses (featuring custom Capybara and Raccoon UFOs!). Bosses scale in difficulty and feature dynamic, pulsating health auras and spread-shot attacks.
- **✈️ High-Quality Visual Assets:** Pilot a newly integrated, photorealistic high-fidelity space fighter jet. Player bullets have been upgraded to glowing cyan laser beams, while enemy projectiles are now pulsating plasma capsules with engine flares.
- **👾 Classic Retro Aesthetics:** Dynamic 130-star scrolling parallax background with alternating leg-animation frames for alien grunts, and Monospace font styling (`Consolas`) for terminal-style layouts.
- **📱 Fluid Responsive Design:** Drag and resize the window to any resolution or aspect ratio; the gameplay area, UI, and enemy spawning grid adapt automatically in real-time.
- **🔊 Programmatic Retro Audio:** Real-time wave-synthesized sound effects (featuring a deep synthesized explosion boom) and a looping retro bass background music track built dynamically using NumPy.
- **🛡️ Interactive Pause Menu (`ESC`):** Instant game suspension with interactive volume adjustment sliders for SFX and BGM, plus quick access to the leaderboard and dashboard.
- **🗃️ Persistent MySQL Database (with Offline Support):** Tracks player profiles, high scores, total playtime, accuracy, and power-up collection statistics. The game now gracefully falls back to offline mode if the database connection fails.

---

## 🚀 What's Next?
As we build on top of Version 1.4, upcoming milestones include:
- **Leaderboard filters & search:** Filter the leaderboard by player or date range.
- **Enhanced Settings:** Additional configuration sliders for difficulty tuning and key re-binding options.

---

## ⌨️ Controls

| Key / Input | Action |
| :--- | :--- |
| **Arrow Keys / A & D** | Move Left / Right |
| **SPACEBAR** | Shoot Blaster |
| **ESCAPE (ESC)** | Toggle Pause Menu / Back to Main Menu (Settings) |
| **F1** *(Main Menu)* | View Leaderboard |
| **F2** *(Main Menu)* | Open Audio Settings |
| **R** *(Game Over)* | Quick Restart (saves previous session stats first) |
| **D** *(Game Over)* | Return to Dashboard / Callsign Screen |
| **Q** *(Game Over)* | Exit Application |
| **Mouse / Click** | Navigate buttons and drag settings sliders |

---

## 🏗️ Architecture & Database Structure

The project connects to a local MySQL instance using database settings defined in `config.py`.

### Database Schema

1. **`players`:**
   - Stores user profiles using a unique callsign (`username`).
   - Accumulates historical metrics (highest score, total games played, total enemies killed).
2. **`game_sessions`:**
   - Logs specific details of every played game (score, accuracy, duration, shield/multishot/heart counts).
3. **`leaderboard` (View):**
   - Combines player identities and game sessions into a sorted list representing the top 10 highest performances.

---

## ⚙️ Requirements & Installation

1. **Prerequisites:**
   - Python 3.8+
   - MySQL Server running locally with a database named `space_invaders`.
   - Python libraries: `pygame`, `mysql-connector-python`, and `numpy` (for synthesized audio and sprite transparency). Install all of them at once with:
     ```
     pip install -r requirements.txt
     ```
     > ⚠️ **Important:** `numpy` is required for both the procedural sound effects/music *and* correct sprite transparency (boss/player-ship backgrounds). If it's missing, audio will silently disable itself and sprites may show a solid colored background box instead of being transparent. Always run the command above after cloning on a new machine.

2. **Configuration:**
   - Update database credentials in `config.py` (e.g., host, user, password).

3. **Running the game:**
   - Run `python main.py`. The database tables and views are automatically created on first launch if they do not exist.