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

    def __str__(self):
        return self.value
