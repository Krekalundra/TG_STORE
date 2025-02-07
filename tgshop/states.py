from aiogram.fsm.state import State, StatesGroup

class AddToCartStates(StatesGroup):
    waiting_for_quantity = State()  # Состояние ожидания ввода количества

class OrderStates(StatesGroup):
    waiting_for_name = State()  # Добавляем новое состояние
    waiting_for_phone = State()
    waiting_for_delivery = State()
    waiting_for_address = State()
    waiting_for_comment = State() 