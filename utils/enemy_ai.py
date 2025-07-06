import random
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ActionType(Enum):
    ATTACK = "attack"
    USE_ABILITY = "use_ability"
    DEFEND = "defend"
    FLEE = "flee"
    WAIT = "wait"

class EnemyAI:
    def __init__(self, enemy_data: dict, combat_data: dict):
        self.enemy_data = self._validate_enemy_data(enemy_data)
        self.combat_data = self._validate_combat_data(combat_data)
        self.ability_cooldowns = {}
        self.turn_count = 0
        
    def _validate_enemy_data(self, data: dict) -> dict:
        """Validate and sanitize enemy data."""
        if not isinstance(data, dict):
            raise TypeError("enemy_data must be a dictionary")
        
        required_fields = ['hp', 'attack']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        return data
    
    def _validate_combat_data(self, data: dict) -> dict:
        """Validate and sanitize combat data."""
        if not isinstance(data, dict):
            raise TypeError("combat_data must be a dictionary")
        
        required_fields = ['enemy_hp', 'player_hp']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        return data

    def get_hp_percent(self) -> float:
        """Calculate enemy's current HP percentage."""
        max_hp = self.enemy_data.get('hp', 1)
        current_hp = self.combat_data.get('enemy_hp', 0)
        return max(0.0, min(1.0, current_hp / max_hp))

    def get_player_hp_percent(self) -> float:
        """Calculate player's current HP percentage."""
        max_hp = self.combat_data.get('player_max_hp', self.combat_data.get('player_hp', 1))
        current_hp = self.combat_data.get('player_hp', 0)
        return max(0.0, min(1.0, current_hp / max_hp))

    def _is_ability_available(self, ability_name: str, ability_data: dict) -> bool:
        """Check if an ability can be used (cooldown, resources, etc.)."""
        # Check cooldown
        if ability_name in self.ability_cooldowns:
            if self.ability_cooldowns[ability_name] > 0:
                return False
        
        # Check mana cost
        mana_cost = ability_data.get('mana_cost', 0)
        if mana_cost > 0:
            current_mana = self.combat_data.get('enemy_mana', 0)
            if current_mana < mana_cost:
                return False
        
        # Check usage limit
        max_uses = ability_data.get('max_uses')
        if max_uses is not None:
            uses_key = f"{ability_name}_uses"
            current_uses = self.combat_data.get(uses_key, 0)
            if current_uses >= max_uses:
                return False
        
        return True

    def _evaluate_ability_priority(self, ability_name: str, ability_data: dict) -> float:
        """Calculate priority score for an ability."""
        priority = 0.0
        hp_percent = self.get_hp_percent()
        player_hp_percent = self.get_player_hp_percent()
        
        # Base priority
        priority += ability_data.get('base_priority', 1.0)
        
        # HP threshold modifiers
        hp_threshold = ability_data.get('hp_threshold', 0.0)
        if hp_percent <= hp_threshold:
            priority += ability_data.get('threshold_bonus', 2.0)
        
        # Situational modifiers
        if ability_data.get('type') == 'heal' and hp_percent < 0.5:
            priority += 3.0
        elif ability_data.get('type') == 'offensive' and player_hp_percent < 0.3:
            priority += 2.0
        elif ability_data.get('type') == 'defensive' and hp_percent < 0.3:
            priority += 2.5
        
        # Turn-based modifiers
        if ability_data.get('prefer_early') and self.turn_count < 3:
            priority += 1.5
        elif ability_data.get('prefer_late') and self.turn_count > 5:
            priority += 1.5
        
        return priority

    def _get_available_abilities(self) -> List[Tuple[str, dict, float]]:
        """Get list of available abilities with their priority scores."""
        abilities = []
        
        if 'abilities' not in self.enemy_data:
            return abilities
        
        for ability_name, ability_data in self.enemy_data['abilities'].items():
            if not isinstance(ability_data, dict):
                continue
                
            # Check availability
            if not self._is_ability_available(ability_name, ability_data):
                continue
            
            # Check chance
            chance = ability_data.get('chance', 1.0)
            if random.random() > chance:
                continue
            
            # Calculate priority
            priority = self._evaluate_ability_priority(ability_name, ability_data)
            abilities.append((ability_name, ability_data, priority))
        
        return abilities

    def _should_flee(self) -> bool:
        """Determine if enemy should attempt to flee."""
        if not self.enemy_data.get('can_flee', False):
            return False
        
        hp_percent = self.get_hp_percent()
        flee_threshold = self.enemy_data.get('flee_threshold', 0.1)
        
        if hp_percent <= flee_threshold:
            flee_chance = self.enemy_data.get('flee_chance', 0.3)
            return random.random() < flee_chance
        
        return False

    def _should_defend(self) -> bool:
        """Determine if enemy should defend."""
        if not self.enemy_data.get('can_defend', True):
            return False
        
        hp_percent = self.get_hp_percent()
        defend_threshold = self.enemy_data.get('defend_threshold', 0.2)
        
        if hp_percent <= defend_threshold:
            defend_chance = self.enemy_data.get('defend_chance', 0.4)
            return random.random() < defend_chance
        
        return False

    def _get_attack_strategy(self) -> dict:
        """Determine attack strategy and target."""
        strategy = {"action": ActionType.ATTACK.value}
        
        # Attack power variance
        base_attack = self.enemy_data.get('attack', 10)
        variance = self.enemy_data.get('attack_variance', 0.1)
        min_attack = int(base_attack * (1 - variance))
        max_attack = int(base_attack * (1 + variance))
        strategy['damage'] = random.randint(min_attack, max_attack)
        
        # Critical hit chance
        crit_chance = self.enemy_data.get('crit_chance', 0.05)
        if random.random() < crit_chance:
            strategy['critical'] = True
            strategy['damage'] = int(strategy['damage'] * 1.5)
        
        return strategy

    def get_action(self) -> dict:
        """Main method to determine enemy action."""
        try:
            self.turn_count += 1
            
            # Update cooldowns
            for ability in list(self.ability_cooldowns.keys()):
                self.ability_cooldowns[ability] -= 1
                if self.ability_cooldowns[ability] <= 0:
                    del self.ability_cooldowns[ability]
            
            # Check for flee
            if self._should_flee():
                return {"action": ActionType.FLEE.value}
            
            # Check for defend
            if self._should_defend():
                return {"action": ActionType.DEFEND.value}
            
            # Get available abilities
            available_abilities = self._get_available_abilities()
            
            # Use ability if available and prioritized
            if available_abilities:
                # Sort by priority (highest first)
                available_abilities.sort(key=lambda x: x[2], reverse=True)
                
                ability_name, ability_data, priority = available_abilities[0]
                
                # Set cooldown
                cooldown = ability_data.get('cooldown', 0)
                if cooldown > 0:
                    self.ability_cooldowns[ability_name] = cooldown
                
                # Track usage
                max_uses = ability_data.get('max_uses')
                if max_uses is not None:
                    uses_key = f"{ability_name}_uses"
                    current_uses = self.combat_data.get(uses_key, 0)
                    self.combat_data[uses_key] = current_uses + 1
                
                return {
                    "action": ActionType.USE_ABILITY.value,
                    "ability_name": ability_name,
                    "ability_data": ability_data
                }
            
            # Default to attack with strategy
            return self._get_attack_strategy()
            
        except Exception as e:
            logger.error(f"Error in enemy AI: {e}")
            return {"action": ActionType.ATTACK.value}

