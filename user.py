from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.state import default_state
from config import USERS_SHEET, REQUESTS_SHEET, RATES_SHEET, ButtonTexts, Messages, RateFields, RequestFields, RequestStatus, UserFields, UserStatus
from exchange import start_exchange
from uiux import UIUX

user_router = Router()
user_router.sheet_manager = None

class AdminStates(StatesGroup):
    writing_to_admin = State()

async def main_menu(bot, user_id: str):
    await bot.send_message(chat_id=user_id, text=Messages.MAIN_MENU_TEXT, reply_markup=UIUX.main_menu())

@user_router.message(Command("menu"))
async def menu_command(message: types.Message):
    await main_menu(message.bot, str(message.from_user.id))

@user_router.message(F.text.in_({ButtonTexts.HELP, ButtonTexts.VIEW_RATES, ButtonTexts.MY_REQUESTS, ButtonTexts.CALCULATE_EXCHANGE}))
async def handle_main_menu_commands(message: types.Message, state: FSMContext):
    await state.clear()  # Прерываем текущее состояние
    if message.text == ButtonTexts.HELP:
        await show_help(message, state)
    elif message.text == ButtonTexts.VIEW_RATES:
        await show_exchange_rates(message)
    elif message.text == ButtonTexts.MY_REQUESTS:
        await show_user_requests(message)
    elif message.text == ButtonTexts.CALCULATE_EXCHANGE:
        await start_exchange(message, state)

@user_router.message(F.text == ButtonTexts.MY_REQUESTS)
async def show_user_requests(message: types.Message):
    sheet_manager = user_router.sheet_manager
    user_id = str(message.from_user.id)
    requests = get_user_requests(user_id, sheet_manager)
    
    active_requests = [req for req in requests if req[RequestFields.STATUS] in [RequestStatus.CHECK, RequestStatus.RUN]]

    if not active_requests:
        await message.answer(Messages.NO_REQUESTS)
        return

    for req in active_requests:
        if req[RequestFields.STATUS] in [RequestStatus.CHECK, RequestStatus.RUN]:
            await message.answer(
                UIUX.format_request(req, is_admin=False),
                reply_markup=UIUX.user_request_actions(req[RequestFields.REQUEST_ID]),
                parse_mode="Markdown"
            )
    
    await message.answer(Messages.MAIN_MENU_ACTION_MESSAGE, reply_markup=UIUX.main_menu())

@user_router.message(F.text == ButtonTexts.VIEW_RATES)
async def show_exchange_rates(message: types.Message):
    sheet_manager = user_router.sheet_manager
    rates = sheet_manager.get_data(RATES_SHEET)

    response = Messages.CURRENT_EXCHANGE_RATES

    all_pairs = {}

    for rate in rates:
        source_currency = rate[RateFields.SOURCE_CURRENCY]
        target_currency = rate[RateFields.TARGET_CURRENCY]
        rate_value = float(rate[RateFields.RATE])
        min_amount = rate[RateFields.MIN_AMOUNT]

        pair_key = (source_currency, target_currency)
        
        if pair_key not in all_pairs or rate_value > all_pairs[pair_key]['rate']:
            all_pairs[pair_key] = {
                'rate': rate_value,
                'min_amount': min_amount
            }

    for (source, target), data in all_pairs.items():
        if source != target and not (source in target or target in source):
            response += f"1 {source} = {data['rate']:.3f} {target} " \
                        f"({Messages.MIN_AMOUNT}: {int(float(data['min_amount'].replace(',', ''))):,})\n"

    await message.answer(response, reply_markup=UIUX.main_menu())

@user_router.message(Command("help"))
@user_router.message(F.text == ButtonTexts.HELP, StateFilter(default_state))
async def show_help(message: types.Message, state: FSMContext):
    await state.clear()
    help_text = (Messages.HELP_TEXT)
    await message.answer(help_text, reply_markup=UIUX.help_menu())

@user_router.message(Command("rates"))
@user_router.message(F.text == ButtonTexts.VIEW_RATES, StateFilter(default_state))
async def show_exchange_rates(message: Message, state: FSMContext):
    await state.clear()
    sheet_manager = user_router.sheet_manager
    rates = sheet_manager.get_data(RATES_SHEET)

    response = Messages.CURRENT_EXCHANGE_RATES

    all_pairs = {}

    for rate in rates:
        source_currency = rate[RateFields.SOURCE_CURRENCY]
        target_currency = rate[RateFields.TARGET_CURRENCY]
        rate_value = float(rate[RateFields.RATE])
        min_amount = rate[RateFields.MIN_AMOUNT]

        pair_key = (source_currency, target_currency)
        
        if pair_key not in all_pairs or rate_value > all_pairs[pair_key]['rate']:
            all_pairs[pair_key] = {
                'rate': rate_value,
                'min_amount': min_amount
            }

    for (source, target), data in all_pairs.items():
        if source != target and not (source in target or target in source):
            response += Messages.EXCHANGE_RATE_FORMAT.format(
                        source=source,
                        rate=data['rate'],
                        target=target,
                        min_amount=int(float(data['min_amount'].replace(',', '')))
                    )

    await message.answer(response, reply_markup=UIUX.main_menu())

