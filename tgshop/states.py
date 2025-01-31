from aiogram.fsm.state import State, StatesGroup

class AddToCartStates(StatesGroup):
    waiting_for_quantity = State()  # Состояние ожидания ввода количества 