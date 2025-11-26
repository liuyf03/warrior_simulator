"""
This module holds global configuration parameters for the game simulation.
"""

class GameConfig:
    """
    A static class to hold global game configuration parameters.
    """
    N: int = 6  # Size parameter for hunting grounds
    M: int = 3  # Width parameter for border areas

    @staticmethod
    def border_half_width() -> int:
        """Calculates half the width of the central border area."""
        return (GameConfig.M - 1) // 2

    @staticmethod
    def border_extent() -> int:
        """Calculates the extent of the border strips."""
        # (M-1)/2 + M + N
        return GameConfig.border_half_width() + GameConfig.M + GameConfig.N
