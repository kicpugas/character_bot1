import random

def is_critical_hit(luck: int) -> bool:
    """Checks if an attack is a critical hit."""
    crit_chance: float = 5 + (luck * 0.5)
    return random.uniform(0, 100) < crit_chance

def is_evaded(luck: int) -> bool:
    """Checks if an attack is evaded."""
    evade_chance: float = 2 + (luck * 0.1)
    return random.uniform(0, 100) < evade_chance

def calculate_damage(attack: int, defense: int, is_crit: bool = False, is_defending: bool = False) -> int:
    """Calculates damage dealt, considering critical hits and defense."""
    base_damage: int = max(1, attack - defense)
    damage: int = int(base_damage * 1.5) if is_crit else base_damage
    if is_defending:
        damage = int(damage * 0.5)
    return damage

def get_hp_bar(current_hp: int, max_hp: int, length: int = 10) -> str:
    """Creates a text-based HP bar."""
    fill: str = "█"
    empty: str = "░"
    percent: float = current_hp / max_hp
    filled_length: int = int(length * percent)
    bar: str = fill * filled_length + empty * (length - filled_length)
    return f"[{bar}]"