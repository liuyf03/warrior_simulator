import unittest
from unittest.mock import MagicMock

from enums import ClanName, Rank, Direction, TileType
from game_config import GameConfig
from game_engine import GameEngine

# --- Mock Classes ---

class MockCat:
    """A mock Cat class for testing the GameEngine."""
    def __init__(self, name, clan_id, position):
        self.name = name
        self.clan_id = clan_id
        self.position = position
        self.move = MagicMock()

    def __repr__(self):
        return f"MockCat(name='{self.name}', position={self.position})"

# --- Test Suite for Border Patrol Moves ---

class TestBorderPatrol(unittest.TestCase):
    """Test suite for the GameEngine's execute_border_patrol_move method."""

    def setUp(self):
        """This method runs before each test."""
        self.original_m = GameConfig.M
        self.original_n = GameConfig.N
        GameConfig.M = 3
        GameConfig.N = 6
        self.engine = GameEngine()
        # No need for mock clans if we aren't testing resource changes

    def tearDown(self):
        """This method runs after each test to clean up."""
        GameConfig.M = self.original_m
        GameConfig.N = self.original_n

    def test_patrol_stops_at_enemy_scent(self):
        """
        Tests that a patrol stops immediately upon finding an enemy paw print.
        """
        # SETUP
        start_pos = (-1, 5)
        cat = MockCat("Bluestar", ClanName.THUNDERCLAN, start_pos)
        enemy_scent_pos = (-1, 1)
        enemy_scent_tile = self.engine.board.get_tile(enemy_scent_pos)
        enemy_scent_tile.paw_print = ClanName.RIVERCLAN

        # ACTION
        final_pos, _ = self.engine.execute_border_patrol_move(cat, Direction.S, 5)

        # ASSERTIONS
        self.assertEqual(final_pos, enemy_scent_pos)
        cat.move.assert_called_once_with(enemy_scent_pos)

    def test_patrol_leaves_scent_only_on_highlighted_tiles(self):
        """
        Tests that a cat on patrol only leaves its scent on highlighted tiles.
        """
        # SETUP
        start_pos = (-5, -1)
        cat = MockCat("Whitestorm", ClanName.THUNDERCLAN, start_pos)
        path_tile_1 = self.engine.board.get_tile((-4, -1))
        highlighted_tile = self.engine.board.get_tile((-3, -1))
        highlighted_tile.is_highlighted = True

        # ACTION
        self.engine.execute_border_patrol_move(cat, Direction.E, 3)

        # ASSERTIONS
        self.assertIsNone(path_tile_1.paw_print)
        self.assertEqual(highlighted_tile.paw_print, cat.clan_id)

    def test_patrol_stops_at_enemy_territory(self):
        """
        Tests that a patrol can walk on the border but stops before entering enemy territory.
        """
        # SETUP
        start_pos = (0, 5) # Border tile
        cat = MockCat("Graystripe", ClanName.THUNDERCLAN, start_pos)

        # ACTION
        final_pos, _ = self.engine.execute_border_patrol_move(cat, Direction.E, 3)

        # ASSERTIONS
        last_pos_before_enemy_territory = (1,5)
        self.assertEqual(final_pos, last_pos_before_enemy_territory)

if __name__ == '__main__':
    unittest.main()