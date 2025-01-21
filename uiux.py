from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import math
from config import ButtonTexts, Messages, RequestStatus, RequestFields, UserFields

class UIUX:
    @staticmethod
    def main_menu():
        return ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text=ButtonTexts.MY_REQUESTS), KeyboardButton(text=ButtonTexts.CALCULATE_EXCHANGE)],
            [KeyboardButton(text=ButtonTexts.VIEW_RATES), KeyboardButton(text=ButtonTexts.HELP)]
        ], resize_keyboard=True)

    @staticmethod
    def admin_menu():
        return ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text=ButtonTexts.FRIENDS), KeyboardButton(text=ButtonTexts.REQUESTS)],
            [KeyboardButton(text=ButtonTexts.COMPLETED_REQUESTS), KeyboardButton(text=ButtonTexts.ANALYTICS)]
        ], resize_keyboard=True)

    @staticmethod
    def currency_keyboard(currencies):
        keyboard = []
        for i in range(0, len(currencies), 2):
            row = [KeyboardButton(text=curr) for curr in currencies[i:i+2]]
            keyboard.append(row)
        keyboard.append([KeyboardButton(text=ButtonTexts.CANCEL)])
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    
    @staticmethod
    def confirm_exchange():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=ButtonTexts.EXCHANGE, callback_data="confirm_exchange")],
            [InlineKeyboardButton(text=ButtonTexts.RECALCULATE, callback_data="recalculate")]
        ])

    @staticmethod
    def admin_request_actions(request_id, status):
        buttons = []
        if status == RequestStatus.CHECK:
            buttons.append([InlineKeyboardButton(text=ButtonTexts.ACCEPT_REQUEST, callback_data=f"admin_accept_{request_id}")])
        buttons.append([InlineKeyboardButton(text=ButtonTexts.REJECT_REQUEST, callback_data=f"admin_reject_{request_id}")])
        if status == RequestStatus.RUN:
            buttons.append([InlineKeyboardButton(text=ButtonTexts.COMPLETE_REQUEST, callback_data=f"admin_complete_{request_id}")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)


    @staticmethod
    def user_request_actions(request_id):
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=ButtonTexts.CANCEL_REQUEST, callback_data=f"cancel_request_{request_id}")]
        ])

    @staticmethod
    def help_actions():
        return ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text=ButtonTexts.WRITE_TO_ADMIN)],
            [KeyboardButton(text=ButtonTexts.BACK_TO_MENU)]
        ], resize_keyboard=True)

    @staticmethod
    def cancel_action():
        return ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text=ButtonTexts.CANCEL)]
        ], resize_keyboard=True)

    @staticmethod
    def admin_cancel_action():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=ButtonTexts.CANCEL, callback_data="admin_cancel")]
        ])

    @staticmethod
    def referral_actions(user_id):
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=ButtonTexts.CONFIRM_REFERRAL, callback_data=f"confirm_referral_{user_id}")],
            [InlineKeyboardButton(text=ButtonTexts.DOUBT_REFERRAL, callback_data=f"doubt_{user_id}")],
            [InlineKeyboardButton(text=ButtonTexts.BAN_USER, callback_data=f"ban_{user_id}")]
        ])

    @staticmethod
    def format_request(request, is_admin=False):
        status_text = RequestStatus.CHECK_TEXT if request[RequestFields.STATUS] == RequestStatus.CHECK else RequestStatus.RUN_TEXT
        date = datetime.strptime(request[RequestFields.CREATED_AT], "%Y-%m-%dT%H:%M:%S.%f").strftime("%d %b %y")
        
        formatted_request = Messages.REQUEST_FORMAT.format(
            request_id=request[RequestFields.REQUEST_ID],
            date=date,
            status_text=status_text,
            amount=f"{math.ceil(float(request[RequestFields.AMOUNT])):,}",
            source_currency=request[RequestFields.SOURCE_CURRENCY],
            result=f"{math.ceil(float(request[RequestFields.RESULT])):,}",
            target_currency=request[RequestFields.TARGET_CURRENCY]
        )
        
        if is_admin:
            formatted_request = Messages.ADMIN_REQUEST_FORMAT.format(
                username=request.get(UserFields.USERNAME, Messages.UNKNOWN_USER),
                request_id=request[RequestFields.REQUEST_ID],
                date=date,
                status_text=status_text,
                amount=f"{math.ceil(float(request[RequestFields.AMOUNT])):,}",
                source_currency=request[RequestFields.SOURCE_CURRENCY],
                result=f"{math.ceil(float(request[RequestFields.RESULT])):,}",
                target_currency=request[RequestFields.TARGET_CURRENCY]
            )
        
        return formatted_request

    @staticmethod
    def format_notification(message):
        return f"*Новое уведомление:*\n{message}"
 
    @staticmethod
    def help_menu():
        return ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text=ButtonTexts.BACK_TO_MENU)],
            [KeyboardButton(text=ButtonTexts.WRITE_TO_ADMIN)]
        ], resize_keyboard=True)

    @staticmethod
    def format_exchange_result(amount, source_currency, result, target_currency, rate):
        return Messages.EXCHANGE_RESULT.format(
            result=math.ceil(result),
            target_currency=target_currency,
            amount=math.ceil(amount),
            source_currency=source_currency,
            rate=rate
        )
        
def format_amount(amount):
    rounded = math.ceil(amount)
    formatted = f"{rounded:,}"
    return formatted
