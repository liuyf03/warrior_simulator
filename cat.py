import uuid
import logging
from typing import Optional, Tuple

from enums import Rank, ClanName

class Cat:
    """
    Represents a single cat in the game simulation.

    Each cat has a unique ID, a name, a rank within its clan, and tracks
    its physical state and position on the game board.

    Attributes:
        name (str): The name of the cat.
        clan_id (ClanName): The identifier for the clan this cat belongs to.
        rank (Rank): The cat's current rank in the clan.
        id (uuid.UUID): A unique identifier for the cat.
        is_wounded (bool): True if the cat is injured, False otherwise.
        position (Optional[Tuple[int, int]]): The (x, y) coordinates of the cat
            on the map. Is None if the cat is in the Medicine Den.
    """

    def __init__(self, name: str, clan_id: ClanName, rank: Rank, position: Optional[Tuple[int, int]]):
        """Initializes a new Cat instance."""
        self.id: uuid.UUID = uuid.uuid4()
        self.name: str = name
        self.clan_id: ClanName = clan_id
        self.rank: Rank = rank
        self.original_rank: Rank = rank # Store the initial rank for resets
        self.is_wounded: bool = False
        self.position: Optional[Tuple[int, int]] = position
        self.wounded_turn_index: Optional[int] = None

    def log_state(self, debug: bool = False):
        """Prints the detailed state of the cat if debug mode is active."""
        if debug:
            # This uses a multi-line string for cleaner formatting in logs.
            # We use logging.debug for high-verbosity information.
            logging.debug(f"--- Cat State: {self.name} ---\n"
                        f"  ID: {self.id}\n"
                        f"  Clan: {self.clan_id}\n"
                        f"  Rank: {self.rank}, Wounded: {self.is_wounded}\n"
                        f"  Position: {self.position}\n"
                        f"  ------------------------")

    def move(self, new_position: Tuple[int, int]):
        """
        Updates the cat's position on the map.
        A cat cannot move if it is wounded.
        """
        if self.is_wounded:
            logging.info(f"{self.name} is wounded and cannot move from the Medicine Den.")
            return
        self.position = new_position
        logging.info(f"{self.name} moved to {self.position}.")

    def promote(self) -> bool:
        """
        Promotes the cat to the next rank.
        Returns True if promotion was successful, False otherwise.
        """
        if self.rank == Rank.APPRENTICE:
            self.rank = Rank.WARRIOR
            logging.info(f"{self.name} has been promoted to Warrior!")
            return True
        elif self.rank == Rank.WARRIOR:
            self.rank = Rank.DEPUTY
            logging.info(f"{self.name} has been promoted to Deputy!")
        else:
            logging.warning(f"{self.name} cannot be promoted from the rank of {self.rank}.")
            return False

    def sustain_injury(self, current_turn: int):
        """
        Inflicts an injury on the cat.
        The cat is moved to the Medicine Den (position becomes None).
        """
        self.is_wounded = True
        self.wounded_turn_index = current_turn
        self.position = None  # Represents being in the Medicine Den
        logging.info(f"{self.name} has been wounded and is now in the Medicine Den.")

    def heal(self, camp_entrance: Tuple[int, int]):
        """
        Heals the cat from its injuries.
        The cat is moved to the provided camp entrance coordinates.
        """
        if not self.is_wounded:
            logging.info(f"{self.name} is not wounded.")
            return

        self.is_wounded = False
        self.wounded_turn_index = None
        self.position = camp_entrance
        logging.info(f"{self.name} has healed and returned to the camp entrance at {self.position}.")

    def __repr__(self) -> str:
        """Provides a developer-friendly representation of the Cat."""
        return f"Cat(name='{self.name}', rank='{self.rank}', clan='{self.clan_id}')"

    def __str__(self) -> str:
        """Provides a user-friendly representation of the Cat."""
        return f"{self.name} ({self.rank})"