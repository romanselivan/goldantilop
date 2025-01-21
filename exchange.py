import logging
from typing import Union
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from states import ExchangeStates
import math
from datetime import datetime
import uuid
from config import RATES_SHEET, REQUESTS_SHEET, USERS_SHEET, ButtonTexts, Messages, RateFields, RequestFields, RequestStatus, UserFields, UserStatus
from uiux import UIUX

exchange_router = Router()

__all__ = ['exchange_router', 'setup_exchange_router']

def generate_request_id():
    current_time = datetime.now()
    milliseconds = current_time.microsecond // 1000
    ms_chars = f"{milliseconds:03d}"[:2]
    random_char = uuid.uuid4().hex[0]
    last_char = uuid.uuid4().hex[0]
    return f"{ms_chars}{random_char}{last_char}".upper()

@exchange_router.message(F.text == ButtonTexts.CALCULATE_EXCHANGE)
@exchange_router.callback_query(F.data == "recalculate")
async def start_exchange(message: Union[Message, CallbackQuery], state: FSMContext):
    await state.clear()
    sheet_manager = exchange_router.sheet_manager
    source_currencies = get_source_currencies(sheet_manager)
    
    kb = InlineKeyboardBuilder()
    for currency in source_currencies:
        kb.button(text=currency, callback_data=f"source_{currency}")
    kb.adjust(3)
    
    text = Messages.CHOOSE_SOURCE_CURRENCY
    
    if isinstance(message, CallbackQuery):
        await message.answer()
        await message.message.edit_text(text, reply_markup=kb.as_markup())
    else:
        await message.answer(text, reply_markup=kb.as_markup())
    
    await state.set_state(ExchangeStates.choosing_source)

