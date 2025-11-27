import unittest
from unittest.mock import MagicMock

from enums import ClanName, Rank, Direction, TileType, CombatMove
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

class MockClan:
    """A mock Clan class for testing."""
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return f"MockClan(name='{self.name}')"

# --- Test Suite for Border Patrol Moves ---

class TestBorderPatrol(unittest.TestCase):
    """Test suite for the GameEngine's execute_border_patrol_move method."""

    def setUp(self):
        """This method runs before each test."""
        self.original_border_width = GameConfig.BORDER_WIDTH
        self.original_hunting_size = GameConfig.HUNTING_GROUND_SIZE
        GameConfig.BORDER_WIDTH = 3
        GameConfig.HUNTING_GROUND_SIZE = 6
        self.engine = GameEngine()
        # Add mock clans needed for combat trigger tests
        self.mock_thunderclan = MockClan(ClanName.THUNDERCLAN)
        self.mock_riverclan = MockClan(ClanName.RIVERCLAN)
        self.engine.clans[ClanName.THUNDERCLAN] = self.mock_thunderclan
        self.engine.clans[ClanName.RIVERCLAN] = self.mock_riverclan

    def tearDown(self):
        """This method runs after each test to clean up."""
        GameConfig.BORDER_WIDTH = self.original_border_width
        GameConfig.HUNTING_GROUND_SIZE = self.original_hunting_size

    @unittest.mock.patch('game_engine.GameEngine._trigger_clan_combat')
    def test_patrol_stops_at_enemy_scent_and_triggers_combat(self, mock_trigger_combat):
        """
        Tests that a patrol stops upon finding an enemy paw print and
        correctly triggers the combat system.
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

        # 2. Assert that the combat function was called exactly once with the correct clans
        mock_trigger_combat.assert_called_once_with(self.mock_thunderclan, self.mock_riverclan)

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

    @unittest.mock.patch('combat_system.CombatSystem.calculate_fight_results')
    @unittest.mock.patch('deck.Deck.draw')
    def test_trigger_clan_combat_handles_draw_and_rerun(self, mock_draw, mock_calculate_results):
        """
        Tests that _trigger_clan_combat correctly re-runs a fight on a draw.
        """
        # SETUP
        # 1. Mock the combat results: First round is a draw (0, 0), second round is a win for Clan A (5, 0).
        mock_calculate_results.side_effect = [(0, 0), (5, 0)]

        # 2. Mock the deck to return predictable cards.
        mock_draw.return_value = CombatMove.CLAW_SCRATCH

        # 3. Create mock clans and set up their combat squads.
        # We need to mock the return of get_combat_squad for each clan.
        clan_a = self.mock_thunderclan
        clan_b = self.mock_riverclan
        
        # Create mock cats and ranks for the squad. The actual content doesn't matter as much
        # as the structure, since we are mocking the result calculation.
        squad_size = GameConfig.NUM_CATS_PER_CLAN
        mock_squad_cats = [MockCat("cat", ClanName.THUNDERCLAN, (0,0))] * squad_size
        mock_squad_ranks = [Rank.WARRIOR] * squad_size

        clan_a.get_combat_squad = MagicMock(return_value=(mock_squad_cats, mock_squad_ranks))
        clan_b.get_combat_squad = MagicMock(return_value=(mock_squad_cats, mock_squad_ranks))

        # ACTION
        # Directly call the private method we want to test.
        self.engine._trigger_clan_combat(clan_a, clan_b)

        # ASSERTIONS
        # Assert that the fight calculation was called twice (once for the draw, once for the win).
        self.assertEqual(mock_calculate_results.call_count, 2, "Should have run combat twice due to the initial draw.")

if __name__ == '__main__':
    unittest.main()