from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def payout_panel():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Заявка на выплату", callback_data="payout_request")],
        [InlineKeyboardButton("Задать вопрос", callback_data="ask_question")]
    ])

def admin_payout_panel():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Заявки на выплату", callback_data="admin_payouts")],
        [InlineKeyboardButton("Статус поддержки", callback_data="admin_support")],
        [InlineKeyboardButton("Ответить", callback_data="admin_reply")],
        [InlineKeyboardButton("Заблокировать", callback_data="admin_block")]
    ])

def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="back")]])

def admin_back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="admin_back")]])

def support_status_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Активна", callback_data="set_support_active")],
        [InlineKeyboardButton("Неактивна", callback_data="set_support_inactive")],
        [InlineKeyboardButton("Назад", callback_data="admin_support")]
    ])

def payout_status_buttons(request_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Одобрить", callback_data=f"payout_approve_{request_id}")],
        [InlineKeyboardButton("Отклонить", callback_data=f"payout_reject_{request_id}")],
        [InlineKeyboardButton("Назад", callback_data="admin_payouts")]
    ])
