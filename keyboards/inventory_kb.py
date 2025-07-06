import json
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

RARITY_COLORS = {
    "common": "⚪",
    "uncommon": "🟢",
    "rare": "🔵",
    "epic": "🟣",
    "legendary": "🟠"
}

EQUIPMENT_SLOTS = {
    "weapon": "🗡 Оружие",
    "head": "👑 Голова",
    "chest": "🛡 Тело",
    "legs": "🦵 Ноги",
    "hands": "🧤 Руки",
    "feet": "👢 Ступни",
    "amulet": "🔮 Амулет"
}

with open('data/items.json', 'r', encoding='utf-8') as f:
    ITEMS_DATA = json.load(f)

def inventory_keyboard(items: list, page: int, total_pages: int, start_index: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i, item_id in enumerate(items):
        item_info = ITEMS_DATA.get(item_id, {})
        if not item_info:
            continue
        rarity_icon = RARITY_COLORS.get(item_info.get('rarity', 'common'), '⚪')
        builder.button(text=f"{start_index + i + 1}. {rarity_icon} {item_info['name']}", callback_data=f"inventory:view_item:{item_id}")
    builder.adjust(1)

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"inventory:page:{page-1}"))
    if total_pages > 0:
        nav_buttons.append(InlineKeyboardButton(text=f"📦 Страница {page}/{total_pages}", callback_data="inventory:current_page"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="➡️ Вперёд", callback_data=f"inventory:page:{page+1}"))
    if nav_buttons:
        builder.row(*nav_buttons)

    builder.row(
        InlineKeyboardButton(text="🔙 Меню", callback_data="main_menu")
    )
    return builder.as_markup()

def item_action_keyboard(item_id: str, is_equipped: bool, is_consumable: bool, source: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if is_consumable:
        builder.button(text="✅ Использовать", callback_data=f"inventory:use_item:{item_id}")
    elif is_equipped:
        if source == 'equipment':
            builder.button(text="🛑 Снять", callback_data=f"profile:unequip_item:{item_id}")
        else:
            builder.button(text="🛑 Снять", callback_data=f"inventory:unequip_item:{item_id}")
    else:
        builder.button(text="✅ Экипировать", callback_data=f"inventory:equip_item:{item_id}")
    
    builder.button(text="🗑 Удалить", callback_data=f"inventory:delete_item:{item_id}")
    
    if source == 'equipment':
        builder.button(text="❌ Назад", callback_data="profile:equipment")
    else:
        builder.button(text="❌ Назад", callback_data="inventory:back_to_inventory")
        
    builder.adjust(1)
    return builder.as_markup()

def get_equipment_keyboard(character_equipment: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for slot, icon in EQUIPMENT_SLOTS.items():
        item_id = character_equipment.get(slot)
        if item_id:
            item_info = ITEMS_DATA.get(item_id, {})
            item_name = item_info.get('name', 'Пусто')
            rarity_icon = RARITY_COLORS.get(item_info.get('rarity', 'common'), '⚪')
            builder.button(text=f"{icon}: {rarity_icon} {item_name}", callback_data=f"profile:view_equipped_item:{item_id}")
        else:
            builder.button(text=f"{icon}: Пусто", callback_data=f"inventory:equip_slot:{slot}")
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu"))
    return builder.as_markup()