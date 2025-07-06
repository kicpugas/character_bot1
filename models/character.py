from dataclasses import dataclass, field

@dataclass
class Character:
    user_id: int
    name: str
    age: int
    race: str
    character_class: str
    photo_id: str | None = None
    level: int = 1
    exp: int = 0
    exp_to_next: int = 100
    stat_points: int = 0
    gold: int = 0
    current_mana: int = 50 # Added current_mana
    stats: dict = field(default_factory=lambda: {
        "hp": 100,
        "max_hp": 100, # Added max_hp
        "attack": 10,
        "defense": 10,
        "magic": 10,
        "agility": 10,
        "mana": 50,
        "max_mana": 50, # Added max_mana
        "luck": 0
    })
    inventory: list = field(default_factory=list)
    equipment: dict = field(default_factory=lambda: {})
    active_effects: list = field(default_factory=list)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "name": self.name,
            "age": self.age,
            "race": self.race,
            "character_class": self.character_class,
            "photo_id": self.photo_id,
            "level": self.level,
            "exp": self.exp,
            "exp_to_next": self.exp_to_next,
            "stat_points": self.stat_points,
            "gold": self.gold,
            "current_mana": self.current_mana, # Added current_mana
            "stats": self.stats,
            "inventory": self.inventory,
            "equipment": self.equipment,
            "active_effects": self.active_effects
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            user_id=data["user_id"],
            name=data["name"],
            age=data["age"],
            race=data["race"],
            character_class=data["character_class"],
            photo_id=data.get("photo_id"),
            level=data.get("level", 1),
            exp=data.get("exp", 0),
            exp_to_next=data.get("exp_to_next", 100),
            stat_points=data.get("stat_points", 0),
            gold=data.get("gold", 0),
            current_mana=data.get("current_mana", 50), # Added current_mana
            stats=(lambda s: (s.update({"max_hp": s["hp"]}) if "max_hp" not in s else None, s)[1])(data.get("stats", {
                "hp": 100,
                "max_hp": 100,
                "attack": 10,
                "defense": 10,
                "magic": 10,
                "agility": 10,
                "mana": 50,
                "max_mana": 50, # Added max_mana
                "luck": 0
            })),
            inventory=data.get("inventory", []),
            equipment=data.get("equipment", {}),
            active_effects=data.get("active_effects", [])
        )