"""
🤖 ТЕЛЕГРАМ БОТ С ГЛАВНЫМ АДМИНИСТРАТОРОМ
Исправленная версия: 
1. Убрана кнопка "Мой ID" для главного админа
2. Исправлена отправка тестовых заявок
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ========== НАСТРОЙКИ ==========
TOKEN = "8305687625:AAHFu4mrz_lA-Lor8hHfaZo20-_QeI3qxbU"

# ⚠️ ВАЖНО: ЗАМЕНИТЕ ЭТОТ ID НА ВАШ РЕАЛЬНЫЙ ID из Telegram!
# Как узнать свой ID: напишите боту /myid (команда добавлена ниже)
MAIN_ADMIN_ID = 1139442447  # ⬅️ ЗАМЕНИТЕ НА ВАШ ID!

# На Railway используем /tmp для данных
if 'RAILWAY_ENVIRONMENT' in os.environ:
    DATA_DIR = Path('/tmp/telegram_bot_data')
else:
    DATA_DIR = Path('data')

DATA_DIR.mkdir(exist_ok=True)
ADMINS_FILE = DATA_DIR / 'admins.json'

# ========== ЛОГИРОВАНИЕ ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========== СОЗДАЕМ БОТА ==========
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

# ========== ФУНКЦИИ ДЛЯ ДАННЫХ ==========
def load_admins():
    """Загружаем список администраторов"""
    try:
        if ADMINS_FILE.exists():
            with open(ADMINS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                admin_ids = data.get('admin_ids', [])
                logger.info(f"📊 Загружено {len(admin_ids)} администраторов")
                
                # Гарантируем, что главный админ всегда в списке
                admin_set = set(admin_ids)
                if MAIN_ADMIN_ID not in admin_set:
                    admin_set.add(MAIN_ADMIN_ID)
                    save_admins(admin_set)
                    logger.info(f"✅ Главный админ {MAIN_ADMIN_ID} добавлен в список")
                
                return admin_set
    except Exception as e:
        logger.error(f"Ошибка загрузки: {e}")
    
    # Если файла нет, создаем с главным админом
    initial_admins = {MAIN_ADMIN_ID}
    save_admins(initial_admins)
    return initial_admins

def save_admins(admin_ids):
    """Сохраняем список администраторов"""
    try:
        data = {
            'admin_ids': list(admin_ids),
            'updated': datetime.now().isoformat(),
            'total': len(admin_ids),
            'main_admin': MAIN_ADMIN_ID
        }
        
        with open(ADMINS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Сохранено {len(admin_ids)} администраторов")
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения: {e}")
        return False

def is_main_admin(user_id):
    """Проверяет, является ли пользователь главным админом"""
    return user_id == MAIN_ADMIN_ID

# ========== ОСНОВНЫЕ ФУНКЦИИ ==========
def send_to_admins(message_text, exclude_id=None):
    """
    Отправляет сообщение всем администраторам
    ФИКС: Теперь учитывает exclude_id правильно
    """
    admins = load_admins()
    sent_count = 0
    total_admins = len(admins)
    
    logger.info(f"📤 Начинаю отправку сообщения {len(admins)} админам, exclude: {exclude_id}")
    
    for admin_id in admins:
        # Проверяем, нужно ли пропустить этого админа
        should_skip = False
        if exclude_id:
            if isinstance(exclude_id, list):
                if admin_id in exclude_id:
                    should_skip = True
            elif admin_id == exclude_id:
                should_skip = True
        
        if should_skip:
            logger.info(f"  ⏭️ Пропускаем админа {admin_id} (exclude)")
            continue
            
        try:
            bot.send_message(admin_id, message_text, parse_mode='HTML')
            sent_count += 1
            logger.info(f"  ✅ Отправлено админу {admin_id}")
        except Exception as e:
            logger.error(f"  ❌ Ошибка отправки {admin_id}: {e}")
    
    logger.info(f"📊 Итог: отправлено {sent_count}/{total_admins}")
    return sent_count, total_admins

def get_admin_info(admin_id):
    """Получает информацию об админе по ID"""
    try:
        chat = bot.get_chat(admin_id)
        return {
            'id': admin_id,
            'first_name': chat.first_name or '',
            'last_name': chat.last_name or '',
            'username': chat.username or 'нет',
            'full_name': f"{chat.first_name or ''} {chat.last_name or ''}".strip()
        }
    except:
        return {
            'id': admin_id,
            'first_name': 'Неизвестно',
            'last_name': '',
            'username': 'нет',
            'full_name': f'Пользователь ID: {admin_id}'
        }

# ========== КОМАНДА /START ==========
@bot.message_handler(commands=['start'])
def start_command(message):
    """Обработка команды /start - ГЛАВНОЕ МЕНЮ"""
    try:
        user = message.from_user
        admins = load_admins()
        user_is_main_admin = is_main_admin(user.id)
        user_is_admin = user.id in admins
        
        logger.info(f"👤 {user.id} ({user.username}) запустил бота. Главный: {user_is_main_admin}, Админ: {user_is_admin}")
        
        if user_is_admin:
            if user_is_main_admin:
                # ========== ИНТЕРФЕЙС ДЛЯ ГЛАВНОГО АДМИНА ==========
                text = (f"👑 <b>ГЛАВНЫЙ АДМИНИСТРАТОР: {user.first_name}</b>\n\n"
                       f"Ваши права:\n"
                       f"• ✅ Получать заявки с сайта\n"
                       f"• 📋 Отправлять тестовые заявки\n"
                       f"• 👥 Видеть список всех администраторов\n"
                       f"• 🗑 Удалять ЛЮБЫХ администраторов\n\n"
                       f"📊 Всего администраторов: {len(admins)}")
                
                keyboard = InlineKeyboardMarkup()
                keyboard.row(
                    InlineKeyboardButton("📋 Тестовая заявка", callback_data='test'),
                    InlineKeyboardButton("👥 Список админов", callback_data='list_admins')
                )
                keyboard.row(
                    InlineKeyboardButton("🗑 Удалить админа", callback_data='remove_admin_menu')
                )
                # ⬆️ УБРАНА КНОПКА "МОЙ ID" ⬆️
            
            else:
                # ========== ИНТЕРФЕЙС ДЛЯ ОБЫЧНОГО АДМИНА ==========
                text = (f"✅ <b>АДМИНИСТРАТОР: {user.first_name}</b>\n\n"
                       f"Ваши права:\n"
                       f"• ✅ Получать заявки с сайта\n"
                       f"• 📋 Отправлять тестовые заявки\n\n"
                       f"📊 Всего администраторов: {len(admins)}\n"
                       f"👑 Главный админ управляет списком")
                
                keyboard = InlineKeyboardMarkup()
                keyboard.row(
                    InlineKeyboardButton("📋 Тестовая заявка", callback_data='test'),
                    InlineKeyboardButton("🆔 Мой ID", callback_data='myid')
                )
        
        else:
            # ========== ИНТЕРФЕЙС ДЛЯ НЕ-АДМИНА ==========
            text = (f"👋 <b>{user.first_name}</b>, добро пожаловать!\n\n"
                   f"Вы не в списке администраторов.\n\n"
                   f"<b>Чтобы начать получать заявки с сайта:</b>\n"
                   f"1. Нажмите кнопку ниже\n"
                   f"2. Главный администратор получит уведомление\n"
                   f"3. После одобрения вы будете получать все заявки\n\n"
                   f"📊 Сейчас администраторов: {len(admins)}")
            
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("✅ ДОБАВИТЬ СЕБЯ В АДМИНИСТРАТОРЫ", callback_data='add'))
        
        bot.send_message(message.chat.id, text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Ошибка в start_command: {e}")
        bot.send_message(message.chat.id, "⚠️ Произошла ошибка. Попробуйте еще раз.")

# ========== КОМАНДА ДЛЯ ПОЛУЧЕНИЯ СВОЕГО ID ==========
@bot.message_handler(commands=['myid'])
def myid_command(message):
    """Показывает ID пользователя (для настройки главного админа)"""
    user = message.from_user
    bot.reply_to(
        message,
        f"🆔 <b>Ваш ID Telegram:</b>\n<code>{user.id}</code>\n\n"
        f"📝 <b>Имя:</b> {user.first_name}\n"
        f"👤 <b>Username:</b> @{user.username or 'нет'}",
        parse_mode='HTML'
    )

# ========== ОБРАБОТЧИК КНОПОК ==========
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """Обработка нажатий на кнопки"""
    try:
        user = call.from_user
        user_is_main_admin = is_main_admin(user.id)
        admins = load_admins()
        user_is_admin = user.id in admins
        
        logger.info(f"🔘 {user.id} нажал: {call.data}. Главный: {user_is_main_admin}")
        
        bot.answer_callback_query(call.id)
        
        # ========== ДОБАВЛЕНИЕ В АДМИНЫ ==========
        if call.data == 'add':
            if not user_is_admin:
                admins.add(user.id)
                save_admins(admins)
                
                # Уведомляем главного админа о новом пользователе
                try:
                    bot.send_message(
                        MAIN_ADMIN_ID,
                        f"👤 <b>НОВЫЙ ЗАПРОС НА ДОБАВЛЕНИЕ</b>\n\n"
                        f"<b>Пользователь:</b>\n"
                        f"Имя: {user.full_name}\n"
                        f"Username: @{user.username or 'нет'}\n"
                        f"ID: <code>{user.id}</code>\n\n"
                        f"<b>Автоматически добавлен в список администраторов.</b>\n\n"
                        f"📊 Теперь администраторов: {len(admins)}\n\n"
                        f"Чтобы удалить, используйте кнопку '🗑 Удалить админа'",
                        parse_mode='HTML'
                    )
                except Exception as e:
                    logger.error(f"Не удалось уведомить главного админа: {e}")
                
                # Обновляем интерфейс для нового админа
                keyboard = InlineKeyboardMarkup()
                keyboard.row(
                    InlineKeyboardButton("📋 Тестовая заявка", callback_data='test'),
                    InlineKeyboardButton("🆔 Мой ID", callback_data='myid')
                )
                
                text = (f"✅ <b>{user.first_name}, вы добавлены в список администраторов!</b>\n\n"
                       f"Теперь вы будете получать <b>все заявки с сайта</b>.\n\n"
                       f"<b>Ваши права:</b>\n"
                       f"• ✅ Получать заявки с сайта\n"
                       f"• 📋 Отправлять тестовые заявки\n\n"
                       f"📊 <b>Всего администраторов:</b> {len(admins)}\n\n"
                       f"👑 Главный администратор получил уведомление.")
                
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            else:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="✅ Вы уже в списке администраторов!"
                )
        
        # ========== ТЕСТОВАЯ ЗАЯВКА (ДЛЯ ВСЕХ АДМИНОВ) ==========
        elif call.data == 'test':
            if user_is_admin:
                time_now = datetime.now().strftime("%H:%M:%S")
                date_now = datetime.now().strftime("%d.%m.%Y")
                
                # ФИКС: Отправляем всем админам, включая отправителя!
                # Но сообщение "заявка отправлена" должно учитывать, что себе не отправляем
                message_text = (
                    f"📋 <b>ТЕСТОВАЯ ЗАЯВКА С САЙТА</b>\n\n"
                    f"👤 <b>ФИО:</b> {user.full_name} (тест)\n"
                    f"📞 <b>Телефон:</b> +7 (999) 999-99-99\n"
                    f"💬 <b>Комментарий:</b> Тестовая заявка для проверки работы бота\n"
                    f"📅 <b>Дата:</b> {date_now}\n"
                    f"⏰ <b>Время:</b> {time_now}\n"
                    f"🔧 <b>Тип:</b> Тестовое уведомление"
                )
                
                # Отправляем всем админам (включая отправителя)
                sent_count = 0
                total_admins = len(admins)
                
                for admin_id in admins:
                    try:
                        bot.send_message(admin_id, message_text, parse_mode='HTML')
                        sent_count += 1
                        logger.info(f"✅ Тест отправлен админу {admin_id}")
                    except Exception as e:
                        logger.error(f"❌ Ошибка отправки {admin_id}: {e}")
                
                # Для отправителя показываем, сколько другим админам отправилось
                # (не считая себя, если он сам получил сообщение)
                others_count = sent_count
                if user.id in admins:
                    others_count = max(0, sent_count - 1)  # Вычитаем себя
                
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=f"✅ Тестовая заявка отправлена!\n\n"
                         f"📊 <b>Статистика:</b>\n"
                         f"• Вы получили тестовое уведомление\n"
                         f"• Отправлено другим админам: {others_count} из {total_admins - 1}",
                    parse_mode='HTML'
                )
            else:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="❌ Только администраторы могут отправлять тестовые заявки!"
                )
        
        # ========== СПИСОК АДМИНОВ (ТОЛЬКО ДЛЯ ГЛАВНОГО) ==========
        elif call.data == 'list_admins':
            if user_is_main_admin:
                admins_list = load_admins()
                
                if not admins_list:
                    text = "📭 <b>Список администраторов пуст.</b>"
                else:
                    text = "👥 <b>СПИСОК АДМИНИСТРАТОРОВ</b>\n\n"
                    
                    for idx, admin_id in enumerate(sorted(admins_list), 1):
                        info = get_admin_info(admin_id)
                        
                        if admin_id == MAIN_ADMIN_ID:
                            role = "👑 ГЛАВНЫЙ"
                        else:
                            role = "✅ Админ"
                        
                        text += (f"{idx}. <b>{info['full_name']}</b>\n"
                                f"   👤 @{info['username']}\n"
                                f"   🆔 <code>{admin_id}</code>\n"
                                f"   {role}\n\n")
                    
                    text += f"📊 <b>Всего: {len(admins_list)} администраторов</b>"
                
                # Кнопка возврата
                keyboard = InlineKeyboardMarkup()
                keyboard.row(
                    InlineKeyboardButton("📋 Тестовая заявка", callback_data='test'),
                    InlineKeyboardButton("🗑 Удалить админа", callback_data='remove_admin_menu')
                )
                keyboard.row(InlineKeyboardButton("🔙 Назад", callback_data='back_to_main'))
                
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            else:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="❌ Только главный администратор может просматривать список!"
                )
        
        # ========== МЕНЮ УДАЛЕНИЯ АДМИНА (ТОЛЬКО ДЛЯ ГЛАВНОГО) ==========
        elif call.data == 'remove_admin_menu':
            if user_is_main_admin:
                admins_list = load_admins()
                
                # Фильтруем - нельзя удалить самого себя (главного админа)
                admins_to_remove = [aid for aid in admins_list if aid != MAIN_ADMIN_ID]
                
                if not admins_to_remove:
                    text = "📭 <b>Нет администраторов для удаления.</b>\n\nВы единственный администратор."
                else:
                    text = "🗑 <b>ВЫБЕРИТЕ АДМИНИСТРАТОРА ДЛЯ УДАЛЕНИЯ</b>\n\n"
                    
                    for idx, admin_id in enumerate(admins_to_remove, 1):
                        info = get_admin_info(admin_id)
                        text += f"{idx}. <b>{info['full_name']}</b> (<code>{admin_id}</code>)\n"
                
                # Создаем клавиатуру с кнопками для удаления
                keyboard = InlineKeyboardMarkup()
                
                for admin_id in admins_to_remove:
                    info = get_admin_info(admin_id)
                    btn_text = f"🗑 {info['first_name']} (ID: {admin_id})"
                    keyboard.add(InlineKeyboardButton(btn_text, callback_data=f'remove_{admin_id}'))
                
                # Кнопка возврата
                keyboard.row(
                    InlineKeyboardButton("👥 Список админов", callback_data='list_admins'),
                    InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')
                )
                
                if not admins_to_remove:
                    keyboard = InlineKeyboardMarkup()
                    keyboard.row(InlineKeyboardButton("🔙 Назад", callback_data='back_to_main'))
                
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            else:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="❌ Только главный администратор может удалять администраторов!"
                )
        
        # ========== УДАЛЕНИЕ КОНКРЕТНОГО АДМИНА ==========
        elif call.data.startswith('remove_'):
            if user_is_main_admin:
                try:
                    # Извлекаем ID из callback_data: remove_123456789
                    admin_id_to_remove = int(call.data.replace('remove_', ''))
                    
                    # Проверяем, что это не главный админ
                    if admin_id_to_remove == MAIN_ADMIN_ID:
                        bot.edit_message_text(
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            text="❌ Нельзя удалить главного администратора!"
                        )
                        return
                    
                    admins_list = load_admins()
                    
                    if admin_id_to_remove in admins_list:
                        # Удаляем из списка
                        admins_list.remove(admin_id_to_remove)
                        save_admins(admins_list)
                        
                        # Получаем инфо об удаленном пользователе
                        removed_info = get_admin_info(admin_id_to_remove)
                        
                        # Уведомляем удаленного пользователя
                        try:
                            bot.send_message(
                                admin_id_to_remove,
                                f"❌ <b>ВЫ УДАЛЕНЫ ИЗ СПИСКА АДМИНИСТРАТОРОВ</b>\n\n"
                                f"Главный администратор удалил вас из списка.\n"
                                f"Вы больше не будете получать заявки с сайта.\n\n"
                                f"Чтобы вернуться, снова нажмите 'Добавить себя' в боте.",
                                parse_mode='HTML'
                            )
                        except:
                            pass  # Не критично, если не удалось уведомить
                        
                        # Обновляем интерфейс главного админа
                        keyboard = InlineKeyboardMarkup()
                        keyboard.row(
                            InlineKeyboardButton("👥 Список админов", callback_data='list_admins'),
                            InlineKeyboardButton("🗑 Удалить еще", callback_data='remove_admin_menu')
                        )
                        keyboard.row(InlineKeyboardButton("🔙 Назад", callback_data='back_to_main'))
                        
                        bot.edit_message_text(
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            text=f"✅ <b>Администратор удален!</b>\n\n"
                                 f"👤 Имя: {removed_info['full_name']}\n"
                                 f"🆔 ID: <code>{admin_id_to_remove}</code>\n\n"
                                 f"📊 Осталось администраторов: {len(admins_list)}",
                            reply_markup=keyboard,
                            parse_mode='HTML'
                        )
                    else:
                        bot.edit_message_text(
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            text="❌ Этот пользователь не является администратором."
                        )
                        
                except ValueError:
                    bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text="❌ Ошибка при обработке запроса."
                    )
            else:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="❌ Только главный администратор может удалять администраторов!"
                )
        
        # ========== ПОКАЗАТЬ СВОЙ ID (ТОЛЬКО ДЛЯ ОБЫЧНЫХ АДМИНОВ) ==========
        elif call.data == 'myid':
            # Проверяем, что это НЕ главный админ
            if not user_is_main_admin:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=f"🆔 <b>Ваш ID Telegram:</b>\n<code>{user.id}</code>\n\n"
                         f"📝 <b>Имя:</b> {user.first_name}\n"
                         f"👤 <b>Username:</b> @{user.username or 'нет'}\n\n"
                         f"Сохраните этот ID для настройки.",
                    parse_mode='HTML'
                )
            else:
                # Главный админ не должен видеть эту кнопку, но если нажал случайно:
                bot.answer_callback_query(call.id, "👑 Вы главный администратор!", show_alert=True)
        
        # ========== ВОЗВРАТ В ГЛАВНОЕ МЕНЮ ==========
        elif call.data == 'back_to_main':
            # Просто вызываем команду /start заново
            class FakeMessage:
                def __init__(self, user, chat_id):
                    self.from_user = user
                    self.chat = type('Chat', (), {'id': chat_id})()
                    self.message_id = call.message.message_id
            
            fake_msg = FakeMessage(user, call.message.chat.id)
            start_command(fake_msg)
    
    except Exception as e:
        logger.error(f"Ошибка в handle_callback: {e}")
        bot.answer_callback_query(call.id, "⚠️ Ошибка обработки", show_alert=True)

# ========== ЗАПУСК БОТА ==========
if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("🚀 ЗАПУСК ТЕЛЕГРАМ БОТА С ГЛАВНЫМ АДМИНОМ")
    logger.info("=" * 50)
    
    # Загружаем администраторов
    admins = load_admins()
    logger.info(f"📊 Загружено администраторов: {len(admins)}")
    logger.info(f"👑 Главный админ ID: {MAIN_ADMIN_ID}")
    
    print("\n" + "=" * 50)
    print("🤖 БОТ С ГЛАВНЫМ АДМИНИСТРАТОРОМ (ИСПРАВЛЕННЫЙ)")
    print("=" * 50)
    print(f"👑 Главный админ: {MAIN_ADMIN_ID}")
    print(f"📊 Администраторов: {len(admins)}")
    print("📱 Откройте Telegram и напишите /start")
    print("🆔 Чтобы узнать свой ID, напишите /myid")
    print("=" * 50)
    print("⚡ Работает 24/7 на Railway")
    print("=" * 50)
    
    try:
        bot.polling(none_stop=True, interval=0, timeout=30)
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        # Railway автоматически перезапустит бота