from typing import List, Optional, Tuple

from enums import Rank, CombatMove
from game_config import GameConfig

class CombatSystem:
    """
    Handles the logic for resolving fights between clans based on cards and ranks.
    """
    # Rock-Paper-Scissors Logic for combat moves
    WIN_RULES = {
        CombatMove.CLAW_SCRATCH: [CombatMove.BITE, CombatMove.LEAP],
        CombatMove.BITE: [CombatMove.KICK, CombatMove.LEAP],
        CombatMove.LEAP: [CombatMove.KICK],
        CombatMove.KICK: [CombatMove.CLAW_SCRATCH]
    }

    @staticmethod
    def get_card_winner(card_a: CombatMove, card_b: CombatMove) -> int:
        """
        Compares two combat cards and determines the winner.
        Returns 1 if A wins, -1 if B wins, 0 if Tie/Void.
        """
        if card_b in CombatSystem.WIN_RULES.get(card_a, []): # type: ignore
            return 1
        elif card_a in CombatSystem.WIN_RULES.get(card_b, []): # type: ignore
            return -1
        return 0

    @staticmethod
    def calculate_fight_results(clan_a_cards: List[Optional[CombatMove]], clan_b_cards: List[Optional[CombatMove]], clan_a_ranks: List[Optional[Rank]], clan_b_ranks: List[Optional[Rank]]) -> Tuple[int, int, List[int]]:
        """
        Compares combat slots and returns total scores and individual slot results.
        
        Returns:
            A tuple containing (score_a, score_b, slot_results).
            slot_results is a list of integers: 1 for A win, -1 for B win, 0 for tie.
        """
        score_a = 0
        score_b = 0
        slot_results: List[int] = [0] * GameConfig.NUM_CATS_PER_CLAN
        
        # Loop up to the configured squad size
        for i in range(GameConfig.NUM_CATS_PER_CLAN):
            card_a, card_b = clan_a_cards[i], clan_b_cards[i]
            rank_a, rank_b = clan_a_ranks[i], clan_b_ranks[i]
            
            # Handle cases where one or both cats are wounded (card is None)
            if card_a is None and card_b is not None and rank_b is not None:
                score_b += GameConfig.SCORE_MAP.get(rank_b, 0)
                slot_results[i] = -1
            elif card_b is None and card_a is not None and rank_a is not None:
                score_a += GameConfig.SCORE_MAP.get(rank_a, 0)
                slot_results[i] = 1
            elif card_a is not None and card_b is not None:
                # Both cats are healthy, compare cards
                slot_results[i] = CombatSystem.get_card_winner(card_a, card_b)
                if slot_results[i] == 1 and rank_a is not None:
                    score_a += GameConfig.SCORE_MAP.get(rank_a, 0)
                elif slot_results[i] == -1 and rank_b is not None:
                    score_b += GameConfig.SCORE_MAP.get(rank_b, 0)
            
        return score_a, score_b, slot_results
                
