import logging
import json
import random
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Make sure to import your Character class correctly
from models.character import Character  # Adjust the path as per your project structure

from keyboards.combat_kb import combat_keyboard, ability_selection_keyboard, inventory_keyboard
from keyboards.main_kb import main_menu_keyboard
from utils.combat_logic import calculate_damage, is_critical_hit, is_evaded, get_hp_bar
from utils.effect_processor import process_effects, get_effects_str, apply_effect
from utils.loot import get_loot
from utils.enemy_ai import get_enemy_action

class CombatState(StatesGroup):
    in_combat = State()
    ability_choice = State()
    inventory_choice = State()

# Define base path for data files
BASE_DATA_PATH = Path(__file__).parent.parent / 'data'

with open(BASE_DATA_PATH / 'enemies.json', 'r', encoding='utf-8') as f:
    ENEMIES_DATA = json.load(f)

with open(BASE_DATA_PATH / 'items.json', 'r', encoding='utf-8') as f:
    ITEMS_DATA = json.load(f)

with open(BASE_DATA_PATH / 'abilities.json', 'r', encoding='utf-8') as f:
    ABILITIES_DATA = json.load(f)

router = Router()

# --- Helper function for consistent inventory handling ---
def get_inventory_items(character: Character):
    """Return a list of item dicts from character inventory."""
    inventory = character.inventory or []
    items = []
    for item_id in inventory:
        item = ITEMS_DATA.get(item_id)
        if item:
            items.append(item)
    return items

async def start_combat(message: Message, state: FSMContext, character: Character, enemy_id: str):
    """Initialize combat with proper error handling."""
    if enemy_id not in ENEMIES_DATA:
        await message.answer("❌ <b>Ошибка:</b> враг не найден!", reply_markup=main_menu_keyboard())
        return

    enemy_data = ENEMIES_DATA[enemy_id]
    combat_data = {
        "player_hp": character.stats['hp'],
        "player_max_hp": character.stats['max_hp'],
        "player_mana": character.current_mana,
        "player_max_mana": character.stats['max_mana'],
        "enemy_hp": enemy_data['hp'],
        "enemy_max_hp": enemy_data['hp'],
        "enemy_id": enemy_id,
        "round": 1,
        "player_effects": [],
        "enemy_effects": [],
        "player_defending": False
    }

    # Initialize default inventory if missing
    if not character.inventory:
        character.inventory = [
            "small_healing_potion",
            "poison_bomb"
        ]

    await state.set_state(CombatState.in_combat)
    await state.update_data(character=character, combat_data=combat_data)

    # Enhanced combat start message
    initial_message = get_combat_status_message(character, enemy_data, combat_data)
    enemy_type_emoji = {"weak": "🐸", "normal": "🐺", "elite": "🦁", "boss": "🐉"}.get(enemy_data.get('type', 'normal'), "👹")

    await message.answer(
        f"⚔️ <b>БОЕВОЙ РЕЖИМ</b> ⚔️\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"{enemy_type_emoji} <b>Противник:</b> {enemy_data['name']}\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"{initial_message}", 
        reply_markup=combat_keyboard()
    )

def get_combat_status_message(character: Character, enemy_data, combat_data) -> str:
    """Generate enhanced combat status display."""
    char_hp_bar = get_hp_bar(combat_data['player_hp'], combat_data['player_max_hp'])
    enemy_hp_bar = get_hp_bar(combat_data['enemy_hp'], combat_data['enemy_max_hp'])

    char_effects_str = get_effects_str(combat_data['player_effects'])
    enemy_effects_str = get_effects_str(combat_data['enemy_effects'])

    status = (f"🛡️ <b>{character.name}</b>\n"
              f"❤️ {char_hp_bar} <code>{combat_data['player_hp']}/{combat_data['player_max_hp']}</code>\n"
              f"✨ {get_hp_bar(character.current_mana, character.stats['max_mana'], bar_char='💙')} <code>{character.current_mana}/{character.stats['max_mana']}</code>\n"
             )

    if char_effects_str:
        status += f"🔮 {char_effects_str}\n"

    status += f"\n🆚\n\n"

    status += (
        f"👹 <b>{enemy_data['name']}</b>\n"
        f"💀 {enemy_hp_bar} <code>{combat_data['enemy_hp']}/{combat_data['enemy_max_hp']}</code>\n"
    )

    if enemy_effects_str:
        status += f"🔮 {enemy_effects_str}\n"

    status += f"\n⏱️ <b>Раунд:</b> {combat_data['round']}"

    return status

