import unittest
from unittest.mock import MagicMock, patch, call

from game_engine import GameEngine
from enums import ClanName, Season, Activity, Rank
from activity_card import ActivityCard

class TestGameTurn(unittest.TestCase):
    """
    Unit tests for the turn execution logic in GameEngine, specifically _execute_clan_turn.
    """

    def setUp(self):
        """Set up a fresh GameEngine instance before each test."""
        # We patch _populate_initial_prey to speed up engine initialization
        with patch.object(GameEngine, '_populate_initial_prey'):
            self.engine = GameEngine()

        # Mock the clan and its cats
        self.mock_clan = MagicMock()
        self.mock_clan.name = "MockClan"
        self.mock_warrior_1 = MagicMock()
        self.mock_warrior_2 = MagicMock()

        # Mock the activity card and deck
        self.mock_card = ActivityCard([Activity.HUNT, Activity.PATROL, Activity.TRAIN_HUNT, Activity.TRAIN_PATROL])
        self.engine.activity_deck = MagicMock()
        self.engine.activity_deck.draw.return_value = self.mock_card

    @patch('game_engine.GameEngine.execute_border_patrol')
    @patch('game_engine.GameEngine.execute_hunt')
    def test_turn_with_sufficient_warriors_no_bonus(self, mock_execute_hunt, mock_execute_patrol):
        """
        Tests a standard turn in a season without a prey bonus (e.g., Leaf-fall).
        Ensures the correct number of actions are dispatched.
        """
        # ARRANGE
        # Clan has 2 active warriors
        self.mock_clan.get_active_warriors.return_value = [self.mock_warrior_1, self.mock_warrior_2]
        self.engine.current_season = Season.LEAF_FALL
        self.engine.execute_prey_replenish = MagicMock()

        # ACT
        self.engine._execute_clan_turn(self.mock_clan)

        # ASSERT
        # 1. A card was drawn and later discarded
        self.engine.activity_deck.draw.assert_called_once()
        self.engine.activity_deck.discard.assert_called_once_with(self.mock_card)

        # 2. Actions were dispatched for the two available warriors
        mock_execute_hunt.assert_called_once_with(self.mock_warrior_1)
        mock_execute_patrol.assert_called_once_with(self.mock_warrior_2)

        # 3. The seasonal prey bonus was NOT triggered
        self.engine.execute_prey_replenish.assert_not_called()

    @patch('game_engine.GameEngine.execute_border_patrol')
    @patch('game_engine.GameEngine.execute_hunt')
    def test_turn_with_seasonal_prey_bonus(self, mock_execute_hunt, mock_execute_patrol):
        """
        Tests that the leader's prey replenish bonus is triggered during Newleaf.
        """
        # ARRANGE
        self.mock_clan.get_active_warriors.return_value = [self.mock_warrior_1]
        self.engine.current_season = Season.NEW_LEAF # A season with the bonus
        self.engine.execute_prey_replenish = MagicMock()

        # ACT
        self.engine._execute_clan_turn(self.mock_clan)

        # ASSERT
        # 1. A card was drawn and later discarded
        self.engine.activity_deck.draw.assert_called_once()
        self.engine.activity_deck.discard.assert_called_once_with(self.mock_card)
        
        # 2. Only the HUNT action was dispatched
        mock_execute_hunt.assert_called_once_with(self.mock_warrior_1)
        mock_execute_patrol.assert_not_called()

        # 2. The seasonal prey bonus WAS triggered
        self.engine.execute_prey_replenish.assert_called_once_with(self.mock_clan, count=1)

    @patch('game_engine.GameEngine.execute_border_patrol')
    @patch('game_engine.GameEngine.execute_hunt')
    def test_turn_with_no_active_warriors(self, mock_execute_hunt, mock_execute_patrol):
        """
        Tests that no actions are dispatched if a clan has no active warriors.
        """
        # ARRANGE
        self.mock_clan.get_active_warriors.return_value = [] # No warriors available
        self.engine.current_season = Season.LEAF_BARE
        self.engine.execute_prey_replenish = MagicMock()

        # ACT
        self.engine._execute_clan_turn(self.mock_clan)

        # ASSERT
        # 1. A card was still drawn and discarded
        self.engine.activity_deck.draw.assert_called_once()
        self.engine.activity_deck.discard.assert_called_once_with(self.mock_card)

        # 2. No actions were dispatched
        mock_execute_hunt.assert_not_called()
        mock_execute_patrol.assert_not_called()

        # 3. The seasonal bonus was not triggered
        self.engine.execute_prey_replenish.assert_not_called()

    @patch('game_engine.GameEngine.execute_hunt')
    def test_execute_train_hunt_with_apprentice(self, mock_execute_hunt):
        """
        Tests that TRAIN_HUNT activity makes both the warrior and an available apprentice hunt.
        """
        # ARRANGE
        # 1. Mock the clan to have one active warrior and one available apprentice
        mock_apprentice = MagicMock()
        self.mock_clan.get_active_warriors.return_value = [self.mock_warrior_1]
        self.mock_clan.get_apprentices.return_value = [mock_apprentice]

        # 2. Mock the activity card to draw a TRAIN_HUNT action
        train_hunt_card = ActivityCard([Activity.TRAIN_HUNT])
        self.engine.activity_deck.draw.return_value = train_hunt_card

        # 3. Set a season without a bonus to isolate the test
        self.engine.current_season = Season.LEAF_FALL

        # ACT
        self.engine._execute_clan_turn(self.mock_clan)

        # ASSERT
        # 1. Check that get_apprentices was called to find a trainee
        self.mock_clan.get_apprentices.assert_called_once()

        # 2. Check that execute_hunt was called for both the warrior and the apprentice
        self.assertEqual(mock_execute_hunt.call_count, 2)
        mock_execute_hunt.assert_has_calls([call(self.mock_warrior_1), call(mock_apprentice)])

    # --- Tests for play_full_turn ---

    @patch('game_engine.GameEngine._advance_turn')
    @patch('game_engine.GameEngine._execute_clan_turn')
    @patch('game_engine.GameEngine._check_game_over', return_value=False)
    def test_play_full_turn_executes_in_order(self, mock_check_over, mock_execute_turn, mock_advance_turn):
        """
        Tests that play_full_turn executes turns for all clans in the correct
        clockwise order and then advances the turn.
        """
        # ACT
        self.engine.play_full_turn()

        # ASSERT
        # 1. Check that the game over condition was checked
        mock_check_over.assert_called_once()

        # 2. Check that _execute_clan_turn was called for each clan in the correct order
        expected_calls = [
            call(self.engine.clans[ClanName.THUNDERCLAN]),
            call(self.engine.clans[ClanName.RIVERCLAN]),
            call(self.engine.clans[ClanName.WINDCLAN]),
            call(self.engine.clans[ClanName.SHADOWCLAN])
        ]
        mock_execute_turn.assert_has_calls(expected_calls)
        self.assertEqual(mock_execute_turn.call_count, 4)

        # 3. Check that the turn was advanced at the end
        mock_advance_turn.assert_called_once()

    @patch('game_engine.GameEngine._advance_turn')
    @patch('game_engine.GameEngine._execute_clan_turn')
    @patch('game_engine.GameEngine._check_game_over', return_value=True)
    def test_play_full_turn_stops_if_game_is_over(self, mock_check_over, mock_execute_turn, mock_advance_turn):
        """
        Tests that play_full_turn does nothing if the game over condition is met.
        """
        self.engine.play_full_turn()
        mock_check_over.assert_called_once()
        mock_execute_turn.assert_not_called()
        mock_advance_turn.assert_not_called()

if __name__ == '__main__':
    unittest.main()
