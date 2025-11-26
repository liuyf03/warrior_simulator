import logging
from typing import List, Dict, Tuple

from enums import ClanName, Rank
from cat import Cat

class Clan:
    """
    Represents a Clan in the game, managing cats, resources, and territory.

    Attributes:
        name (ClanName): The name of the Clan.
        cats (List[Cat]): A list of all cats belonging to this Clan.
        prey_pile (int): The current amount of prey the Clan has stored.
        territory_bounds (Dict[str, Tuple[int, int]]): A dictionary defining the
            Clan's territory, e.g., {'min': (x, y), 'max': (x, y)}.
        camp_entrance (Tuple[int, int]): The coordinates for the Clan's camp entrance.
    """

    def __init__(self, name: ClanName, territory_bounds: Dict[str, Tuple[int, int]], camp_entrance: Tuple[int, int]):
        """Initializes a new Clan instance."""
        self.name: ClanName = name
        self.cats: List[Cat] = []
        self.prey_pile: int = 0
        self.territory_bounds: Dict[str, Tuple[int, int]] = territory_bounds
        self.camp_entrance: Tuple[int, int] = camp_entrance
        logging.info(f"{self.name} has been established.")

    def add_cat(self, cat: Cat):
        """Adds a new cat to the clan, verifying it belongs."""
        if cat.clan_id == self.name:
            self.cats.append(cat)
            logging.info(f"{cat.name} has joined {self.name}.")
        else:
            logging.warning(f"Attempted to add {cat.name} to {self.name}, but they belong to {cat.clan_id}.")

    def log_state(self, debug: bool = False):
        """Logs the detailed state of the Clan if debug mode is active."""
        if debug:
            cat_names = [cat.name for cat in self.cats]
            logging.debug(f"--- Clan State: {self.name} ---\n"
                        f"  Prey Pile: {self.prey_pile}\n"
                        f"  Member Count: {len(self.cats)}\n"
                        f"  Members: {cat_names}\n"
                        f"  ------------------------")

    def get_warriors(self) -> List[Cat]:
        """Returns a list of all cats with the rank of Warrior or Deputy."""
        return [cat for cat in self.cats if cat.rank in (Rank.WARRIOR, Rank.DEPUTY)]

    def get_apprentices(self) -> List[Cat]:
        """Returns a list of all healthy (unwounded) apprentices."""
        return [cat for cat in self.cats if cat.rank == Rank.APPRENTICE and not cat.is_wounded]

    def add_prey(self, amount: int):
        """
        Adds a specified amount of prey to the clan's prey pile.
        The amount can be negative to represent consumption.
        """
        if amount == 0:
            return
        self.prey_pile += amount
        if amount > 0:
            logging.info(f"{self.name} added {amount} servings to the prey pile. Total: {self.prey_pile}.")
        else:
            logging.info(f"{self.name} consumed {-amount} servings. Total: {self.prey_pile}.")

    def has_deputy(self) -> bool:
        """Checks if the Clan currently has a cat with the rank of Deputy."""
        return any(cat.rank == Rank.DEPUTY for cat in self.cats)

    def __repr__(self) -> str:
        """Provides a developer-friendly representation of the Clan."""
        return f"Clan(name='{self.name}', members={len(self.cats)}, prey={self.prey_pile})"

    def __str__(self) -> str:
        """Provides a user-friendly representation of the Clan."""
        return f"The brave cats of {self.name}"
