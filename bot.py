import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен из переменных окружения
TOKEN = os.getenv("BOT_TOKEN", "8260705298:AAENyMKweAnwU_lV59_9lh00Rt-Wahu43bg")

# Инициализация
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

CREATOR_ID = 1344785777


class MessageStates(StatesGroup):
    waiting_for_message = State()
    waiting_for_reply = State()


messages_db = {}


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    welcome_text = """👋 Анонимный Бот для Сообщений
    
✨ Отправляйте анонимные сообщения создателю бота!

📝 Как использовать:
1. Нажмите /send чтобы начать
2. Напишите ваше сообщение
3. Оно будет доставлено анонимно

🛡️ Ваша конфиденциальность гарантирована"""
    
    await message.answer(welcome_text)


@dp.message_handler(commands=['send'], state='*')
async def cmd_send(message: types.Message):
    instructions = """✍️ Напишите ваше анонимное сообщение:
    
• Максимум 4000 символов
• Только текст
• Нажмите /cancel для отмены"""
    
    await message.answer(instructions)
    await MessageStates.waiting_for_message.set()


@dp.message_handler(state=MessageStates.waiting_for_message)
async def process_message(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Отправьте текстовое сообщение")
        return
    
    if len(message.text) > 4000:
        await message.answer("❌ Слишком длинное сообщение (макс. 4000 символов)")
        return
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Отправить", callback_data="confirm"),
        InlineKeyboardButton("❌ Отмена", callback_data="cancel")
    )
    
    await message.answer(
        f"📝 Ваше сообщение:\n\n{message.text}\n\nОтправить анонимно?",
        reply_markup=keyboard
    )
    
    await state.update_data(
        message_text=message.text,
        sender_id=message.from_user.id
    )


@dp.callback_query_handler(lambda c: c.data == 'confirm', state='*')
async def confirm_send(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    # Отправляем создателю
    try:
        message_to_creator = f"""🔔 Новое анонимное сообщение:
        
{data.get('message_text', '')}
        
_Отправлено через бота_"""
        
        await bot.send_message(CREATOR_ID, message_to_creator)
        await callback_query.message.edit_text("✅ Сообщение отправлено анонимно!")
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await callback_query.message.edit_text("❌ Ошибка при отправке")
    
    await state.finish()
    await callback_query.answer()


@dp.callback_query_handler(lambda c: c.data == 'cancel', state='*')
async def cancel_send(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text("❌ Отправка отменена")
    await state.finish()
    await callback_query.answer()


@dp.message_handler(commands=['cancel'], state='*')
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("❌ Действие отменено")


@dp.message_handler()
async def handle_other(message: types.Message):
    await message.answer("ℹ️ Используйте /send для отправки сообщения")


if __name__ == '__main__':
    logger.info("🚀 Бот запускается...")
    executor.start_polling(dp, skip_updates=True)