@exchange_router.message(lambda message: message.text in [ButtonTexts.MY_REQUESTS, ButtonTexts.VIEW_RATES, ButtonTexts.HELP, ButtonTexts.BACK_TO_MENU])
async def interrupt_exchange(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state in [ExchangeStates.choosing_source, ExchangeStates.choosing_target, ExchangeStates.entering_amount]:
        await state.clear()
        await message.answer(Messages.OPERATION_CANCELLED, reply_markup=UIUX.main_menu())
        
        if message.text == ButtonTexts.MY_REQUESTS:
            await show_user_requests(message)
        elif message.text == ButtonTexts.VIEW_RATES:
            await show_exchange_rates(message)
        elif message.text == ButtonTexts.HELP:
            await show_help(message, state)
        else:
            await return_to_main_menu(message, state)
    else:
        if message.text == ButtonTexts.MY_REQUESTS:
            await show_user_requests(message)
        elif message.text == ButtonTexts.VIEW_RATES:
            await show_exchange_rates(message)
        elif message.text == ButtonTexts.HELP:
            await show_help(message, state)
        elif message.text == ButtonTexts.BACK_TO_MENU:
            await return_to_main_menu(message, state)

@exchange_router.callback_query(lambda c: c.data.startswith('source_'))
async def process_source_currency(callback: CallbackQuery, state: FSMContext):
    if callback.message.text in [ButtonTexts.MY_REQUESTS, ButtonTexts.VIEW_RATES, ButtonTexts.HELP, ButtonTexts.BACK_TO_MENU]:
        await interrupt_exchange(callback.message, state)
        return
    source_currency = callback.data.split('_')[1]
    await state.update_data(SELECTED_SOURCE_CURRENCY=source_currency)
    
    target_currencies = get_target_currencies(exchange_router.sheet_manager, source_currency)
    
    kb = InlineKeyboardBuilder()
    for currency in target_currencies:
        kb.button(text=currency, callback_data=f"target_{currency}")
    kb.adjust(3)
    
    await callback.message.edit_text(
        Messages.SOURCE_AND_TARGET_CURRENCY.format(source_currency=source_currency),
        reply_markup=kb.as_markup()
    )
    await state.set_state(ExchangeStates.choosing_target)

@exchange_router.callback_query(lambda c: c.data.startswith('target_'))
async def process_target_currency(callback: CallbackQuery, state: FSMContext):
    if callback.message.text in [ButtonTexts.MY_REQUESTS, ButtonTexts.VIEW_RATES, ButtonTexts.HELP, ButtonTexts.BACK_TO_MENU]:
        await interrupt_exchange(callback.message, state)
        return
    target_currency = callback.data.split('_')[1]
    user_data = await state.get_data()
    source_currency = user_data['SELECTED_SOURCE_CURRENCY']

    await state.update_data(SELECTED_TARGET_CURRENCY=target_currency)

    exchange_info = get_exchange_info(exchange_router.sheet_manager, source_currency, target_currency)
    if not exchange_info:
        await callback.message.edit_text(Messages.EXCHANGE_RATE_NOT_FOUND.format(source_currency=source_currency, target_currency=target_currency))
        await state.clear()
        return

    exchange_rate = float(exchange_info[RateFields.RATE])
    min_amount = float(exchange_info[RateFields.MIN_AMOUNT].replace(',', ''))
    await state.update_data(exchange_rate=exchange_rate, min_amount=min_amount)

    await callback.message.edit_text(
        Messages.ENTER_EXCHANGE_AMOUNT.format(
            source_currency=source_currency,
            target_currency=target_currency,
            min_amount=math.ceil(min_amount)
        )
    )
    await state.set_state(ExchangeStates.entering_amount)

@exchange_router.message(ExchangeStates.entering_amount)
async def process_amount(message: Message, state: FSMContext):
    if message.text in [ButtonTexts.MY_REQUESTS, ButtonTexts.VIEW_RATES, ButtonTexts.HELP, ButtonTexts.BACK_TO_MENU]:
        await interrupt_exchange(message, state)
        return

    try:
        user_data = await state.get_data()
        selected_source_currency = user_data['SELECTED_SOURCE_CURRENCY']
        selected_target_currency = user_data['SELECTED_TARGET_CURRENCY']
        exchange_rate = user_data['exchange_rate']
        min_amount = user_data['min_amount']

        amount = float(message.text.replace(',', '').strip())

        if amount < min_amount:
            await message.answer(
                Messages.MINIMUM_AMOUNT_ERROR.format(min_amount=math.ceil(min_amount), currency=selected_source_currency)
            )
            return

        result = math.ceil(amount * exchange_rate)
    
        await message.answer(
            UIUX.format_exchange_result(amount, selected_source_currency, result, selected_target_currency, exchange_rate),
            reply_markup=UIUX.confirm_exchange(),
            parse_mode="Markdown"
        )
        await state.update_data(amount=amount, result=result)
        await state.set_state(ExchangeStates.confirming_exchange)
    except ValueError:
        await message.answer(Messages.INVALID_AMOUNT)

@exchange_router.callback_query(F.data == "confirm_exchange")
async def confirm_exchange(callback: CallbackQuery, state: FSMContext):
    try:
        user_data = await state.get_data()
        if user_data.get("request_created"):
            await callback.answer(Messages.REQUEST_ALREADY_CREATED)
            return

        sheet_manager = exchange_router.sheet_manager
        
        user_id = str(callback.from_user.id)
        user_info = sheet_manager.get_data(USERS_SHEET, user_id)
        username = user_info.get(UserFields.USERNAME, Messages.UNKNOWN_USER)
        
        request_id = generate_request_id()
        logging.info(f"Generated REQUEST_ID: {request_id}")
        while sheet_manager.get_data(REQUESTS_SHEET, request_id):
            request_id = generate_request_id()
        
        new_request = {
            RequestFields.REQUEST_ID: request_id,
            RequestFields.USER_ID: user_id,
            RequestFields.USERNAME: username,
            RequestFields.SOURCE_CURRENCY: user_data['SELECTED_SOURCE_CURRENCY'],
            RequestFields.TARGET_CURRENCY: user_data['SELECTED_TARGET_CURRENCY'],
            RequestFields.AMOUNT: user_data['amount'],
            RequestFields.RESULT: user_data['result'],
            RequestFields.STATUS: RequestStatus.CHECK,
            RequestFields.CREATED_AT: datetime.now().isoformat(),
            RequestFields.UPDATED_AT: datetime.now().isoformat()
        }
        
        logging.info(f"Attempting to create new request: {new_request}")
        sheet_manager.add_new_entry(REQUESTS_SHEET, new_request)
        logging.info("New request created successfully")
        
        await callback.message.edit_text(
            UIUX.format_request(new_request),
            reply_markup=None,
            parse_mode="Markdown"
        )
        await callback.message.answer(Messages.EXCHANGE_CONFIRMED, reply_markup=UIUX.main_menu())
        
        admin_message = UIUX.format_request(new_request, is_admin=True)
        admin_keyboard = UIUX.admin_request_actions(new_request[RequestFields.REQUEST_ID], new_request[RequestFields.STATUS])
        await notify_admin(callback.bot, sheet_manager, admin_message, admin_keyboard)
        
        await state.update_data(request_created=True)
        await state.clear()

    except Exception as e:
        logging.error(f"Error in confirm_exchange: {e}", exc_info=True)
        await callback.answer(Messages.REQUEST_CREATION_ERROR)
        await state.clear()

@exchange_router.callback_query(F.data == "recalculate")
async def recalculate_exchange(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await start_exchange(callback, state)

def get_source_currencies(sheet_manager):
    rates = sheet_manager.get_data(RATES_SHEET)
    return list(set(rate[RateFields.SOURCE_CURRENCY] for rate in rates))

def get_target_currencies(sheet_manager, source_currency):
    rates = sheet_manager.get_data(RATES_SHEET)
    return list(set(rate[RateFields.TARGET_CURRENCY] for rate in rates if rate[RateFields.SOURCE_CURRENCY] == source_currency))

def get_exchange_info(sheet_manager, source_currency, target_currency):
    rates = sheet_manager.get_data(RATES_SHEET)
    return next((rate for rate in rates if rate[RateFields.SOURCE_CURRENCY] == source_currency and rate[RateFields.TARGET_CURRENCY] == target_currency), None)

async def notify_admin(bot, sheet_manager, message, keyboard=None):
    admin_users = [user for user in sheet_manager.get_data(USERS_SHEET) if user[UserFields.USER_STATUS] == UserStatus.ADMIN]
    for admin in admin_users:
        await bot.send_message(chat_id=admin[UserFields.USER_ID], text=message, reply_markup=keyboard)

def setup_exchange_router(return_to_main_menu_func, show_exchange_rates_func, show_help_func, show_user_requests_func, start_exchange_func=None):
    global return_to_main_menu, show_exchange_rates, show_help, show_user_requests, start_exchange
    return_to_main_menu = return_to_main_menu_func
    show_exchange_rates = show_exchange_rates_func
    show_help = show_help_func
    show_user_requests = show_user_requests_func
    if start_exchange_func:
        start_exchange = start_exchange_func