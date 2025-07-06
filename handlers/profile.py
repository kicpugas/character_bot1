import logging
import json
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest

from utils.database import get_character_data, save_character
from keyboards.profile_kb import profile_keyboard
from keyboards.inventory_kb import get_equipment_keyboard, item_action_keyboard, EQUIPMENT_SLOTS
from utils.stat_names import STAT_NAMES
from utils.stat_calculator import calculate_total_stats
from models.character import Character

class ProfileState(StatesGroup):
    viewing_equipment = State()
    viewing_equipment_item = State()

router = Router()

with open('data/items.json', 'r', encoding='utf-8') as f:
    ITEMS_DATA = json.load(f)

@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    character = await get_character_data(user_id)

    if character:
        # Enhanced profile display with better formatting
        character_summary = (
            f"✨ <b>ПРОФИЛЬ ПЕРСОНАЖА</b> ✨\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
            f"👤 <b>Имя:</b> {character['name']}\n"
            f"🎯 <b>Уровень:</b> {character['level']}\n"
            f"⚡ <b>Опыт:</b> {character['exp']} / {character['exp_to_next']}\n"
        )
        
        # Progress bar for experience
        exp_progress = character['exp'] / character['exp_to_next']
        filled_blocks = int(exp_progress * 10)
        progress_bar = "█" * filled_blocks + "░" * (10 - filled_blocks)
        character_summary += f"📊 [{progress_bar}] {int(exp_progress * 100)}%\n"
        
        if character['stat_points'] > 0:
            character_summary += f"\n🎁 <b>Доступные очки:</b> <code>{character['stat_points']}</code>\n"
        
        character_summary += f"\n━━━━━━━━━━━━━━━━━━━"

        try:
            await callback.message.delete()
        except TelegramBadRequest:
            pass 
        if character.get('photo_id'):
            await callback.message.answer_photo(
                photo=character['photo_id'],
                caption=character_summary,
                reply_markup=profile_keyboard(character['stat_points']),
                parse_mode='HTML'
            )
        else:
            await callback.message.answer(
                text=character_summary,
                reply_markup=profile_keyboard(character['stat_points']),
                parse_mode='HTML'
            )
    else:
        await callback.message.answer(
            "❌ <b>У тебя ещё нет персонажа</b>\n\n"
            "💡 Создай его, чтобы увидеть профиль!",
            parse_mode='HTML'
        )
    await callback.answer()

@router.callback_query(F.data == "profile:equipment")
async def show_equipment(callback: CallbackQuery, state: FSMContext):
    logging.info(f"Entering show_equipment. Current state: {await state.get_state()}")
    await state.set_state(ProfileState.viewing_equipment)
    logging.info("State set to ProfileState.viewing_equipment")
    character_data = await get_character_data(callback.from_user.id)
    if not character_data:
        await callback.answer("Данные персонажа не найдены.", show_alert=True)
        return

    equipment = character_data.get('equipment', {})

    # Enhanced equipment display
    equipment_text = (
        "⚔️ <b>ЭКИПИРОВКА</b> ⚔️\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
    )
    
    if not equipment:
        equipment_text += (
            "🕳️ <i>Экипировка пуста</i>\n\n"
            "💡 Найди предметы в приключениях\n"
            "   и экипируй их из инвентаря!"
        )
    else:
        total_bonuses = {stat: 0 for stat in STAT_NAMES.keys()}
        
        # Group equipment by slots for better organization
        slot_order = ['helmet', 'chest', 'legs', 'boots', 'weapon', 'shield', 'ring', 'artifact']
        
        for slot in slot_order:
            if slot in equipment:
                item_id = equipment[slot]
                item_info = ITEMS_DATA.get(item_id)
                if item_info:
                    slot_icon = EQUIPMENT_SLOTS.get(slot, '')
                    equipment_text += f"{slot_icon} <b>{item_info['name']}</b>\n"
                    
                    # Show bonuses with better formatting
                    item_bonuses = item_info.get('stats', {})
                    if item_bonuses:
                        bonuses = []
                        for stat, value in item_bonuses.items():
                            sign = "+" if value >= 0 else ""
                            stat_name = STAT_NAMES.get(stat, stat.capitalize())
                            bonuses.append(f"{sign}{value} {stat_name}")
                            total_bonuses[stat] += value
                        equipment_text += f"   <i>{' • '.join(bonuses)}</i>\n"
                    equipment_text += "\n"
        
        # Total bonuses section
        equipment_text += "📈 <b>ИТОГО БОНУСЫ:</b>\n"
        total_bonuses_list = []
        for stat, value in total_bonuses.items():
            if value != 0:
                sign = "+" if value >= 0 else ""
                stat_name = STAT_NAMES.get(stat, stat.capitalize())
                total_bonuses_list.append(f"{sign}{value} {stat_name}")
        
        if total_bonuses_list:
            equipment_text += f"🎯 {' • '.join(total_bonuses_list)}"
        else:
            equipment_text += "❌ <i>Нет активных бонусов</i>"
    
    equipment_text += "\n\n━━━━━━━━━━━━━━━━━━━"

    try:
        await callback.message.edit_text(
            equipment_text, 
            reply_markup=get_equipment_keyboard(equipment),
            parse_mode='HTML'
        )
    except TelegramBadRequest as e:
        logging.error(f"Error editing message in show_equipment: {e}. Sending new message instead.")
        await callback.message.answer(
            equipment_text, 
            reply_markup=get_equipment_keyboard(equipment),
            parse_mode='HTML'
        )
    await callback.answer()

