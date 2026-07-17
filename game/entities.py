"""Compatibility shim for historical game.entities imports."""
from game.player import Player
from game.enemy import Enemy, Boss
from game.powerup import PowerUp

__all__ = ['Player', 'Enemy', 'Boss', 'PowerUp']
