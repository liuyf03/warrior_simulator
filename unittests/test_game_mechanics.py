import unittest

from game_mechanics import Dice, Spinner
from enums import Direction

class TestDice(unittest.TestCase):
    """Test suite for the Dice class."""

    def test_initialization(self):
        """Tests both default and custom initialization."""
        default_die = Dice()
        self.assertEqual(default_die.sides, 6, "Die should default to 6 sides.")

        custom_die = Dice(sides=20)
        self.assertEqual(custom_die.sides, 20, "Die should be initialized with custom sides.")

    def test_roll_default_sides(self):
        """Tests that a roll is within the default range [1, 6]."""
        die = Dice()
        for _ in range(100):
            roll_value = die.roll()
            self.assertGreaterEqual(roll_value, 1)
            self.assertLessEqual(roll_value, 6)

    def test_roll_override_sides(self):
        """Tests that a roll's sides can be temporarily overridden."""
        die = Dice(sides=6) # A standard die
        for _ in range(100):
            # Temporarily roll it as a 10-sided die
            roll_value = die.roll(sides=10)
            self.assertGreaterEqual(roll_value, 1)
            self.assertLessEqual(roll_value, 10)

    def test_roll_history(self):
        """Tests that the roll history is recorded correctly."""
        die = Dice()
        self.assertEqual(len(die.history), 0, "History should be empty initially.")
        
        roll1 = die.roll()
        self.assertEqual(len(die.history), 1)
        self.assertEqual(die.history[0], roll1)

        roll2 = die.roll()
        self.assertEqual(len(die.history), 2)
        self.assertEqual(die.history[1], roll2)


class TestSpinner(unittest.TestCase):
    """Test suite for the Spinner class."""

    def setUp(self):
        """Set up a spinner for testing."""
        self.spinner = Spinner()

    def test_initialization(self):
        """Tests that the spinner contains all directions from the enum."""
        all_directions = list(Direction)
        self.assertCountEqual(self.spinner.directions, all_directions, "Spinner should contain all directions from the enum.")

    def test_spin_returns_valid_direction(self):
        """Tests that spinning returns a valid Direction enum member."""
        for _ in range(100):
            result = self.spinner.spin()
            self.assertIsInstance(result, Direction, "Spin result must be an instance of the Direction enum.")


if __name__ == '__main__':
    unittest.main()
