import pygame
import sys
import config
from database import Database

import constants
from managers.asset_manager import load_game_images
from managers.audio_manager import AudioManager
from managers.screen_manager import ProfileScreen
from managers.game_manager import GameManager as Game

# Pre-initialise audio before pygame.init()
pygame.mixer.pre_init(44100, -16, 2, 1024)
pygame.init()

def main():
    # Setup Database and Audio Manager
    db = Database(
        host=config.DB_CONFIG['host'],
        user=config.DB_CONFIG['user'],
        password=config.DB_CONFIG['password'],
        database=config.DB_CONFIG['database']
    )
    audio = AudioManager()

    # Initialise the display surface
    pygame.display.set_mode(
        (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT),
        pygame.RESIZABLE
    )
    pygame.display.set_caption("Space Invaders - Cabardo, Sonjeev C")
    
    # Load game textures/sprites AFTER display init
    load_game_images()

    # Main user flow loop
    while True:
        # Run user profile selection screen
        username = ProfileScreen(pygame.display.get_surface(), db, audio).run()
        if not username:
            break
            
        print(f"\nStarting game session for: {username}")
        # Run main game loop
        result = Game(username, db, audio).run()
        
        # If user did not request return to dashboard/profile selection, exit
        if result != 'dashboard':
            break

    # Clean up resources
    if db and db.connection:
        db.close()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()