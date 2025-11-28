import unittest
from unittest.mock import MagicMock, patch, call

from game_engine import GameEngine
from enums import Season, ClanName

class TestGameSetup(unittest.TestCase):
    """
    Unit tests for the GameEngine's setup_game method.
    """

    @patch('game_engine.GameEngine._populate_initial_prey')
    def setUp(self, mock_populate_prey):
        """Set up a fresh GameEngine instance before each test."""
        self.engine = GameEngine()

    @patch('clan.Clan.reset_clan_state')
    @patch('deck.Deck.reshuffle')
    @patch('board.Board.clear_paw_prints')
    @patch('board.Board.clear_prey')
    @patch('game_engine.GameEngine._populate_initial_prey')
    def test_setup_game_resets_and_initializes_state(self, mock_populate_prey, mock_clear_prey, mock_clear_prints, mock_reshuffle, mock_reset_clan):
        """
        Tests that setup_game correctly calls all necessary reset and initialization methods.
        """
        # ARRANGE
        # Simulate a "dirty" state from a previous game
        self.engine.turn_count = 10
        self.engine.current_season = Season.LEAF_FALL

        # ACT
        self.engine.setup_game()

        # ASSERT
        # 1. Assert that global counters are reset
        self.assertEqual(self.engine.turn_count, 1, "Turn count should be reset to 1.")
        self.assertEqual(self.engine.current_season, Season.NEW_LEAF, "Season should be reset to Newleaf.")

        # 2. Assert that board state is cleared
        mock_clear_prey.assert_called_once()
        mock_clear_prints.assert_called_once()

        # 3. Assert that all clans have their state reset
        self.assertEqual(mock_reset_clan.call_count, len(self.engine.clans), "reset_clan_state should be called for each clan.")

        # 4. Assert that both decks are reshuffled
        # We expect two calls to reshuffle: one for the activity deck, one for the combat deck.
        self.assertEqual(mock_reshuffle.call_count, 2, "reshuffle() should be called for both decks.")

        # 5. Assert that initial prey is populated at the end
        mock_populate_prey.assert_called_once()


if __name__ == '__main__':
    unittest.main()
