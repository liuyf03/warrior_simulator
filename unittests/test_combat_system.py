import unittest
from typing import List, Optional

from combat_system import CombatSystem
from enums import CombatMove, Rank

class TestCombatSystem(unittest.TestCase):
    """Test suite for the CombatSystem class."""

    # --- Tests for get_card_winner ---

    def test_get_card_winner_a_wins(self):
        """Tests a clear win scenario (Claw Scratch > Bite)."""
        result = CombatSystem.get_card_winner(CombatMove.CLAW_SCRATCH, CombatMove.BITE)
        self.assertEqual(result, 1, "Card A should win.")

    def test_get_card_winner_b_wins(self):
        """Tests a clear loss scenario (Leap < Kick)."""
        result = CombatSystem.get_card_winner(CombatMove.CLAW_SCRATCH, CombatMove.KICK)
        self.assertEqual(result, -1, "Card B should win.")

    def test_get_card_winner_tie(self):
        """Tests a tie scenario (Bite vs Bite)."""
        result = CombatSystem.get_card_winner(CombatMove.BITE, CombatMove.BITE)
        self.assertEqual(result, 0, "The result should be a tie.")

    # --- Tests for calculate_fight_results ---

    def test_calculate_fight_results_simple_scenario(self):
        """Tests a straightforward fight with clear winners."""
        # Ranks
        clan_a_ranks = [Rank.LEADER, Rank.DEPUTY, Rank.WARRIOR, Rank.APPRENTICE, Rank.APPRENTICE]
        clan_b_ranks = [Rank.LEADER, Rank.WARRIOR, Rank.WARRIOR, Rank.APPRENTICE, Rank.APPRENTICE]
        
        # Clan A wins slot 1 (5 pts), Clan B wins slot 2 (3 pts), Clan A wins slot 3 (3 pts)
        clan_a_cards = [CombatMove.CLAW_SCRATCH, CombatMove.KICK, CombatMove.BITE, None, None]
        clan_b_cards = [CombatMove.BITE, CombatMove.LEAP, CombatMove.KICK, None, None]
        
        # ACT
        score_a, score_b, slot_results = CombatSystem.calculate_fight_results(clan_a_cards, clan_b_cards, clan_a_ranks, clan_b_ranks)
        
        # ASSERT
        expected_score_a = 5 + 3   # Leader wins + Warrior wins
        expected_score_b = 3       # WARRIOR wins
        expected_slot_results = [1, -1, 1, 0, 0] # A wins, B wins, A wins, tie, tie
        self.assertEqual(score_a, expected_score_a)
        self.assertEqual(score_b, expected_score_b)
        self.assertEqual(slot_results, expected_slot_results)

    def test_calculate_fight_results_with_wounded_cat_and_ties(self):
        """Tests that a wounded cat (None card) automatically loses the slot."""
        # Ranks
        clan_a_ranks = [Rank.LEADER, Rank.DEPUTY, Rank.WARRIOR, Rank.APPRENTICE, Rank.APPRENTICE]
        clan_b_ranks = [Rank.LEADER, Rank.WARRIOR, Rank.WARRIOR, Rank.APPRENTICE, Rank.APPRENTICE]
        
        # Clan A wins slot 1 (5 pts), slot 2 (4 pts), slot 4 (1 pt)
        # Clan B has a wounded warrior in slot 2 and wins slot 5 (1 pt)
        # Slot 3 is a tie 
        clan_a_cards = [CombatMove.CLAW_SCRATCH, CombatMove.KICK, CombatMove.KICK, CombatMove.LEAP, CombatMove.KICK]
        clan_b_cards = [CombatMove.BITE, None, CombatMove.KICK, CombatMove.KICK, CombatMove.BITE]
        
        # ACT
        score_a, score_b, slot_results = CombatSystem.calculate_fight_results(clan_a_cards, clan_b_cards,  clan_a_ranks, clan_b_ranks)
        
        # ASSERT
        expected_score_a = 5 + 4 + 1
        expected_score_b = 1
        expected_slot_results = [1, 1, 0, 1, -1] # A wins, A wins (wounded), tie, A wins, B wins
        self.assertEqual(score_a, expected_score_a)
        self.assertEqual(score_b, expected_score_b)
        self.assertEqual(slot_results, expected_slot_results)

    def test_calculate_fight_results_empty_slots(self):
        """Tests a scenario where both cats in a slot are wounded."""
        # Ranks
        clan_a_ranks = [Rank.LEADER, Rank.DEPUTY, Rank.WARRIOR, Rank.APPRENTICE, Rank.APPRENTICE]
        clan_b_ranks = [Rank.LEADER, Rank.WARRIOR, Rank.WARRIOR, Rank.APPRENTICE, Rank.APPRENTICE]
        
        # Slot 2 has both cats wounded.
        clan_a_cards = [CombatMove.CLAW_SCRATCH, None, CombatMove.KICK, None, None]
        clan_b_cards = [CombatMove.BITE, None, CombatMove.LEAP, None, None]
        
        # ACT
        score_a, score_b, slot_results = CombatSystem.calculate_fight_results(clan_a_cards, clan_b_cards, clan_a_ranks, clan_b_ranks)
        
        # ASSERT
        # Clan A wins slot 1 (5 pts). Slot 2 is empty. Clan B wins slot 3 (3 pts).
        expected_score_a = 5
        expected_score_b = 3
        expected_slot_results = [1, 0, -1, 0, 0] # A wins, tie (both wounded), B wins, tie, tie
        self.assertEqual(score_a, expected_score_a)
        self.assertEqual(score_b, expected_score_b)
        self.assertEqual(slot_results, expected_slot_results)


if __name__ == '__main__':
    unittest.main()
