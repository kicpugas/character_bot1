import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils.database import get_character_data, save_character
from keyboards.profile_kb import profile_keyboard, leveling_keyboard
from utils.stat_names import STAT_NAMES
from models.character import Character

router = Router()

class LevelingStates(StatesGroup):
    choosing_stat = State()

@router.callback_query(F.data == "profile_upgrade")
async def start_leveling(callback: CallbackQuery, state: FSMContext):
    logging.info(f"User {callback.from_user.id} entered leveling menu.")
    user_id = callback.from_user.id
    character = await get_character_data(user_id)

    if not character or character['stat_points'] == 0:
        logging.info(f"User {user_id} has no stat points or character not found.")
        try:
            await callback.message.delete()
        except TelegramBadRequest:
            pass
        await callback.message.answer("У тебя нет очков характеристик для распределения.", reply_markup=profile_keyboard())
        await callback.answer()
        return

    await state.set_state(LevelingStates.choosing_stat)
    await state.update_data(original_stats=character['stats'].copy(), original_stat_points=character['stat_points'], current_character=character)
    logging.info(f"User {user_id} entered choosing_stat state with {character['stat_points']} stat points.")

    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass
    await callback.message.answer(
        text=get_leveling_message(character),
        reply_markup=get_leveling_keyboard(character['stats'])
    )
    await callback.answer()

def get_leveling_message(character) -> str:
    message = f"🎚 Распределение очков\n\nОсталось: {character['stat_points']}\n\n"
    for stat, value in character['stats'].items():
        message += f"{STAT_NAMES[stat]}: {value}\n"
    return message

def get_leveling_keyboard(current_stats) -> InlineKeyboardMarkup:
    return leveling_keyboard(current_stats)

@router.callback_query(LevelingStates.choosing_stat, F.data.startswith("level_up_"))
async def process_stat_choice(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split("level_up_")[1]
    data = await state.get_data()
    character = data["current_character"]
    user_id = callback.from_user.id

    logging.info(f"User {user_id} chose action: {action} in leveling menu.")

    if action == "complete":
        character['stat_points'] = 0
        char_obj = Character.from_dict(character)
        await save_character(char_obj)
        await state.clear()
        logging.info(f"User {user_id} completed leveling. Character saved.")
        try:
            await callback.message.delete()
        except TelegramBadRequest:
            pass
        await callback.message.answer("🎉 Прокачка завершена!\nТвои характеристики обновлены.", reply_markup=profile_keyboard())
    elif action == "reset":
        character['stats'] = data["original_stats"]
        character['stat_points'] = data["original_stat_points"]
        await state.update_data(current_character=character)
        logging.info(f"User {user_id} reset leveling. Stat points: {character['stat_points']}")
        try:
            await callback.message.delete()
        except TelegramBadRequest:
            pass
        await callback.message.answer(
            text=get_leveling_message(character),
            reply_markup=get_leveling_keyboard(character['stats'])
        )
    else:
        stat_to_increase = action
        if character['stat_points'] > 0:
            if stat_to_increase not in character['stats']:
                character['stats'][stat_to_increase] = 0  # Initialize if missing
            character['stats'][stat_to_increase] += 1 # Assuming 1 point per stat increase
            character['stat_points'] -= 1
            await state.update_data(current_character=character)
            logging.info(f"User {user_id} increased {stat_to_increase}. Remaining stat points: {character['stat_points']}")
            try:
                await callback.message.delete()
            except TelegramBadRequest:
                pass
            await callback.message.answer(
                text=get_leveling_message(character),
                reply_markup=get_leveling_keyboard(character['stats'])
            )
        else:
            logging.warning(f"User {user_id} tried to increase {stat_to_increase} but has no stat points.")
            await callback.message.answer("У тебя нет очков характеристик для распределения.")
    await callback.answer()
