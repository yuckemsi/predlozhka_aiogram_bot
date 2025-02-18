from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton,
                           KeyboardButtonRequestChat)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

import app.database.db as db

admin_panel = InlineKeyboardMarkup(inline_keyboard=[
	[InlineKeyboardButton(text='✉️ Проверить посты', callback_data='check_posts')],
    [InlineKeyboardButton(text='👤 Все пользователи', callback_data='all_users')],
    [InlineKeyboardButton(text='? Админы', callback_data='all_admins')],
    [InlineKeyboardButton(text='⛔️ Банлист', callback_data='banlist')],
    [InlineKeyboardButton(text='📍 Управлять каналами', callback_data='channels')],
    [InlineKeyboardButton(text='⬅️ На главную', callback_data='main')]
])

to_main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='⬅️ На главную', callback_data='main')]
])

async def all_users():
    users = {}
    all_users = await db.all_users()
    keyboard = InlineKeyboardBuilder()
    for user in all_users:
        users.update({user[0]: {'tg_id': user[1], 'first_name': user[2]}})
        tg_id = users[user[0]].get('tg_id')
        first_name = users[user[0]].get('first_name')
        keyboard.add(InlineKeyboardButton(text=f'{first_name}', url=f'tg://user?id={tg_id}', callback_data=f'id_{tg_id}'))
    return keyboard.adjust(2).as_markup()

async def banlist():
    banlist = {}
    all_bans = await db.banlist()
    keyboard = InlineKeyboardBuilder()
    for ban_user in all_bans:
        banlist.update({ban_user[0]: {'tg_id': ban_user[1], 'first_name': ban_user[2]}})
        tg_id = banlist[ban_user[0]].get('tg_id')
        first_name = banlist[ban_user[0]].get('first_name')
        keyboard.add(InlineKeyboardButton(text=f'{first_name}', url=f'tg://user?id={tg_id}', callback_data=f'id_{tg_id}'))
    return keyboard.as_markup()

async def admin_list():
    admin_list = {}
    all_admins = await db.all_admins()
    keyboard = InlineKeyboardBuilder()
    for admin in all_admins:
        admin_list.update({admin[0]: {'tg_id': admin[1], 'first_name': admin[2]}})
        tg_id = admin_list[admin[0]].get('tg_id')
        first_name = admin_list[admin[0]].get('first_name')
        keyboard.add(InlineKeyboardButton(text=f'{first_name}', url=f'tg://user?id={tg_id}', callback_data=f'id_{tg_id}'))
    return keyboard.as_markup()

async def get_main(tg_id: int):
    is_user_admin = await db.check_admin(tg_id)
    if is_user_admin == True:
        admin_main = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Отправить пост', callback_data='send_post')],
            [InlineKeyboardButton(text='📍 Админ-панель', callback_data='admin_panel')]
        ])
        return admin_main
    if is_user_admin == False:
        main = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Отправить пост', callback_data='send_post')],
        ])
        return main

async def post_settings(tg_id: int, post_id: int, channel_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text='⛔️', callback_data=f'ban_{tg_id}'),InlineKeyboardButton(text='❌', callback_data=f'delete_{post_id}'),InlineKeyboardButton(text='✅', callback_data=f'_{channel_id}.{post_id}'),InlineKeyboardButton(text='👤', url=f'tg://user?id={tg_id}'))
    return keyboard.as_markup()

async def choose_channel():
    channels = {}
    all_channels = await db.all_channels()
    keyboard = InlineKeyboardBuilder()
    for channel in all_channels:
        channels.update({channel[0]: {'tg_id': channel[1], 'channel_name': channel[2]}})
        channel_id = channels[channel[0]].get('tg_id')
        channel_name = channels[channel[0]].get('channel_name')
        keyboard.add(InlineKeyboardButton(text=f'{channel_name}', callback_data=f'to_{channel_id}'))
    return keyboard.adjust(1).as_markup()

async def manage_channels():
    channels = {}
    all_channels = await db.all_channels()
    keyboard = InlineKeyboardBuilder()
    for channel in all_channels:
        channels.update({channel[0]: {'tg_id': channel[1], 'channel_name': channel[2]}})
        channel_id = channels[channel[0]].get('tg_id')
        channel_name = channels[channel[0]].get('channel_name')
        keyboard.add(InlineKeyboardButton(text=f'📍 {channel_name}', callback_data=f'channel_{channel_id}'))
    return keyboard.adjust(1).as_markup()

async def manage_channel(channel_id: int):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text='❌ Удалить канал', callback_data=f'delete-channel_{channel_id}'),InlineKeyboardButton(text='📍 Список каналов', callback_data=f'channels'),InlineKeyboardButton(text='Админ-панель', callback_data=f'admin_panel'))
    return keyboard.adjust(1).as_markup()
