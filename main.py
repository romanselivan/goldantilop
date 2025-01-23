import asyncio
import logging
import os
import sys

from aiohttp import web
from aiogram import Bot, Dispatcher, Router, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command

from config import (
    ADMIN_IDS, BOT_TOKEN, G_SHEET_ID, USERS_SHEET, 
    ButtonTexts, Messages, UserFields, UserState, UserStatus
)
from sheet_manager import SheetManager
from onboarding import onboarding_router, start_onboarding
from user import main_menu, user_router, return_to_main_menu, show_exchange_rates, show_help, show_user_requests
from admin import admin_router
from exchange import exchange_router, setup_exchange_router, start_exchange
from errors import error_router, handle_errors, setup_global_error_handler
from uiux import UIUX

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def handle(request):
    return web.Response(text="Bot is running")

class BotApp:
    def __init__(self):
        self.bot = Bot(
            token=BOT_TOKEN, 
            default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
        )
        self.storage = MemoryStorage()
        self.dp = Dispatcher(storage=self.storage)
        self.main_router = Router()
        
        try:
            self.sheet_manager = SheetManager(G_SHEET_ID)
        except Exception as e:
            logger.error(f"Failed to initialize SheetManager: {e}")
            sys.exit(1)

    async def start(self):
        self.dp.include_router(error_router)
        self.dp.include_router(self.main_router)
        self.dp.include_router(exchange_router)
        self.dp.include_router(onboarding_router)
        self.dp.include_router(user_router)
        self.dp.include_router(admin_router)

        for router in [onboarding_router, user_router, admin_router, exchange_router]:
            router.sheet_manager = self.sheet_manager
            router.bot = self.bot

        setup_exchange_router(
            return_to_main_menu, 
            show_exchange_rates, 
            show_help, 
            show_user_requests
        )

        setup_global_error_handler(self.dp)

        self.setup_routes()
        logger.info("Bot started")

        await self.dp.start_polling(self.bot)

    def setup_routes(self):
        @self.main_router.message(Command("start"))
        @handle_errors
        async def cmd_start(message: types.Message, state: FSMContext):
            return await self.process_start_command(message, state)

        @self.main_router.message(lambda message: message.text in [
            ButtonTexts.HELP, 
            ButtonTexts.VIEW_RATES, 
            ButtonTexts.MY_REQUESTS, 
            ButtonTexts.CALCULATE_EXCHANGE
        ])
        async def handle_main_menu_commands(message: types.Message, state: FSMContext):
            await state.clear()
            if message.text == ButtonTexts.HELP:
                await show_help(message, state)
            elif message.text == ButtonTexts.VIEW_RATES:
                await show_exchange_rates(message, state)
            elif message.text == ButtonTexts.MY_REQUESTS:
                await show_user_requests(message)
            elif message.text == ButtonTexts.CALCULATE_EXCHANGE:
                await start_exchange(message, state)

    async def process_start_command(self, message: types.Message, state: FSMContext):
        user_id = str(message.from_user.id)
        username = message.from_user.username

        if not username:
            await message.answer(Messages.SET_USERNAME)
            return

        try:
            user_data = self.sheet_manager.get_data(USERS_SHEET, user_id)
            logger.info(f"User data for {user_id}: {user_data}")

            if not user_data:
                if str(user_id) in ADMIN_IDS:
                    new_admin_data = {
                        UserFields.USER_ID: user_id,
                        UserFields.USERNAME: username,
                        UserFields.USER_STATUS: UserStatus.ADMIN,
                        UserFields.USER_STATE: UserState.ADMIN_MENU
                    }
                    logger.info(f"Attempting to add new admin: {new_admin_data}")
                    self.sheet_manager.add_new_entry(USERS_SHEET, new_admin_data)
                    await message.answer(Messages.ADMIN_WELCOME, reply_markup=UIUX.admin_menu())
                else:
                    all_users = self.sheet_manager.get_data(USERS_SHEET)
                    logger.info(f"All users: {all_users}")
                    admin_exists = any(
                        user.get(UserFields.USER_STATUS) == UserStatus.ADMIN 
                        for user in all_users if isinstance(user, dict)
                    )
                    if admin_exists:
                        new_user_data = {
                            UserFields.USER_ID: user_id,
                            UserFields.USERNAME: username,
                            UserFields.USER_STATUS: UserStatus.PENDING,
                            UserFields.USER_STATE: UserState.WAITING_REFERRAL
                        }
                        self.sheet_manager.add_new_entry(USERS_SHEET, new_user_data)
                        await message.answer(Messages.USER_WELCOME, reply_markup=types.ReplyKeyboardRemove())
                        await start_onboarding(message, state)
                    else:
                        await message.answer(Messages.SYSTEM_NOT_READY)
            else:
                await self.handle_user_status(user_id, user_data, message, state)
        except Exception as e:
            logger.error(f"Error in cmd_start: {str(e)}", exc_info=True)
            await message.answer(Messages.ERROR)

    async def handle_user_status(self, user_id: str, user_data: dict, message: types.Message, state: FSMContext):
        user_status = user_data.get(UserFields.USER_STATUS)
        if not user_status:
            logger.warning(f"User {user_id} has no USER_STATUS. Data: {user_data}")
            if str(user_id) in ADMIN_IDS:
                user_status = UserStatus.ADMIN
                self.sheet_manager.batch_update(
                    USERS_SHEET, 
                    user_id, 
                    {
                        UserFields.USER_STATUS: UserStatus.ADMIN, 
                        UserFields.USER_STATE: UserState.ADMIN_MENU
                    }
                )
            else:
                user_status = UserStatus.PENDING
                self.sheet_manager.batch_update(
                    USERS_SHEET, 
                    user_id, 
                    {
                        UserFields.USER_STATUS: UserStatus.PENDING, 
                        UserFields.USER_STATE: UserState.WAITING_REFERRAL
                    }
                )

        if user_status == UserStatus.ADMIN:
            await message.answer(Messages.ADMIN_WELCOME, reply_markup=UIUX.admin_menu())
        elif user_status == UserStatus.ACTIVE:
            await main_menu(message.bot, user_id)
        elif user_status == UserStatus.PENDING:
            await start_onboarding(message, state)
        elif user_status == UserStatus.BAN:
            await message.answer(Messages.USER_BANNED, reply_markup=types.ReplyKeyboardRemove())
        else:
            logger.error(f"Unknown user status for user {user_id}: {user_status}")
            await message.answer(Messages.UNKNOWN_STATUS, reply_markup=types.ReplyKeyboardRemove())

async def shutdown(dp: Dispatcher, bot: Bot):
    logger.info("Shutting down...")
    await dp.storage.close()
    if hasattr(dp.storage, 'wait_closed'):
        await dp.storage.wait_closed()
    await bot.session.close()

async def main():
    bot_app = BotApp()
    
    app = web.Application()
    app.router.add_get("/", handle)
    
    port = int(os.environ.get("PORT", 5000))
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host='0.0.0.0', port=port)
    
    await site.start()
    
    try:
        await bot_app.start()
        await bot_app.dp.start_polling(bot_app.bot)
    except Exception as e:
        logger.error(f"Critical error during bot execution: {e}", exc_info=True)
    finally:
        await shutdown(bot_app.dp, bot_app.bot)
        await runner.cleanup()
        logger.info("Bot stopped")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