@router.callback_query(ProfileState.viewing_equipment, F.data.startswith("profile:view_equipped_item:"))
async def view_equipped_item(callback: CallbackQuery, state: FSMContext):
    logging.info(f"Entering view_equipped_item. Current state: {await state.get_state()}")
    item_id = callback.data.split(":")[2]
    logging.info(f"item_id: {item_id}")
    item_info = ITEMS_DATA.get(item_id)
    if not item_info:
        await callback.answer("Предмет не найден.", show_alert=True)
        return

    # Enhanced item display with better formatting
    item_text = (
        f"🔍 <b>ПРЕДМЕТ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"📦 <b>{item_info['name']}</b>\n"
    )
    
    if item_info.get('type') in ['armor', 'weapon', 'artifact']:
        slot_name_russian = EQUIPMENT_SLOTS.get(item_info.get('slot'), '').split(' ', 1)[1] if ' ' in EQUIPMENT_SLOTS.get(item_info.get('slot'), '') else item_info.get('slot', '').capitalize()
        item_text += f"🛡️ <b>Тип:</b> {slot_name_russian}\n"
    
    if 'stats' in item_info:
        item_text += f"\n⚡ <b>БОНУСЫ:</b>\n"
        bonuses = []
        for stat, value in item_info['stats'].items():
            sign = "+" if value >= 0 else ""
            stat_name = STAT_NAMES.get(stat, stat.capitalize())
            bonuses.append(f"   🔸 {sign}{value} к {stat_name}")
        item_text += "\n".join(bonuses) + "\n"
    
    if 'description' in item_info:
        item_text += f"\n📖 <b>Описание:</b>\n<i>{item_info['description']}</i>\n"
    
    item_text += "\n━━━━━━━━━━━━━━━━━━━"

    await state.set_state(ProfileState.viewing_equipment_item)
    try:
        await callback.message.edit_text(
            item_text, 
            reply_markup=item_action_keyboard(item_id, is_equipped=True, is_consumable=False, source='equipment'),
            parse_mode='HTML'
        )
    except TelegramBadRequest as e:
        logging.error(f"Error editing message in view_equipped_item: {e}. Sending new message instead.")
        await callback.message.answer(
            item_text, 
            reply_markup=item_action_keyboard(item_id, is_equipped=True, is_consumable=False, source='equipment'),
            parse_mode='HTML'
        )
    await callback.answer()

