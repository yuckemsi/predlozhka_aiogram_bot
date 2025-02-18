from aiogram import F, Router, Bot
from aiogram.filters import CommandStart, Command,ChatMemberUpdatedFilter
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, JOIN_TRANSITION, LEAVE_TRANSITION
from aiogram.types import Message, CallbackQuery, ContentType, ChatMemberUpdated, ReplyKeyboardRemove
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

import app.database.db as db
import app.keyboards as kb

import re
from app.middlewares import BanMiddleware, CheckFirstName

import asyncio

rt = Router()

rt.message.outer_middleware(CheckFirstName())
rt.callback_query.outer_middleware(CheckFirstName())
rt.message.outer_middleware(BanMiddleware())
rt.callback_query.outer_middleware(BanMiddleware())

class Post(StatesGroup):
    post = State()

@rt.message(CommandStart())
async def start(message: Message):
    tg_id = message.from_user.id
    first_name = message.from_user.first_name
    await db.set_user(tg_id, first_name)
    await message.answer(f'Привет, {first_name}!\n\nЭтот бот предназначен для предложки каналов, пиши пост в канал на который подписан!')
    await message.answer('ПРЕДЛОЖКА БОТ', reply_markup=await kb.get_main(tg_id))

@rt.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION))
async def bot_added(event: ChatMemberUpdated, bot: Bot):
    tg_id = event.chat.id
    channel_name = event.chat.title
    await db.add_channel(tg_id, channel_name)
    await bot.send_message(chat_id=1175527638, text=f"Бот добавлен в новый канал!\n Название: {event.chat.title}\n id: {event.chat.id}")

@rt.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=LEAVE_TRANSITION))
async def bot_added(event: ChatMemberUpdated, bot: Bot):
    tg_id = event.chat.id
    await db.delete_channel(tg_id)
    await bot.send_message(chat_id=1175527638, text=f"Бот удален из канала!\n Название: {event.chat.title}\n id: {event.chat.id}")

