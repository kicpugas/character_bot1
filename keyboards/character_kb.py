from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton



def generate_race_selection_keyboard(races, current_page=0, items_per_page=4):
    keyboard = []
    start_index = current_page * items_per_page
    end_index = start_index + items_per_page
    
    for i in range(start_index, min(end_index, len(races))):
        race_id = list(races.keys())[i]
        race_name = races[race_id]["name"]
        keyboard.append([InlineKeyboardButton(text=race_name, callback_data=f"select_race_{race_id}")])

    navigation_row = []
    if current_page > 0:
        navigation_row.append(InlineKeyboardButton(text="🔙 Назад", callback_data=f"races_page_{current_page - 1}"))
    if end_index < len(races):
        navigation_row.append(InlineKeyboardButton(text="📄 След. страница", callback_data=f"races_page_{current_page + 1}"))
    if navigation_row:
        keyboard.append(navigation_row)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def generate_class_selection_keyboard(classes, current_page=0, items_per_page=4):
    keyboard = []
    start_index = current_page * items_per_page
    end_index = start_index + items_per_page
    
    for i in range(start_index, min(end_index, len(classes))):
        class_id = list(classes.keys())[i]
        class_name = classes[class_id]["name"]
        keyboard.append([InlineKeyboardButton(text=class_name, callback_data=f"select_class_{class_id}")])

    navigation_row = []
    if current_page > 0:
        navigation_row.append(InlineKeyboardButton(text="🔙 Назад", callback_data=f"classes_page_{current_page - 1}"))
    if end_index < len(classes):
        navigation_row.append(InlineKeyboardButton(text="📄 След. страница", callback_data=f"classes_page_{current_page + 1}"))
    if navigation_row:
        keyboard.append(navigation_row)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def confirm_selection_keyboard(item_type: str, item_id: str, back_list_text: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"✅ Выбрать {item_type.capitalize()}", callback_data=f"confirm_{'race' if item_type == 'расу' else 'class'}_{item_id}")],
        [InlineKeyboardButton(text=f"🔙 Назад к списку {back_list_text}", callback_data=f"back_to_{'races' if item_type == 'расу' else 'classes'}_list")]
    ])

def final_confirmation_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить создание", callback_data="confirm_character_creation")],
        [InlineKeyboardButton(text="❌ Отменить и начать заново", callback_data="cancel_character_creation")]
    ])