from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User, Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable, Union

from app.database import db
from app.database.db import ban_user

class BanMiddleware(BaseMiddleware):
    async def __call__(self,
                       handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: Union[Message, CallbackQuery],
                       data: Dict[str, Any]) -> Any:
        user: User = data.get('event_from_user')
        ban = await db.check_ban(tg_id=user.id)
        if user is not None:
            if ban == True:
                await event.answer('Ты был забанен! За разбаном: @locustt')
            if ban == False:
                result = await handler(event, data)
                return result

class CheckFirstName(BaseMiddleware):
    async def __call__(self,
                       handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: Union[Message, CallbackQuery],
                       data: Dict[str, Any]) -> Any:
        user: User = data.get('event_from_user')
        name = await db.check_username(tg_id=user.id, first_name=user.first_name)
        if name == True:
            return await handler(event, data)
        if name == False:
            return await handler(event, data)
