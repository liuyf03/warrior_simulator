from enum import Enum, auto

class Rank(str, Enum):
    """Defines the possible ranks a cat can hold within a clan."""
    LEADER = "Leader"
    DEPUTY = "Deputy"
    WARRIOR = "Warrior"
    APPRENTICE = "Apprentice"

    def __str__(self):
        return self.value

class Season(str, Enum):
    """Defines the four seasons, known as Newleaf, Greenleaf, Leaf-fall, and Leaf-bare."""
    NEW_LEAF = "Newleaf"
    GREEN_LEAF = "Greenleaf"
    LEAF_FALL = "Leaf-fall"
    LEAF_BARE = "Leaf-bare"

    def __str__(self):
        return self.value

class Activity(str, Enum):
    """Defines the activities cats can be assigned to."""
    HUNT = "Hunting"
    PATROL = "Border Patrol"
    TRAIN_HUNT = "Training Hunting"
    TRAIN_PATROL = "Training Patrolling"

    def __str__(self):
        return self.value

class CardType(str, Enum):
    """Defines the types of event cards in the game."""
    CLAN_WAR = "Clan War"
    STAR_CLAN = "StarClan's Blessing"

    def __str__(self):
        return self.value

class StarClanCard(str, Enum):
    """Defines the names of the possible StarClan blessing/curse cards."""
    A_BLESSING_OF_NEW_LEAF = "A Blessing of New Leaf"
    THE_BOUNTIFUL_SEASON = "The Bountiful Season"
    WARRIOR_CODE_UPHELD = "Warrior Code Upheld"
    BORDER_WASHOUT = "Border Washout"
    WHISPERS_OF_BATTLE = "Whispers of Battle"
    A_SWIFT_PAW = "A Swift Paw"
    THE_SICKNESS_SPREADS = "The Sickness Spreads"
    THE_BADGER_SET = "The Badger Set"
    A_TRUE_WARRIORS_HEART = "A True Warrior's Heart"
    PROPHECY_OF_UNITY = "Prophecy of Unity"
    THE_MOONSTONE_VISION = "The Moonstone Vision"
    ROGUE_INTRUDER = "Rogue Intruder"
    LEADERSHIP_TRIAL = "Leadership Trial"
    HUNTERS_LUCK = "Hunter's Luck"
    RISING_SPIRIT = "Rising Spirit"
    SUDDEN_ILLNESS = "Sudden Illness"
    RAVENS_PLUNDER = "Raven's Plunder"
    UNEXPECTED_ENCOUNTER = "Unexpected Encounter"

    def __str__(self):
        return self.value

class ClanName(str, Enum):
    """Defines the names of the four major Clans."""
    THUNDERCLAN = "ThunderClan"
    RIVERCLAN = "RiverClan"
    WINDCLAN = "WindClan"
    SHADOWCLAN = "ShadowClan"

    def __str__(self):
        return self.value

class TileType(str, Enum):
    """Defines the type of terrain for a given tile."""
    BORDER = "Border"
    THUNDER_TERRITORY = "ThunderClan Territory"
    RIVER_TERRITORY = "RiverClan Territory"
    WIND_TERRITORY = "WindClan Territory"
    SHADOW_TERRITORY = "ShadowClan Territory"
    OBSTACLE = "Obstacle"


    def __str__(self):
        return self.value

class Direction(Enum):
    """
    Defines the eight directions of movement as coordinate tuples (x, y).
    """
    N = (0, 1)
    S = (0, -1)
    E = (1, 0)
    W = (-1, 0)
    NE = (1, 1)
    NW = (-1, 1)
    SE = (1, -1)
    SW = (-1, -1)

class CombatMove(str, Enum):
    """Defines the possible combat moves a cat can make."""
    CLAW_SCRATCH = "Claw scratch"
    BITE = "Bite"
    LEAP = "Leap"
    KICK = "Kick"

    def __str__(self):
        return self.value