async def end_combat_victory(callback: CallbackQuery, state: FSMContext, character: Character, enemy):
    """Handle victory with enhanced message design."""
    await state.clear()

    try:
        loot_result = await get_loot(character.stats.get('luck', 0), enemy['type'])

        # Update character data
        character.exp += loot_result['xp']
        character.gold += loot_result['gold']
        character.stats['hp'] = character.stats['max_hp']
        character.current_mana = character.stats['max_mana'] # Restore mana after combat

        if not character.inventory:
            character.inventory = []

        for item in loot_result['items']:
            character.inventory.append(item['item_id'])

        # Check for level up
        from utils.level_system import grant_exp
        character, leveled_up = grant_exp(character)

        # Save character
        from utils.database import save_character
        await save_character(character)

        rarity_colors = {
            "common": "⚪", "uncommon": "🟢", "rare": "🔵", 
            "epic": "🟣", "legendary": "🟠"
        }

        loot_items_str = ""
        if loot_result['items']:
            for item in loot_result['items']:
                rarity_icon = rarity_colors.get(item['rarity'], '⚪')
                loot_items_str += f"  {rarity_icon} <b>{item['name']}</b>\n"

        level_up_message = ""
        if leveled_up:
            level_up_message = (
                f"🎉 <b>ПОЗДРАВЛЯЕМ!</b> 🎉\n"
                f"🆙 Уровень повышен до <b>{character.level}</b>!\n"
                f"⭐ +5 очков характеристик\n"
                f"━━━━━━━━━━━━━━━━━━━\n\n"
            )

        victory_message = (
            f"🏆 <b>ПОБЕДА!</b> 🏆\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"💀 Побежден: <b>{enemy['name']}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
            f"{level_up_message}"
            f"💎 <b>Награды:</b>\n"
            f"  📈 <b>+{loot_result['xp']}</b> опыта\n"
            f"  💰 <b>+{loot_result['gold']}</b> золота\n\n"
            f"🎁 <b>Добыча:</b>\n"
            f"{loot_items_str if loot_items_str else '  🚫 Ничего не найдено'}\n"
            f"━━━━━━━━━━━━━━━━━━━"
        )

        await callback.message.edit_text(victory_message, reply_markup=main_menu_keyboard())

    except Exception as e:
        logging.error(f"Error in end_combat_victory: {e}")
        await callback.message.edit_text(
            "🏆 <b>ПОБЕДА!</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "❌ Ошибка при обработке награды", 
            reply_markup=main_menu_keyboard()
        )

async def end_combat_defeat(callback: CallbackQuery, state: FSMContext, character: Character):
    """Handle defeat with enhanced message design."""
    await state.clear()

    try:
        gold_loss = int(character.gold * 0.10)
        character.gold = max(0, character.gold - gold_loss)
        character.stats['hp'] = 1
        character.current_mana = character.stats['max_mana'] # Restore mana after defeat

        # Save character
        from utils.database import save_character
        await save_character(character)

        defeat_message = (
            f"💀 <b>ПОРАЖЕНИЕ...</b> 💀\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"⚰️ Вы потерпели поражение\n"
            f"💸 Потеряно: <b>{gold_loss}</b> золота\n"
            f"🏠 Возвращение в лагерь...\n"
            f"━━━━━━━━━━━━━━━━━━━"
        )
        await callback.message.edit_text(defeat_message, reply_markup=main_menu_keyboard())

    except Exception as e:
        logging.error(f"Error in end_combat_defeat: {e}")
        await callback.message.edit_text(
            "💀 <b>ПОРАЖЕНИЕ!</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "🏠 Возвращение в лагерь...", 
            reply_markup=main_menu_keyboard()
        )

