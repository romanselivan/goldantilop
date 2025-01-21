from datetime import datetime
import math
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import USERS_SHEET, REQUESTS_SHEET, ButtonTexts, Messages, RequestFields, RequestStatus, UserFields, UserStatus
from uiux import UIUX

admin_router = Router()

class AdminStates(StatesGroup):
    # waiting_for_completion_message = State()
    waiting_for_rejection_message = State()

@admin_router.message(Command("admin"))
async def cmd_admin(message: Message):
    await message.answer(Messages.ADMIN_MENU_MESSAGE, reply_markup=UIUX.admin_menu())
    
@admin_router.message(F.text == ButtonTexts.FRIENDS)
async def show_friends(message: Message):
    sheet_manager = admin_router.sheet_manager
    all_users = sheet_manager.get_data(USERS_SHEET)
    active_users = [user for user in all_users if user[UserFields.USER_STATUS] == UserStatus.ACTIVE]
    
    response = Messages.ALL_USERS.format(total=len(all_users))
    response += Messages.ACTIVE_USERS_HEADER
    
    for user in active_users:
        response += Messages.ACTIVE_USER_INFO.format(
            username=user[UserFields.USERNAME],
            rating=user[UserFields.RATING],
            balance=user[UserFields.BALANCE]
        )
    
    await message.answer(response, reply_markup=UIUX.admin_menu())

@admin_router.message(F.text == ButtonTexts.REQUESTS)
async def show_admin_requests(message: Message):
    sheet_manager = admin_router.sheet_manager
    all_requests = sheet_manager.get_data(REQUESTS_SHEET)
    
    active_requests = [req for req in all_requests if req[RequestFields.STATUS] in [RequestStatus.CHECK, RequestStatus.RUN]]
    
    if not active_requests:
        await message.answer(Messages.NO_REQUESTS, reply_markup=UIUX.admin_menu())
        return
    
    for req in active_requests:
        await message.answer(
            UIUX.format_request(req, is_admin=True),
            reply_markup=UIUX.admin_request_actions(req[RequestFields.REQUEST_ID], req[RequestFields.STATUS]),
            parse_mode="Markdown"
        )
    
    await message.answer(Messages.ADMIN_MENU_MESSAGE, reply_markup=UIUX.admin_menu())

@admin_router.message(F.text == ButtonTexts.COMPLETED_REQUESTS)
async def show_completed_requests(message: Message):
    sheet_manager = admin_router.sheet_manager
    all_requests = sheet_manager.get_data(REQUESTS_SHEET)
    
    completed_requests = [req for req in all_requests if req[RequestFields.STATUS] == RequestStatus.DONE]
    
    if not completed_requests:
        await message.answer(Messages.NO_COMPLETED_REQUESTS, reply_markup=UIUX.admin_menu())
        return
    
    response = Messages.COMPLETED_REQUESTS_HEADER
    for req in completed_requests:
        user_data = sheet_manager.get_data(USERS_SHEET, req[RequestFields.USER_ID])
        username = user_data[UserFields.USERNAME] if user_data else Messages.UNKNOWN_USER
        completed_date = datetime.strptime(req[RequestFields.UPDATED_AT], "%Y-%m-%dT%H:%M:%S.%f").strftime("%d/%m/%y")
        response += (
            f"@{username}: {math.ceil(float(req[RequestFields.AMOUNT])):,} {req[RequestFields.SOURCE_CURRENCY]} -> "
            f"{math.ceil(float(req[RequestFields.RESULT])):,} {req[RequestFields.TARGET_CURRENCY]}, {completed_date}\n"
        )
    
    await message.answer(response, reply_markup=UIUX.admin_menu())

@admin_router.message(F.text == ButtonTexts.ANALYTICS)
async def show_analytics(message: Message):
    sheet_manager = admin_router.sheet_manager
    all_users = sheet_manager.get_data(USERS_SHEET)
    all_requests = sheet_manager.get_data(REQUESTS_SHEET)
    
    total_users = len(all_users)
    total_exchanges = len([req for req in all_requests if req[RequestFields.STATUS] == RequestStatus.DONE])
    
    if total_exchanges > 0:
        average_exchange_volume = sum(math.ceil(float(req[RequestFields.AMOUNT])) for req in all_requests if req[RequestFields.STATUS] == RequestStatus.DONE) / total_exchanges
    else:
        average_exchange_volume = 0

    currency_pairs = [(req[RequestFields.SOURCE_CURRENCY], req[RequestFields.TARGET_CURRENCY]) for req in all_requests if req[RequestFields.STATUS] == RequestStatus.DONE]
    most_popular_pair = max(set(currency_pairs), key=currency_pairs.count) if currency_pairs else None

    response = Messages.ANALYTICS_HEADER
    response += Messages.TOTAL_USERS.format(total_users=total_users)
    response += Messages.TOTAL_EXCHANGES.format(total_exchanges=total_exchanges)
    response += Messages.AVERAGE_EXCHANGE_VOLUME.format(average_volume=math.ceil(average_exchange_volume))
    response += Messages.MOST_POPULAR_PAIR.format(pair=' -> '.join(most_popular_pair) if most_popular_pair else Messages.NO_DATA)
    
    await message.answer(response, reply_markup=UIUX.admin_menu())

