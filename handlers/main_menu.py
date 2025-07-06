import json
import random
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from keyboards.main_kb import create_character_keyboard, main_menu_keyboard, back_to_main_menu_keyboard
from utils.database import get_character_data
from handlers.profile import show_profile, show_equipment
from handlers.combat import start_combat

router = Router()

# Define base path for data files
BASE_DATA_PATH = Path(__file__).parent.parent / 'data'

# Load races and classes data for display
with open(BASE_DATA_PATH / 'races.json', 'r', encoding='utf-8') as f:
    RACES_DATA = json.load(f)

with open(BASE_DATA_PATH / 'classes.json', 'r', encoding='utf-8') as f:
    CLASSES_DATA = json.load(f)

with open(BASE_DATA_PATH / 'enemies.json', 'r', encoding='utf-8') as f:
    ENEMIES_DATA = json.load(f)

with open(BASE_DATA_PATH / 'items.json', 'r', encoding='utf-8') as f:
    ITEMS_DATA = json.load(f)

@router.message(Command("menu"))
async def show_main_menu(message: Message):
    user_id = message.from_user.id
    character = await get_character_data(user_id)

    if character is None:
        await message.answer(
            "😕 У тебя ещё нет персонажа.\nСоздай его с помощью кнопки ниже:",
            reply_markup=create_character_keyboard()
        )
    else:
        await message.answer(
            "📜 Главное меню\n\nЧто хочешь сделать?\nВыбери действие с помощью кнопок ниже.",
            reply_markup=main_menu_keyboard()
        )

@router.callback_query(F.data == "menu_profile")
async def process_menu_profile(callback: CallbackQuery, state: FSMContext):
    await show_profile(callback, state)

@router.callback_query(F.data == "menu_battle")
async def process_menu_battle(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    character = await get_character_data(user_id)

    if character is None:
        await callback.answer("Сначала создайте персонажа!", show_alert=True)
        return

    enemy_id = random.choice(list(ENEMIES_DATA.keys()))
    await callback.message.edit_text(f"⚔️ Начинается бой с {ENEMIES_DATA[enemy_id]['name']}!", reply_markup=None)
    await start_combat(callback.message, state, character, enemy_id)
    await callback.answer()



@router.callback_query(F.data == "menu_inventory")
async def process_menu_inventory(callback: CallbackQuery):
    try:
        await callback.message.delete() # Delete the old message
    except TelegramBadRequest:
        pass # Ignore if message is already deleted
    await callback.message.answer("🎒 Открываем инвентарь...", reply_markup=back_to_main_menu_keyboard())
    await callback.answer()

@router.callback_query(F.data == "menu_shop")
async def process_menu_shop(callback: CallbackQuery):
    try:
        await callback.message.delete() # Delete the old message
    except TelegramBadRequest:
        pass # Ignore if message is already deleted
    await callback.message.answer("🛒 Заходим в магазин...", reply_markup=back_to_main_menu_keyboard())
    await callback.answer()

@router.callback_query(F.data == "main_menu:equipment")
async def process_menu_equipment(callback: CallbackQuery, state: FSMContext):
    await show_equipment(callback, state)

@router.callback_query(F.data == "menu_settings")
async def process_menu_settings(callback: CallbackQuery):
    try:
        await callback.message.delete() # Delete the old message
    except TelegramBadRequest:
        pass # Ignore if message is already deleted
    await callback.message.answer("🔧 Открываем настройки...", reply_markup=back_to_main_menu_keyboard())
    await callback.answer()

@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    character = await get_character_data(user_id)

    if character is None:
        try:
            await callback.message.delete() # Delete the old message
        except TelegramBadRequest:
            pass # Ignore if message is already deleted
        await callback.message.answer(
            "😕 У тебя ещё нет персонажа.\nСоздай его с помощью кнопки ниже:",
            reply_markup=create_character_keyboard()
        )
    else:
        try:
            await callback.message.delete() # Delete the old message
        except TelegramBadRequest:
            pass # Ignore if message is already deleted
        await callback.message.answer(
            "📜 Главное меню\n\nЧто хочешь сделать?\nВыбери действие с помощью кнопок ниже.",
            reply_markup=main_menu_keyboard()
        )
    await callback.answer()

@router.callback_query(F.data == "menu_back")
async def process_menu_back(callback: CallbackQuery):
    user_id = callback.from_user.id
    character = await get_character_data(user_id)

    if character is None:
        try:
            await callback.message.delete() # Delete the old message
        except TelegramBadRequest:
            pass # Ignore if message is already deleted
        await callback.message.answer(
            "😕 У тебя ещё нет персонажа.\nСоздай его с помощью кнопки ниже:",
            reply_markup=create_character_keyboard()
        )
    else:
        try:
            await callback.message.delete() # Delete the old message
        except TelegramBadRequest:
            pass # Ignore if message is already deleted
        await callback.message.answer(
            "📜 Главное меню\n\nЧто хочешь сделать?\nВыбери действие с помощью кнопок ниже.",
            reply_markup=main_menu_keyboard()
        )
    await callback.answer()