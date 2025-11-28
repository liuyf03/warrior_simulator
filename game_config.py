"""
This module holds global configuration parameters for the game simulation.
"""
from enums import ClanName, Rank

class GameConfig:
    """
    A static class to hold global game configuration parameters.
    """
    HUNTING_GROUND_SIZE: int = 6  # The size of the square hunting grounds
    BORDER_WIDTH: int = 3         # The width of the central border area
    COMBAT_CARD_COPIES: int = 15  # The number of copies of each combat card
    NUM_INITIAL_WARRIORS_PER_CLAN: int = 2
    NUM_INITIAL_APPRENTICES_PER_CLAN: int = 2
    NUM_CATS_PER_CLAN: int = (
        NUM_INITIAL_WARRIORS_PER_CLAN + NUM_INITIAL_APPRENTICES_PER_CLAN + 1
      )   # +1 for leader
    MAX_PATROL_REROLLS: int = 3  # Max retries for a patrol to find a good move
    MAX_NUM_GAME_TURNS: int = 20 # Max number of turns before game ends
    NUM_ACTIVITY_CARDS_IN_DECK: int = 40  # Total activity cards in the deck
    ACTIVITY_SLOTS_PER_CARD: int = 4      # Number of activity slots on

    # Point values for winning a fight based on rank
    SCORE_MAP = {
        Rank.LEADER: 5,
        Rank.DEPUTY: 4,
        Rank.WARRIOR: 3,
        Rank.APPRENTICE: 1
    }

    @staticmethod
    def border_half_width() -> int:
        """Calculates half the width of the central border area."""
        return (GameConfig.BORDER_WIDTH - 1) // 2

    @staticmethod
    def border_extent() -> int:
        """Calculates the extent of the border strips."""
        return GameConfig.border_half_width() + GameConfig.BORDER_WIDTH + GameConfig.HUNTING_GROUND_SIZE

    @staticmethod
    def get_clan_camps() -> dict:
        """
        Calculates the coordinates for each clan's camp entrance based on N and M.
        These are typically the corner-most tiles of each territory.
        """
        offset = (GameConfig.BORDER_WIDTH + 1) // 2
        n = GameConfig.HUNTING_GROUND_SIZE

        # Calculate the corner coordinates
        tc_x = -offset - n + 1
        tc_y = offset + n - 1
        rc_x = offset + n - 1

        return {
            ClanName.THUNDERCLAN: (tc_x, tc_y),      # Top-Left
            ClanName.RIVERCLAN: (rc_x, tc_y),       # Top-Right
            ClanName.SHADOWCLAN: (tc_x, -tc_y),     # Bottom-Left
            ClanName.WINDCLAN: (rc_x, -tc_y)      # Bottom-Right
        }
