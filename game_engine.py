import logging
from typing import Tuple, Dict

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
