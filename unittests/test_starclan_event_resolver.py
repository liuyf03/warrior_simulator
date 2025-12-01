import unittest
import logging
import random

from game_engine import GameEngine
from enums import StarClanCard, ClanName, Rank
from cat import Cat

class TestStarClanEventResolver(unittest.TestCase):
    """
    Tests the various card effect resolution methods in the StarClanEventResolver.
    """

    def setUp(self):
        """
        Set up a fresh GameEngine and resolver for each test.
        This ensures tests are isolated from each other.
        """
        # Suppress detailed game logging during tests for cleaner output
        logging.disable(logging.INFO)

        self.engine = GameEngine()
        self.engine.setup_game()
        self.resolver = self.engine.starclan_resolver

        # Get a consistent cat and clan for triggering events
        self.test_clan = self.engine.clans[ClanName.THUNDERCLAN]
        self.trigger_cat = self.test_clan.get_warriors()[0]

    def tearDown(self):
        """Re-enable logging after tests are done."""
        logging.disable(logging.NOTSET)

    def test_resolve_a_blessing_of_new_leaf(self):
        """Test that a wounded cat is healed."""
        self.trigger_cat.sustain_injury(self.engine.turn_count)
        self.assertTrue(self.trigger_cat.is_wounded)
        self.resolver._resolve_a_blessing_of_new_leaf(StarClanCard.A_BLESSING_OF_NEW_LEAF, self.trigger_cat)
        self.assertFalse(self.trigger_cat.is_wounded, "The wounded cat should have been healed.")

    def test_resolve_the_bountiful_season(self):
        """Test that 2 prey are added to the clan's territory."""
        def count_prey_in_territory(clan_name):
            count = 0
            for slot_pos in self.engine.board.spawn_points.get(clan_name, {}).values():
                tile = self.engine.board.get_tile(slot_pos)
                if tile:
                    count += tile.prey_count
            return count

        initial_prey_count = count_prey_in_territory(self.test_clan.name)
        self.resolver._resolve_the_bountiful_season(StarClanCard.THE_BOUNTIFUL_SEASON, self.trigger_cat)
        final_prey_count = count_prey_in_territory(self.test_clan.name)
        self.assertEqual(final_prey_count, initial_prey_count + 2, "Should have added exactly 2 prey to the territory.")

    def test_resolve_warrior_code_upheld(self):
        """Test that a warrior is promoted to deputy if the spot is open."""
        # Ensure there is no deputy to start
        for cat in self.test_clan.cats:
            if cat.rank == Rank.DEPUTY:
                cat.rank = Rank.WARRIOR # Demote for test purposes
        self.assertFalse(self.test_clan.has_deputy())

        self.resolver._resolve_warrior_code_upheld(StarClanCard.WARRIOR_CODE_UPHELD, self.trigger_cat)
        self.assertTrue(self.test_clan.has_deputy(), "A deputy should have been promoted.")

    def test_resolve_border_washout(self):
        """Test that an enemy paw print is removed from a border tile."""
        # Place a paw print on a highlighted border tile
        border_tiles = [t for t in self.engine.board.grid.values() if t.is_highlighted]
        self.assertTrue(len(border_tiles) > 0, "Board setup should have highlighted border tiles.")
        # Ensure there is only one paw print to remove ramdomness
        self.engine.board.clear_paw_prints() 
        target_tile = border_tiles[0]
        target_tile.paw_print = ClanName.THUNDERCLAN # Enemy clan

        self.resolver._resolve_border_washout(StarClanCard.BORDER_WASHOUT, self.trigger_cat)
        self.assertIsNone(target_tile.paw_print, "The enemy paw print should have been washed away.")

    def test_resolve_whispers_of_battle(self):
        """Test that two specific clan fights are triggered."""
        # We can't easily check the result, but we can mock the trigger function
        # to see if it's called with the right arguments.
        call_log = []
        def mock_trigger_combat(clan_a, clan_b):
            call_log.append((clan_a.name, clan_b.name))

        # Temporarily replace the real method with our mock
        original_method = self.engine._trigger_clan_combat
        self.engine._trigger_clan_combat = mock_trigger_combat

        self.resolver._resolve_whispers_of_battle(StarClanCard.WHISPERS_OF_BATTLE, self.trigger_cat)

        # Restore the original method
        self.engine._trigger_clan_combat = original_method

        self.assertIn((ClanName.THUNDERCLAN, ClanName.WINDCLAN), call_log, "ThunderClan vs WindClan fight was not triggered.")
        self.assertIn((ClanName.RIVERCLAN, ClanName.SHADOWCLAN), call_log, "RiverClan vs ShadowClan fight was not triggered.")
        self.assertEqual(len(call_log), 2)

    def test_resolve_the_sickness_spreads(self):
        """Test that the triggering cat becomes wounded."""
        self.assertFalse(self.trigger_cat.is_wounded)
        self.resolver._resolve_the_sickness_spreads(StarClanCard.THE_SICKNESS_SPREADS, self.trigger_cat)
        self.assertTrue(self.trigger_cat.is_wounded, "The triggering cat should be wounded.")
        self.assertIsNone(self.trigger_cat.position, "Wounded cat should be in the Medicine Den (position is None).")

    def test_resolve_the_badger_set(self):
        """Test that the clan loses 2 prey from its fresh-kill pile."""
        self.test_clan.add_prey(5)
        initial_prey = self.test_clan.prey_pile
        self.resolver._resolve_the_badger_set(StarClanCard.THE_BADGER_SET, self.trigger_cat)
        self.assertEqual(self.test_clan.prey_pile, initial_prey - 2, "Clan should lose 2 prey.")

        # Test at zero
        self.test_clan.prey_pile = 0
        self.resolver._resolve_the_badger_set(StarClanCard.THE_BADGER_SET, self.trigger_cat)
        self.assertEqual(self.test_clan.prey_pile, 0, "Prey pile should not go below zero.")

    def test_resolve_a_true_warriors_heart(self):
        """Test that an apprentice is promoted and then wounded."""
        apprentice = self.test_clan.get_apprentices()[0]
        self.assertIsNotNone(apprentice)
        self.assertEqual(apprentice.rank, Rank.APPRENTICE)

        self.resolver._resolve_a_true_warriors_heart(StarClanCard.A_TRUE_WARRIORS_HEART, self.trigger_cat)

        self.assertEqual(apprentice.rank, Rank.WARRIOR, "Apprentice should have been promoted to Warrior.")
        self.assertTrue(apprentice.is_wounded, "The newly promoted warrior should be wounded.")

    def test_resolve_rogue_intruder(self):
        """Test that one prey is removed from a hunting ground slot."""
        # Ensure there is only 1 prey at fixed position
        self.engine.board.clear_prey()
        self.engine.board.spawn_prey(self.test_clan.name, 1)
        slot_pos = self.engine.board.spawn_points[self.test_clan.name][1]
        tile = self.engine.board.get_tile(slot_pos)
        initial_prey_on_tile = tile.prey_count
        self.assertGreater(initial_prey_on_tile, 0)

        self.resolver._resolve_rogue_intruder(StarClanCard.ROGUE_INTRUDER, self.trigger_cat)
        self.assertEqual(tile.prey_count, initial_prey_on_tile - 1, "One prey should have been stolen from the tile.")

    def test_resolve_hunters_luck(self):
        """Test that one prey moves from hunting ground to fresh-kill pile."""
        # Ensure there is only 1 prey at fixed position
        self.engine.board.clear_prey()
        self.engine.board.spawn_prey(self.test_clan.name, 1)
        slot_pos = self.engine.board.spawn_points[self.test_clan.name][1]
        tile = self.engine.board.get_tile(slot_pos)
        initial_prey_on_tile = tile.prey_count
        initial_pile = self.test_clan.prey_pile

        self.resolver._resolve_hunters_luck(StarClanCard.HUNTERS_LUCK, self.trigger_cat)

        self.assertEqual(tile.prey_count, initial_prey_on_tile - 1, "Prey should be removed from the board.")
        self.assertEqual(self.test_clan.prey_pile, initial_pile + 1, "Prey should be added to the fresh-kill pile.")

    def test_resolve_rising_spirit(self):
        """Test that an apprentice is promoted to warrior."""
        apprentice = self.test_clan.get_apprentices()[0]
        self.assertIsNotNone(apprentice)
        self.assertEqual(apprentice.rank, Rank.APPRENTICE)

        self.resolver._resolve_rising_spirit(StarClanCard.RISING_SPIRIT, self.trigger_cat)
        self.assertEqual(apprentice.rank, Rank.WARRIOR, "Apprentice should have been promoted.")
        self.assertFalse(apprentice.is_wounded, "Promoted warrior should be healthy.")

    def test_resolve_sudden_illness(self):
        """Test that a random healthy apprentice is injured."""
        # Ensure all apprentices are healthy first
        for app in self.test_clan.get_apprentices():
            app.heal(self.test_clan.camp_entrance)

        healthy_apprentices = self.test_clan.get_apprentices()
        self.assertTrue(len(healthy_apprentices) > 0)

        self.resolver._resolve_sudden_illness(StarClanCard.SUDDEN_ILLNESS, self.trigger_cat)

        wounded_count = sum(1 for cat in self.test_clan.cats if cat.rank == Rank.APPRENTICE and cat.is_wounded)
        self.assertEqual(wounded_count, 1, "Exactly one apprentice should be wounded.")

    def test_resolve_ravens_plunder(self):
        """Test that the clan loses 1 prey from its fresh-kill pile."""
        self.test_clan.add_prey(3)
        self.resolver._resolve_ravens_plunder(StarClanCard.RAVENS_PLUNDER, self.trigger_cat)
        self.assertEqual(self.test_clan.prey_pile, 2, "Clan should lose 1 prey.")

        # Test at zero
        self.test_clan.prey_pile = 0
        self.resolver._resolve_ravens_plunder(StarClanCard.RAVENS_PLUNDER, self.trigger_cat)
        self.assertEqual(self.test_clan.prey_pile, 0, "Prey pile should not go below zero.")

    def test_resolve_unexpected_encounter(self):
        """Test that a combat is triggered against a random enemy clan."""
        call_log = []
        def mock_trigger_combat(clan_a, clan_b):
            call_log.append((clan_a.name, clan_b.name))

        original_method = self.engine._trigger_clan_combat
        self.engine._trigger_clan_combat = mock_trigger_combat

        self.resolver._resolve_unexpected_encounter(StarClanCard.UNEXPECTED_ENCOUNTER, self.trigger_cat)

        self.engine._trigger_clan_combat = original_method

        self.assertEqual(len(call_log), 1, "Exactly one combat should be triggered.")
        triggered_aggressor, triggered_defender = call_log[0]
        self.assertEqual(triggered_aggressor, self.trigger_cat.clan_id, "The triggering cat's clan should be the aggressor.")
        self.assertNotEqual(triggered_defender, self.trigger_cat.clan_id, "The defender should be a different clan.")

if __name__ == '__main__':
    unittest.main()
