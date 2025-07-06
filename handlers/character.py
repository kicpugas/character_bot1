import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest

from models.character import Character
from keyboards.character_kb import (
    generate_race_selection_keyboard,
    generate_class_selection_keyboard,
    confirm_selection_keyboard,
    final_confirmation_keyboard
)
from utils.database import save_character, get_character_data
from utils.stat_calculator import calculate_total_stats, apply_race_class_modifiers
from utils.stat_names import STAT_NAMES

logger = logging.getLogger(__name__)
router = Router()

class CharacterCreation(StatesGroup):
    waiting_for_name = State()
    waiting_for_age = State()
    waiting_for_race_selection = State()
    waiting_for_race_confirmation = State()
    waiting_for_class_selection = State()
    waiting_for_class_confirmation = State()
    waiting_for_photo = State()
    confirm_creation = State()

# Load races and classes data with error handling
def load_json_data(filename: str) -> Dict[str, Any]:
    """Load JSON data with error handling."""
    try:
        # Get the project root directory (one level up from handlers/)
        project_root = Path(__file__).parent.parent
        file_path = project_root / 'data' / filename
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading {filename}: {e}")
        return {}

RACES_DATA = load_json_data('races.json')
CLASSES_DATA = load_json_data('classes.json')

# Constants
MIN_NAME_LENGTH = 2
MAX_NAME_LENGTH = 20
MIN_AGE = 10
MAX_AGE = 100
BASE_STATS = {
    "hp": 100,
    "attack": 10,
    "defense": 10,
    "magic": 10,
    "agility": 10,
    "mana": 10
}

async def safe_edit_message(callback: CallbackQuery, text: str, reply_markup=None):
    """Safely edit message with error handling."""
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as e:
        logger.warning(f"Failed to edit message: {e}")
        # If editing fails, send a new message
        await callback.message.answer(text, reply_markup=reply_markup)

@router.callback_query(F.data == "start_create_character")
async def request_character_name(callback: CallbackQuery, state: FSMContext):
    """Start character creation by requesting name."""
    await safe_edit_message(
        callback,
        "👋 Добро пожаловать, путник!\n\nКак зовут твоего персонажа?\n📝 Просто отправь его имя сообщением."
    )
    await state.set_state(CharacterCreation.waiting_for_name)
    await callback.answer()

@router.message(CharacterCreation.waiting_for_name)
async def process_character_name(message: Message, state: FSMContext):
    """Process character name input."""
    if not message.text:
        await message.answer("🚫 Пожалуйста, отправь текстовое сообщение с именем.")
        return
    
    name = message.text.strip()
    if not (MIN_NAME_LENGTH <= len(name) <= MAX_NAME_LENGTH):
        await message.answer(f"🚫 Имя должно быть от {MIN_NAME_LENGTH} до {MAX_NAME_LENGTH} символов. Попробуй снова.")
        return
    
    await state.update_data(name=name)
    await message.answer(f"Отлично, {name}! А сколько ему лет?\n📅 Введи число от {MIN_AGE} до {MAX_AGE}.")
    await state.set_state(CharacterCreation.waiting_for_age)

@router.message(CharacterCreation.waiting_for_age)
async def process_character_age(message: Message, state: FSMContext):
    """Process character age input."""
    if not message.text:
        await message.answer("🚫 Пожалуйста, отправь число.")
        return
    
    try:
        age = int(message.text.strip())
        if not (MIN_AGE <= age <= MAX_AGE):
            await message.answer(f"🚫 Возраст должен быть от {MIN_AGE} до {MAX_AGE} лет. Попробуй снова.")
            return
        
        await state.update_data(age=age)
        
        if not RACES_DATA:
            await message.answer("🚫 Ошибка загрузки данных рас. Попробуйте позже.")
            return
        
        await message.answer(
            "🧬 Выбери расу для своего персонажа.\nКаждая раса даёт уникальные бонусы, влияющие на характеристики!",
            reply_markup=generate_race_selection_keyboard(RACES_DATA)
        )
        await state.set_state(CharacterCreation.waiting_for_race_selection)
    except ValueError:
        await message.answer("🚫 Возраст должен быть числом. Попробуй снова.")

