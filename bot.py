import os
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters import Command

# Получаем токен из переменных окружения
TOKEN = os.getenv(
    "BOT_TOKEN", 
    "8260705298:AAENyMKweAnwU_lV59_9lh00Rt-Wahu43bg"
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Создаем бота и диспетчер
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

CREATOR_ID = 1344785777

# В aiogram 2.x нет StatesGroup, поэтому определим состояния как класс
class MessageStates:
    waiting_for_message = 'waiting_for_message'
    waiting_for_reply = 'waiting_for_reply'

messages_db = {}

@dp.message_handler(Command("start"))
async def cmd_start(message: types.Message):
    welcome_text = """👋 Анонимный Бот для Сообщений

✨ Send anonymous messages to the bot creator!

📝 Как использовать:
1. Нажмите /send чтобы начать создание сообщения
2. Напишите ваше анонимное сообщение
3. Оно будет доставлено анонимно

🛡️ Ваша конфиденциальность гарантирована:
• Информация об отправителе не собирается и не передается
• Сообщения нельзя отследить до вас
• Ваша личность остается полностью скрытой

🔍 Доступные команды:
/start - Показать это приветственное сообщение
/send - Отправить анонимное сообщение
/info - Информация о боте
"""
    await message.answer(welcome_text)


@dp.message_handler(Command("info"))
async def cmd_info(message: types.Message):
    info_text = """🤖 Анонимный Бот для Сообщений

Версия 1.2

🔒 Функции конфиденциальности:
• Полная анонимность
• Нет сбора информации об отправителях
• Нет хранения данных пользователей
• Безопасная доставка сообщений

📊 Статистика:
• Данный бот не собирает никакой информации о пользователях.
• Создатель видит только текст сообщений без каких-либо данных 
  об отправителе.

🛠️ Создатель:
• Разработано с ❤️ от @w3yron
• Помогу создать такого же бота лично для вас❤️

💳 Поддержи автора:
<code>2200700882269227 Т-Банк</code>
Нажмите на номер карты, чтобы скопировать

⚠️ Важно:
Этот бот предназначен только для законного анонимного общения.
Создатель не виноват в нарушении правил спокойного общения.
"""
    await message.answer(info_text, parse_mode="HTML")


@dp.message_handler(Command("send"))
async def cmd_send(message: types.Message):
    instructions = """✍️ Составьте ваше анонимное сообщение:

• Напишите ваше сообщение ниже (макс. 4000 символов)
• Вы можете использовать текст, эмодзи и базовое форматирование
• Нажмите /cancel для отмены

Ваше сообщение будет доставлено полностью анонимно.
"""
    await message.answer(instructions)
    await MessageStates.waiting_for_message.set()


@dp.message_handler(state=MessageStates.waiting_for_message)
async def process_anonymous_message(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, отправьте текстовое сообщение.")
        return

    if len(message.text) > 4000:
        msg = ("❌ Сообщение слишком длинное. "
               "Пожалуйста, ограничьтесь 4000 символами.")
        await message.answer(msg)
        return

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(
            text="✅ Подтвердить",
            callback_data=f"confirm_{message.message_id}"
        ),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )

    await message.answer(
        f"📝 Предпросмотр сообщения:\n\n{message.text}\n\n"
        f"Отправить это сообщение анонимно?",
        reply_markup=keyboard
    )

    await state.update_data(
        message_text=message.text,
        sender_id=message.from_user.id
    )


@dp.callback_query_handler(lambda c: c.data.startswith("confirm_"), state="*")
async def confirm_message(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    anonymous_message = f"""🔔 Новое Анонимное Сообщение
━━━━━━━━━━━━━━━━━━━━
{data.get('message_text', 'Сообщение отсутствует')}
━━━━━━━━━━━━━━━━━━━━
Получено через Анонимный Бот
"""

    reply_keyboard = InlineKeyboardMarkup()
    reply_keyboard.add(
        InlineKeyboardButton(
            text="💬 Ответить Анонимно",
            callback_data=f"reply_{data.get('sender_id', 0)}"
        )
    )

    try:
        sent_message = await bot.send_message(
            chat_id=CREATOR_ID,
            text=anonymous_message,
            reply_markup=reply_keyboard
        )

        messages_db[sent_message.message_id] = {
            "sender_id": data.get('sender_id'),
            "original_msg_id": callback.message.message_id
        }

        success_msg = """✅ *Сообщение отправлено анонимно!*

Ваше сообщение было успешно доставлено создателю.

🛡️ *Ваша конфиденциальность:*
• Никакая информация об отправителе не собирается и не передаётся
• Сообщения нельзя отследить до вас
• Ваша личность остается полностью скрытой

_Спасибо за использование нашего сервиса!_"""

        await callback.message.edit_text(
            success_msg,
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")
        error_msg = """❌ *Не удалось отправить сообщение.*

Пожалуйста, попробуйте позже

_Приносим извинения за неудобства._"""
        await callback.message.edit_text(
            error_msg,
            parse_mode="Markdown"
        )

    await state.finish()
    await callback.answer()


@dp.callback_query_handler(lambda c: c.data == "cancel", state="*")
async def cancel_message(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("❌ Отправка сообщения отменена.")
    await state.finish()
    await callback.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("reply_"), state="*")
async def start_reply(callback: types.CallbackQuery, state: FSMContext):
    try:
        sender_id = int(callback.data.split("_")[1])
        await MessageStates.waiting_for_reply.set()
        await state.update_data(
            recipient_id=sender_id,
            original_callback=callback
        )

        reply_keyboard = InlineKeyboardMarkup()
        reply_keyboard.add(
            InlineKeyboardButton(
                text="❌ Отменить ответ",
                callback_data="cancel_reply"
            )
        )

        msg1 = "💭 Напишите ваш анонимный ответ:\n\n"
        msg2 = "Получатель не будет знать, что это от вас."

        await callback.message.answer(
            msg1 + msg2,
            reply_markup=reply_keyboard
        )
    except (IndexError, ValueError) as e:
        logger.error(f"Ошибка при обработке callback: {e}")
        await callback.answer("❌ Ошибка: неверный формат данных")
    await callback.answer()


@dp.message_handler(state=MessageStates.waiting_for_reply)
async def process_reply(message: types.Message, state: FSMContext):
    data = await state.get_data()

    if not message.text:
        await message.answer("❌ Пожалуйста, отправьте текстовое сообщение.")
        return

    reply_message = f"""💌 Анонимный Ответ
━━━━━━━━━━━━━━━━━━━━
{message.text}
━━━━━━━━━━━━━━━━━━━━
Это анонимный ответ на ваше сообщение
"""

    try:
        await bot.send_message(
            chat_id=data.get('recipient_id'),
            text=reply_message
        )
        await message.answer("✅ Ответ отправлен анонимно!")
    except Exception as e:
        logger.error(f"Ошибка при отправке ответа: {e}")
        msg = ("❌ Не удалось отправить ответ. "
               "Возможно, пользователь заблокировал бота.")
        await message.answer(msg)

    await state.finish()


@dp.callback_query_handler(lambda c: c.data == "cancel_reply", state="*")
async def cancel_reply(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("❌ Отправка ответа отменена.")
    await state.finish()
    await callback.answer()


@dp.message_handler(Command("cancel"), state="*")
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("❌ Действие отменено.")


@dp.message_handler(state=None)
async def handle_any_message(message: types.Message):
    msg1 = "ℹ️ Напишите /send чтобы начать отправку анонимного сообщения\n"
    msg2 = "Напишите /info для получения дополнительной информации"
    await message.answer(msg1 + msg2)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
