"""
This module holds global configuration parameters for the game simulation.
"""
from enums import ClanName, Rank

class GameConfig:
    """
    A static class to hold global game configuration parameters.
    """
    N: int = 6  # Size parameter for hunting grounds
    M: int = 3  # Width parameter for border areas

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
        return (GameConfig.M - 1) // 2

    @staticmethod
    def border_extent() -> int:
        """Calculates the extent of the border strips."""
        # (M-1)/2 + M + N
        return GameConfig.border_half_width() + GameConfig.M + GameConfig.N

    @staticmethod
    def get_clan_camps() -> dict:
        """
        Calculates the coordinates for each clan's camp entrance based on N and M.
        These are typically the corner-most tiles of each territory.
        """
        offset = (GameConfig.M + 1) // 2
        n = GameConfig.N

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