def format_turn_log(turn_log: list) -> str:
    """Format turn log with enhanced visual design."""
    if not turn_log:
        return ""

    formatted_log = "📝 <b>Ход боя:</b>\n" + "─" * 15 + "\n"

    for i, action in enumerate(turn_log, 1):
        formatted_log += f"{i}. {action}\n"

    return formatted_log + "─" * 15 + "\n"

async def process_combat_turn(callback: CallbackQuery, state: FSMContext, player_action: dict):
    """Process combat turn with enhanced message formatting."""
    try:
        data = await state.get_data()
        character: Character = data.get('character')
        combat_data = data.get('combat_data')

        if not character or not combat_data:
            await callback.message.edit_text(
                "❌ <b>Ошибка:</b> данные боя не найдены",
                reply_markup=main_menu_keyboard()
            )
            return [], "Ошибка данных боя."

        enemy = ENEMIES_DATA.get(combat_data['enemy_id'])
        if not enemy:
            await callback.message.edit_text(
                "❌ <b>Ошибка:</b> враг не найден",
                reply_markup=main_menu_keyboard()
            )
            return [], "Ошибка данных врага."

        turn_log = []

        # Process effects at start of turn
        player_effects_summary = process_effects(character.stats, combat_data['player_effects'])
        combat_data['player_hp'] -= player_effects_summary['damage']
        combat_data['player_hp'] = min(
            combat_data['player_max_hp'], 
            combat_data['player_hp'] + player_effects_summary['heal']
        )

        enemy_effects_summary = process_effects(enemy, combat_data['enemy_effects'])
        combat_data['enemy_hp'] -= enemy_effects_summary['damage']
        combat_data['enemy_hp'] = min(
            combat_data['enemy_max_hp'], 
            combat_data['enemy_hp'] + enemy_effects_summary['heal']
        )

        turn_log.extend(player_effects_summary['messages'])
        turn_log.extend(enemy_effects_summary['messages'])

        # Reset defending status
        combat_data['player_defending'] = False

        # Process player action
        if player_action['action'] != 'enemy_turn_only':
            if player_effects_summary.get('skip_turn', False):
                turn_log.append("🚫 Вы пропускаете ход из-за эффекта!")
            else:
                await process_player_action(player_action, character, combat_data, enemy, turn_log)

        # Check if enemy is defeated
        if combat_data['enemy_hp'] <= 0:
            await end_combat_victory(callback, state, character, enemy)
            return [], "Победа!"

        # Process enemy turn
        if not enemy_effects_summary.get('skip_turn', False):
            await process_enemy_action(enemy, combat_data, character, turn_log)

        # Check if player is defeated
        if combat_data['player_hp'] <= 0:
            await end_combat_defeat(callback, state, character)
            return [], "Поражение..."

        # Increment round and update state
        combat_data['round'] += 1
        await state.update_data(character=character, combat_data=combat_data)

        status_message = get_combat_status_message(character, enemy, combat_data)
        return turn_log, status_message

    except Exception as e:
        logging.error(f"Error in process_combat_turn: {e}")
        await callback.message.edit_text(
            "❌ <b>Ошибка в бою</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "🔄 Попробуйте еще раз", 
            reply_markup=main_menu_keyboard()
        )
        return [], "Ошибка обработки хода."

