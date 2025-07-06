def exp_required_for(level: int) -> int:
    """Calculates the experience required for a given level."""
    return 100 + (level - 1) * 50

async def check_and_apply_level_up(character):
    """Checks if the character has enough experience to level up and applies the level up."""
    leveled_up = False
    while character.exp >= character.exp_to_next:
        character.exp -= character.exp_to_next
        character.level += 1
        character.exp_to_next = exp_required_for(character.level)
        character.stat_points += 5
        leveled_up = True
    return leveled_up
