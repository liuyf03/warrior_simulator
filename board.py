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

        Args:
            seed: An optional integer to seed the random number generator for reproducible boards.
        """
        self.grid: dict[Tuple[int, int], Tile] = {}
        self.spawn_points: dict[ClanName, dict[int, Tuple[int, int]]] = {}
        self._rng = random.Random(GameConfig.SEED_FOR_BOARD_GENERATION)  # Create a dedicated random generator instance
        self._initialize_board()
        logging.info(f"Board initialized with HUNTING_GROUND_SIZE={GameConfig.HUNTING_GROUND_SIZE}, BORDER_WIDTH={GameConfig.BORDER_WIDTH}. Total tiles: {len(self.grid)}")

    def _initialize_board(self):
        """Generates all legal tiles based on N and M."""
        self._generate_border()
        self._generate_clan_territories()
        self._assign_spawn_points()
        self._assign_border_highlights()
        self._assign_starclan_landmarks()

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

    def _reflect_and_set(self, base_x: int, base_y: int, setter_func, use_clan_context: bool = True):
        """
        Takes a base coordinate from the positive-positive quadrant (RiverClan)
        and calls a setter function for it and its three reflections. Can operate
        with or without passing a clan context to the setter.
        """
        positions = [(base_x, base_y), (-base_x, base_y), (base_x, -base_y), (-base_x, -base_y)]
        clans = [ClanName.RIVERCLAN, ClanName.THUNDERCLAN, ClanName.WINDCLAN, ClanName.SHADOWCLAN]

        if use_clan_context:
            for pos, clan in zip(positions, clans):
                setter_func(pos[0], pos[1], clan)
        else:
            for x, y in positions:
                setter_func(x, y)

    def _generate_clan_territories(self):
        """
        Generates the four clan territory quadrants by calculating the base
        positive-positive quadrant and reflecting it.
        """
        m = GameConfig.BORDER_WIDTH
        n = GameConfig.HUNTING_GROUND_SIZE
        offset = (m + 1) // 2
        
        # Define the tile types for each clan
        clan_tile_map = {
            ClanName.RIVERCLAN: TileType.RIVER_TERRITORY,
            ClanName.THUNDERCLAN: TileType.THUNDER_TERRITORY,
            ClanName.WINDCLAN: TileType.WIND_TERRITORY,
            ClanName.SHADOWCLAN: TileType.SHADOW_TERRITORY,
        }

        def tile_setter(x, y, clan_name):
            self.grid[(x, y)] = Tile(x, y, clan_tile_map[clan_name])

        # Iterate over the base positive-positive quadrant (RiverClan)
        for x in range(offset, offset + n):
            for y in range(offset, offset + n):
                self._reflect_and_set(x, y, tile_setter)

    def _assign_spawn_points(self):
        """
        Assigns 6 prey spawn slots per clan using a symmetrical pattern.
        Constraint 1: One prey per row/column in the territory (Permutation).
        Constraint 2: All clans share the exact same pattern, reflected.
        """
        n = GameConfig.HUNTING_GROUND_SIZE
        offset = (GameConfig.BORDER_WIDTH + 1) // 2

        # Get all camp coordinates to avoid placing spawn points on them
        camp_coords = set(GameConfig.get_clan_camps().values())

        # 1. Generate and validate the Master Pattern for one quadrant
        master_pattern = []
        while True:
            potential_pattern = list(range(n))
            self._rng.shuffle(potential_pattern)
            
            overlap_found = False
            for row_idx, col_idx in enumerate(potential_pattern):
                base_x = offset + col_idx
                base_y = offset + row_idx
                
                # Check all 4 reflections for camp overlap
                if any(pos in camp_coords for pos in [(base_x, base_y), (-base_x, base_y), (base_x, -base_y), (-base_x, -base_y)]):
                    overlap_found = True
                    break
            
            if not overlap_found:
                master_pattern = potential_pattern
                break

        # 2. Define the setter function to be used by the reflection helper
        def spawn_point_setter(x, y, clan_name):
            # Initialize dict for clan if it doesn't exist
            if clan_name not in self.spawn_points:
                self.spawn_points[clan_name] = {}

            # The row index determines the slot ID (1-6)
            slot_id = abs(y) - offset + 1
            self.spawn_points[clan_name][slot_id] = (x, y)
            
            # Flag the tile for visualization
            tile = self.get_tile((x, y))
            if tile:
                tile.is_spawn_point = True
                tile.slot_id = slot_id

        # 3. Apply the master pattern using the reflection helper
        for row_idx, col_idx in enumerate(master_pattern):
            base_x = offset + col_idx
            base_y = offset + row_idx
            self._reflect_and_set(base_x, base_y, spawn_point_setter)

    def _assign_border_highlights(self):
        """
        Randomly selects a percentage of BORDER tiles to be 'Highlighted' using
        a symmetrical pattern. It picks points in the first quadrant (positive x,
        positive y) and reflects them to the other three quadrants.
        """
        # 1. Filter: Get a list of all border tiles in the first quadrant (x > 0, y > 0)
        base_border_positions = [
            pos for pos, tile in self.grid.items() if
            tile.type == TileType.BORDER and pos[0] > 0 and pos[1] > 0
        ]

        # 2. Calculate Count: We want the total number of highlights to match the ratio.
        # Since each point we pick in the base quadrant will create up to 4 highlighted tiles,
        # we divide the total target by 4.
        total_border_tiles = len([t for t in self.grid.values() if t.type == TileType.BORDER])
        total_target_highlights = int(total_border_tiles * GameConfig.BORDER_HIGHLIGHT_RATIO)
        num_base_points_to_pick = total_target_highlights // 4

        if num_base_points_to_pick == 0 or not base_border_positions:
            return

        # 3. Random Selection: Choose the base points from the first quadrant.
        chosen_base_positions = self._rng.sample(base_border_positions, min(num_base_points_to_pick, len(base_border_positions)))

        # 4. Define the setter and apply reflections
        def highlight_setter(x, y):
            if (x, y) in self.grid:
                self.grid[(x, y)].is_highlighted = True

        for x, y in chosen_base_positions:
            self._reflect_and_set(x, y, highlight_setter, use_clan_context=False)

    def _assign_starclan_landmarks(self):
        """
        Randomly selects a percentage of eligible tiles to be 'StarClan Landmarks'
        using a symmetrical pattern.
        """
        camp_coords = set(GameConfig.get_clan_camps().values())

        def is_eligible(pos: Tuple[int, int]) -> bool:
            """Helper to check if a single tile can be a landmark."""
            tile = self.get_tile(pos)
            return (
                tile is not None and
                tile.is_walkable and
                not tile.is_spawn_point and
                not tile.is_highlighted and
                pos not in camp_coords
            )

        # 1. Find all potential base points in the first quadrant (x>0, y>0)
        # and validate that all four of their reflections are eligible.
        valid_base_positions = []
        for pos in self.grid:
            x, y = pos
            if x > 0 and y > 0:
                # Check the base point and all its reflections
                if all(is_eligible(p) for p in [(x, y), (-x, y), (x, -y), (-x, -y)]):
                    valid_base_positions.append(pos)

        # 2. Calculate how many sets of 4 landmarks to create
        total_tiles = len(self.grid)
        total_target_landmarks = int(total_tiles * GameConfig.STARCLAN_LANDMARK_RATIO)
        num_base_points_to_pick = total_target_landmarks // 4

        if num_base_points_to_pick == 0 or not valid_base_positions:
            return

        # 3. Randomly select the base points
        chosen_base_positions = self._rng.sample(valid_base_positions, min(num_base_points_to_pick, len(valid_base_positions)))

        # 4. Define the setter and apply reflections
        def landmark_setter(x, y):
            self.grid[(x, y)].is_starclan_landmark = True

        for x, y in chosen_base_positions:
            self._reflect_and_set(x, y, landmark_setter, use_clan_context=False)

    # --- Public Methods ---

    def clear_prey(self):
        """Resets the prey count on all tiles to zero."""
        logging.info("Clearing all prey from the board.")
        for tile in self.grid.values():
            tile.prey_count = 0

    def clear_paw_prints(self):
        """Removes all paw prints from the board."""
        logging.info("Clearing all paw prints from the board.")
        for tile in self.grid.values():
            tile.paw_print = None

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
