import json
import random

LOOT_TABLE_PATH = 'data/loot_table.json'

async def get_loot(luck: int, enemy_type: str) -> dict:
    """
    Generates loot based on the enemy type and player's luck, including gold, XP, and items.
    """
    with open(LOOT_TABLE_PATH, 'r', encoding='utf-8') as f:
        loot_table = json.load(f)

    loot_data = loot_table.get(enemy_type, {})
    if not loot_data:
        return {"gold": 0, "xp": 0, "items": []}

    # Get gold and XP
    gold_range = loot_data.get("gold_range", [0, 0])
    xp_range = loot_data.get("xp_range", [0, 0])
    gold = random.randint(gold_range[0], gold_range[1])
    xp = random.randint(xp_range[0], xp_range[1])

    # Get items
    dropped_items = []
    for item_info in loot_data.get("loot", []):
        base_chance = item_info.get("chance", 0)
        adjusted_chance = base_chance + (luck * 0.5)  # Luck increases drop chance
        if random.uniform(0, 100) < adjusted_chance:
            dropped_items.append({
                "item_id": item_info["item_id"],
                "name": item_info.get("name", "Unknown Item"),
                "rarity": item_info.get("rarity", "common")
            })

    return {"gold": gold, "xp": xp, "items": dropped_items}
