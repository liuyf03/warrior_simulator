import logging
import random

from enums import StarClanCard, ClanName
from cat import Cat

class StarClanEventResolver:
    """
    Handles the logic for resolving the effects of StarClan cards when drawn.
    """
    def __init__(self, game_engine):
        """
        Initializes the resolver.
        Args:
            game_engine: A reference to the main GameEngine instance.
        """
        self.engine = game_engine
        
        # Maps each effect type to its corresponding handler method
        self._effect_map = {
            StarClanCard.A_BLESSING_OF_NEW_LEAF: self._resolve_a_blessing_of_new_leaf,
            StarClanCard.THE_BOUNTIFUL_SEASON: self._resolve_the_bountiful_season,
            StarClanCard.WARRIOR_CODE_UPHELD: self._resolve_warrior_code_upheld,
            StarClanCard.BORDER_WASHOUT: self._resolve_border_washout,
            StarClanCard.WHISPERS_OF_BATTLE: self._resolve_whispers_of_battle,
            StarClanCard.A_SWIFT_PAW: self._resolve_a_swift_paw,
            StarClanCard.THE_SICKNESS_SPREADS: self._resolve_the_sickness_spreads,
            StarClanCard.THE_BADGER_SET: self._resolve_the_badger_set,
            StarClanCard.A_TRUE_WARRIORS_HEART: self._resolve_a_true_warriors_heart,
            StarClanCard.PROPHECY_OF_UNITY: self._resolve_prophecy_of_unity,
            StarClanCard.THE_MOONSTONE_VISION: self._resolve_the_moonstone_vision,
            StarClanCard.ROGUE_INTRUDER: self._resolve_rogue_intruder,
            StarClanCard.LEADERSHIP_TRIAL: self._resolve_leadership_trial,
            StarClanCard.HUNTERS_LUCK: self._resolve_hunters_luck,
            StarClanCard.RISING_SPIRIT: self._resolve_rising_spirit,
            StarClanCard.SUDDEN_ILLNESS: self._resolve_sudden_illness,
            StarClanCard.RAVENS_PLUNDER: self._resolve_ravens_plunder,
            StarClanCard.UNEXPECTED_ENCOUNTER: self._resolve_unexpected_encounter,
        }

    def resolve(self, card: StarClanCard, trigger_cat: Cat):
        """
        The main entry point called by the GameEngine. It finds the correct
        handler for the card's effect and executes it.
        """
        logging.info(f"\n*** StarClan Speaks! A cat has drawn a card. ***")
        logging.info(f"    Card: {card}")

        handler = self._effect_map.get(card)
        if handler:
            # Pass the card data and the context (the cat who triggered it)
            handler(card, trigger_cat)
        else:
            logging.warning(f"[Warning] No handler defined for effect: {card}")

    # --- Specific Effect Implementations ---

    def _resolve_a_blessing_of_new_leaf(self, card: StarClanCard, cat: Cat):
        """
        Heals one cat.
        """
        clan = self.engine.clans[cat.clan_id]
        
        # Find a wounded cat to heal, prioritizing others if the trigger cat is healthy
        wounded_cats = [c for c in clan.cats if c.is_wounded]
        if not wounded_cats:
            logging.info(f"  -> StarClan card {card} healing light shines, but everyone is healthy.")
            return

        # If the triggering cat is wounded, they are the target. Otherwise, pick a random wounded cat.
        target_cat = cat if cat.is_wounded else random.choice(wounded_cats)
        
        logging.info(f"  -> StarClan card {card} healed {target_cat.name} miraculously!")
        target_cat.heal(clan.camp_entrance)

    def _resolve_the_bountiful_season(self, card: StarClanCard, cat: Cat):
        """
        Adds 2 extra preys in the Hunting Ground.
        """
        clan = self.engine.clans[cat.clan_id]
        logging.info(f"  -> StarClan card {card}, adding 2 new prey in {clan.name}'s territory.")
        self.engine.execute_prey_replenish(clan, count=2)

    def _resolve_warrior_code_upheld(self, card: StarClanCard, cat: Cat):
        """
        Promotes one Warrior to Deputy if there is no current Deputy.
        """
        clan = self.engine.clans[cat.clan_id]

        promoted_deputy = clan.promote_warrior_to_deputy()
        if promoted_deputy:
            logging.info(f"  -> StarClan card {card}, {promoted_deputy.name} has been promoted to a Deputy!")
        else:
            logging.info(f"  -> StarClan card {card} sees great potential, but clan already has a Deputy.")

    def _resolve_border_washout(self, card: StarClanCard, cat: Cat):
        """
        Remove one paw print on the border tiles.
        """
        scent_marked_tiles = [
            tile for _, tile in self.engine.board.grid.items()
            if tile.paw_print and tile.paw_print == cat.clan_id
        ]
        if scent_marked_tiles:
            washed_tile = random.choice(scent_marked_tiles)
            washed_tile.paw_print = None
            logging.info(f"  -> StarClan card {card}, one paw print removed.")
            return
        logging.info(f"  -> StarClan card {card}, but no paw print to be removed.")

    def _resolve_whispers_of_battle(self, card: StarClanCard, cat: Cat):
        """
        Triggers two simultaneous battles: ThunderClan vs. WindClan and
        RiverClan vs. ShadowClan.
        """
        logging.info(f"  -> StarClan card {card} fills the air with whispers of battle!")

        # Battle 1: ThunderClan vs. WindClan
        thunder_clan = self.engine.clans.get(ClanName.THUNDERCLAN)
        wind_clan = self.engine.clans.get(ClanName.WINDCLAN)
        self.engine._trigger_clan_combat(thunder_clan, wind_clan)

        # Battle 2: RiverClan vs. ShadowClan
        river_clan = self.engine.clans.get(ClanName.RIVERCLAN)
        shadow_clan = self.engine.clans.get(ClanName.SHADOWCLAN)
        self.engine._trigger_clan_combat(river_clan, shadow_clan)

    def _resolve_a_swift_paw(self, card: StarClanCard, cat: Cat):
        """
        Allows the cate to move 3 extra spaces this turn.
        """
        pass

    def _resolve_the_sickness_spreads(self, card: StarClanCard, cat: Cat):
        """ Sustain an injury on the cat that triggered the card. """
        # The cat that stepped on the landmark is the one to be injured
        logging.info(f"  -> StarClan card {card}, misfortune falls upon {cat.name}!")
        cat.sustain_injury(self.engine.turn_count)

    def _resolve_the_badger_set(self, card: StarClanCard, cat: Cat):
        """ Removes 2 preys from the clans's fresh-kill pile. """
        clan = self.engine.clans[cat.clan_id]
        clan.prey_pile = max(0, clan.prey_pile - 2)
        logging.info(f"  -> StarClan card {card} causes misfortune! 2 preys removed from {clan.name}'s fresh-kill pile.")

    def _resolve_a_true_warriors_heart(self, card: StarClanCard, cat: Cat):
        """
        Promotes one Apprentice to Warrior, but put them in the Medicine Den (wounded).
        """
        clan = self.engine.clans[cat.clan_id]

        promoted_warrior = clan.promote_apprentice()
        if promoted_warrior:
            promoted_warrior.sustain_injury(self.engine.turn_count)
            logging.info(f"  -> StarClan card {card}, {promoted_warrior.name} has been promoted to a Warrior!")
        else:
            logging.info(f"  -> StarClan card {card} sees great potential, but no apprentices are eligible for promotion.")

    def _resolve_prophecy_of_unity(self, card: StarClanCard, cat: Cat):
        """ All warriors can take one apprentice on their hunting / patrol mission for their next turn.
        """
        pass

    def _resolve_the_moonstone_vision(self, card: StarClanCard, cat: Cat):
        """ Look at the top 3 cards of the StarClan Deck.
        Choose one to put at the bottom and the remaining two back on top.
        """
        pass

    def _resolve_rogue_intruder(self, card: StarClanCard, cat: Cat):
        """ A rogue steals one prey from the clan's hunting ground.
        """
        clan = self.engine.clans[cat.clan_id]

        # 1. Find all hunting ground slots for the clan that have prey
        prey_tiles = []
        for slot_pos in self.engine.board.spawn_points.get(clan.name, {}).values():
            tile = self.engine.board.get_tile(slot_pos)
            if tile and tile.prey_count > 0:
                prey_tiles.append(tile)

        # 2. If prey is found, remove one
        if prey_tiles:
            chosen_tile = random.choice(prey_tiles)
            chosen_tile.prey_count -= 1
            logging.info(f"  -> StarClan card {card} signals misfortune! A rogue stole a prey from ({chosen_tile.x}, {chosen_tile.y}).")
        else:
            logging.info(f"  -> StarClan card {card} was drawn, but no prey could be found in the hunting grounds.")

    def _resolve_leadership_trial(self, card: StarClanCard, cat: Cat):
        """ The Leader must choose between:
        1) Lose a Prey from the Fresh-Kill Pile, OR
        2) Pick a Warrior to skip their next turn.
        """
        pass

    def _resolve_hunters_luck(self, card: StarClanCard, cat: Cat):
        """
        Finds a random prey on one of the clan's hunting slots and moves it
        directly to the fresh-kill pile.
        """
        clan = self.engine.clans[cat.clan_id]

        # 1. Find all hunting ground slots for the clan that have prey
        prey_tiles = []
        for slot_pos in self.engine.board.spawn_points.get(clan.name, {}).values():
            tile = self.engine.board.get_tile(slot_pos)
            if tile and tile.prey_count > 0:
                prey_tiles.append(tile)

        # 2. If prey is found, move one to the pile
        if prey_tiles:
            chosen_tile = random.choice(prey_tiles)
            chosen_tile.prey_count -= 1
            clan.add_prey(1)
            logging.info(f"  -> StarClan card {card} guided a cat's paws! A prey from ({chosen_tile.x}, {chosen_tile.y}) was moved to the fresh-kill pile.")
        else:
            logging.info(f"  -> StarClan card {card} was drawn, but no prey could be found in the hunting grounds.")

    def _resolve_rising_spirit(self, card: StarClanCard, cat: Cat):
        """ Promotes one Apprentice to Warrior.
        """
        clan = self.engine.clans[cat.clan_id]

        promoted_warrior = clan.promote_apprentice()
        if promoted_warrior:
            logging.info(f"  -> StarClan card {card}, {promoted_warrior.name} has been promoted to a Warrior!")
        else:
            logging.info(f"  -> StarClan card {card} sees great potential, but no apprentices are eligible for promotion.")

    def _resolve_sudden_illness(self, card: StarClanCard, cat: Cat):
        """ Inflicts an injury on one random Apprentice in the clan."""
        clan = self.engine.clans[cat.clan_id]

        healthy_apprentices = clan.get_apprentices()
        if not healthy_apprentices:       
            logging.info(f"  -> StarClan card {card} misfortune strikes, but no healthy apprentices are available to be injured.")
            return

        injured_apprentice = random.choice(healthy_apprentices)
        logging.info(f"  -> StarClan card {card}, misfortune falls upon {injured_apprentice.name}!")
        injured_apprentice.sustain_injury(self.engine.turn_count)   

    def _resolve_ravens_plunder(self, card: StarClanCard, cat: Cat):
        """ A raven steals one prey from the clan's fresh-kill pile.
        """
        clan = self.engine.clans[cat.clan_id]
        if clan.prey_pile > 0:
            clan.prey_pile -= 1
            logging.info(f"  -> StarClan card {card} causes misfortune! A raven stole a prey from {clan.name}'s fresh-kill pile.")
        else:
            logging.info(f"  -> StarClan card {card} was drawn, but no prey could be found in the fresh-kill pile.")

    def _resolve_unexpected_encounter(self, card: StarClanCard, cat: Cat):
        """ Pick a Clan to immediately start a Clan Fight. """
        my_clan = self.engine.clans[cat.clan_id]
        enemy_clans = [c for c in self.engine.clans.values() if c.name != cat.clan_id]
        
        if not enemy_clans:
            logging.info(f"  -> StarClan card {card} prophecy of battle echoes, but there are no other clans to fight.")
            return

        enemy_clan = random.choice(enemy_clans)
        logging.info(f"  -> StarClan card {card}, an ominous prophecy sparks immediate conflict between {my_clan.name} and {enemy_clan.name}!")
        self.engine._trigger_clan_combat(my_clan, enemy_clan)
