from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def user_panel():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Добавить номер", callback_data="add_number")],
        [InlineKeyboardButton("Очередь", callback_data="queue")],
        [InlineKeyboardButton("Архив", callback_data="archive")],
        [InlineKeyboardButton("Статистика", callback_data="stats")],
        [InlineKeyboardButton("Вывести", callback_data="payout")]
    ])

def admin_panel():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Очередь", callback_data="admin_queue")],
        [InlineKeyboardButton("Начислить баланс", callback_data="admin_balance")],
        [InlineKeyboardButton("Обработать заявку", callback_data="admin_process")]
    ])

def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="back")]])

def admin_back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="admin_back")]])

def process_buttons(queue_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Успешно", callback_data=f"process_success_{queue_id}")],
        [InlineKeyboardButton("Слетел", callback_data=f"process_failed_{queue_id}")],
        [InlineKeyboardButton("Назад", callback_data="admin_process")]
    ])
