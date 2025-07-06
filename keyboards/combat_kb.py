from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def combat_keyboard() -> InlineKeyboardMarkup:
    """Creates the keyboard for combat actions."""
    buttons = [
        [InlineKeyboardButton(text="⚔️ Атаковать", callback_data="combat:attack"),
         InlineKeyboardButton(text="🛡 Защита", callback_data="combat:defend")],
        [InlineKeyboardButton(text="💫 Способность", callback_data="combat:ability"),
         InlineKeyboardButton(text="🧪 Инвентарь", callback_data="combat:inventory")],
        [InlineKeyboardButton(text="🏃 Убежать", callback_data="combat:run")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def boss_selection_keyboard(bosses: dict) -> InlineKeyboardMarkup:
    """Creates a keyboard to select a boss to summon."""
    buttons = []
    for boss_id, boss_data in bosses.items():
        buttons.append([InlineKeyboardButton(text=boss_data['name'], callback_data=f"admin:summon_boss:{boss_id}")])
    buttons.append([InlineKeyboardButton(text="Отмена", callback_data="admin:cancel_summon")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def ability_selection_keyboard(abilities: list) -> InlineKeyboardMarkup:
    """Creates a keyboard for selecting an ability to use."""
    buttons = []
    for ability in abilities:
        buttons.append([InlineKeyboardButton(text=ability['display_name'], callback_data=f"combat:use_ability:{ability['name']}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="combat:back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def inventory_keyboard(items: list) -> InlineKeyboardMarkup:
    """Creates a keyboard for selecting an item to use from inventory."""
    buttons = []
    for item in items:
        # Assuming item is a dict with 'name' and 'display_name'
        buttons.append([InlineKeyboardButton(text=item['name'], callback_data=f"combat:use_item:{item['name']}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="combat:back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
