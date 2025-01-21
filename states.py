# states.py
from aiogram.fsm.state import State, StatesGroup

class ExchangeStates(StatesGroup):
    choosing_source = State()
    choosing_target = State()
    entering_amount = State()
    confirming_exchange = State()
