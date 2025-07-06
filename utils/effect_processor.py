import random

EFFECTS = {
    "poison": {"icon": "☠️", "duration": 3, "damage_percent": (0.05, 0.10), "type": "damage"},
    "burn": {"icon": "🔥", "duration": 3, "damage_percent": 0.10, "defense_debuff": 0.10, "type": "damage"},
    "freeze": {"icon": "❄️", "duration": 1, "skip_turn": True, "type": "control"},
    "stun": {"icon": "💫", "duration": 2, "skip_turn_chance": 0.5, "type": "control"},
    "regen": {"icon": "✨", "duration": 3, "heal_percent": (0.10, 0.20), "type": "heal"},
    "shield": {"icon": "🛡️", "duration": 2, "damage_reduction": 0.5, "type": "buff"},
    "curse": {"icon": "👁️", "duration": 3, "stat_debuff": 0.10, "type": "debuff"}
}

def apply_effect(target_effects: list, effect_name: str) -> None:
    """Applies an effect to a target's effects list."""
    if effect_name in EFFECTS:
        if not any(e['name'] == effect_name for e in target_effects):
            effect_data = EFFECTS[effect_name].copy()
            effect_data['name'] = effect_name
            effect_data['turns_left'] = effect_data['duration']
            target_effects.append(effect_data)

def process_effects(target_stats: dict, target_effects: list) -> dict:
    """Processes all active effects on a target and returns a summary of what happened."""
    summary = {"damage": 0, "heal": 0, "skip_turn": False, "defense_modifier": 1.0, "attack_modifier": 1.0, "messages": []}
    active_effects = []

    for effect in target_effects:
        effect_name = effect['name']
        
        if effect_name == "poison":
            damage = int(target_stats.get('max_hp', target_stats.get('hp')) * random.uniform(*effect['damage_percent']))
            summary["damage"] += damage
            summary["messages"].append(f"{effect['icon']} {effect_name.capitalize()}: -{damage} HP")
        
        elif effect_name == "burn":
            damage = int(target_stats.get('max_hp', target_stats.get('hp')) * effect['damage_percent'])
            summary["damage"] += damage
            summary["defense_modifier"] -= effect['defense_debuff']
            summary["messages"].append(f"{effect['icon']} {effect_name.capitalize()}: -{damage} HP, защита снижена")

        elif effect_name == "freeze" and effect.get('skip_turn'):
            summary["skip_turn"] = True
            summary["messages"].append(f"{effect['icon']} {effect_name.capitalize()}: пропуск хода")

        elif effect_name == "stun" and random.random() < effect['skip_turn_chance']:
            summary["skip_turn"] = True
            summary["messages"].append(f"{effect['icon']} {effect_name.capitalize()}: пропуск хода")

        elif effect_name == "regen":
            heal = int(target_stats.get('max_hp', target_stats.get('hp')) * random.uniform(*effect['heal_percent']))
            summary["heal"] += heal
            summary["messages"].append(f"{effect['icon']} {effect_name.capitalize()}: +{heal} HP")

        elif effect_name == "shield":
            summary["defense_modifier"] *= (1 - effect['damage_reduction'])

        elif effect_name == "curse":
            # This should be applied to all stats, which is complex here.
            # For now, we'll just reduce attack and defense as an example.
            summary["attack_modifier"] -= effect['stat_debuff']
            summary["defense_modifier"] -= effect['stat_debuff']
            summary["messages"].append(f"{effect['icon']} {effect_name.capitalize()}: характеристики снижены")

        effect['turns_left'] -= 1
        if effect['turns_left'] > 0:
            active_effects.append(effect)

    target_effects[:] = active_effects
    return summary

def get_effects_str(target_effects: list) -> str:
    """Returns a string representation of active effects for the combat message."""
    if not target_effects:
        return ""
    
    effects_list = [f"{e['icon']} {e['name'].capitalize()} ({e['turns_left']} х.)" for e in target_effects]
    return "\n📛 Эффекты: " + ", ".join(effects_list)