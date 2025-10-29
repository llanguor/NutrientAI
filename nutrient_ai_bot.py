import json_io
from nutrient_ai_network import predict
import json
import telebot
import threading
from telebot import types
from logger import get_logger
from json_io import load_data, save_data
import os

saved_dishes_path = "saved_dishes.json"
data_path = "appsettings.json"

logger = get_logger()
data = load_data(data_path)
saved_dishes = load_data(saved_dishes_path)

tg_session = telebot.TeleBot(data["tg_token"])
logger.info("Successfully logged into Telegram")



def run_polling():
    while True:
        try:
            tg_session.polling(none_stop=True, interval=1)
        except Exception as e:
            logger.error(f"Exception in polling: {e}")


def start_bot_thread():
    threading.Thread(target=run_polling, daemon=True).start()
    threading.Event().wait()


def register_handlers(bot: telebot.TeleBot):

    @bot.message_handler(commands=['start'])
    def start(message):
        """Приветственное сообщение"""
        try:
            logger.info(f"User {message.chat.id} called /start")
            bot.send_message(
                message.chat.id,
                "👋 Привет!\nОтправь название блюда, чтобы узнать его КБЖУ",
                disable_notification=True
            )
        except Exception as e:
            logger.error(f"Error in /start for user {message.chat.id}: {e}")
            bot.send_message(message.chat.id, "Ошибка при выполнении команды /start")

    @bot.message_handler(commands=['list'])
    def my_list(message):
        """Показ сохранённых блюд"""
        try:
            user_id = str(message.chat.id)
            user_items = saved_dishes.get(user_id, [])

            if not user_items:
                bot.send_message(message.chat.id, "📭 Ваш список пуст.")
                return

            text = "📋 *Ваш список сохранённых блюд:*\n\n"
            for item in user_items:
                text += (
                    f"*{item['dish']}*\n"
                    f"🔥 Калории: `{item['calories']:.0f}`\n"
                    f"🥩 Белки: `{item['proteins']:.1f}`\n"
                    f"🥑 Жиры: `{item['fats']:.1f}`\n"
                    f"🍞 Углеводы: `{item['carbs']:.1f}`\n\n"
                )

            bot.send_message(message.chat.id, text, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error in /mylist: {e}")
            bot.send_message(message.chat.id, "Ошибка при чтении списка")

    @bot.message_handler(func=lambda message: True)
    def all_messages(message):
        """Реакция на все текстовые сообщения"""
        try:
            if "/" in message.text:
                return

            if not message.text:
                bot.send_message(message.chat.id, "Пожалуйста, отправь название блюда текстом")
                return

            dish_name = message.text.strip()
            logger.info(f"User {message.chat.id} get dish: {dish_name}")

            calories, fats, carbs, proteins = predict(dish_name)

            answer = (
                f"*{dish_name}*\n"
                f"🔥 Калории: {calories:.0f} ккал\n"
                f"🥩 Белки: {proteins:.1f} г\n"
                f"🥑 Жиры: {fats:.1f} г\n"
                f"🍞 Углеводы: {carbs:.1f} г"
            )

            markup = types.InlineKeyboardMarkup()
            save_btn = types.InlineKeyboardButton(
                text="Сохранить в мой список",
                callback_data=f"save|{dish_name}"
            )
            markup.add(save_btn)

            # Отправляем сообщение
            bot.send_message(message.chat.id, answer, parse_mode="Markdown", reply_markup=markup)

        except Exception as e:
            logger.error(f"Error in all_messages handler: {e}")
            bot.send_message(message.chat.id, "Не удалось определить КБЖУ. Попробуй другое блюдо.")


    @bot.callback_query_handler(func=lambda call: call.data.startswith("save|"))
    def save_dish_callback(call):
        try:
            dish_name = call.data.split("|", 1)[1]
            user_id = str(call.message.chat.id)

            # Пересчёт КБЖУ (чтобы точно сохранить те же данные)
            calories, fats, carbs, proteins = predict(dish_name)
            user_items = saved_dishes.get(user_id, [])

            # Проверяем, есть ли уже это блюдо
            if any(item['dish'].lower() == dish_name.lower() for item in user_items):
                bot.answer_callback_query(call.id, "⚠️ Это блюдо уже есть в списке.")
                return

            # Добавляем новое блюдо
            user_items.append({
                "dish": dish_name,
                "calories": float(calories),
                "fats": float(fats),
                "carbs": float(carbs),
                "proteins": float(proteins)
            })
            saved_dishes[user_id] = user_items

            json_io.save_data(saved_dishes_path, saved_dishes)

            bot.answer_callback_query(call.id, "✅ Добавлено в ваш список!")

        except Exception as e:
            logger.error(f"Error in save_dish_callback: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка при сохранении.")



register_handlers(tg_session)