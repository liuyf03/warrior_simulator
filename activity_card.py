import random
from typing import List

from enums import Activity
from game_config import GameConfig

class ActivityCard:
    """
    Represents a card that dictates which activities a clan can perform.
    """
    def __init__(self, actions: List[Activity]):
        """
        Initializes an ActivityCard.

        Args:
            actions: A list of Activity enums that are on the card.
        """
        self.actions = actions

    def __repr__(self) -> str:
        """Helper to print nice names (e.g. "<ActivityCard: ['HUNT', 'PATROL']>")."""
        names = [a.name for a in self.actions]
        return f"<ActivityCard: {names}>"

def generate_balanced_activity_deck(
    num_cards: int = GameConfig.NUM_ACTIVITY_CARDS_IN_DECK,
    actions_per_card: int = GameConfig.ACTIVITY_SLOTS_PER_CARD
) -> List[ActivityCard]:
    """
    Generates a deck of ActivityCards using the 'Pool & Deal' algorithm.
    This ensures that across the entire deck, every Activity type appears
    the exact same number of times.

    Args:
        num_cards: The total number of cards to create in the deck.
        actions_per_card: The number of activity slots on each card.

    Returns:
        A list of ActivityCard objects.

    Raises:
        ValueError: If the total number of action slots is not perfectly
                    divisible by the number of available activity types.
    """
    activity_types = list(Activity)
    num_types = len(activity_types)

    # 1. Calculate Math
    total_slots = num_cards * actions_per_card

    if total_slots % num_types != 0:
        raise ValueError(
            f"Cannot balance deck! Total slots ({total_slots}) is not "
            f"divisible by number of activity types ({num_types})."
        )

    count_per_type = total_slots // num_types

    # 2. Create the Pool (The "Bag") and shuffle it
    pool = [activity for activity in activity_types for _ in range(count_per_type)]
    random.shuffle(pool)

    # 3. Deal into Cards
    return [ActivityCard(pool[i : i + actions_per_card]) for i in range(0, total_slots, actions_per_card)]
