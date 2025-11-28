import logging
from typing import List, Dict, Tuple

from enums import ClanName, Rank
from game_config import GameConfig
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

    def _reset_clan_cats(self):
        """Creates and adds the starting cats (Leader, Warriors, Apprentices) to the clan."""
        # 1. Leader (1 per clan)
        self.add_cat(name=f"{self.name.value}star", rank=Rank.LEADER)

        # 2. Warriors
        for i in range(GameConfig.NUM_INITIAL_WARRIORS_PER_CLAN):
            self.add_cat(name=f"Warrior {i+1}", rank=Rank.WARRIOR)

        # 3. Apprentices
        for i in range(GameConfig.NUM_INITIAL_APPRENTICES_PER_CLAN):
            self.add_cat(name=f"Apprentice {i+1}", rank=Rank.APPRENTICE)
    
    def add_cat(self, name: str, rank: Rank):
        """Creates a new cat with the clan's properties and adds it."""
        new_cat = Cat(name=name, clan_id=self.name, rank=rank, position=self.camp_entrance)
        self.cats.append(new_cat)
        logging.info(f"{new_cat.name} has joined {self.name}.")

    def reset_clan_state(self):
        """Resets the clan's prey pile and the state of all its cats for a new game."""
        logging.info(f"Resetting state for {self.name}...")
        self.prey_pile = 0

        self._reset_clan_cats()
        for cat in self.cats:
            cat.is_wounded = False
            cat.rank = cat.original_rank # Revert any promotions
            cat.position = self.camp_entrance  # Move cat back to camp
        logging.info(f"{self.name} state has been reset.")

    def heal_cats(self, current_turn: int):
        """Checks for and heals any cats that have recovered from their wounds."""
        for cat in self.cats:
            if cat.is_wounded and cat.wounded_turn_index is not None:
                turns_wounded = current_turn - cat.wounded_turn_index
                if turns_wounded >= GameConfig.WOUNDED_CATS_TURNS_TO_SKIP:
                    logging.info(f"  Healing {cat.name} who was wounded on turn {cat.wounded_turn_index}.")
                    cat.heal(self.camp_entrance)


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

    def get_active_warriors(self) -> List[Cat]:
        """Returns a list of healthy (unwounded) cats with the rank of Warrior or Deputy."""
        return [cat for cat in self.cats if cat.rank in (Rank.WARRIOR, Rank.DEPUTY) and not cat.is_wounded]

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
