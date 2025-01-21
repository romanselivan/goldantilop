import logging
from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import USERS_SHEET, Messages, UserFields, UserStatus
from uiux import UIUX

onboarding_router = Router()

class OnboardingStates(StatesGroup):
    waiting_referral = State()

async def start_onboarding(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    sheet_manager = onboarding_router.sheet_manager
    user_data = sheet_manager.get_data(USERS_SHEET, user_id)
    
    referral_count = sum(1 for field in [UserFields.REFERRAL1_ID, UserFields.REFERRAL2_ID] if user_data.get(field))

    if referral_count == 0:
        await message.answer(Messages.ENTER_REFERRAL, reply_markup=types.ReplyKeyboardRemove())
    elif referral_count == 1:
        await message.answer(Messages.ENTER_SECOND_REFERRAL, reply_markup=types.ReplyKeyboardRemove())
    elif referral_count == 2:
        await message.answer(Messages.WAITING_REFERRAL_CONFIRMATION, reply_markup=types.ReplyKeyboardRemove())
    
    await state.set_state(OnboardingStates.waiting_referral)

@onboarding_router.message(OnboardingStates.waiting_referral)
async def process_referral(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    sheet_manager = onboarding_router.sheet_manager
    referral_username = message.text.strip()

    if not referral_username.startswith('@'):
        await message.answer(Messages.INVALID_REFERRAL_FORMAT)
        return

    referral_username = referral_username[1:]  # Убираем @

    if referral_username == message.from_user.username:
        await message.answer(Messages.SELF_REFERRAL_ERROR)
        return

    user_data = sheet_manager.get_data(USERS_SHEET, user_id)
    if user_data is None:
        await message.answer(Messages.ERROR_REFERRAL)
        return

    if referral_username in [user_data.get(UserFields.REFERRAL1_USERNAME), user_data.get(UserFields.REFERRAL2_USERNAME)]:
        await message.answer(Messages.DUPLICATE_REFERRAL)
        return

    referral_data = next((user for user in sheet_manager.get_data(USERS_SHEET) if user[UserFields.USERNAME] == referral_username and user[UserFields.USER_STATUS] in [UserStatus.ADMIN, UserStatus.ACTIVE]), None)
    if not referral_data:
        await message.answer(Messages.UNKNOWN_REFERRAL)
        return

    referral_field = UserFields.REFERRAL1_ID if not user_data.get(UserFields.REFERRAL1_ID) else UserFields.REFERRAL2_ID
    sheet_manager.batch_update(USERS_SHEET, user_id, {
        referral_field: referral_data[UserFields.USER_ID],
        f'{referral_field[:-3]}_USERNAME': referral_username,
        f'{referral_field[:-3]}_STATUS': 'ask'
    })

    await send_referral_request(user_id, referral_data[UserFields.USER_ID])
    await message.answer(Messages.REFERRAL_REQUEST_SENT.format(username=referral_username), reply_markup=UIUX.cancel_action())
    await start_onboarding(message, state)

async def send_referral_request(user_id: str, referral_id: str):
    sheet_manager = onboarding_router.sheet_manager
    user_data = sheet_manager.get_data(USERS_SHEET, user_id)
    
    sent_message = await onboarding_router.bot.send_message(
        chat_id=referral_id,
        text=Messages.REFERRAL_CONFIRMATION_REQUEST.format(username=user_data[UserFields.USERNAME]),
        reply_markup=UIUX.referral_actions(user_id)
    )
    
    sheet_manager.batch_update(USERS_SHEET, user_id, {f"{UserFields.REFERRAL1_MESSAGE_ID if referral_id == user_data[UserFields.REFERRAL1_ID] else UserFields.REFERRAL2_MESSAGE_ID}": sent_message.message_id})

@onboarding_router.callback_query(F.data.startswith("confirm_referral_"))
async def confirm_referral(callback: CallbackQuery):
    sheet_manager = onboarding_router.sheet_manager
    user_id = callback.data.split('_')[2]
    referral_id = str(callback.from_user.id)
    
    user_data = sheet_manager.get_data(USERS_SHEET, user_id)
    if user_data is None:
        await callback.answer(Messages.REFERRAL_NOT_EXIST)
        return

    referral_field = 'REFERRAL1' if user_data.get('REFERRAL1_ID') == referral_id else 'REFERRAL2'
    
    sheet_manager.batch_update(USERS_SHEET, user_id, {f'{referral_field}_STATUS': 'ok'})
    
    await callback.answer(Messages.REFERRAL_APPROVE.format(username=user_data[UserFields.USERNAME]))
    await callback.message.edit_text(Messages.REFERRAL_APPROVE.format(username=user_data[UserFields.USERNAME]), reply_markup=None)

    other_referral_field = 'REFERRAL2' if referral_field == 'REFERRAL1' else 'REFERRAL1'
    other_referral_id = user_data.get(f'{other_referral_field}_ID')
    other_message_id = user_data.get(f'{other_referral_field}_MESSAGE_ID')

    if other_referral_id and other_message_id:
        try:
            await onboarding_router.bot.delete_message(chat_id=other_referral_id, message_id=other_message_id)
        except Exception as e:
            logging.error(f"Error deleting message for other referral: {e}")

    await check_user_status(user_id)

@onboarding_router.callback_query(F.data.startswith("doubt_"))
async def doubt_referral(callback: CallbackQuery):
    sheet_manager = onboarding_router.sheet_manager
    user_id = callback.data.split('_')[1]
    referral_id = str(callback.from_user.id)
    
    user_data = sheet_manager.get_data(USERS_SHEET, user_id)
    referral_field = 'REFERRAL1' if user_data['REFERRAL1_ID'] == referral_id else 'REFERRAL2'
    
    sheet_manager.batch_update(USERS_SHEET, user_id, {f'{referral_field}_STATUS': 'notsure'})
    await callback.answer(Messages.REFERRAL_REJECT)
    await callback.message.edit_text(Messages.REFERRAL_REJECT, reply_markup=None)
    await check_user_status(user_id)

@onboarding_router.callback_query(F.data.startswith("ban_"))
async def ban_user(callback: CallbackQuery):
    sheet_manager = onboarding_router.sheet_manager
    user_id = callback.data.split('_')[1]
    user_data = sheet_manager.get_data(USERS_SHEET, user_id)
    sheet_manager.batch_update(USERS_SHEET, user_id, {'USER_STATUS': 'ban'})
    await callback.answer(Messages.REFERRAL_BAN.format(username=user_data[UserFields.USERNAME]))
    await callback.message.edit_text(Messages.REFERRAL_BAN.format(username=user_data[UserFields.USERNAME]), reply_markup=None)
    await onboarding_router.bot.send_message(chat_id=user_id, text=Messages.USER_BANNED)

async def check_user_status(user_id: str):
    sheet_manager = onboarding_router.sheet_manager
    user_data = sheet_manager.get_data(USERS_SHEET, user_id)
    referral1_status = user_data.get(UserFields.REFERRAL1_STATUS)
    referral2_status = user_data.get(UserFields.REFERRAL2_STATUS)

    if 'ok' in [referral1_status, referral2_status]:
        sheet_manager.batch_update(USERS_SHEET, user_id, {
            UserFields.USER_STATUS: UserStatus.ACTIVE,
            UserFields.USER_STATE: 'user_menu'
        })
        
        confirmed_referral = user_data[UserFields.REFERRAL1_USERNAME] if referral1_status == 'ok' else user_data[UserFields.REFERRAL2_USERNAME]
        await onboarding_router.bot.send_message(
            chat_id=user_id,
            text=Messages.ACCOUNT_ACTIVATED.format(username=confirmed_referral),
            reply_markup=UIUX.main_menu()
        )

    elif referral1_status == 'notsure' and referral2_status == 'notsure':
        sheet_manager.batch_update(USERS_SHEET, user_id, {UserFields.USER_STATUS: UserStatus.BAN})
        await onboarding_router.bot.send_message(chat_id=user_id, text=Messages.ACCOUNT_BANNED)