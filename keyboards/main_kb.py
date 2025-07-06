from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def create_character_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛠 Создать персонажа", callback_data="start_create_character")]
    ])
    return keyboard

def main_menu_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📜 Профиль", callback_data="menu_profile"),
         InlineKeyboardButton(text="⚔️ Битва", callback_data="menu_battle")],
        [InlineKeyboardButton(text="🎒 Инвентарь", callback_data="main_menu:inventory"),
         InlineKeyboardButton(text="🛒 Магазин", callback_data="menu_shop")],
        [InlineKeyboardButton(text="⚙ Снаряжение", callback_data="main_menu:equipment"),
         InlineKeyboardButton(text="🔧 Настройки", callback_data="menu_settings")]
    ])
    return keyboard

def back_to_main_menu_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_main_menu")]
    ])
    return keyboard