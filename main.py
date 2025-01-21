import asyncio
import logging
from aiogram import Bot, Dispatcher, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from config import ADMIN_IDS, BOT_TOKEN, G_SHEET_ID, USERS_SHEET, ButtonTexts, Messages, UserFields, UserState, UserStatus
from aiogram.filters import Command
from sheet_manager import SheetManager
from onboarding import onboarding_router, start_onboarding
from user import main_menu, user_router, return_to_main_menu, show_exchange_rates, show_help, show_user_requests
from admin import admin_router
from exchange import exchange_router, setup_exchange_router, start_exchange
from errors import error_router, handle_errors, setup_global_error_handler
from uiux import UIUX
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

main_router = Router()

try:
    sheet_manager = SheetManager(G_SHEET_ID)
except Exception as e:
    logger.error(f"Failed to initialize SheetManager: {e}")
    sys.exit(1)

@main_router.message(Command("start"))
@handle_errors
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    username = message.from_user.username

    if not username:
        await message.answer(Messages.SET_USERNAME)
        return

    try:
        user_data = sheet_manager.get_data(USERS_SHEET, user_id)
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
                sheet_manager.add_new_entry(USERS_SHEET, new_admin_data)
                await message.answer(Messages.ADMIN_REGISTERED, reply_markup=UIUX.admin_menu())
            else:
                all_users = sheet_manager.get_data(USERS_SHEET)
                logger.info(f"All users: {all_users}")
                admin_exists = any(user.get(UserFields.USER_STATUS) == UserStatus.ADMIN for user in all_users if isinstance(user, dict))
                if admin_exists:
                    new_user_data = {
                        UserFields.USER_ID: user_id,
                        UserFields.USERNAME: username,
                        UserFields.USER_STATUS: UserStatus.PENDING,
                        UserFields.USER_STATE: UserState.WAITING_REFERRAL
                    }
                    sheet_manager.add_new_entry(USERS_SHEET, new_user_data)
                    await message.answer(Messages.USER_WELCOME, reply_markup=types.ReplyKeyboardRemove())
                    await start_onboarding(message, state)
                else:
                    await message.answer(Messages.SYSTEM_NOT_READY)
        else:
            await handle_user_status(user_id, user_data, message, state)
    except Exception as e:
        logger.error(f"Error in cmd_start: {str(e)}", exc_info=True)
        await message.answer(Messages.ERROR)

async def handle_user_status(user_id: str, user_data: dict, message: types.Message, state: FSMContext):
    user_status = user_data.get(UserFields.USER_STATUS)
    if not user_status:
        logger.warning(f"User {user_id} has no USER_STATUS. Data: {user_data}")
        if str(user_id) in ADMIN_IDS:
            user_status = UserStatus.ADMIN
            sheet_manager.batch_update(USERS_SHEET, user_id, {UserFields.USER_STATUS: UserStatus.ADMIN, UserFields.USER_STATE: UserState.ADMIN_MENU})
        else:
            user_status = UserStatus.PENDING
            sheet_manager.batch_update(USERS_SHEET, user_id, {UserFields.USER_STATUS: UserStatus.PENDING, UserFields.USER_STATE: UserState.WAITING_REFERRAL})

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

@main_router.message(lambda message: message.text in [ButtonTexts.HELP, ButtonTexts.VIEW_RATES, ButtonTexts.MY_REQUESTS, ButtonTexts.CALCULATE_EXCHANGE])
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

async def main():
    dp.include_router(error_router)
    dp.include_router(main_router)
    dp.include_router(exchange_router)
    dp.include_router(onboarding_router)
    dp.include_router(user_router)
    dp.include_router(admin_router)

    for router in [onboarding_router, user_router, admin_router, exchange_router]:
        router.sheet_manager = sheet_manager
        router.bot = bot

    setup_exchange_router(return_to_main_menu, show_exchange_rates, show_help, show_user_requests)

    setup_global_error_handler(dp)

    logger.info("Bot started")
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Critical error during bot execution: {e}", exc_info=True)
    finally:
        await bot.session.close()
        logger.info("Bot stopped")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
