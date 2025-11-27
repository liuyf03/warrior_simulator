import random
import logging
from typing import List, TypeVar, Union

# A generic type variable to represent the items in the deck
T = TypeVar('T')

class Deck:
    """
    A generic class for managing a deck of items (e.g., cards).
    Handles shuffling, drawing, and reshuffling.
    """
    def __init__(self, items: List[T]):
        """
        Initializes the deck with a list of items.

        Args:
            items: A list of objects (strings, Card objects, etc.) that make up the deck.
        """
        self._original_items: List[T] = list(items)  # Keep a backup for reshuffling
        self._draw_pile: List[T] = []
        self._discard_pile: List[T] = []
        self.reshuffle()

    def reshuffle(self):
        """Resets the deck using the original items."""
        self._draw_pile = list(self._original_items)
        random.shuffle(self._draw_pile)
        self._discard_pile = []
        logging.info("  [Deck] Reshuffled!")

    def draw(self) -> T:
        """Returns the top card. Automatically reshuffles if empty."""
        if not self._draw_pile:
            logging.info("Draw pile empty, reshuffling deck.")
            self.reshuffle()
        
        return self._draw_pile.pop()

    def discard(self, cards: Union[T, List[T]]):
        """
        Adds cards to the discard pile.
        Accepts a single card or a list of cards.
        """
        if isinstance(cards, list):
            self._discard_pile.extend(cards)
        else:
            self._discard_pile.append(cards)

    @property
    def remaining(self) -> int:
        """Returns the number of cards left in the draw pile."""
        return len(self._draw_pile)
