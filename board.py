import logging
import random
from typing import Tuple, List, Optional

from enums import ClanName, TileType, Direction
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
        self.grid: dict[Tuple[int, int], Tile] = {}
        self.spawn_points: dict[ClanName, dict[int, Tuple[int, int]]] = {}
        self._initialize_board()
        logging.info(f"Board initialized with HUNTING_GROUND_SIZE={GameConfig.HUNTING_GROUND_SIZE}, BORDER_WIDTH={GameConfig.BORDER_WIDTH}. Total tiles: {len(self.grid)}")

    def _initialize_board(self):
        """Generates all legal tiles based on N and M."""
        self._generate_border()
        self._generate_clan_territories()
        self._assign_spawn_points()

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
        m = GameConfig.BORDER_WIDTH
        n = GameConfig.HUNTING_GROUND_SIZE
        
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

    def _assign_spawn_points(self):
        """
        Assigns 6 prey spawn slots per clan using a symmetrical pattern.
        Constraint 1: One prey per row/column in the territory (Permutation).
        Constraint 2: All clans share the exact same pattern, reflected.
        """
        n = GameConfig.HUNTING_GROUND_SIZE
        m = GameConfig.BORDER_WIDTH
        
        # Calculate Base (ThunderClan) Start Coordinates
        # ThunderClan is Top-Left: Negative X, Positive Y
        offset = (m + 1) // 2
        base_x_start = -offset - n + 1
        base_y_start = offset

        # Get all camp coordinates to avoid placing spawn points on them
        camp_coords = set(GameConfig.get_clan_camps().values())

        col_indices = []
        # 1. Generate and validate the Master Pattern (The "Seed")
        while True:
            # Generate a potential pattern
            potential_indices = list(range(n))
            random.shuffle(potential_indices)
            
            # Check if this pattern would cause any spawn point to overlap with a camp
            overlap_found = False
            for row_idx, col_idx in enumerate(potential_indices):
                base_x = base_x_start + col_idx
                base_y = base_y_start + row_idx
                
                # Check all 4 reflections for this single point
                if (base_x, base_y) in camp_coords or \
                   (-base_x, base_y) in camp_coords or \
                   (base_x, -base_y) in camp_coords or \
                   (-base_x, -base_y) in camp_coords:
                    overlap_found = True
                    break # This permutation is invalid, no need to check further
            
            if not overlap_found:
                col_indices = potential_indices
                break # Found a valid permutation, exit the loop

        # Multipliers for reflections: (x_mult, y_mult)
        clan_orientations = {
            ClanName.THUNDERCLAN: (1, 1),   # Base
            ClanName.RIVERCLAN:   (-1, 1),  # Reflect X
            ClanName.SHADOWCLAN:  (1, -1),  # Reflect Y
            ClanName.WINDCLAN:    (-1, -1)  # Reflect Both
        }

        for clan_name, (x_mult, y_mult) in clan_orientations.items():
            # Reset/Ensure dict exists
            self.spawn_points[clan_name] = {}

            # Apply the Master Pattern
            for row_idx, col_idx in enumerate(col_indices):
                
                # Calculate Base Position (relative to ThunderClan's territory)
                # row_idx maps to Y (0 to 5)
                # col_idx maps to X (0 to 5, randomized)
                base_x = base_x_start + col_idx
                base_y = base_y_start + row_idx
                
                # Apply Reflection to get the final coordinates
                final_x = base_x * x_mult
                final_y = base_y * y_mult
                
                # Map to Slot ID (1-6)
                slot_id = row_idx + 1
                
                # Store the spawn point coordinate
                self.spawn_points[clan_name][slot_id] = (final_x, final_y)
                
                # Optional: Flag the tile for visualization
                if (final_x, final_y) in self.grid:
                    self.grid[(final_x, final_y)].is_spawn_point = True

    # --- Public Methods ---

    def spawn_prey(self, clan_name: ClanName, slot_number: int) -> bool:
        """
        Places a prey on the specific numbered slot for the given clan.
        Returns True if successful, False if invalid.
        """
        clan_spawns = self.spawn_points.get(clan_name)
        if not clan_spawns:
            logging.warning(f"Attempted to spawn prey for non-existent clan: {clan_name}")
            return False

        target_pos = clan_spawns.get(slot_number)
        if target_pos:
            tile = self.get_tile(target_pos)
            if tile:
                tile.prey_count += 1
                logging.info(f"  [Board] Prey spawned for {clan_name.value} at slot {slot_number} {target_pos}")
                return True
            else:
                logging.error(f"Spawn point {target_pos} for {clan_name.value} does not exist on grid.")
                return False
        return False

    def get_tile(self, pos: Tuple[int, int]) -> Optional[Tile]:
        """Returns the Tile object at the given position, or None if no tile exists."""
        return self.grid.get(pos)

    def trace_path(self, start_pos: Tuple[int, int], direction: Direction, steps: int, can_enter_func, stop_cond_func=None) -> Tuple[Tuple[int, int], List[Tile]]:
        """
        Simulates a move step-by-step and returns the final position and path taken.
        
        Args:
            start_pos: The starting (x, y) coordinate tuple.
            direction: The Direction enum member to move in.
            steps: The maximum number of tiles to move (e.g., from a dice roll).
            can_enter_func: A function that takes a Tile object and returns True if a cat
                            is allowed to step onto it based on game rules.
            stop_cond_func: An optional function that takes a position tuple and returns
                            True if the movement should stop after reaching that tile.
                            
        Returns:
            A tuple containing:
            - final_pos (Tuple[int, int]): The coordinate where the cat stopped.
            - visited_tiles (List[Tile]): The list of tiles the cat stepped on.
        """
        current_pos = start_pos
        visited_tiles = []

        dx, dy = direction.value
        for _ in range(steps):
            next_pos = (current_pos[0] + dx, current_pos[1] + dy)
            tile = self.get_tile(next_pos)

            # Stop if the move is invalid (hits edge, obstacle, or breaks a rule)
            if not tile or not tile.is_walkable or not can_enter_func(tile):
                break

            # If the move is valid, update position and record the tile
            current_pos = next_pos
            visited_tiles.append(tile)

            # Check post-move stopping condition
            if stop_cond_func and stop_cond_func(current_pos):
                break

        return current_pos, visited_tiles

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

    def get_distance_to_border(self, pos: Tuple[int, int]) -> int:
        """
        Calculates Chebyshev distance from pos to the nearest Border tile.
        Returns 0 if the tile is on the border or does not exist.
        """
        tile = self.get_tile(pos)
        if not tile or tile.type == TileType.BORDER:
            return 0

        x, y = pos
            
        # Border Geometry (Union of two rectangles)
        half_m = GameConfig.border_half_width()
        extent = GameConfig.border_extent()
        
        # Distance to the vertical border strip
        # This is the Chebyshev distance from (x,y) to the rectangle defined by
        # x in [-half_m, half_m] and y in [-extent, extent].
        dx_v = max(-half_m - x, 0, x - half_m)
        dy_v = max(-extent - y, 0, y - extent) # This is usually 0 for valid tiles
        dist_v = max(dx_v, dy_v)
        
        # Distance to the horizontal border strip
        dy_h = max(-half_m - y, 0, y - half_m)
        dx_h = max(-extent - x, 0, x - extent) # This is usually 0 for valid tiles
        dist_h = max(dx_h, dy_h)
        
        # The distance to the border area is the minimum of the distances to the two strips.
        return min(dist_v, dist_h)
