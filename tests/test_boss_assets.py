import unittest

import pygame

from entities.enemy import Boss
from managers import asset_manager


class BossAssetTests(unittest.TestCase):
    def setUp(self):
        self.original_bosses = asset_manager._IMG_BOSSES
        self.original_capybara = asset_manager._IMG_BOSS_CAPYBARA
        self.original_animal = asset_manager._IMG_BOSS_ANIMAL

    def tearDown(self):
        asset_manager._IMG_BOSSES = self.original_bosses
        asset_manager._IMG_BOSS_CAPYBARA = self.original_capybara
        asset_manager._IMG_BOSS_ANIMAL = self.original_animal

    def test_boss_images_cycle_by_level(self):
        bosses = [object() for _ in range(4)]
        asset_manager._IMG_BOSSES = bosses

        for level, boss in enumerate(bosses * 2, start=1):
            with self.subTest(level=level):
                self.assertIs(asset_manager.get_boss_img(level), boss)

    def test_boss_entity_uses_rotating_sprite(self):
        bosses = [object() for _ in range(4)]
        asset_manager._IMG_BOSSES = bosses

        for level, boss in enumerate(bosses * 2, start=1):
            with self.subTest(level=level):
                entity = Boss(level=level)
                self.assertIs(entity.img, boss)

    def test_missing_boss_image_uses_legacy_level_fallback(self):
        asset_manager._IMG_BOSSES = [None, None, None, None]
        asset_manager._IMG_BOSS_CAPYBARA = object()
        asset_manager._IMG_BOSS_ANIMAL = object()

        self.assertIs(asset_manager.get_boss_img(1), asset_manager._IMG_BOSS_CAPYBARA)
        self.assertIs(asset_manager.get_boss_img(2), asset_manager._IMG_BOSS_ANIMAL)

    def test_boss_without_sprite_draws_procedural_fallback(self):
        asset_manager._IMG_BOSSES = [None, None, None, None]
        asset_manager._IMG_BOSS_CAPYBARA = None
        asset_manager._IMG_BOSS_ANIMAL = None
        pygame.font.init()

        Boss(level=1).draw(pygame.Surface((800, 600)))


if __name__ == "__main__":
    unittest.main()
