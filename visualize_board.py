import logging
from board import Board
from enums import TileType
from game_config import GameConfig

def get_board_string(board: Board) -> str:
    """
    Generates a 2D text-based representation of the game board as a string.
    """
    if not board.grid:
        return "Board is empty."

    # Get the coordinates of all clan camps for marking
    camp_coords = set(GameConfig.get_clan_camps().values())

    # 1. Define a character mapping for each tile type
    tile_char_map = {
        TileType.BORDER: "+",
        TileType.THUNDER_TERRITORY: "T",
        TileType.RIVER_TERRITORY: "R",
        TileType.SHADOW_TERRITORY: "S",
        TileType.WIND_TERRITORY: "W",
        TileType.OBSTACLE: "X",
    }

    # 2. Find the boundaries of the grid to iterate over
    all_x = [pos[0] for pos in board.grid.keys()]
    all_y = [pos[1] for pos in board.grid.keys()]
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)

    output_lines = []
    output_lines.append(f"Board Visualization (from ({min_x},{max_y}) to ({max_x},{min_y}))")
    output_lines.append("-" * (max_x - min_x + 3))

    # 3. Iterate from top to bottom (max_y to min_y)
    for y in range(max_y, min_y - 1, -1):
        row_str = ""
        # Iterate from left to right (min_x to max_x)
        for x in range(min_x, max_x + 1):
            pos = (x, y)
            tile = board.get_tile(pos)

            if pos in camp_coords:
                # Prioritize marking camp entrances
                row_str += "C"
            elif tile:
                if tile.is_spawn_point:
                    row_str += "P" # Mark Prey spawn points
                elif tile.is_highlighted:
                    row_str += "*" # Mark highlighted border tiles
                else:
                    row_str += tile_char_map.get(tile.type, "?") # Otherwise, show tile type
            else:
                # If no tile exists at this coordinate, it's a void space
                row_str += " "
        output_lines.append(f"|{row_str}|")

    output_lines.append("-" * (max_x - min_x + 3))
    return "\n".join(output_lines)

def print_board(board: Board):
    """
    Prints a 2D text-based representation of the game board to the console.
    """
    print(get_board_string(board))

if __name__ == "__main__":
    # Configure logging to suppress the "Board initialized" message during visualization
    logging.basicConfig(level=logging.WARNING)

    # Create a board instance
    game_board = Board()

    # Print the visual representation
    print_board(game_board)
