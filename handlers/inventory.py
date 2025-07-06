import json
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards.inventory_kb import inventory_keyboard, item_action_keyboard, RARITY_COLORS
from utils.database import get_character_data, save_character
from models.character import Character
from utils.stat_calculator import get_stat_display_name

class InventoryState(StatesGroup):
    in_inventory = State()
    viewing_item = State()

router = Router()

ITEMS_PER_PAGE = 5

with open('data/items.json', 'r', encoding='utf-8') as f:
    ITEMS_DATA = json.load(f)

@router.callback_query(F.data == "main_menu:inventory")
async def inventory_menu(callback: CallbackQuery, state: FSMContext):
    await state.set_state(InventoryState.in_inventory)
    character_data = await get_character_data(callback.from_user.id)
    if not character_data or not character_data.get('inventory'):
        empty_text = (
            "🎒 <b>ИНВЕНТАРЬ</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "📦 <i>Инвентарь пуст</i>\n\n"
            "💡 Найди предметы в приключениях\n"
            "   и собери свою коллекцию!"
        )
        await callback.message.edit_text(empty_text, reply_markup=inventory_keyboard([], 0, 0, 0), parse_mode='HTML')
        return

    inventory = [item_id for item_id in character_data.get('inventory', []) if item_id in ITEMS_DATA]
    character_data['inventory'] = inventory

    total_pages = (len(inventory) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    current_page = 1
    
    start_index = (current_page - 1) * ITEMS_PER_PAGE
    end_index = start_index + ITEMS_PER_PAGE
    items_on_page = inventory[start_index:end_index]

    inventory_text = (
        "🎒 <b>ИНВЕНТАРЬ</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
    )
    
    for i, item_id in enumerate(items_on_page):
        item_info = ITEMS_DATA.get(item_id)
        if item_info:
            rarity_icon = RARITY_COLORS.get(item_info.get('rarity', 'common'), '⚪')
            item_number = start_index + i + 1
            inventory_text += f"<code>{item_number:2d}</code>. {rarity_icon} <b>{item_info['name']}</b>\n"

    inventory_text += f"\n📄 Страница <b>{current_page}</b> из <b>{total_pages}</b>"
    inventory_text += f"\n🎯 Всего предметов: <b>{len(inventory)}</b>"
    inventory_text += "\n━━━━━━━━━━━━━━━━━━━"

    await callback.message.edit_text(inventory_text, reply_markup=inventory_keyboard(items_on_page, current_page, total_pages, start_index), parse_mode='HTML')
    await callback.answer()

@router.callback_query(InventoryState.in_inventory, F.data.startswith("inventory:page:"))
async def inventory_pagination(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split(":")[2])
    character_data = await get_character_data(callback.from_user.id)
    inventory = character_data['inventory']
    total_pages = (len(inventory) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    start_index = (page - 1) * ITEMS_PER_PAGE
    end_index = start_index + ITEMS_PER_PAGE
    items_on_page = inventory[start_index:end_index]

    inventory_text = (
        "🎒 <b>ИНВЕНТАРЬ</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
    )
    
    for i, item_id in enumerate(items_on_page):
        item_info = ITEMS_DATA.get(item_id)
        if item_info:
            rarity_icon = RARITY_COLORS.get(item_info.get('rarity', 'common'), '⚪')
            item_number = start_index + i + 1
            inventory_text += f"<code>{item_number:2d}</code>. {rarity_icon} <b>{item_info['name']}</b>\n"

    inventory_text += f"\n📄 Страница <b>{page}</b> из <b>{total_pages}</b>"
    inventory_text += f"\n🎯 Всего предметов: <b>{len(inventory)}</b>"
    inventory_text += "\n━━━━━━━━━━━━━━━━━━━"

    await callback.message.edit_text(inventory_text, reply_markup=inventory_keyboard(items_on_page, page, total_pages, start_index), parse_mode='HTML')
    await callback.answer()

@router.callback_query(InventoryState.in_inventory, F.data.startswith("inventory:view_item:"))
async def view_item_details(callback: CallbackQuery, state: FSMContext):
    item_id = callback.data.split(":")[2]
    item_info = ITEMS_DATA.get(item_id)
    if not item_info:
        await callback.answer("❌ Предмет не найден.", show_alert=True)
        return

    character_data = await get_character_data(callback.from_user.id)
    is_equipped = item_id in character_data.get('equipment', {}).values()
    is_consumable = item_info.get('type') == 'consumable' or item_info.get('type') == 'potion'

    # Enhanced item details display
    rarity_icon = RARITY_COLORS.get(item_info.get('rarity', 'common'), '⚪')
    item_text = (
        f"🔍 <b>ПРЕДМЕТ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"{rarity_icon} <b>{item_info['name']}</b>\n"
    )
    
    # Item type and slot
    if item_info.get('type') in ['armor', 'weapon', 'artifact']:
        item_text += f"🛡️ <b>Тип:</b> {item_info.get('slot', '').capitalize()}\n"
    elif item_info.get('type') == 'consumable':
        item_text += f"💊 <b>Тип:</b> Расходуемый предмет\n"
    elif item_info.get('type') == 'potion':
        item_text += f"🧪 <b>Тип:</b> Зелье\n"
    
    # Rarity display
    if item_info.get('rarity'):
        rarity_names = {
            'common': 'Обычный',
            'uncommon': 'Необычный', 
            'rare': 'Редкий',
            'epic': 'Эпический',
            'legendary': 'Легендарный'
        }
        rarity_name = rarity_names.get(item_info['rarity'], item_info['rarity'].capitalize())
        item_text += f"✨ <b>Редкость:</b> {rarity_name}\n"
    
    # Equipment status
    if is_equipped:
        item_text += f"✅ <b>Статус:</b> <i>Экипирован</i>\n"
    
    # Stats bonuses
    if 'stats' in item_info:
        item_text += f"\n⚡ <b>БОНУСЫ:</b>\n"
        bonuses = []
        for stat, value in item_info['stats'].items():
            sign = "+" if value >= 0 else ""
            stat_name = get_stat_display_name(stat)
            bonuses.append(f"   🔸 {sign}{value} к {stat_name}")
        item_text += "\n".join(bonuses) + "\n"
    
    # Special effects for consumables
    if item_info.get('effect') == 'heal':
        heal_amount = item_info.get('heal_amount', 0)
        item_text += f"\n💚 <b>Эффект:</b> Восстанавливает {heal_amount} HP\n"
    
    # Description
    if 'description' in item_info:
        item_text += f"\n📖 <b>Описание:</b>\n<i>{item_info['description']}</i>\n"
    
    item_text += "\n━━━━━━━━━━━━━━━━━━━"

    await state.set_state(InventoryState.viewing_item)
    await callback.message.edit_text(
        item_text, 
        reply_markup=item_action_keyboard(item_id, is_equipped, is_consumable, source='inventory'),
        parse_mode='HTML'
    )
    await callback.answer()

@router.callback_query(InventoryState.viewing_item, F.data.startswith("inventory:equip_item:"))
async def equip_item(callback: CallbackQuery, state: FSMContext):
    item_id = callback.data.split(":")[2]
    character_data = await get_character_data(callback.from_user.id)
    item_info = ITEMS_DATA.get(item_id)

    if not item_info or item_id not in character_data['inventory']:
        await callback.answer("❌ Предмет не найден в инвентаре.", show_alert=True)
        return

    slot = item_info.get('slot')
    if not slot:
        await callback.answer("❌ Этот предмет нельзя экипировать.", show_alert=True)
        return

    # Handle slot replacement
    replaced_item = None
    if slot in character_data['equipment']:
        old_item_id = character_data['equipment'][slot]
        old_item_info = ITEMS_DATA.get(old_item_id)
        replaced_item = old_item_info['name'] if old_item_info else "предмет"
        del character_data['equipment'][slot]
        character_data['inventory'].append(old_item_id)

    character_data['equipment'][slot] = item_id
    character_data['inventory'].remove(item_id)

    await save_character(Character.from_dict(character_data))
    
    success_message = f"✅ {item_info['name']} экипирован!"
    if replaced_item:
        success_message += f"\n🔄 Заменён: {replaced_item}"
    
    await callback.answer(success_message, show_alert=True)
    await inventory_menu(callback, state)

@router.callback_query(InventoryState.viewing_item, F.data.startswith("inventory:unequip_item:"))
async def unequip_item(callback: CallbackQuery, state: FSMContext):
    item_id = callback.data.split(":")[2]
    character_data = await get_character_data(callback.from_user.id)
    item_info = ITEMS_DATA.get(item_id)

    if not item_info or item_id not in character_data.get('equipment', {}).values():
        await callback.answer("❌ Предмет не экипирован.", show_alert=True)
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
        await inventory_menu(callback, state)
    else:
        await callback.answer("❌ Ошибка при снятии предмета.", show_alert=True)

@router.callback_query(InventoryState.viewing_item, F.data.startswith("inventory:use_item:"))
async def use_item(callback: CallbackQuery, state: FSMContext):
    item_id = callback.data.split(":")[2]
    character_data = await get_character_data(callback.from_user.id)
    item_info = ITEMS_DATA.get(item_id)

    if not item_info or item_id not in character_data['inventory']:
        await callback.answer("❌ Предмет не найден в инвентаре.", show_alert=True)
        return

    if item_info.get('type') == 'consumable' or item_info.get('type') == 'potion':
        success_message = f"✅ Использован: {item_info['name']}"
        
        if item_info.get('effect') == 'heal':
            heal_amount = item_info.get('heal_amount', 0)
            old_hp = character_data['stats']['hp']
            max_hp = character_data['stats'].get('max_hp', character_data['stats']['hp'])
            character_data['stats']['hp'] = min(max_hp, old_hp + heal_amount)
            actual_heal = character_data['stats']['hp'] - old_hp
            success_message += f"\n💚 Восстановлено: {actual_heal} HP"

        character_data['inventory'].remove(item_id)
        await save_character(Character.from_dict(character_data))
        await callback.answer(success_message, show_alert=True)
        await inventory_menu(callback, state)
    else:
        await callback.answer("❌ Этот предмет нельзя использовать.", show_alert=True)

@router.callback_query(InventoryState.viewing_item, F.data.startswith("inventory:delete_item:"))
async def delete_item(callback: CallbackQuery, state: FSMContext):
    item_id = callback.data.split(":")[2]
    character_data = await get_character_data(callback.from_user.id)
    item_info = ITEMS_DATA.get(item_id)

    if not item_info or item_id not in character_data['inventory']:
        await callback.answer("❌ Предмет не найден в инвентаре.", show_alert=True)
        return

    character_data['inventory'].remove(item_id)
    await save_character(Character.from_dict(character_data))
    await callback.answer(f"🗑️ {item_info['name']} удалён из инвентаря.", show_alert=True)
    await inventory_menu(callback, state)

@router.callback_query(InventoryState.viewing_item, F.data == "inventory:back_to_inventory")
async def back_to_inventory_from_item_details(callback: CallbackQuery, state: FSMContext):
    await inventory_menu(callback, state)