from aiogram.fsm.state import State, StatesGroup


class AddProductStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_quantity = State()


class WriteOffStates(StatesGroup):
    waiting_for_quantity = State()


class SearchStates(StatesGroup):
    waiting_for_query = State()


class DeleteStates(StatesGroup):
    waiting_for_confirmation = State()