# Simplified function for backwards compatibility
def get_enemy_action(enemy_data: dict, combat_data: dict) -> dict:
    """
    Determines the enemy's action based on its state, abilities, and strategy.
    Enhanced version with better AI logic and error handling.
    """
    try:
        ai = EnemyAI(enemy_data, combat_data)
        return ai.get_action()
    except Exception as e:
        logger.error(f"Error in get_enemy_action: {e}")
        return {"action": "attack"}

# Example enemy data structure
"""EXAMPLE_ENEMY = {
    "hp": 100,
    "attack": 15,
    "can_flee": True,
    "flee_threshold": 0.15,
    "flee_chance": 0.3,
    "defend_threshold": 0.25,
    "defend_chance": 0.4,
    "crit_chance": 0.08,
    "attack_variance": 0.15,
    "abilities": {
        "fireball": {
            "type": "offensive",
            "chance": 0.3,
            "base_priority": 2.0,
            "mana_cost": 10,
            "cooldown": 3
        },
        "heal": {
            "type": "heal",
            "chance": 1.0,
            "hp_threshold": 0.4,
            "base_priority": 3.0,
            "mana_cost": 15,
            "max_uses": 2
        },
        "rage": {
            "type": "buff",
            "chance": 0.2,
            "prefer_early": True,
            "base_priority": 1.5,
            "cooldown": 5
        }
    }
}"""