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
    def calculate_fight_results(clan_a_cards: List[Optional[CombatMove]], clan_b_cards: List[Optional[CombatMove]], clan_a_ranks: List[Optional[Rank]], clan_b_ranks: List[Optional[Rank]]) -> Tuple[int, int]:
        """
        Compares 5 combat slots and returns the total scores for each clan.
        """
        score_a = 0
        score_b = 0
        
        # We assume lists are ordered by slot: [Leader, Deputy/Warrior, Warrior, Apprentice, Apprentice]
        for i in range(5):
            card_a, card_b = clan_a_cards[i], clan_b_cards[i]
            rank_a, rank_b = clan_a_ranks[i], clan_b_ranks[i]
            
            # Handle cases where one or both cats are wounded (card is None)
            if card_a is None and card_b is not None and rank_b is not None:
                score_b += GameConfig.SCORE_MAP.get(rank_b, 0)
                continue
            elif card_b is None and card_a is not None and rank_a is not None:
                score_a += GameConfig.SCORE_MAP.get(rank_a, 0)
                continue
            elif card_a is None or card_b is None:
                continue

            # Compare cards to find the winner of the slot
            result = CombatSystem.get_card_winner(card_a, card_b)
            
            if result == 1 and rank_a is not None:
                score_a += GameConfig.SCORE_MAP.get(rank_a, 0)
            elif result == -1 and rank_b is not None:
                score_b += GameConfig.SCORE_MAP.get(rank_b, 0)
                
        return score_a, score_b
