import logging
from typing import Tuple, List, Optional

from enums import ClanName, TileType
from game_config import GameConfig
from tile import Tile

class Board:
    """
    Manages the game board, including territory boundaries and legal positions.

    The board is represented as a grid of Tile objects, accessible by (x, y) coordinates.
    The center of the board is (0,0).

    Attributes:
        grid (dict[Tuple[int, int], Tile]): A dictionary mapping (x, y) coordinates to Tile objects.
    """

    def __init__(self):
        """
        Initializes the Board by generating all legal tiles.
        """
        self.grid: dict[Tuple[int, int], Tile] = {}  # Map (x, y) -> Tile object
        self._initialize_board()
        logging.info(f"Board initialized with N={GameConfig.N}, M={GameConfig.M}. Total tiles: {len(self.grid)}")

    def _initialize_board(self):
        """Generates all legal tiles based on N and M."""
        self._generate_border()
        self._generate_clan_territories()

    def _generate_border(self):
        """
        Generates the cross-shaped border area.
        Horizontal strip: x in [-Extent, Extent], y in [-Half_M, Half_M]
        Vertical strip: x in [-Half_M, Half_M], y in [-Extent, Extent]
        """
        half_m = GameConfig.border_half_width()
        extent = GameConfig.border_extent()

        # 1. Vertical Strip
        # Range includes start and end, so we add +1 to python range
        for x in range(-half_m, half_m + 1):
            for y in range(-extent, extent + 1):
                self.grid[(x, y)] = Tile(x, y, TileType.BORDER)

        # 2. Horizontal Strip (only add new tiles or overwrite existing border tiles)
        for y in range(-half_m, half_m + 1):
            for x in range(-extent, extent + 1):
                # Only add if not already present from vertical strip, or if it's a border tile
                if (x, y) not in self.grid or self.grid[(x, y)].type != TileType.BORDER:
                    self.grid[(x, y)] = Tile(x, y, TileType.BORDER)

    def _generate_clan_territories(self):
        """
        Generates 4 quadrants.
        Thunder: Top Left (Negative X, Positive Y)
        River: Top Right (Positive X, Positive Y)
        Shadow: Bottom Left (Negative X, Negative Y)
        Wind: Bottom Right (Positive X, Negative Y)
        """
        m = GameConfig.M
        n = GameConfig.N
        
        # Calculate start/end for Thunder (Base Quadrant)
        # Based on your coordinates:
        # X: -(M+1)/2 - N + 1  TO  -(M+1)/2
        # Y: (M+1)/2          TO  (M+1)/2 + N - 1
        
        offset = (m + 1) // 2
        
        # Thunder X range: [-offset - n + 1, -offset]
        # Thunder Y range: [offset, offset + n - 1]
        t_x_start = -offset - n + 1
        t_x_end = -offset
        t_y_start = offset
        t_y_end = offset + n - 1

        # We iterate through the base Thunder coordinates and reflect them
        for x in range(t_x_start, t_x_end + 1):
            for y in range(t_y_start, t_y_end + 1):
                
                # Thunder (Top Left)
                self.grid[(x, y)] = Tile(x, y, TileType.THUNDER_TERRITORY)
                
                # River (Reflect X -> Positive)
                self.grid[(-x, y)] = Tile(-x, y, TileType.RIVER_TERRITORY)
                
                # Shadow (Reflect Y -> Negative)
                self.grid[(x, -y)] = Tile(x, -y, TileType.SHADOW_TERRITORY)
                
                # Wind (Reflect X & Y -> Positive X, Negative Y)
                self.grid[(-x, -y)] = Tile(-x, -y, TileType.WIND_TERRITORY)

    # --- Public Methods ---

    def is_valid_position(self, pos: Tuple[int, int]) -> bool:
        """Returns True if pos (x,y) is a walkable tile."""
        return pos in self.grid

    def get_tile(self, pos: Tuple[int, int]) -> Optional[Tile]:
        """Returns the Tile object at the given position, or None if no tile exists."""
        return self.grid.get(pos)

    def get_neighbors(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Returns list of valid adjacent coordinates (N, S, E, W, and diagonals)."""
        x, y = pos
        # 8 directions
        directions = [
            (0, 1), (0, -1), (1, 0), (-1, 0), 
            (1, 1), (1, -1), (-1, 1), (-1, -1)
        ]
        valid_neighbors = []
        for dx, dy in directions:
            new_pos = (x + dx, y + dy)
            if new_pos in self.grid: # Check if the neighbor tile exists in our grid
                valid_neighbors.append(new_pos)
        return valid_neighbors

    def get_territory_of_position(self, position: Tuple[int, int]) -> Optional[ClanName]:
        """Identifies which clan territory a position belongs to, or None if it's a border or invalid tile."""
        tile = self.get_tile(position)
        if tile:
            if tile.type == TileType.THUNDER_TERRITORY:
                return ClanName.THUNDERCLAN
            elif tile.type == TileType.RIVER_TERRITORY:
                return ClanName.RIVERCLAN
            elif tile.type == TileType.SHADOW_TERRITORY:
                return ClanName.SHADOWCLAN
            elif tile.type == TileType.WIND_TERRITORY:
                return ClanName.WINDCLAN
        return None