@router.callback_query(F.data.startswith("races_page_"), CharacterCreation.waiting_for_race_selection)
async def paginate_races(callback: CallbackQuery, state: FSMContext):
    """Handle race pagination."""
    try:
        page = int(callback.data.split('_')[2])
        await callback.message.edit_reply_markup(
            reply_markup=generate_race_selection_keyboard(RACES_DATA, current_page=page)
        )
    except (ValueError, IndexError, TelegramBadRequest) as e:
        logger.error(f"Error in race pagination: {e}")
    await callback.answer()

@router.callback_query(F.data.startswith("select_race_"), CharacterCreation.waiting_for_race_selection)
async def show_race_details(callback: CallbackQuery, state: FSMContext):
    """Show race details for confirmation."""
    try:
        race_id = callback.data.split('_')[2]
        race_info = RACES_DATA.get(race_id)
        
        if not race_info:
            await callback.answer("🚫 Раса не найдена.", show_alert=True)
            return
        
        modifiers_text = "\n".join([
            f"{'+' if mod > 0 else ''}{mod}% к {STAT_NAMES.get(stat, stat)}" 
            for stat, mod in race_info["modifiers"].items()
        ])
        
        await safe_edit_message(
            callback,
            f"🧬 Раса: {race_info['name']}\n\n🎯 Бонусы:\n{modifiers_text}\n\n📖 {race_info['description']}",
            reply_markup=confirm_selection_keyboard("расу", race_id, "рас")
        )
        await state.update_data(selected_race_id=race_id)
        await state.set_state(CharacterCreation.waiting_for_race_confirmation)
    except (IndexError, KeyError) as e:
        logger.error(f"Error showing race details: {e}")
        await callback.answer("🚫 Ошибка при загрузке данных расы.", show_alert=True)
    
    await callback.answer()

@router.callback_query(F.data == "back_to_races_list", CharacterCreation.waiting_for_race_confirmation)
async def back_to_races_list(callback: CallbackQuery, state: FSMContext):
    """Return to races list."""
    await safe_edit_message(
        callback,
        "🧬 Выбери расу для своего персонажа.\nКаждая раса даёт уникальные бонусы, влияющие на характеристики!",
        reply_markup=generate_race_selection_keyboard(RACES_DATA)
    )
    await state.set_state(CharacterCreation.waiting_for_race_selection)
    await callback.answer()

@router.callback_query(F.data.startswith("confirm_race_"), CharacterCreation.waiting_for_race_confirmation)
async def confirm_race(callback: CallbackQuery, state: FSMContext):
    """Confirm race selection and proceed to class selection."""
    try:
        race_id = callback.data.split('_')[2]
        
        if race_id not in RACES_DATA:
            await callback.answer("🚫 Неверная раса.", show_alert=True)
            return
        
        if not CLASSES_DATA:
            await callback.answer("🚫 Ошибка загрузки данных классов.", show_alert=True)
            return
        
        await state.update_data(race=race_id)
        await safe_edit_message(
            callback,
            "🎭 Отлично! Теперь выбери класс.\n\nКаждый класс влияет на стиль игры и характеристики персонажа.",
            reply_markup=generate_class_selection_keyboard(CLASSES_DATA)
        )
        await state.set_state(CharacterCreation.waiting_for_class_selection)
    except (IndexError, KeyError) as e:
        logger.error(f"Error confirming race: {e}")
        await callback.answer("🚫 Ошибка при подтверждении расы.", show_alert=True)
    
    await callback.answer()

