import json
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from config import ADMIN_ID
from keyboards.combat_kb import boss_selection_keyboard

router = Router()

BOSSES_DATA_PATH = 'data/bosses.json'

@router.message(Command("boss"), F.from_user.id == ADMIN_ID)
async def summon_boss_command(message: Message):
    """Handles the /boss command for admins to summon a boss."""
    with open(BOSSES_DATA_PATH, 'r', encoding='utf-8') as f:
        bosses = json.load(f)
    
    await message.answer(
        text="Выберите босса, которого хотите призвать:",
        reply_markup=boss_selection_keyboard(bosses)
    )

# You will need a callback handler for 'select_boss_{boss_id}' in your callbacks handler file.
