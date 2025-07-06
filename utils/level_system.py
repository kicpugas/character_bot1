def get_exp_for_level(level):
    """
    Calculates the experience required to reach a given level.
    This represents the *threshold* for the level up.
    """
    if level <= 1:
        return 100
    # This formula determines the XP needed to get FROM (level-1) TO level.
    return int(100 * ((level-1) ** 1.5) + 100)

def grant_exp(character):
    """
    Grants experience to a character and handles level ups.
    The amount of exp to grant should be added to character['exp'] before calling this.
    """
    leveled_up = False
    while character['exp'] >= character['exp_to_next']:
        leveled_up = True
        # Subtract the XP needed for the level up
        character['exp'] -= character['exp_to_next']
        # Increase level
        character['level'] += 1
        # Grant stat points
        character['stat_points'] += 5
        # Increase max_hp and heal character
        character['stats']['max_hp'] += 10
        character['stats']['hp'] = character['stats']['max_hp']
        # Set the XP requirement for the *new* next level
        character['exp_to_next'] = get_exp_for_level(character['level'] + 1)

    return character, leveled_up

def get_stat_points_for_level_up(level):
    """
    Returns the number of stat points a character gets for leveling up.
    """
    return 5 # Example: 5 stat points per level

def get_exp_for_next_level(level):
    """
    Calculates the experience required to reach the next level.
    """
    return get_exp_for_level(level + 1)