@router.callback_query(F.data.startswith("classes_page_"), CharacterCreation.waiting_for_class_selection)
async def paginate_classes(callback: CallbackQuery, state: FSMContext):
    """Handle class pagination."""
    try:
        page = int(callback.data.split('_')[2])
        await callback.message.edit_reply_markup(
            reply_markup=generate_class_selection_keyboard(CLASSES_DATA, current_page=page)
        )
    except (ValueError, IndexError, TelegramBadRequest) as e:
        logger.error(f"Error in class pagination: {e}")
    await callback.answer()

@router.callback_query(F.data.startswith("select_class_"), CharacterCreation.waiting_for_class_selection)
async def show_class_details(callback: CallbackQuery, state: FSMContext):
    """Show class details for confirmation."""
    try:
        class_id = callback.data.split('_')[2]
        class_info = CLASSES_DATA.get(class_id)
        
        if not class_info:
            await callback.answer("🚫 Класс не найден.", show_alert=True)
            return
        
        modifiers_text = "\n".join([
            f"{'+' if mod > 0 else ''}{mod}% к {STAT_NAMES.get(stat, stat)}" 
            for stat, mod in class_info["modifiers"].items()
        ])
        
        await safe_edit_message(
            callback,
            f"🎭 Класс: {class_info['name']}\n\n🎯 Бонусы:\n{modifiers_text}\n\n📖 {class_info['description']}",
            reply_markup=confirm_selection_keyboard("класс", class_id, "классов")
        )
        await state.update_data(selected_class_id=class_id)
        await state.set_state(CharacterCreation.waiting_for_class_confirmation)
    except (IndexError, KeyError) as e:
        logger.error(f"Error showing class details: {e}")
        await callback.answer("🚫 Ошибка при загрузке данных класса.", show_alert=True)
    
    await callback.answer()

@router.callback_query(F.data == "back_to_classes_list", CharacterCreation.waiting_for_class_confirmation)
async def back_to_classes_list(callback: CallbackQuery, state: FSMContext):
    """Return to classes list."""
    await safe_edit_message(
        callback,
        "🎭 Отлично! Теперь выбери класс.\n\nКаждый класс влияет на стиль игры и характеристики персонажа.",
        reply_markup=generate_class_selection_keyboard(CLASSES_DATA)
    )
    await state.set_state(CharacterCreation.waiting_for_class_selection)
    await callback.answer()

@router.callback_query(F.data.startswith("confirm_class_"), CharacterCreation.waiting_for_class_confirmation)
async def confirm_class(callback: CallbackQuery, state: FSMContext):
    """Confirm class selection and proceed to photo upload."""
    try:
        class_id = callback.data.split('_')[2]
        
        if class_id not in CLASSES_DATA:
            await callback.answer("🚫 Неверный класс.", show_alert=True)
            return
        
        await state.update_data(character_class=class_id)
        await safe_edit_message(
            callback,
            "📸 Остался последний шаг — отправь картинку своего персонажа!\nЭто может быть рисунок, аватар или любой другой образ."
        )
        await state.set_state(CharacterCreation.waiting_for_photo)
    except (IndexError, KeyError) as e:
        logger.error(f"Error confirming class: {e}")
        await callback.answer("🚫 Ошибка при подтверждении класса.", show_alert=True)
    
    await callback.answer()

