# Space Invaders: Classic Arcade Edition (V.1.3)
### A Project for **INTEGRATIVE PROGRAMMING TECHNOLOGY**

Welcome to **Space Invaders: Classic Arcade Edition (V.1.3)**—a premium, fully-featured retro space shooter built as a project for **Integrative Programming Technology**.

## 💻 System Overview
This system is a desktop-based 2D arcade shooter that seamlessly integrates a standalone Python/Pygame client with a persistent MySQL backend database. Its primary purpose is to demonstrate **Integrative Programming Technology** concepts by combining procedural audio generation, real-time graphics rendering, object-oriented game logic, and external database management into a single, unified software application. The system tracks individual player sessions, manages high scores, and generates real-time performance analytics (such as weapon accuracy and playtime).

---

## 📜 Version History & Changelog

### **Version 1.3 (Current Update)**
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

- **🛸 Wave Progression & Epic Boss Fights (NEW in v1.3):** Clear the grid of alien invaders to face off against powerful end-of-wave Bosses (featuring custom Capybara and Raccoon UFOs!). Bosses scale in difficulty and feature dynamic, pulsating health auras and spread-shot attacks.
- **✈️ High-Quality Visual Assets (NEW in v1.3):** Pilot a newly integrated, photorealistic high-fidelity space fighter jet. Player bullets have been upgraded to glowing cyan laser beams, while enemy projectiles are now pulsating plasma capsules with engine flares.
- **👾 Classic Retro Aesthetics:** Dynamic 130-star scrolling parallax background with alternating leg-animation frames for alien grunts, and Monospace font styling (`Consolas`) for terminal-style layouts.
- **📱 Fluid Responsive Design:** Drag and resize the window to any resolution or aspect ratio; the gameplay area, UI, and enemy spawning grid adapt automatically in real-time.
- **🔊 Programmatic Retro Audio:** Real-time wave-synthesized sound effects (featuring a deep synthesized explosion boom) and a looping retro bass background music track built dynamically using NumPy.
- **🛡️ Interactive Pause Menu (`ESC`):** Instant game suspension with interactive volume adjustment sliders for SFX and BGM.
- **🗃️ Persistent MySQL Database (with Offline Support):** Tracks player profiles, high scores, total playtime, accuracy, and power-up collection statistics. The game now gracefully falls back to offline mode if the database connection fails.

---

## 🚀 What's Next?
As we build on top of Version 1.3, upcoming milestones include:
- **Implementing the Leaderboard UI:** Further refining the dashboard leaderboards with fully sorted global lists, search filters, and player profile inspect cards.
- **Enhanced Settings:** Additional configuration sliders for difficulty tuning and key re-binding options.

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