@admin_router.callback_query(F.data.startswith("admin_accept_"))
async def admin_accept_request(callback: CallbackQuery):
    sheet_manager = admin_router.sheet_manager
    request_id = callback.data.split('_')[-1]
    sheet_manager.batch_update(REQUESTS_SHEET, request_id, {RequestFields.STATUS: RequestStatus.RUN})
    await callback.answer(Messages.REQUEST_ACCEPTED)
    
    request_data = sheet_manager.get_data(REQUESTS_SHEET, request_id)
    await callback.message.edit_text(
        UIUX.format_request(request_data),
        reply_markup=UIUX.admin_request_actions(request_id, RequestStatus.RUN),
        parse_mode="Markdown"
    )
    
    # Уведомление пользователя
    user_id = request_data[RequestFields.USER_ID]
    await notify_user_status_change(user_id, request_id, RequestStatus.RUN)

@admin_router.callback_query(F.data.startswith("admin_reject_"))
async def admin_reject_request(callback: CallbackQuery, state: FSMContext):
    sheet_manager = admin_router.sheet_manager
    request_id = callback.data.split('_')[-1]
    await state.update_data(request_id=request_id)
    await callback.message.edit_text(Messages.ENTER_REJECTION_MESSAGE, reply_markup=None)
    await state.set_state(AdminStates.waiting_for_rejection_message)

@admin_router.message(AdminStates.waiting_for_rejection_message)
async def process_rejection_message(message: Message, state: FSMContext):
    sheet_manager = admin_router.sheet_manager
    user_data = await state.get_data()
    request_id = user_data['request_id']
    
    sheet_manager.batch_update(REQUESTS_SHEET, request_id, {RequestFields.STATUS: RequestStatus.CANCEL})
    
    request_data = sheet_manager.get_data(REQUESTS_SHEET, request_id)
    user_id = request_data[RequestFields.USER_ID]
    
    await notify_user_status_change(user_id, request_id, RequestStatus.CANCEL, message.text)
    
    await message.answer(Messages.ADMIN_REQUEST_REJECTED, reply_markup=UIUX.admin_menu())
    await state.clear()

@admin_router.callback_query(F.data.startswith("admin_complete_"))
async def admin_complete_request(callback: CallbackQuery, state: FSMContext):
    sheet_manager = admin_router.sheet_manager
    request_id = callback.data.split('_')[-1]
    
    sheet_manager.batch_update(REQUESTS_SHEET, request_id, {RequestFields.STATUS: RequestStatus.DONE})
    
    request_data = sheet_manager.get_data(REQUESTS_SHEET, request_id)
    user_id = request_data[RequestFields.USER_ID]
    
    await notify_user_status_change(user_id, request_id, RequestStatus.DONE)
    
    await callback.message.edit_text(Messages.ADMIN_REQUEST_COMPLETED, reply_markup=None)
    await callback.answer(Messages.ADMIN_REQUEST_COMPLETED)

# @admin_router.message(AdminStates.waiting_for_completion_message)
# async def process_completion_message(message: Message, state: FSMContext):
#     sheet_manager = admin_router.sheet_manager
#     user_data = await state.get_data()
#     request_id = user_data.get('request_id')
    
#     if not request_id:
#         await message.answer(Messages.ERROR_NO_REQUEST_ID, reply_markup=UIUX.admin_menu())
#         await state.clear()
#         return

#     sheet_manager.batch_update(REQUESTS_SHEET, request_id, {RequestFields.STATUS: RequestStatus.DONE})
    
#     # Уведомление пользователя
#     request_data = sheet_manager.get_data(REQUESTS_SHEET, request_id)
#     user_id = request_data[RequestFields.USER_ID]
    
#     await notify_user_status_change(user_id, request_id, RequestStatus.DONE, message.text)
    
#     await message.answer(Messages.ADMIN_REQUEST_COMPLETED, reply_markup=UIUX.admin_menu())
#     await state.clear()

async def notify_user_status_change(user_id, request_id, status, message=None):
    if status == RequestStatus.RUN:
        notification = Messages.REQUEST_ACCEPTED.format(request_id=request_id)
    elif status == RequestStatus.CANCEL:
        if message:
            notification = Messages.REQUEST_REJECTED_WITH_REASON.format(request_id=request_id, reason=message)
        else:
            notification = Messages.REQUEST_REJECTED.format(request_id=request_id)
    elif status == RequestStatus.DONE:
        notification = Messages.REQUEST_COMPLETED.format(request_id=request_id)
    else:
        notification = Messages.REQUEST_STATUS_CHANGED.format(request_id=request_id, status=status)

    await admin_router.bot.send_message(user_id, notification)

async def notify_admin_request_cancelled(bot, admin_id, request_id):
    message = Messages.USER_CANCELLED_REQUEST.format(request_id=request_id)
    await bot.send_message(chat_id=admin_id, text=message)

async def notify_admin(bot, sheet_manager, message, keyboard=None):
    admin_users = [user for user in sheet_manager.get_data(USERS_SHEET) if user[UserFields.USER_STATUS] == 'admin']
    for admin in admin_users:
        formatted_message = UIUX.format_notification(message)
        await bot.send_message(chat_id=admin[UserFields.USER_ID], text=formatted_message, reply_markup=keyboard, parse_mode="Markdown")
