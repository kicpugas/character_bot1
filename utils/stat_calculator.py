import json
from typing import Dict, Tuple, Optional, Union
import logging

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

STAT_NAMES = {
    "hp": "Здоровье",
    "attack": "Атака", 
    "defense": "Защита",
    "magic": "Магия",
    "agility": "Ловкость",
    "mana": "Мана",
    "luck": "Удача"
}

# Global variable for items data with lazy loading
_ITEMS_DATA: Optional[Dict] = None

def _load_items_data() -> Dict:
    """Lazy loading of items data with error handling."""
    global _ITEMS_DATA
    if _ITEMS_DATA is None:
        try:
            with open('data/items.json', 'r', encoding='utf-8') as f:
                _ITEMS_DATA = json.load(f)
        except FileNotFoundError:
            logger.error("Items data file not found: data/items.json")
            _ITEMS_DATA = {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in items data: {e}")
            _ITEMS_DATA = {}
        except Exception as e:
            logger.error(f"Error loading items data: {e}")
            _ITEMS_DATA = {}
    return _ITEMS_DATA

def get_item_bonuses(item_id: Union[str, None]) -> Dict[str, int]:
    """
    Extracts stat bonuses from a given item ID.
    
    Args:
        item_id: Item identifier (can be None)
    
    Returns:
        Dictionary of stat bonuses, empty dict if item not found
    """
    if not item_id:
        return {}
    
    items_data = _load_items_data()
    item = items_data.get(str(item_id))
    
    if not item:
        logger.warning(f"Item not found: {item_id}")
        return {}
    
    if not isinstance(item, dict):
        logger.warning(f"Item data is not a dictionary: {item_id}")
        return {}
    
    stats = item.get("stats", {})
    if not isinstance(stats, dict):
        logger.warning(f"Item stats is not a dictionary: {item_id}")
        return {}
    
    # Validate and convert stat values to integers
    validated_stats = {}
    for stat, value in stats.items():
        try:
            validated_stats[str(stat)] = int(value)
        except (ValueError, TypeError):
            logger.warning(f"Invalid stat value for {item_id}.{stat}: {value}")
            continue
    
    return validated_stats

def calculate_total_stats(base_stats: Dict[str, int], equipment: Dict[str, str]) -> Tuple[Dict[str, int], Dict[str, int]]:
    """
    Calculates total character stats including equipment bonuses.
    
    Args:
        base_stats: Base character stats
        equipment: Equipment mapping (slot -> item_id)
    
    Returns:
        Tuple of (total_stats, total_bonuses)
    """
    if not isinstance(base_stats, dict):
        raise TypeError("base_stats must be a dictionary")
    
    if not isinstance(equipment, dict):
        raise TypeError("equipment must be a dictionary")
    
    # Create copies to avoid modifying original data
    total_stats = {}
    for stat, value in base_stats.items():
        try:
            total_stats[str(stat)] = int(value)
        except (ValueError, TypeError):
            logger.warning(f"Invalid base stat value for {stat}: {value}")
            total_stats[str(stat)] = 0
    
    total_bonuses = {stat: 0 for stat in STAT_NAMES.keys()}
    
    for slot, item_id in equipment.items():
        if not item_id:  # Skip empty slots
            continue
            
        bonuses = get_item_bonuses(item_id)
        for stat, value in bonuses.items():
            stat_key = str(stat)
            bonus_value = int(value)
            
            # Add to total stats
            total_stats[stat_key] = total_stats.get(stat_key, 0) + bonus_value
            
            # Track bonuses for known stats
            if stat_key in total_bonuses:
                total_bonuses[stat_key] += bonus_value
    
    return total_stats, total_bonuses

def get_stat_display_name(stat_key: str) -> str:
    """
    Returns the display name for a given stat key.
    
    Args:
        stat_key: Stat identifier
    
    Returns:
        Display name for the stat
    """
    if not isinstance(stat_key, str):
        return str(stat_key).capitalize()
    
    return STAT_NAMES.get(stat_key.lower(), stat_key.capitalize())

def apply_race_class_modifiers(base_stats: Dict[str, int], race_modifiers: Dict[str, int], class_modifiers: Dict[str, int]) -> Dict[str, int]:
    """
    Applies race and class modifiers to base stats.
    
    Args:
        base_stats: Base character stats
        race_modifiers: Race-based stat modifiers
        class_modifiers: Class-based stat modifiers
    
    Returns:
        Modified stats dictionary
    """
    if not isinstance(base_stats, dict):
        raise TypeError("base_stats must be a dictionary")
    
    if not isinstance(race_modifiers, dict):
        raise TypeError("race_modifiers must be a dictionary")
    
    if not isinstance(class_modifiers, dict):
        raise TypeError("class_modifiers must be a dictionary")
    
    # Create copy to avoid modifying original
    modified_stats = {}
    for stat, value in base_stats.items():
        try:
            modified_stats[str(stat)] = int(value)
        except (ValueError, TypeError):
            logger.warning(f"Invalid base stat value for {stat}: {value}")
            modified_stats[str(stat)] = 0
    
    # Apply race modifiers
    for stat, value in race_modifiers.items():
        try:
            stat_key = str(stat)
            modifier_value = int(value)
            modified_stats[stat_key] = modified_stats.get(stat_key, 0) + modifier_value
        except (ValueError, TypeError):
            logger.warning(f"Invalid race modifier value for {stat}: {value}")
            continue
    
    # Apply class modifiers
    for stat, value in class_modifiers.items():
        try:
            stat_key = str(stat)
            modifier_value = int(value)
            modified_stats[stat_key] = modified_stats.get(stat_key, 0) + modifier_value
        except (ValueError, TypeError):
            logger.warning(f"Invalid class modifier value for {stat}: {value}")
            continue
    
    return modified_stats

def validate_stats_data(stats: Dict[str, int]) -> Dict[str, int]:
    """
    Validates and cleans stats data.
    
    Args:
        stats: Stats dictionary to validate
    
    Returns:
        Validated stats dictionary
    """
    if not isinstance(stats, dict):
        raise TypeError("stats must be a dictionary")
    
    validated = {}
    for stat, value in stats.items():
        try:
            validated[str(stat)] = int(value)
        except (ValueError, TypeError):
            logger.warning(f"Invalid stat value for {stat}: {value}")
            validated[str(stat)] = 0
    
    return validated

def get_character_summary(base_stats: Dict[str, int], equipment: Dict[str, str], race_modifiers: Dict[str, int] = None, class_modifiers: Dict[str, int] = None) -> Dict[str, any]:
    """
    Gets complete character stats summary.
    
    Args:
        base_stats: Base character stats
        equipment: Equipment mapping
        race_modifiers: Optional race modifiers
        class_modifiers: Optional class modifiers
    
    Returns:
        Complete character stats summary
    """
    try:
        # Apply race/class modifiers if provided
        if race_modifiers or class_modifiers:
            race_mods = race_modifiers or {}
            class_mods = class_modifiers or {}
            modified_base = apply_race_class_modifiers(base_stats, race_mods, class_mods)
        else:
            modified_base = validate_stats_data(base_stats)
        
        # Calculate equipment bonuses
        total_stats, equipment_bonuses = calculate_total_stats(modified_base, equipment)
        
        return {
            "base_stats": modified_base,
            "equipment_bonuses": equipment_bonuses,
            "total_stats": total_stats,
            "display_names": {stat: get_stat_display_name(stat) for stat in total_stats.keys()}
        }
    
    except Exception as e:
        logger.error(f"Error calculating character summary: {e}")
        return {
            "base_stats": {},
            "equipment_bonuses": {},
            "total_stats": {},
            "display_names": {},
            "error": str(e)
        }