from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.stat_names import STAT_NAMES

def profile_keyboard(stat_points: int = 0, back_to_profile: bool = False, show_stats_button: bool = True) -> InlineKeyboardMarkup:
    buttons = []
    if show_stats_button:
        buttons.append([InlineKeyboardButton(text="📊 Статистика", callback_data="profile_stats")],)
    if stat_points > 0:
        buttons.append([InlineKeyboardButton(text="📈 Прокачать", callback_data="profile_upgrade")])
    if back_to_profile:
        buttons.append([InlineKeyboardButton(text="🔙 К профилю", callback_data="profile")])
    else:
        buttons.append([InlineKeyboardButton(text="🔙 В меню", callback_data="menu_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def leveling_keyboard(current_stats) -> InlineKeyboardMarkup:
    buttons = []
    # Create buttons for each stat
    for stat_key, stat_name in STAT_NAMES.items():
        buttons.append([InlineKeyboardButton(text=f"+ {stat_name}", callback_data=f"level_up_{stat_key}")])

    buttons.append([InlineKeyboardButton(text="✅ Завершить", callback_data="level_up_complete")])
    buttons.append([InlineKeyboardButton(text="🔄 Сбросить", callback_data="level_up_reset")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