@router.callback_query(ProfileState.viewing_equipment_item, F.data.startswith("profile:unequip_item:"))
async def unequip_item_from_profile(callback: CallbackQuery, state: FSMContext):
    logging.info(f"Entering unequip_item_from_profile. Current state: {await state.get_state()}")
    item_id = callback.data.split(":")[2]
    logging.info(f"item_id to unequip: {item_id}")
    character_data = await get_character_data(callback.from_user.id)
    item_info = ITEMS_DATA.get(item_id)

    if not item_info or item_id not in character_data.get('equipment', {}).values():
        await callback.answer("Предмет не экипирован.", show_alert=True)
        return

    slot_to_unequip = None
    for slot, equipped_item_id in character_data['equipment'].items():
        if equipped_item_id == item_id:
            slot_to_unequip = slot
            break
    
    if slot_to_unequip:
        del character_data['equipment'][slot_to_unequip]
        character_data['inventory'].append(item_id)
        await save_character(Character.from_dict(character_data))
        await callback.answer(f"✅ {item_info['name']} снят с персонажа!", show_alert=True)
        await show_equipment(callback, state)
    else:
        await callback.answer("❌ Ошибка при снятии предмета.", show_alert=True)

@router.callback_query(F.data == "profile_stats")
async def show_stats_wrapper(callback: CallbackQuery, state: FSMContext):
    await show_character_stats(callback, state)

async def show_character_stats(callback: CallbackQuery, state: FSMContext):
    character_data = await get_character_data(callback.from_user.id)
    if not character_data:
        await callback.answer("Данные персонажа не найдены.", show_alert=True)
        return

    base_stats = character_data['stats']
    equipment = character_data.get('equipment', {})
    total_stats, total_bonuses = calculate_total_stats(base_stats, equipment)

    # Enhanced stats display
    stats_text = (
        "📊 <b>ХАРАКТЕРИСТИКИ</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
    )
    
    if not base_stats:
        stats_text += "❌ <i>Характеристики не найдены</i>"
    else:
        # Group stats by category for better readability
        combat_stats = ['strength', 'agility', 'intelligence']
        defense_stats = ['endurance', 'luck', 'charisma']
        
        stats_text += "⚔️ <b>Боевые характеристики:</b>\n"
        for stat_key in combat_stats:
            if stat_key in base_stats:
                base_value = base_stats[stat_key]
                bonus_value = total_bonuses.get(stat_key, 0)
                display_name = STAT_NAMES.get(stat_key, stat_key.capitalize())
                
                if bonus_value != 0:
                    sign = "+" if bonus_value >= 0 else ""
                    total_value = base_value + bonus_value
                    stats_text += f"   🔸 <b>{display_name}:</b> {total_value} <i>({base_value} {sign}{bonus_value})</i>\n"
                else:
                    stats_text += f"   🔸 <b>{display_name}:</b> {base_value}\n"
        
        stats_text += "\n🛡️ <b>Защитные характеристики:</b>\n"
        for stat_key in defense_stats:
            if stat_key in base_stats:
                base_value = base_stats[stat_key]
                bonus_value = total_bonuses.get(stat_key, 0)
                display_name = STAT_NAMES.get(stat_key, stat_key.capitalize())
                
                if bonus_value != 0:
                    sign = "+" if bonus_value >= 0 else ""
                    total_value = base_value + bonus_value
                    stats_text += f"   🔸 <b>{display_name}:</b> {total_value} <i>({base_value} {sign}{bonus_value})</i>\n"
                else:
                    stats_text += f"   🔸 <b>{display_name}:</b> {base_value}\n"
        
        # Show remaining stats if any
        remaining_stats = [stat for stat in base_stats.keys() if stat not in combat_stats + defense_stats]
        if remaining_stats:
            stats_text += "\n🎯 <b>Прочие характеристики:</b>\n"
            for stat_key in remaining_stats:
                base_value = base_stats[stat_key]
                bonus_value = total_bonuses.get(stat_key, 0)
                display_name = STAT_NAMES.get(stat_key, stat_key.capitalize())
                
                if bonus_value != 0:
                    sign = "+" if bonus_value >= 0 else ""
                    total_value = base_value + bonus_value
                    stats_text += f"   🔸 <b>{display_name}:</b> {total_value} <i>({base_value} {sign}{bonus_value})</i>\n"
                else:
                    stats_text += f"   🔸 <b>{display_name}:</b> {base_value}\n"
    
    stats_text += "\n━━━━━━━━━━━━━━━━━━━"
    
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass
    await callback.message.answer(
        stats_text, 
        reply_markup=profile_keyboard(back_to_profile=True, show_stats_button=False),
        parse_mode='HTML'
    )
    await callback.answer()