@rt.callback_query(F.data == 'send_post')
async def post(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await callback.message.delete()
    await callback.answer('Вы нажали кнопку написания поста')
    await state.set_state(Post.post)
    channels = await db.all_channels()
    if channels == []:
        msg = await callback.message.answer('Нет доступных каналов для поста :(', reply_markup = kb.to_main)
        await asyncio.sleep(5)
        await bot.delete_message(callback.message.chat.id, msg.message_id)
    else:
        await callback.message.answer('Выбери канал:\n\n/cancel - отменить пост', reply_markup = await kb.choose_channel())

@rt.message(Command('cancel'))
async def cancel_post(message: Message, state: FSMContext):
    if state is None:
        pass

    await state.clear()
    await message.answer('Вы отменили пост!', reply_markup=await kb.get_main(tg_id=message.from_user.id))

@rt.callback_query(Post.post, F.data.startswith('to_'))
async def channel_button(callback: CallbackQuery , state: FSMContext):
    channel_id = callback.data.split('_')[1]
    channel = await db.get_channel(channel_id)
    await callback.answer(f'Ты выбрал {channel[2]}')
    await callback.message.delete()
    await state.update_data(post=channel_id)
    await callback.message.answer('ПРИШЛИ СВОЙ ПОСТ\nвидео, фото, текст\n\n/cancel - отменить отправку поста')

@rt.message(Post.post, F.photo)
async def photo_message(message: Message, state: FSMContext, bot: Bot):
    if message.photo:
        await state.update_data('')
        tg_id = message.from_user.id
        data = await state.get_data()
        channel_id = data['post']
        media_id = f"{message.photo[-1].file_id}"
        caption = message.caption
        post_type = 2
        first_name = message.from_user.first_name
        await db.create_post(tg_id, channel_id, first_name, caption, post_type, media_id)
        msg = await message.answer("Твой пост был отправлен на проверку!", reply_markup=await kb.get_main(tg_id))
        await asyncio.sleep(5)
        await bot.delete_message(message.chat.id, msg.message_id)
        await state.clear()


@rt.message(Post.post, F.video)
async def video_message(message: Message, state: FSMContext, bot: Bot):
    if message.video:
        await state.update_data('')
        tg_id = message.from_user.id
        data = await state.get_data()
        channel_id = data['post']
        media_id = f"{message.video.file_id}"
        caption = message.caption
        post_type = 3
        first_name = message.from_user.first_name
        await db.create_post(tg_id, channel_id, first_name, caption, post_type, media_id)
        msg = await message.answer("Твой пост был отправлен на проверку!", reply_markup=await kb.get_main(tg_id))
        await asyncio.sleep(5)
        await bot.delete_message(message.chat.id, msg.message_id)
        await state.clear()


@rt.message(Post.post, F.text)
async def text_message(message: Message, state: FSMContext, bot: Bot):
    if message.text:
        await state.update_data('')
        tg_id = message.from_user.id
        data = await state.get_data()
        channel_id = data['post']
        caption = message.text
        first_name = message.from_user.first_name
        post_type = 1
        await db.create_post(tg_id, channel_id, first_name, caption, post_type)
        await message.answer("Твой пост был отправлен на проверку!", reply_markup=await kb.get_main(tg_id))
        await state.clear()

@rt.callback_query(F.data=='main')
async def main(callback: CallbackQuery):
    await callback.answer('Вы вернулись в главное меню')
    tg_id = callback.from_user.id
    first_name = callback.from_user.first_name
    await db.set_user(tg_id, first_name)
    await callback.message.delete()
    await callback.message.answer('Бот работает исправно\nСкорее пиши самые свежие новости!', reply_markup=await kb.get_main(tg_id))

@rt.callback_query(F.data=='admin_panel')
async def admin_panel(callback: CallbackQuery):
    await callback.answer('Вы открыли админ-панель')
    await callback.message.delete()
    tg_id = callback.from_user.id
    admin = await db.check_admin(tg_id)
    if admin == True:
        await callback.message.answer('АДМИН-ПАНЕЛЬ', reply_markup=kb.admin_panel)
    if admin == False:
        await callback.message.answer('Ты не админ!')

@rt.callback_query(F.data=='check_posts')
async def all_posts(callback: CallbackQuery, bot: Bot):
    await callback.answer('Вы нажали на проверку постов')
    posts = {}
    all_posts = await db.get_all_posts()
    if all_posts == []:
        msg = await callback.message.answer('Нет постов для проверки :(')
        await asyncio.sleep(3)
        await bot.delete_message(callback.message.chat.id, msg.message_id)
    else:
        for post in all_posts:
            posts.update({post[0]: {'tg_id':post[1], 'channel_id': post[2], 'first_name':post[3], 'media_id':post[4], 'caption':post[5], 'type':post[6]}})
            if posts[post[0]].get('type') == 1:
                first_name = posts[post[0]].get('first_name')
                caption = posts[post[0]].get('caption')
                channel_id = posts[post[0]].get('channel_id')
                channel = await db.get_channel(channel_id)
                await callback.message.answer(f'👤 {first_name}\n\n{caption}\n\nКанал: {channel[2]}', reply_markup=await kb.post_settings(tg_id=post[1], post_id=post[0], channel_id=channel_id))
            elif posts[post[0]].get('type') == 2:
                first_name = posts[post[0]].get('first_name')
                caption = posts[post[0]].get('caption')
                photo_id = posts[post[0]].get('media_id')
                channel_id = posts[post[0]].get('channel_id')
                channel = await db.get_channel(channel_id)
                if caption is None:
                    await callback.message.answer_photo(photo=f'{photo_id}', caption=f'👤 {first_name}\n\nКанал: {channel[2]}', reply_markup=await kb.post_settings(tg_id=post[1], post_id=post[0], channel_id=channel_id))
                else:
                    await callback.message.answer_photo(photo=f'{photo_id}', caption=f'👤 {first_name}\n\n{caption}\n\nКанал: {channel[2]}', reply_markup=await kb.post_settings(tg_id=post[1], post_id=post[0], channel_id=channel_id))
            elif posts[post[0]].get('type') == 3:
                first_name = posts[post[0]].get('first_name')
                caption = posts[post[0]].get('caption')
                video_id = posts[post[0]].get('media_id')
                channel_id = posts[post[0]].get('channel_id')
                channel = await db.get_channel(channel_id)
                if caption is None:
                    await callback.message.answer_video(video=f'{video_id}', caption=f'👤 {first_name}\n\nКанал: {channel[2]}', reply_markup=await kb.post_settings(tg_id=post[1], post_id=post[0], channel_id=channel_id))
                else:
                    await callback.message.answer_video(video=f'{video_id}', caption=f'👤 {first_name}\n\n{caption}\n\nКанал: {channel[2]}', reply_markup=await kb.post_settings(tg_id=post[1], post_id=post[0], channel_id=channel_id))

@rt.callback_query(F.data == 'channels')
async def manage_channels(callback: CallbackQuery):
    await callback.answer('')
    await callback.message.delete()
    await callback.message.answer('Выберите канал:', reply_markup=await kb.manage_channels())

@rt.callback_query(F.data.startswith('ban_'))
async def ban(callback: CallbackQuery, bot: Bot):
    await callback.answer('Вы нажали кнопку бана!')
    tg_id = callback.data.split('_')[1]
    user_id = await bot.get_chat(tg_id)
    await callback.message.delete()
    ban = await db.ban_user(tg_id, first_name=user_id.first_name)
    if ban == True:
        msg = await callback.message.answer('Пользователь уже забанен!')
        await asyncio.sleep(3)
        await bot.delete_message(callback.message.chat.id, msg.message_id)
    if ban == False:
        await callback.message.answer('Пользователь забанен!')
    await db.delete_user_posts(tg_id)

@rt.callback_query(F.data.startswith('channel_'))
async def manage_channel(callback: CallbackQuery):
    channel_id = callback.data.split('_')[1]
    channel = await db.get_channel(channel_id)
    await callback.answer(f'Ты выбрал {channel[2]}')
    await callback.message.delete()
    await callback.message.answer(f'Управление каналом: {channel[2]}', reply_markup = await kb.manage_channel(channel_id))

@rt.callback_query(F.data.startswith('delete-channel_'))
async def ban(callback: CallbackQuery, bot: Bot):
    channel_id = callback.data.split('_')[1]
    await db.delete_channel(channel_id)
    await bot.leave_chat(chat_id=channel_id)
    await callback.answer('Бот вышел из канала!')
    await callback.message.delete()

@rt.callback_query(F.data.startswith('delete_'))
async def ban(callback: CallbackQuery, bot: Bot):
    await callback.message.delete()
    await callback.answer('Пост удален!')
    post_id = callback.data.split('_')[1]
    await db.delete_post(post_id)
    

@rt.callback_query(F.data.startswith('_'))
async def post_to_channel(callback: CallbackQuery, bot: Bot):
    await callback.answer('Пост публикуется')
    await callback.message.delete()
    channel = re.split('[_.]', callback.data)[1]
    post_get = re.split('[_.]', callback.data)[-1]
    post_by = await db.get_post(post_id=post_get)
    post_data = list(post_by)
    if post_data[-1] == 1:
        await bot.send_message(chat_id=channel, text=f"{post_data[5]}")
    if post_data[-1] == 2:
        if post_data[5] is None:
            await bot.send_photo(chat_id=channel, photo=f"{post_data[4]}")
        else:
            await bot.send_photo(chat_id=channel, photo=f"{post_data[4]}", caption=f"{post_data[5]}")
    if post_data[-1] == 3:
        if post_data[5] is None:
            await bot.send_video(chat_id=channel, video=f"{post_data[4]}")
        else:
            await bot.send_video(chat_id=channel, video=f"{post_data[4]}", caption=f"{post_data[5]}")
    await db.delete_post(post_get)
    msg = await callback.message.answer('Пост опубликован')
    await asyncio.sleep(3)
    await bot.delete_message(callback.message.chat.id, msg.message_id)

@rt.callback_query(F.data=='all_users')
async def get_users(callback: CallbackQuery, bot: Bot):
    await callback.answer('Вы нажали на список пользователей')
    msg = await callback.message.answer('Список пользователей:', reply_markup=await kb.all_users())
    await asyncio.sleep(20)
    await bot.delete_message(callback.message.chat.id, msg.message_id)

@rt.callback_query(F.data=='all_admins')
async def get_users(callback: CallbackQuery, bot: Bot):
    await callback.answer('Вы нажали на список админов')
    msg = await callback.message.answer('Список админов:', reply_markup=await kb.admin_list())
    await asyncio.sleep(20)
    await bot.delete_message(callback.message.chat.id, msg.message_id)

@rt.callback_query(F.data=='banlist')
async def bans(callback: CallbackQuery, bot: Bot):
    await callback.answer('Вы нажали на банлист')
    banlist = await db.banlist()
    if banlist == []:
        msg = await callback.message.answer('Нет забаненных пользователей!')
        await asyncio.sleep(3)
        await bot.delete_message(callback.message.chat.id, msg.message_id)
    else:
        msg = await callback.message.answer('Банлист:', reply_markup=await kb.banlist())
        await asyncio.sleep(20)
        await bot.delete_message(callback.message.chat.id, msg.message_id)

@rt.message(Command('send'))
async def sendall(message: Message, bot: Bot):
    if message.from_user.id == 1175527638:
        users = {}
        all_users = await db.all_users()
        text = message.text.split(maxsplit=1)[1]
        for user in all_users:
            try:
                users.update({user[0]: {'tg_id': user[1], 'first_name': user[2]}})
                tg_id = users[user[0]].get('tg_id')
                await bot.send_message(chat_id=tg_id, text=text)
            except aiogram.exceptions.TelegramForbiddenError:
                pass

        msg = await message.answer('Рассылка отправлена!')
        await asyncio.sleep(5)
        await bot.delete_message(message.chat.id, msg.message_id)
    else:
        msg = await message.answer('У тебя нет прав!')
        await asyncio.sleep(5)
        await bot.delete_message(message.chat.id, msg.message_id)

@rt.message(Command('admin'))
async def new_admin(message: Message, bot: Bot):
    if message.from_user.id == 1175527638:
        text = message.text.split(maxsplit=1)[1]
        admin_id = await bot.get_chat(text)
        add = await db.add_admin(tg_id=text, first_name=admin_id.first_name)
        if add == True:
            msg = await message.answer('Пользователь теперь админ!')
            await bot.send_message(chat_id=text, text=f'Ты теперь админ!\nНазначил: @{message.from_user.username}')
            await asyncio.sleep(3)
            await bot.delete_message(message.chat.id, msg.message_id)
        if add == False:
            msg = await message.answer('Этот пользователь уже админ!')
            await asyncio.sleep(3)
            await bot.delete_message(message.chat.id, msg.message_id)
    else:
        await message.answer('Ты не админ!')

@rt.message(Command('unadmin'))
async def new_admin(message: Message, bot: Bot):
    text = message.text.split(maxsplit=1)[1]
    if message.from_user.id == 1175527638:
        admin = await db.delete_admin(tg_id=text)
        if admin == True:
            await message.answer('Пользователь больше не админ!')
            await bot.send_message(chat_id=text, text=f'Ты теперь не админ!\nСнял: @{message.from_user.username}')
            await asyncio.sleep(3)
            await bot.delete_message(message.chat.id, msg.message_id)
        if admin == False:
            msg = await message.answer('Этот пользователь не админ!')
            await asyncio.sleep(3)
            await bot.delete_message(message.chat.id, msg.message_id)
    else:
        await message.answer('Ты не админ!')

@rt.message(Command('unban'))
async def new_admin(message: Message, bot: Bot):
    text = message.text.split(maxsplit=1)[1]
    if message.from_user.id == 1175527638:
        user_ban = await db.unban_user(tg_id=text)
        if user_ban == True:
            msg = await message.answer('Пользователь разбанен!')
            await asyncio.sleep(3)
            await bot.delete_message(message.chat.id, msg.message_id)
        if user_ban == False:
            msg = await message.answer('Этот пользователь не в бане!')
            await asyncio.sleep(3)
            await bot.delete_message(message.chat.id, msg.message_id)
    else:
        await message.answer('Ты не админ!')