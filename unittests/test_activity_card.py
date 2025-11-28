import unittest
from collections import Counter

from activity_card import ActivityCard, generate_balanced_activity_deck
from enums import Activity
from game_config import GameConfig

class TestActivityCardAndDeck(unittest.TestCase):
    """
    Unit tests for the ActivityCard class and the generate_balanced_activity_deck function.
    """

    def test_activity_card_creation_and_repr(self):
        """Tests the basic creation and string representation of an ActivityCard."""
        actions = [Activity.HUNT, Activity.PATROL]
        card = ActivityCard(actions)
        self.assertEqual(card.actions, actions)
        # Test the __repr__ for a clean, readable output
        self.assertEqual(repr(card), "<ActivityCard: ['HUNT', 'PATROL']>")

    def test_generate_balanced_deck_properties(self):
        """
        Tests if the generated deck has the correct number of cards and is truly balanced.
        """
        # Use default config values for the test
        num_cards = GameConfig.NUM_ACTIVITY_CARDS_IN_DECK
        actions_per_card = GameConfig.ACTIVITY_SLOTS_PER_CARD

        deck = generate_balanced_activity_deck()

        # 1. Check if the number of generated cards is correct
        self.assertEqual(len(deck), num_cards)

        # 2. Check if each card has the correct number of actions
        for card in deck:
            self.assertIsInstance(card, ActivityCard)
            self.assertEqual(len(card.actions), actions_per_card)

        # 3. Verify the "balanced" property of the deck
        all_activities_in_deck = [action for card in deck for action in card.actions]
        activity_counts = Counter(all_activities_in_deck)

        # Calculate the expected count for each activity type
        total_slots = num_cards * actions_per_card
        expected_count_per_type = total_slots // len(Activity)

        # Assert that every activity type appears the expected number of times
        self.assertEqual(len(activity_counts), len(Activity)) # Ensure all types are present
        for activity_type in Activity:
            with self.subTest(activity=activity_type.name):
                self.assertEqual(activity_counts[activity_type], expected_count_per_type)

    def test_generate_unbalanced_deck_raises_error(self):
        """
        Tests that a ValueError is raised if the deck cannot be balanced.
        """
        # Use parameters that are intentionally not divisible
        num_cards = 7
        actions_per_card = 3 # Total slots = 21, not divisible by 4 activity types
        with self.assertRaises(ValueError):
            generate_balanced_activity_deck(num_cards=num_cards, actions_per_card=actions_per_card)

if __name__ == '__main__':
    unittest.main()
