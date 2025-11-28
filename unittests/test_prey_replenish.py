import unittest
from unittest.mock import patch

from enums import ClanName
from game_config import GameConfig
from game_engine import GameEngine

class TestPreyReplenish(unittest.TestCase):
    """Test suite for the GameEngine's execute_prey_replenish method."""

    def setUp(self):
        """This method runs before each test."""
        self.original_border_width = GameConfig.BORDER_WIDTH
        self.original_hunting_size = GameConfig.HUNTING_GROUND_SIZE
        GameConfig.BORDER_WIDTH = 3
        GameConfig.HUNTING_GROUND_SIZE = 6
        self.engine = GameEngine()

    def tearDown(self):
        """This method runs after each test to clean up."""
        GameConfig.BORDER_WIDTH = self.original_border_width
        GameConfig.HUNTING_GROUND_SIZE = self.original_hunting_size

    @patch('game_mechanics.Dice.roll')
    def test_execute_prey_replenish_adds_prey_to_correct_slots(self, mock_roll):
        """
        Tests that prey is added to the specific slots determined by dice rolls.
        """
        # ARRANGE
        # 1. Configure the mock dice to return predictable slot numbers.
        # We will roll three times, adding prey to slot 1, then slot 3, then slot 1 again.
        mock_roll.side_effect = [1, 3, 1]

        # 2. Get the target clan and the specific tiles we expect to change.
        target_clan = self.engine.clans[ClanName.THUNDERCLAN]
        slot_1_pos = self.engine.board.spawn_points[ClanName.THUNDERCLAN][1]
        slot_3_pos = self.engine.board.spawn_points[ClanName.THUNDERCLAN][3]
        tile_slot_1 = self.engine.board.get_tile(slot_1_pos)
        tile_slot_3 = self.engine.board.get_tile(slot_3_pos)
        # Add initial prey to these tiles to verify increments.
        tile_slot_1.prey_count = 1
        tile_slot_3.prey_count = 1

        # 3. Verify the initial state (each slot starts with 1 prey).
        self.assertEqual(tile_slot_1.prey_count, 1, "Slot 1 should start with 1 prey.")
        self.assertEqual(tile_slot_3.prey_count, 1, "Slot 3 should start with 1 prey.")

        # ACT
        # Replenish prey 3 times, according to our mocked dice rolls.
        self.engine.execute_prey_replenish(target_clan, count=3)

        # ASSERT
        # 1. Check that the dice was rolled 3 times with the correct number of sides.
        mock_roll.assert_called_with(sides=GameConfig.HUNTING_GROUND_SIZE)
        self.assertEqual(mock_roll.call_count, 3)

        # 2. Check the final prey counts on the affected tiles.
        self.assertEqual(tile_slot_1.prey_count, 3, "Slot 1 should have 3 prey (1 initial + 2 added).")
        self.assertEqual(tile_slot_3.prey_count, 2, "Slot 3 should have 2 prey (1 initial + 1 added).")

if __name__ == '__main__':
    unittest.main()
