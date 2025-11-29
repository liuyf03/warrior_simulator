import logging
import os
from game_engine import GameEngine
from game_config import GameConfig
from visualize_board import get_board_string

def run_full_game_simulation():
    """
    Initializes and runs a full game simulation from start to finish,
    logging all events to a file for later examination.
    """
    # --- 1. Configure Logging ---
    log_filename = 'game_simulation.log'
    # Start with a fresh log file for each simulation run
    if os.path.exists(log_filename):
        os.remove(log_filename)

    # Set up logging to output to both the console and a file.
    # The file will contain the detailed turn-by-turn record.
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',  # Using a simple format for clean log readability
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()  # This will also print logs to the console
        ]
    )

    logging.info("--- Initializing New Game Simulation ---")

    # --- 2. Initialize and Set Up the Game ---
    game = GameEngine()
    game.setup_game()

    # --- Log the Initial Board State ---
    board_visualization = get_board_string(game.board)
    logging.info("\n--- Initial Board Layout ---")
    logging.info(board_visualization)

    # --- 3. Main Game Loop ---
    # The loop will run for the maximum number of turns defined in your config.
    # The play_full_turn() method handles all the logic for one turn for all clans.
    while not game._check_game_over():
        game.play_full_turn()

    logging.info(f"\n--- Simulation Complete ---")
    logging.info(f"The detailed game log has been saved to: {log_filename}")

if __name__ == '__main__':
    run_full_game_simulation()