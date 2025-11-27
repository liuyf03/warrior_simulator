import random
import logging
from typing import List

from enums import Direction

class Dice:
    """A simple dice class for generating random numbers."""
    def __init__(self, sides: int = 6):
        self.sides = sides
        self.history: List[int] = [] # Optional: Track rolls for stats

    def roll(self, sides: int = 0) -> int:
        """Rolls the die and returns the result. Can temporarily override the default sides."""
        roll_sides = sides if sides > 0 else self.sides
        val = random.randint(1, roll_sides)
        self.history.append(val)
        logging.debug(f"Rolled a {roll_sides}-sided die: {val}")
        return val

class Spinner:
    """A spinner class for choosing a random direction."""
    def __init__(self):
        # Use the Direction enum for consistency and type safety
        self.directions: List[Direction] = list(Direction)
    
    def spin(self) -> Direction:
        """Spins the spinner and returns a random Direction enum member."""
        chosen_direction = random.choice(self.directions)
        logging.debug(f"Spinner landed on: {chosen_direction.name}")
        return chosen_direction
