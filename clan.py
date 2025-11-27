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

    def __init__(self, name: ClanName, camp_entrance: Tuple[int, int]):
        """Initializes a new Clan instance."""
        self.name: ClanName = name
        self.cats: List[Cat] = []
        self.prey_pile: int = 0
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

    def get_combat_squad(self) -> Tuple[List[Cat | None], List[Rank | None]]:
        """
        Assembles a 5-cat squad for combat based on rank.
        Sorts all cats by rank (Leader > Deputy > Warrior > Apprentice) and
        then by health (healthy > wounded).
        Returns a tuple of the cat list and the rank list for the slots.
        """
        # Define the desired order of ranks for sorting.
        rank_order = {Rank.LEADER: 0, Rank.DEPUTY: 1, Rank.WARRIOR: 2, Rank.APPRENTICE: 3}

        # 1. Sort all cats in the clan.
        # The key sorts by rank first, then by health (False/healthy comes before True/wounded).
        squad_cats = sorted(self.cats, key=lambda cat: (rank_order.get(cat.rank, 99), cat.is_wounded))

        # 2. Populate the final lists, nullifying wounded cats.
        squad_ranks: List[Rank | None] = [None] * len(squad_cats)

        for i, cat in enumerate(squad_cats):
            squad_ranks[i] = cat.rank
            if cat.is_wounded:
                squad_cats[i] = None # Wounded cats can't fight, so their card slot is empty
                
        return squad_cats, squad_ranks

    def promote_apprentice(self) -> Cat | None:
        """
        Finds the best apprentice and promotes them to a warrior.
        Prioritizes healthy apprentices. Returns the promoted cat or None.
        """
        # Sort apprentices by health (healthy first)
        eligible_apprentices = sorted(
            [c for c in self.cats if c.rank == Rank.APPRENTICE],
            key=lambda cat: cat.is_wounded
        )

        if eligible_apprentices:
            cat_to_promote = eligible_apprentices[0]
            if cat_to_promote.promote():
                return cat_to_promote
        return None

    def promote_warrior_to_deputy(self) -> Cat | None:
        """
        If no deputy exists, finds the best warrior and promotes them.
        Prioritizes healthy warriors. Returns the promoted cat or None.
        """
        if self.has_deputy():
            return None

        eligible_warriors = sorted(
            [c for c in self.cats if c.rank == Rank.WARRIOR],
            key=lambda cat: cat.is_wounded
        )

        if eligible_warriors:
            cat_to_promote = eligible_warriors[0]
            if cat_to_promote.promote():
                return cat_to_promote
        return None

    def __repr__(self) -> str:
        """Provides a developer-friendly representation of the Clan."""
        return f"Clan(name='{self.name}', members={len(self.cats)}, prey={self.prey_pile})"

    def __str__(self) -> str:
        """Provides a user-friendly representation of the Clan."""
        return f"The brave cats of {self.name}"
