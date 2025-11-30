import unittest
from unittest.mock import MagicMock, patch

from enums import ClanName, Rank, Direction, TileType, CombatMove
from game_config import GameConfig
from game_engine import GameEngine
from cat import Cat
from clan import Clan

# --- Mock Classes ---

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
        # Patch the board's highlight assignment to prevent random highlights
        self.patcher = patch('board.Board._assign_border_highlights')
        self.mock_assign_highlights = self.patcher.start()

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
        self.patcher.stop() # Stop the patch to clean up the test environment
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
        enemy_scent_tile.is_highlighted = True
        enemy_scent_tile.paw_print = ClanName.RIVERCLAN

        # ACTION
        final_pos, _, combat_triggered = self.engine.execute_border_patrol_move(cat, Direction.S, 5)

        # ASSERTIONS
        self.assertEqual(final_pos, enemy_scent_pos)
        cat.move.assert_called_once_with(enemy_scent_pos)
        self.assertTrue(combat_triggered) 

        # 2. Assert that the combat function was called exactly once with the correct clans
        mock_trigger_combat.assert_called_once_with(self.mock_thunderclan, self.mock_riverclan)
        # After the combat, RIVERCLAN paw print should be cleared, replaced by THUNDERCLAN's paw print
        self.assertEqual(enemy_scent_tile.paw_print, ClanName.THUNDERCLAN)

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
        final_pos, _, combat_triggered = self.engine.execute_border_patrol_move(cat, Direction.E, 3)

        # ASSERTIONS
        last_pos_before_enemy_territory = (1,5)
        self.assertEqual(final_pos, last_pos_before_enemy_territory)
        self.assertFalse(combat_triggered)

    # --- Tests for execute_border_patrol wrapper ---

    @patch('game_engine.GameEngine.execute_border_patrol_move')
    @patch('game_mechanics.Dice.roll')
    @patch('game_mechanics.Spinner.spin')
    def test_patrol_from_border_moves_immediately(self, mock_spin, mock_roll, mock_execute_move):
        """Tests that a cat on the border moves on the first roll."""
        # ARRANGE
        mock_spin.return_value = Direction.S
        mock_roll.return_value = 4
        cat = MockCat("Lionheart", ClanName.THUNDERCLAN, position=(0, 5)) # On the border
        mock_execute_move.return_value = ((0, 0), [], False)

        # ACT
        self.engine.execute_border_patrol(cat)

        # ASSERT
        mock_spin.assert_called_once()
        mock_roll.assert_called_once()
        mock_execute_move.assert_called_once_with(cat, Direction.S, 4)

    @patch('game_engine.GameEngine.execute_border_patrol_move')
    @patch('game_mechanics.Dice.roll')
    @patch('game_mechanics.Spinner.spin')
    def test_patrol_rerolls_to_find_good_move(self, mock_spin, mock_roll, mock_execute_move):
        """Tests that a cat in territory re-rolls a bad move to find a good one."""
        # ARRANGE
        # First spin is 'W' (bad), second is 'E' (good)
        mock_spin.side_effect = [Direction.W, Direction.E]
        mock_roll.return_value = 3
        cat = MockCat("Tigerclaw", ClanName.THUNDERCLAN, position=(-4, 5)) # In territory
        mock_execute_move.return_value = ((0, 0), [], False)

        # ACT
        self.engine.execute_border_patrol(cat)

        # ASSERT
        self.assertEqual(mock_spin.call_count, 2, "Should have spun twice to find a good move.")
        mock_execute_move.assert_called_once_with(cat, Direction.E, 3)

    @patch('game_engine.GameEngine.execute_border_patrol_move')
    @patch('game_mechanics.Dice.roll')
    @patch('game_mechanics.Spinner.spin')
    def test_patrol_gives_up_after_max_rerolls(self, mock_spin, mock_roll, mock_execute_move):
        """Tests that a cat gives up its turn if no good move is found."""
        # ARRANGE
        # All spins are 'W', which is always a bad move from this position
        mock_spin.return_value = Direction.W
        mock_roll.return_value = 2
        cat = MockCat("Darkstripe", ClanName.THUNDERCLAN, position=(-4, 5)) # In territory

        # ACT
        self.engine.execute_border_patrol(cat)

        # ASSERT
        self.assertEqual(mock_spin.call_count, GameConfig.MAX_PATROL_REROLLS)
        mock_execute_move.assert_not_called() # The move function should never be executed

    @unittest.mock.patch('combat_system.CombatSystem.calculate_fight_results')
    @unittest.mock.patch('game_engine.GameEngine._reward_winning_clan')
    @unittest.mock.patch('game_engine.GameEngine._mark_wounded_cats')
    @unittest.mock.patch('deck.Deck.draw')
    def test_trigger_clan_combat_handles_draw_and_rerun(self, mock_draw, mock_mark_wounded_cats, mock_reward_winning_clan, mock_calculate_results):
        """
        Tests that _trigger_clan_combat correctly re-runs a fight on a draw.
        """
        # SETUP
        # 1. Mock the combat results: First round is a draw (0, 0), second round is a win for Clan A (5, 0).
        mock_calculate_results.side_effect = [
            (0, 0, [0] * GameConfig.NUM_CATS_PER_CLAN),
            (5, 0, [1] + [0] * (GameConfig.NUM_CATS_PER_CLAN-1))
        ]

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

    # --- Tests for Combat Resolution ---

    def test_mark_wounded_cats(self):
        """Tests that cats are correctly marked as wounded based on slot results."""
        # ARRANGE
        # Using real Cat objects to check their state
        cat_a1 = Cat("CatA1", ClanName.THUNDERCLAN, Rank.WARRIOR, (0,0))
        cat_a2 = Cat("CatA2", ClanName.THUNDERCLAN, Rank.WARRIOR, (0,0))
        cat_b1 = Cat("CatB1", ClanName.RIVERCLAN, Rank.WARRIOR, (0,0))
        cat_b2 = Cat("CatB2", ClanName.RIVERCLAN, Rank.WARRIOR, (0,0))

        cats_a = [cat_a1, cat_a2]
        cats_b = [cat_b1, cat_b2]
        # Clan A wins slot 1, Clan B wins slot 2
        slot_results = [1, -1]

        # ACT
        self.engine._mark_wounded_cats(cats_a, cats_b, slot_results)

        # ASSERT
        self.assertFalse(cat_a1.is_wounded, "Cat A1 won and should be healthy.")
        self.assertTrue(cat_a2.is_wounded, "Cat A2 lost and should be wounded.")
        self.assertTrue(cat_b1.is_wounded, "Cat B1 lost and should be wounded.")
        self.assertFalse(cat_b2.is_wounded, "Cat B2 won and should be healthy.")

    def test_reward_winning_clan_promotes_apprentice(self):
        """Tests that the first reward is promoting an apprentice."""
        # ARRANGE
        winning_clan = Clan(ClanName.THUNDERCLAN, (0,0))
        winning_clan.add_cat("Testpaw", Rank.APPRENTICE)
        apprentice = winning_clan.cats[0]  # Get the actual Cat object

        # ACT
        self.engine._reward_winning_clan(winning_clan)

        # ASSERT
        self.assertEqual(apprentice.rank, Rank.WARRIOR, "Apprentice should be promoted to Warrior.")

    def test_reward_winning_clan_promotes_to_deputy(self):
        """Tests promoting a warrior to deputy if no apprentices exist."""
        # ARRANGE
        winning_clan = Clan(ClanName.THUNDERCLAN, (0,0))
        winning_clan.add_cat("Testfur",  Rank.WARRIOR) # Clan has no apprentices and no deputy
        warrior = winning_clan.cats[0]  # Get the actual Cat object

        # ACT
        self.engine._reward_winning_clan(winning_clan)

        # ASSERT
        self.assertEqual(warrior.rank, Rank.DEPUTY, "Warrior should be promoted to Deputy.")

    @patch('game_engine.GameEngine.execute_prey_replenish')
    def test_reward_winning_clan_replenishes_prey(self, mock_replenish):
        """
        Tests replenishing prey if no promotions are possible.
        """
        # ARRANGE
        winning_clan = Clan(ClanName.THUNDERCLAN, (0,0))
        winning_clan.add_cat("Teststar", Rank.LEADER)
        winning_clan.add_cat("Testpelt", Rank.DEPUTY) # Clan has a leader and deputy, no apprentices

        # ACT
        self.engine._reward_winning_clan(winning_clan)

        # ASSERT
        # Check that the prey replenish function was called
        mock_replenish.assert_called_once_with(winning_clan, count=1)


if __name__ == '__main__':
    unittest.main()