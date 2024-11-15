from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton,
                           KeyboardButtonRequestChat)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

import app.database.db as db

admin_panel = InlineKeyboardMarkup(inline_keyboard=[
	[InlineKeyboardButton(text='Проверить посты', callback_data='check_posts')],
    [InlineKeyboardButton(text='Управлять каналами', callback_data='channels')],
    [InlineKeyboardButton(text='На главную', callback_data='to_main')]
])

channels_setting = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Добавить канал', callback_data='add_channel')],
    [InlineKeyboardButton(text='Удалить канал', callback_data='delete_channel')],
    [InlineKeyboardButton(text='Список каналов', callback_data='all_channels')],
    [InlineKeyboardButton(text='Админ-панель', callback_data='admin_panel')]
    								])

async def get_main(tg_id: int):
    is_user_admin = await db.check_admin(tg_id)
    if is_user_admin == True:
        admin_main = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Отправить пост', callback_data='send_post')],
            [InlineKeyboardButton(text='Помощь', callback_data='help'),
             InlineKeyboardButton(text='Правила написания постов', callback_data='rules')],
            [InlineKeyboardButton(text='Контакты', callback_data='contacts')],
            [InlineKeyboardButton(text='Админ-панель', callback_data='admin_panel')]
        ])
        return admin_main
    if is_user_admin == False:
        main = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Отправить пост', callback_data='send_post')],
            [InlineKeyboardButton(text='Помощь', callback_data='help'),
             InlineKeyboardButton(text='Правила написания постов', callback_data='rules')],
            [InlineKeyboardButton(text='Контакты', callback_data='contacts')],
        ])
        return main

async def post_settings(tg_id: int, post_id: int):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text='⛔️', callback_data=f'ban_{tg_id}'),InlineKeyboardButton(text='❌', callback_data=f'delete_{post_id}'),InlineKeyboardButton(text='✅', callback_data=f'on_post-{post_id}'),InlineKeyboardButton(text='👤', url=f'tg://user?id={tg_id}'))
    return keyboard.as_markup()

async def get_channels(post_id: int):
    channels = {}
    all_channels = await db.all_channels()
    post = await db.get_post_id(post_id)
    for channel in all_channels:
        channels.update({channel[0]: {'tg_id': channel[1], 'channel_name': channel[2]}})
        keyboard = InlineKeyboardBuilder()
        channel_id = channels[channel[0]].get('tg_id')
        channel_name = channels[channel[0]].get('channel_name')
        keyboard.add(InlineKeyboardButton(text=f'{channel_name}', callback_data=f'_{channel_id}.{post}'))
        return keyboard.adjust(1).as_markup()