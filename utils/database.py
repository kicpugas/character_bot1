import json
import os
from pathlib import Path
from models.character import Character
from utils.stat_calculator import calculate_total_stats, apply_race_class_modifiers

# Define base path for data files
BASE_DATA_PATH = Path(__file__).parent.parent / 'data'

CHARACTER_DB_PATH = BASE_DATA_PATH / 'characters.json'

# Load races and classes data for stat calculation
with open(BASE_DATA_PATH / 'races.json', 'r', encoding='utf-8') as f:
    RACES_DATA = json.load(f)

with open(BASE_DATA_PATH / 'classes.json', 'r', encoding='utf-8') as f:
    CLASSES_DATA = json.load(f)

async def _load_all_characters():
    if not os.path.exists(CHARACTER_DB_PATH) or os.path.getsize(CHARACTER_DB_PATH) == 0:
        return {}
    with open(CHARACTER_DB_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return {int(user_id): Character.from_dict(char_data) for user_id, char_data in data.items()}

async def _save_all_characters(characters):
    with open(CHARACTER_DB_PATH, 'w', encoding='utf-8') as f:
        json.dump({user_id: char.to_dict() for user_id, char in characters.items()}, f, ensure_ascii=False, indent=4)

async def save_character(character: Character):
    all_characters = await _load_all_characters()
    all_characters[character.user_id] = character
    await _save_all_characters(all_characters)

async def get_character_data(user_id: int) -> Character | None:
    all_characters = await _load_all_characters()
    char = all_characters.get(user_id)
    if char:
        return char
    return None