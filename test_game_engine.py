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
        # The move method is a MagicMock so we can track if it's called.
        self.move = MagicMock()

    def __repr__(self):
        return f"MockCat(name='{self.name}', position={self.position})"

class MockClan:
    """A mock Clan class for testing resource updates."""
    def __init__(self, name):
        self.name = name
        self.prey_pile = 0
        # The add_prey method is a MagicMock to track calls.
        self.add_prey = MagicMock(side_effect=self._add_prey)

    def _add_prey(self, amount):
        """Simulates the side effect of adding prey."""
        self.prey_pile += amount

# --- Test Suite ---

class TestGameEngine(unittest.TestCase):
    """Test suite for the GameEngine class."""

    def setUp(self):
        """This method runs before each test."""
        # Store original config values to restore them later
        self.original_m = GameConfig.M
        self.original_n = GameConfig.N

        # Set specific, predictable values for this test suite
        GameConfig.M = 3
        GameConfig.N = 6

        # Now initialize the engine. It will build its board using our test values.
        self.engine = GameEngine()

        # Replace the real clans with our mock clans for this test
        self.mock_thunderclan = MockClan(ClanName.THUNDERCLAN)
        self.engine.clans[ClanName.THUNDERCLAN] = self.mock_thunderclan

    def tearDown(self):
        """This method runs after each test to clean up."""
        # Restore the original GameConfig values
        GameConfig.M = self.original_m
        GameConfig.N = self.original_n

    def test_execute_hunt_move_success_and_catch_prey(self):
        """
        Tests a successful hunt where a cat moves and catches prey
        without hitting a border.
        """
        # 1. SETUP
        # Place a cat in ThunderClan territory
        start_pos = (-5, 5)
        cat = MockCat("Lionheart", ClanName.THUNDERCLAN, start_pos)

        # Place prey on a tile in the cat's path
        prey_pos = (-5, 6)
        prey_tile = self.engine.board.get_tile(prey_pos)
        self.assertIsNotNone(prey_tile, "Prey tile should exist on the board")
        prey_tile.prey_count = 2

        # 2. ACTION
        # Execute a hunt move of 2 steps North
        final_pos, prey_caught = self.engine.execute_hunt_move(cat, Direction.N, 2)

        # 3. ASSERTIONS
        # The cat should move 3 steps, as nothing is blocking it
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
        Tests that a hunting cat correctly stops before entering a BORDER tile,
        even if it has more steps to move.
        """
        # 1. SETUP
        # Place a cat a few steps away from the border in ThunderClan territory.
        # The border starts at x = -1, so this position is 2 steps away.
        start_pos = (-3, 5)
        cat = MockCat("Tigerclaw", ClanName.THUNDERCLAN, start_pos)

        # 2. ACTION
        # Try to move 5 steps East, which would cross the border
        final_pos, prey_caught = self.engine.execute_hunt_move(cat, Direction.E, 5)

        # 3. ASSERTIONS
        # The cat should move 1 step and stop at the last valid hunting tile before the border.
        expected_pos = (-2, 5)
        self.assertEqual(final_pos, expected_pos, "Cat should stop at the tile just before the border.")
        cat.move.assert_called_once_with(expected_pos)
        self.assertEqual(prey_caught, 0, "No prey should be caught.")

if __name__ == '__main__':
    unittest.main()
