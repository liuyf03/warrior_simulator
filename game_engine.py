import logging
import random
from typing import Tuple, Dict, List

from board import Board
from cat import Cat
from clan import Clan
from combat_system import CombatSystem
from deck import Deck
from game_mechanics import Dice, Spinner
from game_config import GameConfig
from enums import Direction, TileType, ClanName, CombatMove, Rank
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
        self.combat_deck = self._initialize_combat_deck()
        self.spinner = Spinner()
        self.dice = Dice(sides=6) # A standard 6-sided die for general purpose rolls
        self._initialize_clans()
        self._populate_initial_prey()

        logging.info("GameEngine initialized.")

    def _initialize_combat_deck(self) -> Deck:
        """Creates and shuffles the main combat card deck."""
        logging.info("Initializing combat deck...")
        card_copies = GameConfig.COMBAT_CARD_COPIES
        all_cards = []
        for move in CombatMove:
            all_cards.extend([move] * card_copies)
        return Deck(all_cards)

    def _populate_initial_prey(self):
        """Adds one prey to every spawn slot on the board."""
        logging.info("Populating board with initial prey...")
        for clan_name in self.clans:
            # The number of spawn slots is equal to the hunting ground size
            for i in range(GameConfig.HUNTING_GROUND_SIZE):
                self.board.spawn_prey(clan_name, slot_number=i + 1)

    def _initialize_clans(self):
        """Creates instances for each clan and stores them."""
        logging.info("Initializing all clans...")
        clan_camps = GameConfig.get_clan_camps()
        for clan_name, camp_pos in clan_camps.items():
            # Create the clan
            new_clan = Clan(name=clan_name, camp_entrance=camp_pos)

            # --- Create and add cats to the clan ---
            # 1. Leader (1 per clan)
            leader_name = f"{clan_name.value}star" # e.g., ThunderClanstar
            leader = Cat(name=leader_name, clan_id=clan_name, rank=Rank.LEADER, position=camp_pos)
            new_clan.add_cat(leader)

            # 2. Warriors
            for i in range(GameConfig.NUM_INITIAL_WARRIORS_PER_CLAN):
                new_clan.add_cat(Cat(name=f"Warrior {i+1}", clan_id=clan_name, rank=Rank.WARRIOR, position=camp_pos))

            # 3. Apprentices
            for i in range(GameConfig.NUM_INITIAL_APPRENTICES_PER_CLAN):
                new_clan.add_cat(Cat(name=f"Apprentice {i+1}", clan_id=clan_name, rank=Rank.APPRENTICE, position=camp_pos))

            # Store the populated clan in the engine
            self.clans[clan_name] = new_clan

    def execute_prey_replenish(self, clan: Clan, count: int = 1):
        """
        Adds a specified number of prey to random spawn slots in a clan's territory.
        """
        logging.info(f"Replenishing {count} prey in {clan.name.value}'s territory.")
        
        num_spawn_slots = GameConfig.HUNTING_GROUND_SIZE
        if num_spawn_slots == 0:
            logging.warning("No spawn slots available to replenish prey.")
            return

        for _ in range(count):
            # Roll a die to determine which prey slot to replenish.
            random_slot = self.dice.roll(sides=num_spawn_slots)
            self.board.spawn_prey(clan.name, random_slot)

    def execute_hunt(self, cat: Cat):
        """
        Spins for a direction, rolls for steps, and executes a hunt move.
        """
        if not cat.position:
            logging.warning(f"{cat.name} is in the medicine den and cannot hunt.")
            return

        # 1. Spin for a random direction
        direction = self.spinner.spin()

        # 2. Roll the dice for the number of steps
        steps = self.dice.roll()

        # 3. Call the underlying move execution method
        self.execute_hunt_move(cat, direction, steps)

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

    def execute_border_patrol(self, cat: Cat):
        """
        Spins, rolls, and executes a patrol move with intelligent re-rolls.
        If a cat is in its territory, it will try to move towards the border.
        """
        if not cat.position:
            logging.warning(f"{cat.name} is in the medicine den and cannot patrol.")
            return

        # --- Determine the move (direction and steps) ---
        chosen_direction: Direction | None = None
        chosen_steps: int | None = None

        initial_dist_to_border = self.board.get_distance_to_border(cat.position)

        # Case 1: Cat is already on the border, any move is fine.
        if initial_dist_to_border == 0:
            logging.info(f"{cat.name} is on the border, choosing a random patrol route.")
            chosen_direction = self.spinner.spin()
            chosen_steps = self.dice.roll()
        else:
            # Case 2: Cat is in territory, try to find a move that gets closer to the border.
            max_retries = GameConfig.MAX_PATROL_REROLLS
            for i in range(max_retries):
                direction = self.spinner.spin()
                steps = self.dice.roll()

                # Check the tile one step in the chosen direction
                dx, dy = direction.value
                next_step_pos = (cat.position[0] + dx, cat.position[1] + dy)
                
                # A "good" move is one that exists and doesn't increase the distance to the border.
                if self.board.get_tile(next_step_pos) and self.board.get_distance_to_border(next_step_pos) < initial_dist_to_border:
                    logging.info(f"{cat.name} chose a good patrol route towards the border after {i+1} tries.")
                    chosen_direction = direction
                    chosen_steps = steps
                    break # Found a good move, exit the retry loop

                logging.debug(f"Patrol reroll {i+1}/{max_retries}: Move {direction.name} was not towards the border.")

        # --- Execute the chosen move ---
        if chosen_direction and chosen_steps:
            self.execute_border_patrol_move(cat, chosen_direction, chosen_steps)
        else:
            logging.info(f"{cat.name} could not find a good patrol route after {GameConfig.MAX_PATROL_REROLLS} tries and gives up the turn.")

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

        # 4. Post-Move Event Check
        # Check if the patrol stopped because it found an enemy scent
        final_tile = self.board.get_tile(final_pos)
        if final_tile and final_tile.paw_print and final_tile.paw_print != cat.clan_id:
            # A fight is triggered!
            aggressor_clan = self.clans[cat.clan_id]
            defender_clan = self.clans[final_tile.paw_print]
            self._trigger_clan_combat(aggressor_clan, defender_clan)

        return final_pos, path_tiles

    def _trigger_clan_combat(self, clan_a: Clan, clan_b: Clan):
        """
        Orchestrates a 5v5 combat between two clans.
        """
        logging.info(f"--- COMBAT! {clan_a.name} vs. {clan_b.name} ---")

        # 1. Assemble the fighting cats from each clan
        cats_a, ranks_a = clan_a.get_combat_squad()
        cats_b, ranks_b = clan_b.get_combat_squad()
        
        max_rounds = 3
        for i in range(max_rounds):
            # 2. Draw combat cards for each clan
            cards_a = [self.combat_deck.draw() if cat else None for cat in cats_a]
            cards_b = [self.combat_deck.draw() if cat else None for cat in cats_b]

            logging.debug(f"Round {i+1} draws for {clan_a.name}: {[c.value if c else 'N/A' for c in cards_a]}")
            logging.debug(f"Round {i+1} draws for {clan_b.name}: {[c.value if c else 'N/A' for c in cards_b]}")

            # 3. Use the CombatSystem to calculate the results
            score_a, score_b, slot_results = CombatSystem.calculate_fight_results(cards_a, cards_b, ranks_a, ranks_b)

            logging.info(f"Combat Round {i+1} Score: {clan_a.name} [{score_a}] - [{score_b}] {clan_b.name}")

            # 4. Discard all used cards
            all_used_cards = [card for card in cards_a + cards_b if card is not None]
            self.combat_deck.discard(all_used_cards)

            # 5. Determine winner or if a re-fight is needed
            if score_a == score_b:
                # This round is a draw
                if i < max_rounds - 1:
                    logging.info("The round is a draw! Another round of fighting begins...")
                else:
                    logging.info("The skirmish ends in a final draw after 3 rounds!")
                continue # Proceed to next round or end
            
            # Resolve winning cat rewards
            if score_a > score_b:
                logging.info(f"{clan_a.name} wins the skirmish!")
                self._reward_winning_clan(clan_a)
            else:
                logging.info(f"{clan_b.name} wins the skirmish!")
                self._reward_winning_clan(clan_b)

            # Mark wounded cats based on slot results
            self._mark_wounded_cats(cats_a, cats_b, slot_results)
            break # A winner is found, exit the loop
                

    def _mark_wounded_cats(self, cats_a: List[Cat | None], cats_b: List[Cat | None], slot_results: List[int]):
        """
        Marks cats as wounded based on the combat slot results.
        """
        for i, result in enumerate(slot_results):
            if result == 1: # Clan A's cat won the bout
                losing_cat = cats_b[i]
                if losing_cat:
                    losing_cat.sustain_injury()
                    logging.info(f"  -> {losing_cat.name} from Clan B was wounded in battle.")
            elif result == -1: # Clan B's cat won the bout
                losing_cat = cats_a[i]
                if losing_cat:
                    losing_cat.sustain_injury()
                    logging.info(f"  -> {losing_cat.name} from Clan A was wounded in battle.")
            else: # It was a tie or both were wounded
                continue


    def _reward_winning_clan(self, winning_clan: Clan):
        """
        Grants rewards to the winning clan.
        """
        logging.info(f"Resolving combat: {winning_clan.name} is victorious.")

        # Reward 1: Promote an Apprentice if possible
        apprentices = [cat for cat in winning_clan.cats if cat.rank == Rank.APPRENTICE]
        if apprentices:
            apprentice_to_promote = apprentices[0]
            apprentice_to_promote.promote()
            logging.info(f"  As a reward for victory, {apprentice_to_promote.name} has been promoted to a Warrior!")
            return

        # Reward 2: If no apprentices, promote a Warrior to Deputy if needed
        if not winning_clan.has_deputy():
            warriors = [cat for cat in winning_clan.cats if cat.rank == Rank.WARRIOR]
            if warriors:
                warrior_to_promote = warriors[0]
                warrior_to_promote.promote()
                logging.info(f"  As a reward for victory, {warrior_to_promote.name} has been promoted to Deputy!")
                return

        # Reward 3: If no promotions are possible, replenish prey
        logging.info(f"  As a reward for victory, the prey has been replenished in {winning_clan.name}'s territory.")
        self.execute_prey_replenish(winning_clan, count=1)
