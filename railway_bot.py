"""
🤖 ТЕЛЕГРАМ БОТ ДЛЯ RAILWAY
Работает 24/7, автоматический перезапуск при ошибках
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
                return set(admin_ids)
    except Exception as e:
        logger.error(f"Ошибка загрузки: {e}")
    
    return set()

def save_admins(admin_ids):
    """Сохраняем список администраторов"""
    try:
        data = {
            'admin_ids': list(admin_ids),
            'updated': datetime.now().isoformat(),
            'total': len(admin_ids)
        }
        
        with open(ADMINS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Сохранено {len(admin_ids)} администраторов")
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения: {e}")
        return False

# ========== ОСНОВНЫЕ ФУНКЦИИ ==========
def send_to_admins(message_text):
    """Отправляет сообщение всем администраторам"""
    admins = load_admins()
    sent_count = 0
    
    for admin_id in admins:
        try:
            bot.send_message(admin_id, message_text, parse_mode='HTML')
            sent_count += 1
        except Exception as e:
            logger.error(f"Не отправлено {admin_id}: {e}")
    
    return sent_count, len(admins)

# ========== КОМАНДА /START ==========
@bot.message_handler(commands=['start'])
def start_command(message):
    """Обработка команды /start"""
    try:
        user = message.from_user
        admins = load_admins()
        
        logger.info(f"👤 {user.id} ({user.username}) запустил бота")
        
        if user.id in admins:
            text = (f"✅ <b>{user.first_name}</b>, вы администратор!\n\n"
                   f"Вы будете получать все заявки с сайта.\n\n"
                   f"📊 <b>Всего администраторов:</b> {len(admins)}")
            
            keyboard = InlineKeyboardMarkup()
            keyboard.row(
                InlineKeyboardButton("📋 Тестовая заявка", callback_data='test'),
                InlineKeyboardButton("👥 Список администраторов", callback_data='list')
            )
            keyboard.row(
                InlineKeyboardButton("❌ Удалить себя", callback_data='remove'),
                InlineKeyboardButton("ℹ️ Помощь", callback_data='help')
            )
        else:
            text = (f"👋 <b>{user.first_name}</b>, добро пожаловать!\n\n"
                   f"Вы не в списке администраторов.\n\n"
                   f"Нажмите кнопку ниже, чтобы <b>добавить себя</b> и начать получать заявки с сайта.\n\n"
                   f"📊 <b>Сейчас администраторов:</b> {len(admins)}")
            
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("✅ ДОБАВИТЬ СЕБЯ В АДМИНИСТРАТОРЫ", callback_data='add'))
        
        bot.send_message(message.chat.id, text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Ошибка в start_command: {e}")
        bot.send_message(message.chat.id, "⚠️ Произошла ошибка. Попробуйте еще раз.")

# ========== ОБРАБОТЧИК КНОПОК ==========
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """Обработка нажатий на кнопки"""
    try:
        user = call.from_user
        admins = load_admins()
        
        logger.info(f"🔘 {user.id} нажал: {call.data}")
        
        bot.answer_callback_query(call.id)
        
        if call.data == 'add':
            if user.id not in admins:
                admins.add(user.id)
                save_admins(admins)
                
                # Уведомляем других
                for admin_id in admins:
                    if admin_id != user.id:
                        try:
                            bot.send_message(
                                admin_id,
                                f"👤 <b>Новый администратор</b>\n{user.full_name}\nID: {user.id}",
                                parse_mode='HTML'
                            )
                        except:
                            pass
                
                keyboard = InlineKeyboardMarkup()
                keyboard.row(
                    InlineKeyboardButton("📋 Тестовая заявка", callback_data='test'),
                    InlineKeyboardButton("👥 Список", callback_data='list')
                )
                keyboard.row(InlineKeyboardButton("❌ Удалить себя", callback_data='remove'))
                
                text = (f"✅ <b>{user.first_name}, вы добавлены!</b>\n\n"
                       f"Теперь будете получать заявки.\n\n"
                       f"📊 Администраторов: {len(admins)}")
                
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
                    text="✅ Вы уже администратор!"
                )
        
        elif call.data == 'remove':
            if user.id in admins:
                admins.remove(user.id)
                save_admins(admins)
                
                keyboard = InlineKeyboardMarkup()
                keyboard.add(InlineKeyboardButton("✅ Добавить себя", callback_data='add'))
                
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="❌ Вы удалены из списка.",
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            else:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="❌ Вас нет в списке."
                )
        
        elif call.data == 'list':
            admins = load_admins()
            
            if not admins:
                text = "📭 <b>Список администраторов пуст.</b>"
            else:
                text = "👥 <b>Список администраторов:</b>\n\n"
                for idx, admin_id in enumerate(sorted(admins), 1):
                    text += f"{idx}. ID: <code>{admin_id}</code>\n"
                text += f"\n📊 <b>Всего: {len(admins)}</b>"
            
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=text,
                parse_mode='HTML'
            )
        
        elif call.data == 'test':
            if user.id in admins:
                time_now = datetime.now().strftime("%H:%M:%S")
                date_now = datetime.now().strftime("%d.%m.%Y")
                
                sent, total = send_to_admins(
                    f"📋 <b>ТЕСТОВАЯ ЗАЯВКА</b>\n\n"
                    f"👤 ФИО: {user.full_name}\n"
                    f"📞 Телефон: +7 (999) 999-99-99\n"
                    f"📅 Дата: {date_now}\n"
                    f"⏰ Время: {time_now}"
                )
                
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=f"✅ Тест отправлен {sent}/{total} админам!"
                )
            else:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="❌ Только администраторы могут отправлять тесты."
                )
        
        elif call.data == 'help':
            help_text = (
                "🤖 <b>Помощь по боту</b>\n\n"
                "<b>Назначение:</b>\n"
                "Этот бот предназначен для получения заявок с сайта.\n\n"
                "<b>Как использовать:</b>\n"
                "1. Нажмите 'Добавить себя в администраторы'\n"
                "2. После добавления вы будете получать все заявки\n"
                "3. Для проверки используйте 'Тестовая заявка'\n\n"
                "<b>Команды:</b>\n"
                "/start - Главное меню\n"
                "/test - Тестовая заявка\n"
                "/admins - Список администраторов\n"
                "/remove - Удалить себя\n"
                "/help - Эта справка\n\n"
                "<b>Хостинг:</b> Railway.app\n"
                "<b>Статус:</b> Работает 24/7"
            )
            
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=help_text,
                parse_mode='HTML'
            )
    
    except Exception as e:
        logger.error(f"Ошибка в handle_callback: {e}")

# ========== ТЕКСТОВЫЕ КОМАНДЫ ==========
@bot.message_handler(commands=['test', 'admins', 'remove', 'help'])
def handle_text_command(message):
    """Обработка текстовых команд"""
    cmd = message.text.split()[0].lower().replace('/', '')
    
    if cmd == 'test':
        call = type('Call', (), {
            'from_user': message.from_user,
            'data': 'test',
            'id': 'text_cmd',
            'message': message
        })()
        handle_callback(call)
    elif cmd == 'admins':
        call = type('Call', (), {
            'from_user': message.from_user,
            'data': 'list',
            'id': 'text_cmd',
            'message': message
        })()
        handle_callback(call)
    elif cmd == 'remove':
        call = type('Call', (), {
            'from_user': message.from_user,
            'data': 'remove',
            'id': 'text_cmd',
            'message': message
        })()
        handle_callback(call)
    elif cmd == 'help':
        bot.reply_to(message, "Используйте /start для начала работы.")

# ========== ЗАПУСК БОТА ==========
if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("🚀 ЗАПУСК ТЕЛЕГРАМ БОТА НА RAILWAY")
    logger.info("=" * 50)
    
    admins = load_admins()
    logger.info(f"📊 Загружено администраторов: {len(admins)}")
    
    print("\n" + "=" * 50)
    print("🤖 БОТ ЗАПУЩЕН НА RAILWAY")
    print("📱 Откройте Telegram и напишите /start")
    print("🟢 Работает 24/7 с автоматическим перезапуском")
    print("=" * 50)
    
    try:
        bot.polling(none_stop=True, interval=0, timeout=30)
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        # Railway автоматически перезапустит бота