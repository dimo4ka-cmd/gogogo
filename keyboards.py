from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import PAGE_SIZE

def user_panel():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 Сдать номер", callback_data="add_number")],
        [InlineKeyboardButton("📋 Моя очередь", callback_data="queue_0")],
        [InlineKeyboardButton("🗂 Архив", callback_data="archive_0")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("💰 Баланс", callback_data="balance")],
        [InlineKeyboardButton("💸 Вывести", callback_data="payout")],
        [InlineKeyboardButton("❓ Поддержка", callback_data="support")]
    ])

def admin_panel():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Очередь заявок", callback_data="admin_queue_0")],
        [InlineKeyboardButton("💰 Начислить баланс", callback_data="admin_balance")],
        [InlineKeyboardButton("⚙️ Обработать заявку", callback_data="admin_process")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("👤 Управление пользователями", callback_data="admin_users")],
        [InlineKeyboardButton("💬 Ответить на вопрос", callback_data="admin_support_reply")]
    ])

def cancel_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="cancel")]])

def admin_cancel_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="admin_cancel")]])

def process_buttons(queue_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Успешно", callback_data=f"process_success_{queue_id}")],
        [InlineKeyboardButton("❌ Слетел", callback_data=f"process_failed_{queue_id}")],
        [InlineKeyboardButton("➡️ Следующая заявка", callback_data="admin_process")]
    ])

def pagination_buttons(current_page, total_items, prefix):
    buttons = []
    total_pages = (total_items + PAGE_SIZE - 1) // PAGE_SIZE
    if current_page > 0:
        buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"{prefix}_{current_page-1}"))
    if current_page < total_pages - 1:
        buttons.append(InlineKeyboardButton("Вперёд ➡️", callback_data=f"{prefix}_{current_page+1}"))
    return InlineKeyboardMarkup([buttons]) if buttons else None

def user_management_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚫 Забанить", callback_data="admin_ban")],
        [InlineKeyboardButton("✅ Разбанить", callback_data="admin_unban")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")]
    ])
