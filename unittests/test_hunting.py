import unittest
from unittest.mock import MagicMock

from enums import ClanName, Rank, Direction, TileType
from game_config import GameConfig
from game_engine import GameEngine

# --- Mock Classes ---
# These classes simulate the behavior of real objects for isolated testing.

class MockCat:
    """A mock Cat class for testing the GameEngine."""
    def __init__(self, name, clan_id, position):
        self.name = name
        self.clan_id = clan_id
        self.position = position
        self.move = MagicMock()

    def __repr__(self):
        return f"MockCat(name='{self.name}', position={self.position})"

class MockClan:
    """A mock Clan class for testing resource updates."""
    def __init__(self, name):
        self.name = name
        self.prey_pile = 0
        self.add_prey = MagicMock(side_effect=self._add_prey)

    def _add_prey(self, amount):
        self.prey_pile += amount

# --- Test Suite for Hunt Moves ---

class TestHuntMove(unittest.TestCase):
    """Test suite for the GameEngine's execute_hunt_move method."""

    def setUp(self):
        """This method runs before each test."""
        self.original_m = GameConfig.M
        self.original_n = GameConfig.N
        GameConfig.M = 3
        GameConfig.N = 6
        self.engine = GameEngine()
        self.mock_thunderclan = MockClan(ClanName.THUNDERCLAN)
        self.engine.clans[ClanName.THUNDERCLAN] = self.mock_thunderclan

    def tearDown(self):
        """This method runs after each test to clean up."""
        GameConfig.M = self.original_m
        GameConfig.N = self.original_n

    def test_execute_hunt_move_success_and_catch_prey(self):
        """
        Tests a successful hunt where a cat moves and catches prey
        without hitting a border.
        """
        # SETUP
        start_pos = (-5, 5)
        cat = MockCat("Lionheart", ClanName.THUNDERCLAN, start_pos)

        # Place prey on a tile in the cat's path
        prey_pos = (-5, 6)
        prey_tile = self.engine.board.get_tile(prey_pos)
        self.assertIsNotNone(prey_tile)
        prey_tile.prey_count = 2

        # ACTION
        # Execute a hunt move of 2 steps North
        final_pos, prey_caught = self.engine.execute_hunt_move(cat, Direction.N, 2)

        # ASSERTIONS
        expected_pos = (-5, 7)
        self.assertEqual(final_pos, expected_pos, "Cat should end up at the new position.")
        cat.move.assert_called_once_with(expected_pos)

        # The cat should have caught the prey
        self.assertEqual(prey_caught, 2, "Should have caught 2 prey.")
        
        # The prey should be removed from the tile
        self.assertEqual(prey_tile.prey_count, 0, "Prey should be removed from the tile after being caught.")

        # The clan's add_prey method should have been called
        self.mock_thunderclan.add_prey.assert_called_once_with(2)

    def test_execute_hunt_move_stops_at_border(self):
        """
        Tests that a hunting cat correctly stops before entering a BORDER tile.
        """
        # SETUP
        start_pos = (-3, 5)
        cat = MockCat("Tigerclaw", ClanName.THUNDERCLAN, start_pos)

        # ACTION
        final_pos, prey_caught = self.engine.execute_hunt_move(cat, Direction.E, 5)

        # ASSERTIONS
        # The cat should move 1 step and stop at the last valid hunting tile before the border.
        expected_pos = (-2, 5)
        self.assertEqual(final_pos, expected_pos)
        cat.move.assert_called_once_with(expected_pos)
        self.assertEqual(prey_caught, 0)

if __name__ == '__main__':
    unittest.main()
