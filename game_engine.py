import logging
import random
from typing import Tuple, Dict, List, Optional
from itertools import cycle

from activity_card import generate_balanced_activity_deck
from board import Board
from cat import Cat
from clan import Clan
from combat_system import CombatSystem
from deck import Deck
from game_mechanics import Dice, Spinner
from game_config import GameConfig
from enums import Direction, TileType, ClanName, CombatMove, Rank, Season, Activity, StarClanCard
from stats_collector import StatsCollector, Metric
from tile import Tile
from starclan_event_resolver import StarClanEventResolver

class GameEngine:
    """
    The main orchestrator for the game simulation. It holds the game state
    and executes game logic and actions.
    """
    def __init__(self):
        """
        Initializes the GameEngine.
        Args:
            seed: An optional integer to seed the random number generator for reproducible board layouts.
        """
        # Build the board, dice and spinner
        self.board = Board()
        self.spinner = Spinner()
        self.dice = Dice(sides=6) # A standard 6-sided die for general purpose rolls

        # Initialize Clans and their Cats
        self.clans: Dict[ClanName, Clan] = {}
        self._initialize_clans()

        # Initialize StarClan Event Resolver
        self.starclan_resolver = StarClanEventResolver(self)

        # Create the Decks
        self.combat_deck = self._initialize_combat_deck()
        self.activity_deck = self._initialize_activity_deck()
        self.starclan_deck = self._initialize_starclan_deck()
        logging.info(f"GameEngine initialized.")

        # Define other game state variables
        self.turn_count: int = None
        self._season_cycle: cycle = None
        self.current_season: Season = None
        # Collect game metrics for analysis
        self.stats: Optional[StatsCollector] = None
        
    def setup_game(self):
        # --- SESSION STATE (Run Every New Game) ---
        
        # 1. Reset Global Counters
        self.turn_count = 1 # Start at turn 1
        self._season_cycle = cycle(Season) # Reset iterator
        self.current_season = next(self._season_cycle)
        
        # 2. Reset Board State
        self.board.clear_prey() # Remove leftovers from previous game
        self.board.clear_paw_prints()
        
        # 3. Reset Agents (Clans and Cats)
        for clan in self.clans.values():
            clan.reset_clan_state()
                
        # 4. Shuffle Decks
        self.activity_deck.reshuffle()
        self.combat_deck.reshuffle()
        self.starclan_deck.reshuffle()
        
        # 5. Initial Spawns
        self._populate_initial_prey()
        
        logging.info(f"New game started. It is {self.current_season.value} of turn {self.turn_count}.")

    def run_simulation(self, stats: Optional[StatsCollector] = None):
        """
        Runs a full game from setup to completion, optionally collecting statistics.
        """
        # 1. ATTACH: The collector becomes a member of the engine
        self.stats = stats
        
        self.setup_game()
        
        while not self._check_game_over():
            self.play_full_turn()

        # 2. DETACH: Remove reference to stats collector
        self.stats = None

    # --- Turn Management ---
    def play_full_turn(self):
        """
        Executes a full turn of the game, iterating through each clan's actions
        and then advancing the season.
        """
        if self._check_game_over():
            return

        # Execute each clan's turn in order
        for clan_name in list(ClanName):
            clan = self.clans[clan_name]
            self._execute_clan_turn(clan)

        # Advance to the next turn/season
        self._advance_turn()

    def _advance_turn(self):
        """
        Advances the game to the next turn, rotating the season.
        """
        self.turn_count += 1
        self.current_season = next(self._season_cycle)
        logging.info(f"--- Advancing to Turn {self.turn_count} ({self.current_season.value}) ---")

    def _check_game_over(self) -> bool:
        """
        Checks if the game over conditions are met.
        Currently, the game ends when self.turn_count exceeds .
        """
        if self.turn_count > GameConfig.MAX_NUM_GAME_TURNS:
            logging.info("Game Over: Maximum number of turns reached.")
            self._record_winner()
            return True
        
        return False
    
    def _record_winner(self):
        """
        Records the winner of the game.
        """
        # --- Announce Final Scores and Winner ---
        logging.info("\n--- FINAL GAME RESULTS ---")
        # 1. Get scores from all clans and log them
        clan_scores = []
        for clan in self.clans.values():
            clan_scores.append((clan.name, clan.prey_pile))
            logging.info(f"  {clan.name}: {clan.prey_pile} prey")

        # 2. Sort clans by prey pile in descending order
        clan_scores.sort(key=lambda x: x[1], reverse=True)

        # 3. Determine the winner(s)
        if not clan_scores:
            logging.info("\nNo clans to determine a winner.")
            return None

        _, winner_score = clan_scores[0]
        winners = [name for name, score in clan_scores if score == winner_score]

        # 4. Record statistics about the result
        if self.stats:
            for winner_name in winners:
                self.stats.aggregate_count(Metric.RESULT, f"num_{winner_name.value}_wins")
            if len(winners) > 1:
                self.stats.aggregate_count(Metric.RESULT, "num_draws")
            self.stats.aggregate_average(Metric.RESULT, "avg_winner_score", winner_score)
            spread = clan_scores[0][1] - clan_scores[-1][1]
            self.stats.aggregate_average(Metric.RESULT, "avg_winner_spread", spread)
            advantage = clan_scores[0][1] - clan_scores[1][1]
            self.stats.aggregate_average(Metric.RESULT, "avg_winner_advantage", advantage)
            num_deputy = sum(1 for clan in self.clans.values() if clan.has_deputy())
            num_warriors = sum(len(clan.get_warriors()) for clan in self.clans.values())
            num_apprentices = sum(len(clan.get_apprentices()) for clan in self.clans.values())
            self.stats.aggregate_average(Metric.RESULT, "avg_num_deputies_endgame", num_deputy)
            self.stats.aggregate_average(Metric.RESULT, "avg_num_warriors_endgame", num_warriors)
            self.stats.aggregate_average(Metric.RESULT, "avg_num_apprentices_endgame", num_apprentices)

        logging.info("\n--- WINNER ANNOUNCEMENT ---")
        if len(winners) > 1:
            winner_names_str = " and ".join([w.value for w in winners])
            logging.info(f"The game ends in a draw between {winner_names_str} with {winner_score} prey!")            
        else:
            logging.info(f"{winners[0].value} wins the game with {winner_score} prey!")

    def _execute_clan_turn(self, clan: Clan):
        """
        Executes the logic for a single clan's turn, from drawing an
        activity card to dispatching actions.
        """
        logging.info(f"\n--- {clan.name}'s Turn ---")

        # 0. Heal any cats that have recovered
        clan.heal_cats(self.turn_count)

        # 1. Draw Activity Card
        card = self.activity_deck.draw()
        logging.info(f"  Drawn Activity Card with actions: {[a.value for a in card.actions]}")

        # 2. Assign available warriors to actions
        active_warriors = clan.get_active_warriors()
        num_actions = len(active_warriors)
        logging.info(f"  {clan.name} has {num_actions} active warriors available for duties.")
        if self.stats:
            num_warriors = len(clan.get_warriors())
            self.stats.aggregate_average(Metric.INJURY, f"avg_injury_skipped_turn_{self.turn_count}", num_warriors - num_actions)
            self.stats.aggregate_average(Metric.PROMOTION, f"avg_num_deputy_at_turn_{self.turn_count}", 1 if clan.has_deputy() else 0)
            self.stats.aggregate_average(Metric.PROMOTION, f"avg_num_warriors_at_turn_{self.turn_count}", num_warriors)

        # 3. Execute Actions based on Warrior Count
        actions_to_perform = card.actions[:num_actions]
        for i, action_type in enumerate(actions_to_perform):
            # TODO: Implement AI to intelligently assign action to cats based on position
            cat_for_action = active_warriors[i]
            self._dispatch_action(cat_for_action, clan, action_type)

        # 4. Discard Card
        self.activity_deck.discard(card)

        # 5. Leader's Prey Replenish Check
        if self.current_season in [Season.NEW_LEAF, Season.GREEN_LEAF]:
            logging.info(f"  {self.current_season.value} Bonus: Leader replenishes prey.")
            self.execute_prey_replenish(clan, count=1)
            if self.stats:
                self.stats.aggregate_count(Metric.HUNT, f"num_seasonal_prey_replenish_for_{clan.name.value}")

    def _dispatch_action(self, cat: Cat, clan: Clan, action_type: Activity):
        """Helper to map an Activity enum to an actual method call for a specific cat."""
        logging.info(f"  Dispatching {cat} to perform: {action_type.value}")
        if action_type == Activity.HUNT:
            self.execute_hunt(cat)
        elif action_type == Activity.PATROL:
            self.execute_border_patrol(cat)
        elif action_type == Activity.TRAIN_HUNT:
            # The warrior performs the action
            self.execute_hunt(cat)
            # Get the list of apprentices for training actions
            clan_apprentices = clan.get_apprentices()
            if clan_apprentices:
                # TODO: AI could pick best apprentice
                apprentice_to_train = clan_apprentices[0]
                logging.info(f"  -> {cat} is taking {apprentice_to_train} for hunting training.")
                self.execute_hunt(apprentice_to_train)
                # Reward: Collect Badge
                apprentice_to_train.collect_training_badge()
                if self.stats:
                    self.stats.aggregate_count(Metric.HUNT, f"num_training_at_turn_{self.turn_count}")
            else:
                logging.info(f"  -> No available apprentices for {cat} to train for hunt.")
        elif action_type == Activity.TRAIN_PATROL:
            # The warrior performs the action first
            combat_triggered = self.execute_border_patrol(cat)
            # Get the list of apprentices for training actions
            clan_apprentices = clan.get_apprentices()
            # The apprentice only goes if the warrior's patrol was uneventful
            if not combat_triggered and clan_apprentices:
                apprentice_to_train = clan_apprentices[0]
                logging.info(f"  -> {cat} is taking {apprentice_to_train} for patrol training.")
                self.execute_border_patrol(apprentice_to_train)
                # Reward: Collect Badge
                apprentice_to_train.collect_training_badge()
                if self.stats:
                    self.stats.aggregate_count(Metric.PATROL, f"num_training_at_turn_{self.turn_count}")
            elif combat_triggered:
                logging.info(f"  -> {cat} encountered conflict and could not train an apprentice.")
            else:
                logging.info(f"  -> No available apprentices for {cat} to train for border patrol.")

        else:
            logging.warning(f"  [Warning] Unknown or unimplemented action type: {action_type}")

    # --- Initialization Methods ---

    def _initialize_combat_deck(self) -> Deck:
        """Creates and shuffles the main combat card deck."""
        logging.info("Initializing combat deck...")
        card_copies = GameConfig.COMBAT_CARD_COPIES
        all_cards = []
        for move in CombatMove:
            all_cards.extend([move] * card_copies)
        return Deck(all_cards)

    def _initialize_activity_deck(self) -> Deck:
        """Creates and shuffles the activity card deck."""
        logging.info("Initializing activity deck...")
        activity_cards = generate_balanced_activity_deck()
        return Deck(activity_cards)
    
    def _initialize_starclan_deck(self) -> Deck:
        """Creates and shuffles the StarClan event card deck."""
        logging.info("Initializing StarClan deck...")
        all_cards = list(StarClanCard)
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
 
            # Store the populated clan in the engine
            self.clans[clan_name] = new_clan

    # --- Game Actions & Mechanics ---

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
            logging.info(f"{cat} is in the medicine den and cannot hunt.")
            return
        
        # Mark last active turn
        cat.record_last_acted_turn(self.turn_count)

        # 1. Spin for a random direction
        direction = self.spinner.spin()

        # 2. Roll the dice for the number of steps
        steps = self.dice.roll()

        # 3. Call the underlying move execution method
        final_pos, _ = self.execute_hunt_move(cat, direction, steps)

        # 4. Check for StarClan event at the destination
        final_tile = self.board.get_tile(final_pos)
        if final_tile and final_tile.is_starclan_landmark:
            self._trigger_starclan_event(cat)


    def execute_hunt_move(self, cat: Cat, direction: Direction, steps: int) -> Tuple[Tuple[int, int], int]:
        """
        Moves a cat according to Hunting rules and processes the outcome.
        """
        logging.info(f"{cat} is hunting {direction.name} for {steps} steps from {cat.position}.")

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
        prey_slot_ids = []
        for tile in path_tiles:
            if tile.prey_count > 0:
                logging.info(f"  -> {cat} caught prey at ({tile.x}, {tile.y})!")
                prey_caught += tile.prey_count
                prey_slot_ids.append(tile.slot_id)
                tile.reset_prey() # Remove prey from the board
        
        # 4. Update the Clan's resources (uncomment when clans are managed by engine)
        if prey_caught > 0 and cat.clan_id in self.clans:
            self.clans[cat.clan_id].add_prey(prey_caught)

        # Check for StarClan landmark on the final tile
        final_tile = self.board.get_tile(final_pos)
        if final_tile and final_tile.is_starclan_landmark:
            self._trigger_starclan_event(cat)


        # 5. Record statistics
        if self.stats:
            self.stats.aggregate_average(Metric.HUNT, f"avg_steps_moved_for_{cat.clan_id.value}", len(path_tiles))
            self.stats.aggregate_average(Metric.HUNT, "avg_prey_caught_rate", 1 if prey_caught > 0 else 0)
            self.stats.aggregate_average(Metric.HUNT, "avg_prey_caught_per_hunt", prey_caught)
            self.stats.aggregate_count(Metric.HUNT, f"num_prey_caught_for_clan_{cat.clan_id.value}")
            self.stats.aggregate_count(Metric.HUNT, f"num_prey_caught_for_turn_{self.turn_count}")
            for slot_id in prey_slot_ids:
                self.stats.aggregate_count(Metric.HUNT, f"num_prey_caught_at_slot_{slot_id}")
        
        return final_pos, prey_caught

    def execute_border_patrol(self, cat: Cat) -> bool:
        """
        Spins, rolls, and executes a patrol move with intelligent re-rolls.
        If a cat is in its territory, it will try to move towards the border.
        Returns True if combat was triggered, False otherwise.
        """
        if not cat.position:
            logging.info(f"{cat} is in the medicine den and cannot patrol.")
            return False
        
        # Mark last active turn
        cat.record_last_acted_turn(self.turn_count)

        # --- Determine the move (direction and steps) ---
        chosen_direction: Direction | None = None
        chosen_steps: int | None = None

        initial_dist_to_border = self.board.get_distance_to_border(cat.position)

        # Case 1: Cat is already on the border, any move is fine.
        if initial_dist_to_border == 0:
            logging.info(f"{cat} is on the border, choosing a random patrol route.")
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
                if self.board.get_tile(next_step_pos) and self.board.get_distance_to_border(next_step_pos) <= initial_dist_to_border:
                    logging.info(f"{cat} chose a good patrol route towards the border after {i+1} tries.")
                    chosen_direction = direction
                    chosen_steps = steps
                    break # Found a good move, exit the retry loop

                logging.info(f"Patrol reroll {i+1}/{max_retries}: Move {direction.name} was not towards the border.")

        if self.stats:
            self.stats.aggregate_average(Metric.PATROL, "avg_insider_border_rate", 1 if initial_dist_to_border == 0 else 0)
            self.stats.aggregate_average(Metric.PATROL, "avg_turn_give_up_rate", 1 if chosen_direction is None or chosen_steps is None else 0)

        # --- Execute the chosen move ---
        combat_triggered = False
        if chosen_direction and chosen_steps:
            final_pos, _, combat_triggered = self.execute_border_patrol_move(cat, chosen_direction, chosen_steps)

            # Check for StarClan event only if combat did NOT occur
            final_tile = self.board.get_tile(final_pos)
            if not combat_triggered and final_tile and final_tile.is_starclan_landmark:
                self._trigger_starclan_event(cat)

        else:
            logging.info(f"{cat} could not find a good patrol route after {GameConfig.MAX_PATROL_REROLLS} tries and gives up the turn.")
        
        return combat_triggered

    def execute_border_patrol_move(self, cat: Cat, direction: Direction, steps: int) -> Tuple[Tuple[int, int], List[Tile], bool]:
        """
        Moves a cat according to Border Patrol rules and processes the outcome.
        Returns the final position, the path taken, and whether combat was triggered.
        """
        logging.info(f"{cat} is patrolling {direction.name} for {steps} steps from {cat.position}.")

        combat_triggered = False
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
                logging.info(f"  -> {cat} found an enemy scent marker from {tile.paw_print.value} at {current_pos}. Halting patrol.")
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

        # 3. Post-Move Event Check
        # Check if the patrol stopped because it found an enemy scent to trigger combat
        final_tile = self.board.get_tile(final_pos)
        if final_tile and final_tile.paw_print and final_tile.paw_print != cat.clan_id:
            # A fight is triggered!
            aggressor_clan = self.clans[cat.clan_id]
            defender_clan = self.clans[final_tile.paw_print]
            self._trigger_clan_combat(aggressor_clan, defender_clan)
            combat_triggered = True
            # Reset the paw print after combat
            final_tile.reset_paw_print()

         # 4. Process interactions along the path (leave paw prints)
        scent_marks_left = 0
        for tile in path_tiles:
            # Rule: A cat on patrol only leaves a scent marker on special "highlighted" tiles.
            if tile.is_highlighted:
                tile.paw_print = cat.clan_id
                scent_marks_left += 1
                logging.info(f"  -> {cat} left a scent marker on a highlighted tile at ({tile.x}, {tile.y}).")

        # Check for StarClan landmark on the final tile (if combat wasn't already triggered)
        final_tile = self.board.get_tile(final_pos)
        if not combat_triggered and final_tile and final_tile.is_starclan_landmark:
            self._trigger_starclan_event(cat)


        # 5. Record statistics
        if self.stats:
            self.stats.aggregate_average(Metric.PATROL, "avg_scent_marks_left", scent_marks_left)
            self.stats.aggregate_average(Metric.PATROL, "avg_combat_trigger_rate", 1 if combat_triggered else 0)
            if combat_triggered:
                self.stats.aggregate_count(Metric.PATROL, "num_combat_triggered")
                self.stats.aggregate_average(Metric.PATROL, "avg_turn_when_combat_triggered", self.turn_count)
            self.stats.aggregate_average(Metric.PATROL, f"avg_steps_moved_for_{cat.clan_id.value}", len(path_tiles))

        return final_pos, path_tiles, combat_triggered

    def _trigger_starclan_event(self, cat: Cat):
        """Draws a StarClan card and resolves its effect."""
        # Draw the card
        card = self.starclan_deck.draw()
        # Call the resolver
        self.starclan_resolver.resolve(card, cat)
        if self.stats:
            self.stats.aggregate_count(Metric.STARCLAN, f"num_starclan_events_triggered_for_{cat.clan_id.value}")
            self.stats.aggregate_count(Metric.STARCLAN, f"num_starclan_event_{card}_triggered")

    def _trigger_clan_combat(self, clan_a: Clan, clan_b: Clan):
        """
        Orchestrates a 5v5 combat between two clans.
        """
        logging.info(f"--- COMBAT! {clan_a.name} vs. {clan_b.name} ---")

        # 1. Assemble the fighting cats from each clan
        cats_a, ranks_a = clan_a.get_combat_squad()
        cats_b, ranks_b = clan_b.get_combat_squad()
        
        max_rounds = 3
        combat_results_in_tie = True
        for i in range(max_rounds):
            # 2. Draw combat cards for each clan
            cards_a = [self.combat_deck.draw() if cat else None for cat in cats_a]
            cards_b = [self.combat_deck.draw() if cat else None for cat in cats_b]

            logging.info(f"Round {i+1} draws for {clan_a.name}: {[c.value if c else 'N/A' for c in cards_a]}")
            logging.info(f"Round {i+1} draws for {clan_b.name}: {[c.value if c else 'N/A' for c in cards_b]}")

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
            
            combat_results_in_tie = False
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

        # Record status
        if self.stats:
            self.stats.aggregate_count(Metric.COMBAT, f"num_{clan_a.name.value}_vs_{clan_b.name.value}")
            self.stats.aggregate_count(Metric.COMBAT, "num_skirmishes_drawn" if combat_results_in_tie else "num_skirmishes_decided")
            if not combat_results_in_tie:
                self.stats.aggregate_count(Metric.COMBAT, f"num_{clan_a.name.value}_skirmish_wins" if score_a > score_b else f"num_{clan_b.name.value}_skirmish_wins")
                

    def _mark_wounded_cats(self, cats_a: List[Cat | None], cats_b: List[Cat | None], slot_results: List[int]):
        """
        Marks cats as wounded based on the combat slot results.
        """
        for i, result in enumerate(slot_results):
            if result == 0:
                continue # No injuries in this slot
            losing_cat = cats_b[i] if result == 1 else cats_a[i]
            if not losing_cat:
                continue
            losing_cat.sustain_injury(self.turn_count)
            logging.info(f"  -> {losing_cat} from {losing_cat.clan_id.value} was wounded in battle.")
            if self.stats:
                self.stats.aggregate_count(Metric.INJURY, f"num_injury_in_combat_{losing_cat.clan_id.value}")

    def _reward_winning_clan(self, winning_clan: Clan):
        """
        Grants rewards to the winning clan.
        """
        logging.info(f"Resolving combat: {winning_clan.name} is victorious.")

        # Reward 1: Try to promote an Apprentice
        promoted_apprentice = winning_clan.promote_apprentice()
        if promoted_apprentice:
            if self.stats:
                self.stats.aggregate_count(Metric.PROMOTION, f"num_clan_{winning_clan.name.value}_to_{Rank.WARRIOR.value}_in_combat")
            logging.info(f"  As a reward for victory, {promoted_apprentice} has been promoted to a Warrior!")
            return

        # Reward 2: If no apprentice was promoted, try to promote a Warrior to Deputy
        promoted_warrior = winning_clan.promote_warrior_to_deputy()
        if promoted_warrior:
            if self.stats:
                self.stats.aggregate_count(Metric.PROMOTION, f"num_clan_{winning_clan.name.value}_to_{Rank.DEPUTY.value}_in_combat")
            logging.info(f"  As a reward for victory, {promoted_warrior} has been promoted to Deputy!")
            return

        # Reward 3: If no promotions are possible, replenish prey
        logging.info(f"  As a reward for victory, the prey has been replenished in {winning_clan.name}'s territory.")
        self.execute_prey_replenish(winning_clan, count=1)
        if self.stats:
            self.stats.aggregate_count(Metric.HUNT, f"num_clan_{winning_clan.name.value}_prey_replenish_in_combat")