@router.message(CharacterCreation.waiting_for_photo, F.photo)
async def process_character_photo(message: Message, state: FSMContext):
    """Process character photo and show final confirmation."""
    try:
        photo_id = message.photo[-1].file_id
        await state.update_data(photo_id=photo_id)
        
        user_data = await state.get_data()
        name = user_data.get('name')
        age = user_data.get('age')
        race_id = user_data.get('race')
        class_id = user_data.get('character_class')
        
        # Validate all required data is present
        if not all([name, age, race_id, class_id]):
            await message.answer("🚫 Ошибка: не все данные персонажа заполнены. Начните создание заново.")
            await state.clear()
            return
        
        race_info = RACES_DATA.get(race_id)
        class_info = CLASSES_DATA.get(class_id)
        
        if not race_info or not class_info:
            await message.answer("🚫 Ошибка: данные расы или класса не найдены.")
            await state.clear()
            return
        
        # Calculate final stats
        final_stats = apply_race_class_modifiers(
            BASE_STATS,
            race_info["modifiers"],
            class_info["modifiers"]
        )
        
        # Store calculated stats
        await state.update_data(final_stats=final_stats)
        
        character_summary = (
            f"📜 Твоя анкета:\n\n"
            f"👤 Имя: {name}\n"
            f"📅 Возраст: {age}\n"
            f"🧬 Раса: {race_info['name']}\n"
            f"🎭 Класс: {class_info['name']}\n"
            f"🖼 Фото: ✅ прикреплено\n\n"
            f"📊 Статы:\n"
        )
        
        for stat, value in final_stats.items():
            stat_name = STAT_NAMES.get(stat, stat)
            character_summary += f"  {stat_name}: {value}\n"
        
        await message.answer_photo(
            photo=photo_id,
            caption=character_summary,
            reply_markup=final_confirmation_keyboard()
        )
        await state.set_state(CharacterCreation.confirm_creation)
    except Exception as e:
        logger.error(f"Error processing photo: {e}")
        await message.answer("🚫 Ошибка при обработке фотографии. Попробуйте снова.")

@router.message(CharacterCreation.waiting_for_photo, ~F.photo)
async def process_character_photo_invalid(message: Message, state: FSMContext):
    """Handle non-photo messages in photo waiting state."""
    await message.answer("🚫 Пожалуйста, отправь именно изображение.")

@router.callback_query(F.data == "confirm_character_creation", CharacterCreation.confirm_creation)
async def confirm_character_creation(callback: CallbackQuery, state: FSMContext):
    """Confirm character creation and save to database."""
    try:
        user_data = await state.get_data()
        user_id = callback.from_user.id
        
        # Validate required data
        required_fields = ['name', 'age', 'race', 'character_class']
        missing_fields = [field for field in required_fields if field not in user_data]
        
        if missing_fields:
            await callback.answer(f"🚫 Отсутствуют данные: {', '.join(missing_fields)}", show_alert=True)
            return
        
        # Create character with validated data
        character = Character(
            user_id=user_id,
            name=user_data['name'],
            age=user_data['age'],
            race=user_data['race'],
            character_class=user_data['character_class'],
            photo_id=user_data.get('photo_id'),
            stats=user_data.get('final_stats')
        )
        
        # Save character to database
        await save_character(character)
        
        await callback.message.answer(
            f"🎉 Персонаж создан!\n\n"
            f"Готовься к захватывающим приключениям, {character.name}!\n"
            f"Посмотреть свой профиль можно с помощью меню! Просто введи /menu"
        )
        await state.clear()
    except Exception as e:
        logger.error(f"Error creating character: {e}")
        await callback.answer("🚫 Ошибка при создании персонажа. Попробуйте снова.", show_alert=True)
    
    await callback.answer()

@router.callback_query(F.data == "cancel_character_creation", CharacterCreation.confirm_creation)
async def cancel_character_creation(callback: CallbackQuery, state: FSMContext):
    """Cancel character creation."""
    await state.clear()
    await callback.message.answer("Создание персонажа отменено. Вы можете начать заново, введя /menu.")
    await callback.answer()

# Error handler for invalid states
@router.callback_query(F.data.startswith(("select_race_", "select_class_", "confirm_race_", "confirm_class_")))
async def handle_invalid_state_callback(callback: CallbackQuery, state: FSMContext):
    """Handle callbacks received in invalid states."""
    current_state = await state.get_state()
    if current_state is None:
        await callback.answer("🚫 Сессия создания персонажа завершена. Начните заново.", show_alert=True)
    else:
        await callback.answer("🚫 Неверное действие для текущего этапа.", show_alert=True)