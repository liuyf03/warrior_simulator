from typing import Optional, TYPE_CHECKING
from enums import TileType, ClanName

class Tile:
    """
    Represents a single tile on the game board.
    """
    def __init__(self, x: int, y: int, tile_type: TileType):
        self.x: int = x
        self.y: int = y
        self.type: TileType = tile_type
        self.is_highlighted: bool = False # For border special spots or UI
        self.is_spawn_point: bool = False # For prey spawn locations
        self.slot_id: Optional[int] = None # The prey spawn slot ID (1-6)
        # State variables
        self.prey_count: int = 0
        self.paw_print: Optional[ClanName] = None  # None or ClanName

    @property
    def is_walkable(self) -> bool:
        """Returns True if the tile is not an obstacle."""
        return self.type != TileType.OBSTACLE
    
    def reset_prey(self):
        """Resets the prey count on this tile to zero."""
        self.prey_count = 0

    def reset_paw_print(self):
        """Removes any paw print from this tile."""
        self.paw_print = None

    def __repr__(self) -> str:
        return f"Tile({self.x}, {self.y}, {self.type.value})"
