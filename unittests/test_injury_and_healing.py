import unittest
from unittest.mock import patch

from cat import Cat
from clan import Clan
from enums import ClanName, Rank
from game_config import GameConfig
from game_engine import GameEngine

class TestInjuryAndHealing(unittest.TestCase):
    """
    Tests for cat injury, recovery, and the associated game mechanics.
    """

    def setUp(self):
        """Set up common objects for tests."""
        self.camp_entrance = (-15, 15) # Using ThunderClan's camp for consistency
        self.clan = Clan(ClanName.THUNDERCLAN, self.camp_entrance)
        self.clan.add_cat("Testpaw", Rank.WARRIOR)
        self.cat = self.clan.cats[0]  # Get the actual Cat object

    def test_cat_sustain_injury(self):
        """Tests that a cat's state is correctly updated upon injury."""
        # ARRANGE
        current_turn = 5
        self.assertFalse(self.cat.is_wounded)
        self.assertIsNone(self.cat.wounded_turn_index)

        # ACT
        self.cat.sustain_injury(current_turn)

        # ASSERT
        self.assertTrue(self.cat.is_wounded, "Cat should be marked as wounded.")
        self.assertEqual(self.cat.wounded_turn_index, current_turn, "The turn of injury should be recorded.")
        self.assertIsNone(self.cat.position, "Wounded cat's position should be None (in Medicine Den).")

    def test_wounded_cat_cannot_move(self):
        """Tests that a wounded cat cannot use the move action."""
        # ARRANGE
        self.cat.sustain_injury(current_turn=1)
        self.assertIsNone(self.cat.position)

        # ACT
        self.cat.move((5, 5))

        # ASSERT
        self.assertIsNone(self.cat.position, "Wounded cat's position should not change after trying to move.")

    def test_clan_heal_cats_after_duration(self):
        """
        Tests that Clan.heal_cats correctly heals a cat after the required number of turns.
        With WOUNDED_CATS_TURNS_TO_SKIP = 2, a cat wounded on turn 1 should heal on turn 3.
        """
        # ARRANGE
        turns_to_skip = GameConfig.WOUNDED_CATS_TURNS_TO_SKIP
        injury_turn = 1
        self.cat.sustain_injury(injury_turn)

        # ACT & ASSERT
        # Check turn right after injury
        self.clan.heal_cats(current_turn=injury_turn)
        self.assertTrue(self.cat.is_wounded, f"Cat should still be wounded on turn {injury_turn}.")

        # Check turn during recovery
        healing_turn = injury_turn + turns_to_skip
        for turn in range(injury_turn + 1, healing_turn):
             self.clan.heal_cats(current_turn=turn)
             self.assertTrue(self.cat.is_wounded, f"Cat should still be wounded on turn {turn}.")

        # Check turn when healing should occur
        self.clan.heal_cats(current_turn=healing_turn)
        self.assertFalse(self.cat.is_wounded, f"Cat should be healed on turn {healing_turn}.")
        self.assertIsNone(self.cat.wounded_turn_index, "Healed cat's wounded_turn_index should be reset to None.")
        self.assertEqual(self.cat.position, self.camp_entrance, "Healed cat should return to the camp entrance.")

    @patch('clan.Clan.heal_cats')
    def test_execute_clan_turn_calls_heal_cats(self, mock_heal_cats):
        """Tests that the main turn logic calls the healing function at the start of a clan's turn."""
        with patch.object(GameEngine, '_populate_initial_prey'):
            engine = GameEngine()
        
        clan_to_test = engine.clans[ClanName.THUNDERCLAN]
        engine._execute_clan_turn(clan_to_test)

        mock_heal_cats.assert_called_once_with(engine.turn_count)

if __name__ == '__main__':
    unittest.main()