async def process_player_action(player_action: dict, character: Character, combat_data: dict, enemy: dict, turn_log: list):
    """Process player's action with enhanced feedback."""
    action = player_action['action']

    if action == 'attack':
        if not is_evaded(enemy.get('luck', 0)):
            is_crit = is_critical_hit(character.stats.get('luck', 0))
            player_damage = calculate_damage(character.stats['attack'], enemy['defense'], is_crit=is_crit)
            combat_data['enemy_hp'] -= player_damage

            if is_crit:
                turn_log.append(f"💥 <b>КРИТИЧЕСКИЙ УДАР!</b> Нанесено <b>{player_damage}</b> урона!")
            else:
                turn_log.append(f"⚔️ Обычная атака • Урон: <b>{player_damage}</b>")
        else:
            turn_log.append(f"💨 {enemy['name']} ловко уклонился!")

    elif action == 'defend':
        combat_data['player_defending'] = True
        turn_log.append("🛡️ Защитная стойка принята!")

    elif action == 'use_ability':
        ability_name = player_action['ability_name']
        ability_details = next((ab for ab in ABILITIES_DATA if ab['name'] == ability_name), None)
        if ability_details:
            mana_cost = ability_details.get('mana_cost', 0)
            if character.current_mana < mana_cost:
                turn_log.append(f"❌ Недостаточно маны для использования {ability_details.get('display_name', ability_name)} (требуется {mana_cost})!")
                return

            character.current_mana -= mana_cost
            turn_log.append(f"✨ Использовано {mana_cost} маны.")

            if ability_name == "fireball":
                damage = ability_details['damage']
                combat_data['enemy_hp'] -= damage
                turn_log.append(f"🔥 <b>Огненный шар!</b> Урон: <b>{damage}</b>")
            elif ability_name == "heal":
                heal_amount = ability_details['heal_amount']
                combat_data['player_hp'] = min(
                    combat_data['player_max_hp'],
                    combat_data['player_hp'] + heal_amount,
                )
                turn_log.append(f"✨ <b>Лечение:</b> +<b>{heal_amount}</b> HP")
        else:
            turn_log.append(f"❌ Неизвестная способность: {ability_name}")

    elif action == 'use_item':
        item_name = player_action['item_name']
        inventory_items = get_inventory_items(character)
        item_details = next((it for it in inventory_items if it['name'] == item_name), None)
        if item_details:
            if item_details['item_id'] in character.inventory:
                character.inventory.remove(item_details['item_id'])
            if item_name == "small_healing_potion":
                heal_amount = item_details['heal_amount']
                combat_data['player_hp'] = min(
                    combat_data['player_max_hp'],
                    combat_data['player_hp'] + heal_amount,
                )
                turn_log.append(f"🧪 <b>Зелье лечения:</b> +<b>{heal_amount}</b> HP")
            elif item_name == "poison_bomb":
                apply_effect(combat_data['enemy_effects'], item_details['effect'])
                turn_log.append(f"💣 <b>Ядовитая бомба!</b> {enemy['name']} отравлен!")
        else:
            turn_log.append(f"❌ Неизвестный предмет: {item_name}")

async def process_enemy_action(enemy: dict, combat_data: dict, character: Character, turn_log: list):
    """Process enemy's action with enhanced feedback."""
    enemy_move = get_enemy_action(enemy, combat_data)

    if enemy_move['action'] == "attack":
        if not is_evaded(character.stats.get('luck', 0)):
            is_crit = is_critical_hit(enemy.get('luck', 0))
            enemy_damage = calculate_damage(
                enemy['attack'],
                character.stats['defense'],
                is_crit=is_crit,
                is_defending=combat_data.get('player_defending', False),
            )
            combat_data['player_hp'] -= enemy_damage

            if is_crit:
                turn_log.append(f"💥 <b>{enemy['name']}</b> наносит критический удар! Урон: <b>{enemy_damage}</b>")
            else:
                turn_log.append(f"⚔️ <b>{enemy['name']}</b> атакует • Урон: <b>{enemy_damage}</b>")
        else:
            turn_log.append("💨 Вы ловко уклонились от атаки!")

    elif enemy_move['action'] == "use_ability":
        ability_name = enemy_move['ability_name']
        heal_ability = enemy.get('abilities', {}).get('heal')

        if ability_name == "heal" and heal_ability:
            heal_amount = heal_ability.get('heal_amount', 0)
            combat_data['enemy_hp'] = min(
                combat_data['enemy_max_hp'], 
                combat_data['enemy_hp'] + heal_amount
            )
            turn_log.append(f"✨ <b>{enemy['name']}</b> исцеляется! +<b>{heal_amount}</b> HP")
        else:
            apply_effect(combat_data['player_effects'], ability_name)
            turn_log.append(f"🔮 <b>{enemy['name']}</b> использует <b>{ability_name}</b>!")

