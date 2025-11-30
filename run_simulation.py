import logging
import os
import time
from game_engine import GameEngine
from visualize_board import get_board_string
from stats_collector import StatsCollector

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

    # --- 2. Initialize Game Engine ---
    game = GameEngine()

    # --- Log the Initial Board State ---
    board_visualization = get_board_string(game.board)
    logging.info("\n--- Initial Board Layout ---")
    logging.info(board_visualization)

    # --- 3. Main Game Loop ---
    # We can now use the run_simulation method from the engine
    game.run_simulation()

    logging.info(f"\n--- Simulation Complete ---")
    logging.info(f"The detailed game log has been saved to: {log_filename}")

def run_mass_simulation(num_simulations: int = 1000):
    """
    Runs a large number of game simulations and collects aggregated statistics.
    This mode is optimized for speed and suppresses detailed turn-by-turn logs.
    """
    # --- 1. Configure Logging for Mass Simulation ---
    log_filename = 'mass_simulation_results.log'
    if os.path.exists(log_filename):
        os.remove(log_filename)

    # Set the root logger level to WARNING to hide detailed game engine logs.
    # We will use a separate, specific logger for our high-level progress updates.
    logging.basicConfig(
        level=logging.WARNING,
        format='%(message)s',
        handlers=[logging.FileHandler(log_filename), logging.StreamHandler()]
    )

    # This logger is specifically for printing progress and the final summary.
    summary_logger = logging.getLogger('summary_logger')
    summary_logger.setLevel(logging.INFO)
    summary_logger.propagate = False # Prevent messages from being handled by the root logger
    for handler in logging.getLogger().handlers:
        summary_logger.addHandler(handler)

    summary_logger.info(f"--- Starting Mass Simulation of {num_simulations} Games ---")
    start_time = time.time()

    # --- 2. Initialize Statistics Collector & Game Engine ---
    stats = StatsCollector()
    game = GameEngine()

    # --- 3. Run Simulations in a Loop ---
    for i in range(num_simulations):
        if (i + 1) % 100 == 0:
            summary_logger.info(f"  ... running simulation {i + 1}/{num_simulations}")
        
    
        # Pass the stats collector to the engine for this run
        game.run_simulation(stats=stats)

    # --- 4. Log Final Aggregated Results ---
    summary_logger.info(stats.get_summary())
    summary_logger.info(f"\nMass simulation complete. Total time: {time.time() - start_time:.2f} seconds.")
    summary_logger.info(f"Aggregated results have been saved to: {log_filename}")

if __name__ == '__main__':
    # --- CHOOSE WHICH SIMULATION TO RUN ---
    RUN_MASS_SIMULATION = False

    if RUN_MASS_SIMULATION:
        run_mass_simulation(num_simulations=1000)
    else:
        run_full_game_simulation()