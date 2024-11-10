from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

start_kb = InlineKeyboardMarkup().add(InlineKeyboardButton('Профиль', callback_data='profil')).add(InlineKeyboardButton('Создать ссылку', callback_data='create_url'))

back_kb = InlineKeyboardMarkup().add(InlineKeyboardButton('« Назад', callback_data='back_main'))

profil_kb = InlineKeyboardMarkup().add(InlineKeyboardButton('Измени адрес', callback_data='change_address')).add(InlineKeyboardButton('Вывод', callback_data='output')).add(InlineKeyboardButton('« Назад', callback_data='back_main'))

skip_kb = InlineKeyboardMarkup().add(InlineKeyboardButton('Пропустить', callback_data=f'skip'))

addrr_kb = InlineKeyboardMarkup().add(InlineKeyboardButton('Подтвердить', callback_data='confirm')).add(InlineKeyboardButton('Отмена', callback_data='cancle'))