# Combat action handlers with enhanced messages
@router.callback_query(CombatState.in_combat, F.data == 'combat:attack')
async def combat_attack(callback: CallbackQuery, state: FSMContext):
    logging.info(f"Combat: Attack button pressed by user {callback.from_user.id}")
    await callback.answer("⚔️ Атака!")

    turn_log, status_message = await process_combat_turn(callback, state, {"action": "attack"})
    if status_message not in ["Победа!", "Поражение..."]:
        formatted_log = format_turn_log(turn_log)
        full_message = formatted_log + "\n" + status_message
        await callback.message.edit_text(full_message, reply_markup=combat_keyboard())

@router.callback_query(CombatState.in_combat, F.data == 'combat:defend')
async def combat_defend(callback: CallbackQuery, state: FSMContext):
    logging.info(f"Combat: Defend button pressed by user {callback.from_user.id}")
    await callback.answer("🛡️ Защита!")

    turn_log, status_message = await process_combat_turn(callback, state, {"action": "defend"})
    if status_message not in ["Победа!", "Поражение..."]:
        formatted_log = format_turn_log(turn_log)
        full_message = formatted_log + "\n" + status_message
        await callback.message.edit_text(full_message, reply_markup=combat_keyboard())

@router.callback_query(CombatState.in_combat, F.data == 'combat:run')
async def combat_run(callback: CallbackQuery, state: FSMContext):
    logging.info(f"Combat: Run button pressed by user {callback.from_user.id}")

    try:
        data = await state.get_data()
        enemy = ENEMIES_DATA[data['combat_data']['enemy_id']]

        run_chance = {'weak': 100, 'normal': 50, 'elite': 0, 'boss': 0}
        chance = random.uniform(0, 100)

        if chance < run_chance.get(enemy['type'], 50):
            await state.clear()
            await callback.message.edit_text(
                "🏃 <b>ПОБЕГ УДАЛСЯ!</b>\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "💨 Вы успешно скрылись!\n"
                "🏠 Возвращение в безопасное место...",
                reply_markup=main_menu_keyboard()
            )
            await callback.answer("💨 Побег!")
        else:
            turn_log, status_message = await process_combat_turn(callback, state, {"action": "enemy_turn_only"})
            if status_message not in ["Победа!", "Поражение..."]:
                formatted_log = format_turn_log(["🚫 Побег не удался!"] + turn_log)
                full_message = formatted_log + "\n" + status_message
                await callback.message.edit_text(full_message, reply_markup=combat_keyboard())
            await callback.answer("🚫 Побег не удался!", show_alert=True)

    except Exception as e:
        logging.error(f"Error in combat_run: {e}")
        await callback.answer("❌ Ошибка при попытке бегства!", show_alert=True)

@router.callback_query(CombatState.in_combat, F.data == 'combat:ability')
async def select_ability(callback: CallbackQuery, state: FSMContext):
    logging.info(f"Combat: Ability button pressed by user {callback.from_user.id}")

    data = await state.get_data()
    character: Character = data['character']
    abilities = ABILITIES_DATA

    if not abilities:
        await callback.answer("🚫 У вас нет способностей!", show_alert=True)
        return

    await state.set_state(CombatState.ability_choice)
    await callback.message.edit_text(
        "🔮 <b>СПОСОБНОСТИ</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "Выберите способность для использования:",
        reply_markup=ability_selection_keyboard(abilities)
    )
    await callback.answer("🔮 Способности")