@user_router.message(F.text == ButtonTexts.BACK_TO_MENU)
async def return_to_main_menu(message: Message, state: FSMContext):
    await state.clear()
    await main_menu(message.bot, str(message.from_user.id))

@user_router.message(F.text == ButtonTexts.WRITE_TO_ADMIN)
async def contact_admin(message: types.Message, state: FSMContext):
    await message.answer(Messages.WRITE_TO_ADMIN_PROMPT, reply_markup=UIUX.cancel_action())
    await state.set_state(AdminStates.writing_to_admin)

@user_router.message(F.text == ButtonTexts.CANCEL, StateFilter(AdminStates.writing_to_admin))
async def cancel_writing_to_admin(message: types.Message, state: FSMContext):
    await state.clear()
    await main_menu(message.bot, str(message.from_user.id))

@user_router.message(
    lambda message: message.text and message.text != ButtonTexts.BACK_TO_MENU,
    StateFilter(AdminStates.writing_to_admin)
)

async def process_user_message_to_admin(message: Message, state: FSMContext):
    sheet_manager = user_router.sheet_manager
    user_info = sheet_manager.get_data(USERS_SHEET, str(message.from_user.id))
    username = user_info.get(UserFields.USERNAME, Messages.UNKNOWN_USER)
    admin_message = f"{Messages.USER_MESSAGE_PREFIX} @{username}:\n\n{message.text}"
    await notify_admins(sheet_manager, admin_message)

    await message.answer(Messages.MESSAGE_SENT_TO_ADMIN, reply_markup=UIUX.main_menu())
    await state.clear()

@user_router.callback_query(F.data.startswith('cancel_request_'))
async def cancel_user_request(callback: CallbackQuery):
    sheet_manager = user_router.sheet_manager
    request_id = callback.data.split('_')[-1]
    request_data = sheet_manager.get_data(REQUESTS_SHEET, request_id)
    
    if request_data[RequestFields.STATUS] in [RequestStatus.CHECK, RequestStatus.RUN]:
        sheet_manager.batch_update(REQUESTS_SHEET, request_id, {RequestFields.STATUS: RequestStatus.CANCEL})
        await callback.answer(Messages.REQUEST_CANCELLED)
        await callback.message.edit_text(
            UIUX.format_request(request_data),
            reply_markup=None,
            parse_mode="Markdown"
        )
        
        # Уведомление админа
        admin_message = Messages.USER_CANCELLED_REQUEST.format(request_id=request_id)
        await notify_admin(callback.bot, sheet_manager, admin_message)
    else:
        await callback.answer(Messages.CANNOT_CANCEL_REQUEST)

@user_router.callback_query(F.data == "main_menu")
async def return_to_main_menu_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await main_menu(callback.bot, str(callback.from_user.id))

def get_user_requests(user_id, sheet_manager):
    all_requests = sheet_manager.get_data(REQUESTS_SHEET)
    user_requests = [req for req in all_requests if req[RequestFields.USER_ID] == user_id]
    
    # Получаем данные пользователя из таблицы Users
    user_data = sheet_manager.get_data(USERS_SHEET, user_id)
    username = user_data.get(UserFields.USERNAME, 'Unknown') if user_data else 'Unknown'
    
    # Добавляем username к каждой заявке
    for req in user_requests:
        req[RequestFields.USERNAME] = username
    
    return user_requests

async def notify_admin(bot, sheet_manager, message, keyboard=None):
    admin_users = [user for user in sheet_manager.get_data(USERS_SHEET) if user[UserFields.USER_STATUS] == UserStatus.ADMIN]
    for admin in admin_users:
        await bot.send_message(chat_id=admin[UserFields.USER_ID], text=message, reply_markup=keyboard)

async def notify_admins(sheet_manager, message):
    admin_users = [user for user in sheet_manager.get_data(USERS_SHEET) if user[UserFields.USER_STATUS] == UserStatus.ADMIN]
    for admin in admin_users:
        await user_router.bot.send_message(chat_id=admin[UserFields.USER_ID], text=message)