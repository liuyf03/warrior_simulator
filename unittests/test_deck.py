import unittest
from deck import Deck

class TestDeck(unittest.TestCase):
    """Test suite for the generic Deck class."""

    def setUp(self):
        """Set up a simple deck for testing before each test."""
        self.sample_items = ['A', 'B', 'C', 'D']
        self.deck = Deck(self.sample_items)

    def test_initialization_and_reshuffle(self):
        """
        Tests that the deck is properly initialized and shuffled.
        """
        # The deck should contain all original items
        self.assertEqual(self.deck.remaining, len(self.sample_items))
        # The draw pile should be a permutation of the original items, not the same order
        # Note: There's a small chance shuffle results in the same order, but it's unlikely for larger decks.
        # A more robust check is to ensure all items are present.
        self.assertCountEqual(self.deck._draw_pile, self.sample_items, "Draw pile should contain all original items.")
        # Discard pile should be empty after a reshuffle
        self.assertEqual(len(self.deck._discard_pile), 0)

    def test_draw(self):
        """
        Tests drawing a card from the deck.
        """
        initial_count = self.deck.remaining
        card = self.deck.draw()

        # The drawn card should be one of the original items
        self.assertIn(card, self.sample_items)
        # The remaining count should decrease by one
        self.assertEqual(self.deck.remaining, initial_count - 1)

    def test_draw_until_empty_and_auto_reshuffle(self):
        """
        Tests that the deck automatically reshuffles when the draw pile is empty.
        """
        # Draw all cards from the deck
        for _ in range(len(self.sample_items)):
            self.deck.draw()

        # The draw pile should now be empty
        self.assertEqual(self.deck.remaining, 0)

        # Drawing one more card should trigger a reshuffle
        card = self.deck.draw()

        # The deck should now have (total_cards - 1) remaining
        self.assertEqual(self.deck.remaining, len(self.sample_items) - 1)
        self.assertIn(card, self.sample_items)

    def test_discard_single_card(self):
        """Tests adding a single card to the discard pile."""
        card_to_discard = 'X'
        self.deck.discard(card_to_discard)
        self.assertIn(card_to_discard, self.deck._discard_pile)
        self.assertEqual(len(self.deck._discard_pile), 1)

    def test_discard_multiple_cards(self):
        """Tests adding a list of cards to the discard pile."""
        cards_to_discard = ['X', 'Y', 'Z']
        self.deck.discard(cards_to_discard)
        self.assertCountEqual(self.deck._discard_pile, cards_to_discard)
        self.assertEqual(len(self.deck._discard_pile), 3)


if __name__ == '__main__':
    unittest.main()