@router.callback_query(CombatState.ability_choice, F.data.startswith('combat:use_ability:'))
async def use_ability(callback: CallbackQuery, state: FSMContext):
    logging.info(f"Combat: Use ability button pressed by user {callback.from_user.id}")

    ability_name = callback.data.split(':')[-1]
    await state.set_state(CombatState.in_combat)
    await callback.answer("✨ Способность активирована!")

    turn_log, status_message = await process_combat_turn(
        callback, state, {"action": "use_ability", "ability_name": ability_name}
    )
    if status_message not in ["Победа!", "Поражение..."]:
        formatted_log = format_turn_log(turn_log)
        full_message = formatted_log + "\n" + status_message
        await callback.message.edit_text(full_message, reply_markup=combat_keyboard())

@router.callback_query(CombatState.ability_choice, F.data == 'combat:back_to_main')
async def back_to_combat_main(callback: CallbackQuery, state: FSMContext):
    logging.info(f"Combat: Back to main (from ability) button pressed by user {callback.from_user.id}")

    await state.set_state(CombatState.in_combat)
    data = await state.get_data()
    character: Character = data['character']
    combat_data = data['combat_data']
    enemy = ENEMIES_DATA[combat_data['enemy_id']]

    status_message = get_combat_status_message(character, enemy, combat_data)
    await callback.message.edit_text(status_message, reply_markup=combat_keyboard())
    await callback.answer("🔙 Назад к бою")

@router.callback_query(CombatState.in_combat, F.data == 'combat:inventory')
async def select_item(callback: CallbackQuery, state: FSMContext):
    logging.info(f"Combat: Inventory button pressed by user {callback.from_user.id}")

    data = await state.get_data()
    character: Character = data['character']
    items = get_inventory_items(character)

    if not items:
        await callback.answer("🚫 Ваш инвентарь пуст!", show_alert=True)
        return

    await state.set_state(CombatState.inventory_choice)
    await callback.message.edit_text(
        "🎒 <b>ИНВЕНТАРЬ</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "Выберите предмет для использования:",
        reply_markup=inventory_keyboard(items)
    )
    await callback.answer("🎒 Инвентарь")

@router.callback_query(CombatState.inventory_choice, F.data.startswith('combat:use_item:'))
async def use_item(callback: CallbackQuery, state: FSMContext):
    logging.info(f"Combat: Use item button pressed by user {callback.from_user.id}")

    item_name = callback.data.split(':')[-1]
    await state.set_state(CombatState.in_combat)
    await callback.answer("📦 Предмет использован!")

    turn_log, status_message = await process_combat_turn(
        callback, state, {"action": "use_item", "item_name": item_name}
    )
    if status_message not in ["Победа!", "Поражение..."]:
        formatted_log = format_turn_log(turn_log)
        full_message = formatted_log + "\n" + status_message
        await callback.message.edit_text(full_message, reply_markup=combat_keyboard())

@router.callback_query(CombatState.inventory_choice, F.data == 'combat:back_to_main')
async def back_to_combat_main_from_inventory(callback: CallbackQuery, state: FSMContext):
    logging.info(f"Combat: Back to main (from inventory) button pressed by user {callback.from_user.id}")

    await state.set_state(CombatState.in_combat)
    data = await state.get_data()
    character: Character = data['character']
    combat_data = data['combat_data']
    enemy = ENEMIES_DATA[combat_data['enemy_id']]

    status_message = get_combat_status_message(character, enemy, combat_data)
    await callback.message.edit_text(status_message, reply_markup=combat_keyboard())
    await callback.answer("🔙 Назад к бою")
