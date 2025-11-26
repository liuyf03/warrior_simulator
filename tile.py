from typing import Optional
from enums import TileType, ClanName

class Tile:
    """
    Represents a single tile on the game board.
    """
    def __init__(self, x: int, y: int, tile_type: TileType):
        self.x: int = x
        self.y: int = y
        self.type: TileType = tile_type
        self.prey_count: int = 0
        self.paw_print: Optional[ClanName] = None  # None or ClanName
        self.is_highlighted: bool = False # For border special spots or UI
        self.cat = None # The cat currently standing here (reference to Cat object)

    def __repr__(self) -> str:
        return f"Tile({self.x}, {self.y}, {self.type.value})"
