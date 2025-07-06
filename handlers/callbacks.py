from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
import json

from handlers.combat import start_combat
from utils.database import get_character_data

router = Router()

BOSSES_DATA_PATH = 'data/bosses.json'

@router.callback_query(F.data.startswith('admin:summon_boss:'))
async def handle_summon_boss(callback: CallbackQuery, state: FSMContext):
    """Handles the selection of a boss to summon."""
    boss_id = callback.data.split(':')[-1]
    
    with open(BOSSES_DATA_PATH, 'r', encoding='utf-8') as f:
        bosses = json.load(f)
        
    boss_data = bosses.get(boss_id)
    if not boss_data:
        await callback.answer("Босс не найден!", show_alert=True)
        return

    # You need a function to start combat. Let's assume it's called start_combat
    # and it takes the user's character data and the enemy data.
    # This is a placeholder call.
    
    character = await get_character_data(callback.from_user.id)
    if character:
        await start_combat(callback.message, state, character, boss_id)
    else:
        await callback.answer("Сначала создайте персонажа!", show_alert=True)
    
    await callback.answer(f"Призыв {boss_data['name']}!", show_alert=True)
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass # Clean up the boss selection message

@router.callback_query(F.data == 'admin:cancel_summon')
async def cancel_summon(callback: CallbackQuery):
    """Cancels the boss summon action."""
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass
    await callback.answer("Призыв отменен.")
