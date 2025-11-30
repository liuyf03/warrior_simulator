import unittest
from unittest.mock import MagicMock, patch

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
        self.record_last_acted_turn = MagicMock()

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
        self.original_border_width = GameConfig.BORDER_WIDTH
        self.original_hunting_size = GameConfig.HUNTING_GROUND_SIZE
        GameConfig.BORDER_WIDTH = 3
        GameConfig.HUNTING_GROUND_SIZE = 6

        # Mock the prey population to control test conditions.
        self.patcher = patch.object(GameEngine, '_populate_initial_prey')
        self.mock_prey_init = self.patcher.start()
        # Create the engine (it uses the active patch)
        self.engine = GameEngine()
        self.mock_thunderclan = MockClan(ClanName.THUNDERCLAN)
        self.engine.clans[ClanName.THUNDERCLAN] = self.mock_thunderclan

    def tearDown(self):
        """This method runs after each test to clean up."""
        GameConfig.BORDER_WIDTH = self.original_border_width
        GameConfig.HUNTING_GROUND_SIZE = self.original_hunting_size
        # Stop the patcher after every test
        self.patcher.stop()

    def test_execute_hunt_move_success_and_catch_prey(self):
        """
        Tests a successful hunt where a cat moves and catches prey
        without hitting a border.
        """
        # SETUP
        start_pos = (-5, 5)
        cat = MockCat("Lionheart", ClanName.THUNDERCLAN, start_pos)

        # Manually place prey for this test, since auto-population is mocked.
        prey_tile = self.engine.board.get_tile((-5, 6))
        self.assertIsNotNone(prey_tile)
        prey_tile.prey_count = 2

        # ACTION
        # Execute a hunt move of 2 steps North
        final_pos, prey_caught = self.engine.execute_hunt_move(cat, Direction.N, 2)

        # ASSERTIONS
        expected_pos = (-5, 7)
        self.assertEqual(final_pos, expected_pos, "Cat should end up at the new position.")
        cat.move.assert_called_once_with(expected_pos)
        self.assertEqual(prey_caught, 2, "Should have caught 2 prey.")
        self.assertEqual(prey_tile.prey_count, 0, "Prey should be removed from the tile after being caught.")
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

    @patch('game_engine.GameEngine.execute_hunt_move')
    @patch('game_mechanics.Dice.roll')
    @patch('game_mechanics.Spinner.spin')
    def test_execute_hunt_wrapper(self, mock_spin, mock_roll, mock_execute_move):
        """Tests that the execute_hunt wrapper correctly calls its dependencies."""
        # ARRANGE
        mock_spin.return_value = Direction.N
        mock_roll.return_value = 5
        cat = MockCat("Lionheart", ClanName.THUNDERCLAN, position=(-5, 5))

        # ACT
        self.engine.execute_hunt(cat)

        # ASSERT
        mock_spin.assert_called_once()
        mock_roll.assert_called_once()
        mock_execute_move.assert_called_once_with(cat, Direction.N, 5)

if __name__ == '__main__':
    unittest.main()
