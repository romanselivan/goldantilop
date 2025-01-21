from aiogram.fsm.context import FSMContext
from aiogram import F, Router, types
from aiogram.types import Message
from uiux import UIUX
from user import main_menu
from config import Messages

user_router = Router()

async def show_help(message: Message, state: FSMContext):
    help_text = (Messages.HELP_TEXT)
    await message.answer(help_text, reply_markup=UIUX.help_menu())
    await state.set_state("waiting_for_help_action")

@user_router.message(F.text == "Вернуться в меню")
async def return_to_main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await main_menu(message.bot, str(message.from_user.id))
