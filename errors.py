from aiogram import Router, types
from aiogram.types import Message
from functools import wraps
from config import Messages
import logging

error_router = Router()

def handle_errors(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logging.exception(f"Error in {func.__name__}: {str(e)}")
            message = args[0] if isinstance(args[0], Message) else None
            if message:
                await message.answer(Messages.ERROR)
            raise  # Перебрасываем исключение для обработки глобальным обработчиком
    return wrapper

@error_router.errors()
async def error_handler(update: types.Update, exception: Exception):
    logging.exception(f"Encountered an error while handling an update: {exception}")
    if update.message:
        await update.message.answer(Messages.UNEXPECTED_ERROR)
    elif update.callback_query:
        await update.callback_query.answer(Messages.ERROR, show_alert=True)

# Функция для установки глобального обработчика ошибок
async def global_error_handler(update: types.Update, exception: Exception):
    logging.exception(f"Global error handler caught an exception: {exception}")
    if update.message:
        await update.message.answer(Messages.CRITICAL_ERROR)
    elif update.callback_query:
        await update.callback_query.answer(Messages.CRITICAL_ERROR, show_alert=True)

def setup_global_error_handler(dp):
    dp.errors.register(global_error_handler)
