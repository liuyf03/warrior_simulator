import logging
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

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
                if tile.is_starclan_landmark:
                    row_str += "S" # Mark StarClan landmarks
                elif tile.is_spawn_point:
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

def save_board_to_file(board: Board, filename: str = "printable_board.png"):
    """
    Generates a graphical representation of the game board using matplotlib
    and saves it to an image file, centered on a letter-sized page.
    """
    if not board.grid:
        print("Board is empty. Cannot generate visualization.")
        return

    # --- Define Colors and Symbols ---
    color_map = {
        TileType.BORDER: '#a9a9a9',  # Dark Gray
        TileType.THUNDER_TERRITORY: '#add8e6',  # Light Blue
        TileType.RIVER_TERRITORY: '#90ee90',  # Light Green
        TileType.SHADOW_TERRITORY: '#d3d3d3',  # Light Gray
        TileType.WIND_TERRITORY: '#f0e68c',  # Khaki
        TileType.OBSTACLE: '#2f4f4f',  # Dark Slate Gray
    }
    camp_coords = set(GameConfig.get_clan_camps().values())

    # --- Setup Matplotlib Figure ---
    # Create a figure for a US Letter page (8.5x11 inches)
    fig, ax = plt.subplots(figsize=(8.5, 11))
    ax.set_aspect('equal')
    ax.axis('off') # Hide the black axes box

    # --- Find Board Boundaries ---
    all_x = [pos[0] for pos in board.grid.keys()]
    all_y = [pos[1] for pos in board.grid.keys()]
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)

    # --- Draw Each Tile ---
    for pos, tile in board.grid.items():
        x, y = pos
        
        # Draw the base tile rectangle
        tile_color = color_map.get(tile.type, 'white')
        ax.add_patch(Rectangle((x - 0.5, y - 0.5), 1, 1, facecolor=tile_color, edgecolor='black', linewidth=0.2))

        # --- Add Markers for Special Tiles ---
        symbol = ''
        symbol_color = 'black'

        if pos in camp_coords:
            symbol = 'C'
            symbol_color = 'black'
        elif tile.is_starclan_landmark:
            symbol = 'S'
            symbol_color = '#4b0082' # Indigo
        elif tile.is_spawn_point:
            symbol = 'P'
            symbol_color = '#8b4513' # Saddle Brown
        
        if tile.is_highlighted:
            # Draw a thicker, yellow border for highlighted tiles
            ax.add_patch(Rectangle((x - 0.5, y - 0.5), 1, 1, facecolor='none', edgecolor='gold', linewidth=1.5))

        if symbol:
            ax.text(x, y, symbol, ha='center', va='center', fontsize=8, fontweight='bold', color=symbol_color)

        if tile.prey_count > 0:
            # Add a small dot for prey
            ax.plot(x, y, 'o', markersize=3, color='darkred')

    # --- Finalize and Save ---
    # Set plot limits to encompass the entire board with a small margin
    ax.set_xlim(min_x - 1.5, max_x + 1.5)
    ax.set_ylim(min_y - 1.5, max_y + 1.5)

    # Add a title to the plot
    fig.suptitle("Warrior Cats: Game Board Layout", fontsize=16)

    try:
        # Save the figure with high resolution for printing
        plt.savefig(filename, dpi=300, format='png', bbox_inches='tight', pad_inches=0.5)
        plt.close(fig) # Close the figure to free up memory
        print(f"\nGraphical board visualization successfully saved to '{filename}'.")
    except IOError as e:
        print(f"Error: Could not write to file '{filename}'. Reason: {e}")

if __name__ == "__main__":
    # Configure logging to suppress the "Board initialized" message during visualization
    logging.basicConfig(level=logging.WARNING)

    # Create a board instance
    game_board = Board()

    # Print the visual representation
    # print_board(game_board) # You can still use this for a quick console view

    # Save the visual representation to a file for printing
    save_board_to_file(game_board)
