# Space Invaders: Classic Arcade Edition (V.1)

Welcome to **Space Invaders: Classic Arcade Edition (V.1)**—a premium, fully-featured retro space shooter built in Python using **Pygame** and backed by a persistent **MySQL** database.

> **Note:** This is **Version 1.0 (V.1)** of the game. Additional changes, optimizations, and updates will be made later as development continues.

---

## 🎮 Key Features

- **👾 Classic Retro Aesthetics:**
  - Dynamic 130-star scrolling parallax background.
  - Three distinct pre-rendered pixel-art alien types (Crab, Squid, UFO) inspired by the original arcade layout.
  - Alternating leg-animation frames and vertical ship bobbing.
  - Monospace font styling (`Consolas`) for terminal-style layouts.
  - Customized pixel-art power-up drop icons (Shield 🛡️, Multi-shot ⚡, Heart ♥) replacing flat text characters.

- **🔊 Programmatic Retro Audio:**
  - Real-time wave-synthesized sound effects (shooting, hits, explosions, power-ups, game-over, and victory fanfare) built dynamically.
  - A looping retro bass/melody background music track (BGM).

- **🛡️ Interactive Pause Menu (`ESC`):**
  - Instant game suspension.
  - Options: **CONTINUE** (resume game), **SETTINGS** (interactive volume adjustment sliders for SFX and BGM), and **DASHBOARD** (safely return to pilot registration).

- **🗃️ Persistent MySQL Database:**
  - Tracks player profiles, high scores, total playtime, accuracy, enemies destroyed, and power-up collection statistics.
  - Computes and displays a live, dynamically updated top-scores leaderboard on the game-over screen.

---

## ⌨️ Controls

| Key / Input | Action |
| :--- | :--- |
| **Arrow Keys / A & D** | Move Left / Right |
| **SPACEBAR** | Shoot Blaster |
| **ESCAPE (ESC)** | Toggle Pause Menu / Back to Main Menu (Settings) |
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
   - Python libraries: `pygame`, `mysql-connector-python`, and `numpy` (for synthesized audio).

2. **Configuration:**
   - Update database credentials in `config.py` (e.g., host, user, password).

3. **Running the game:**
   - Run `python main.py`. The database tables and views are automatically created on first launch if they do not exist.
