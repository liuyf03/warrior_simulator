import logging
from typing import Tuple, Dict, List

from board import Board
from cat import Cat
from clan import Clan
from game_config import GameConfig
from enums import Direction, TileType, ClanName
from tile import Tile

class GameEngine:
    """
    The main orchestrator for the game simulation. It holds the game state
    and executes game logic and actions.
    """
    def __init__(self):
        """Initializes the GameEngine."""
        self.board = Board()
        self.clans: Dict[ClanName, Clan] = {}
        self._initialize_clans()
        logging.info("GameEngine initialized.")

    def _initialize_clans(self):
        """Creates instances for each clan and stores them."""
        logging.info("Initializing all clans...")
        clan_camps = GameConfig.get_clan_camps()
        for clan_name, camp_pos in clan_camps.items():
            self.clans[clan_name] = Clan(name=clan_name, camp_entrance=camp_pos)

    def execute_hunt_move(self, cat: Cat, direction: Direction, steps: int) -> Tuple[Tuple[int, int], int]:
        """
        Moves a cat according to Hunting rules and processes the outcome.
        """
        logging.info(f"{cat.name} is hunting {direction.name} for {steps} steps from {cat.position}.")

        # --- Rule Definition for Hunting ---
        def is_valid_hunt_step(target_tile: Tile) -> bool:
            # Rule: Hunting cats must stop BEFORE entering a border tile.
            if target_tile.type == TileType.BORDER:
                return False
            # Rule: Cats cannot enter enemy territory (implied by stopping at the border).
            return True
        # -----------------------------------

        # 1. Ask the Board to calculate the physical movement
        final_pos, path_tiles = self.board.trace_path(
            cat.position, 
            direction, 
            steps, 
            is_valid_hunt_step
        )

        # 2. Update the Cat's state
        cat.move(final_pos)

        # 3. Process interactions along the path (e.g., collect prey)
        prey_caught = 0
        for tile in path_tiles:
            if tile.prey_count > 0:
                logging.info(f"  -> {cat.name} caught prey at ({tile.x}, {tile.y})!")
                prey_caught += tile.prey_count
                tile.prey_count = 0 # Remove prey from the board
        
        # 4. Update the Clan's resources (uncomment when clans are managed by engine)
        if prey_caught > 0 and cat.clan_id in self.clans:
            self.clans[cat.clan_id].add_prey(prey_caught)
        
        return final_pos, prey_caught

    def execute_border_patrol_move(self, cat: Cat, direction: Direction, steps: int) -> Tuple[Tuple[int, int], List[Tile]]:
        """
        Moves a cat according to Border Patrol rules and processes the outcome.
        """
        logging.info(f"{cat.name} is patrolling {direction.name} for {steps} steps from {cat.position}.")

        # --- Rule Definition for Patrolling ---
        def is_valid_border_patrol_step(target_tile: Tile) -> bool:
            # Rule: Patrolling cats can enter their own territory and border tiles.
            tile_clan = self.board.get_territory_of_position((target_tile.x, target_tile.y))
            if target_tile.type == TileType.BORDER or tile_clan == cat.clan_id:
                return True # It's a border tile or the cat's own territory
            return False # It's enemy territory

        def border_patrol_stop_cond(current_pos: Tuple[int, int]) -> bool:
            # Rule: A patrol move stops if it finds a paw print from another clan.
            tile = self.board.get_tile(current_pos)
            if tile and tile.paw_print and tile.paw_print != cat.clan_id:
                logging.info(f"  -> {cat.name} found an enemy scent marker from {tile.paw_print.value} at {current_pos}. Halting patrol.")
                return True
            return False
        # ------------------------------------

        # 1. Ask the Board to calculate the physical movement
        final_pos, path_tiles = self.board.trace_path(
            cat.position,
            direction,
            steps,
            is_valid_border_patrol_step,
            border_patrol_stop_cond
        )

        # 2. Update the Cat's state
        cat.move(final_pos)

        # 3. Process interactions along the path (leave paw prints)
        for tile in path_tiles:
            # Rule: A cat on patrol only leaves a scent marker on special "highlighted" tiles.
            if tile.is_highlighted:
                tile.paw_print = cat.clan_id
                logging.debug(f"  -> {cat.name} left a scent marker on a highlighted tile at ({tile.x}, {tile.y}).")

        # 4. No clan resources are updated directly from this move.

        return final_pos, path_tiles
