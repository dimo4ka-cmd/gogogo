from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from payout_config import PAGE_SIZE

def payout_panel():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💸 Заявка на выплату", callback_data="payout_request")],
        [InlineKeyboardButton("❓ Задать вопрос", callback_data="ask_question")],
        [InlineKeyboardButton("📋 Мои заявки", callback_data="my_payouts_0")]
    ])

def admin_payout_panel():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Заявки на выплату", callback_data="admin_payouts_0")],
        [InlineKeyboardButton("⚙️ Статус поддержки", callback_data="admin_support")],
        [InlineKeyboardButton("💬 Ответить пользователю", callback_data="admin_reply")],
        [InlineKeyboardButton("🚫 Заблокировать пользователя", callback_data="admin_block")]
    ])

def cancel_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="cancel")]])

def admin_cancel_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="admin_cancel")]])

def support_status_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Активна", callback_data="set_support_active")],
        [InlineKeyboardButton("❌ Неактивна", callback_data="set_support_inactive")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")]
    ])

def payout_status_buttons(request_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Одобрить", callback_data=f"payout_approve_{request_id}")],
        [InlineKeyboardButton("❌ Отклонить", callback_data=f"payout_reject_{request_id}")],
        [InlineKeyboardButton("➡️ Следующая заявка", callback_data="admin_payouts_0")]
    ])

def pagination_buttons(current_page, total_items, prefix):
    buttons = []
    if current_page > 0:
        buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"{prefix}_{current_page-1}"))
    if (current_page + 1) * PAGE_SIZE < total_items:
        buttons.append(InlineKeyboardButton("Вперёд ➡️", callback_data=f"{prefix}_{current_page+1}"))
    return InlineKeyboardMarkup([buttons]) if buttons else None
