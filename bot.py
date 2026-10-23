import os
import threading
from flask import Flask
import telebot
from telebot import types

# ==================== НАСТРОЙКИИ КОНФИГУРАЦИЯ ====================
TOKEN = "8983343058:AAH35u-bqLnEFHWKK52yKwq1lc0Nx9BtUbc"
ADMIN_ID = 6738122971
MARKUP = 1.0  # Фиксированная наценка в TJS

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# База данных пользователей (в памяти)
# Формат: user_id: {"referrals": int, "referred_by": int/None, "state": dict}
users_db = {}


# ==================== ВЕБ-СЕРВЕР ДЛЯ RENDER ====================
@app.route("/")
def home():
  return "PUBG & Free Fire Donat Bot is active and running 24/7!"


def run_web():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def get_user_data(user_id):
  if user_id not in users_db:
    users_db[user_id] = {"referrals": 0, "referred_by": None, "state": {}}
  return users_db[user_id]


# ==================== ОБРАБОТЧИКИ КОМАНД ====================
@bot.message_handler(commands=["start"])
def send_welcome(message):
  user_id = message.from_user.id
  user_data = get_user_data(user_id)
  args = message.text.split()

  # Обработка реферальной ссылки
  if len(args) > 1 and user_data["referred_by"] is None:
    try:
      referrer_id = int(args[1])
      if referrer_id != user_id and referrer_id in users_db:
        user_data["referred_by"] = referrer_id
        users_db[referrer_id]["referrals"] += 1
        bot.send_message(
            referrer_id,
            "🎉 По вашей вашей реферальной ссылке зарегистрировался новый"
            " игрок!",
        )
    except ValueError:
      pass

  bot_username = bot.get_me().username
  ref_link = (
      f"https://t.me/{bot_username}?start={user_id}" if bot_username else "N/A"
  )
  refs_count = user_data["referrals"]
  discount = 10 if refs_count >= 10 else 0

  welcome_text = (
      f"🎮 **Добро пожаловать в бот пополнения PUBG Mobile & Free Fire!**\n\n"
      f"📌 Наша наценка: **{MARKUP} TJS**\n"
      f"👥 Приглашено друзей: **{refs_count}/10**\n"
      f"🎁 Ваша скидка: **{discount}%**\n\n"
      f"🔗 Ваша реферальная ссылка:\n`{ref_link}`\n"
      f"_(Пригласите 10 друзей и получите постоянную скидку 10%!)_\n\n"
      f"Выберите нужную игру в меню ниже:"
  )

  markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
  markup.add(
      types.KeyboardButton("🎮 PUBG Mobile"),
      types.KeyboardButton("🔥 Free Fire"),
  )

  bot.send_message(
      message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup
  )


# ==================== ВЫБОР ИГРЫ И СПОСОБА ОПЛАТЫ ====================
@bot.message_handler(
    func=lambda message: message.text in ["🎮 PUBG Mobile", "🔥 Free Fire"]
)
def choose_game(message):
  user_id = message.from_user.id
  user_data = get_user_data(user_id)
  game_name = message.text

  user_data["state"] = {"game": game_name}

  markup = types.InlineKeyboardMarkup(row_width=1)
  markup.add(
      types.InlineKeyboardButton(
          "💳 Dushanbe City", callback_data=f"pay_dc_{game_name}"
      ),
      types.InlineKeyboardButton(
          "💳 Алиф Карта (Alif)", callback_data=f"pay_alif_{game_name}"
      ),
  )

  bot.send_message(
      message.chat.id,
      f"Вы выбрали **{game_name}**.\nВыберите удобный способ оплаты:",
      parse_mode="Markdown",
      reply_markup=markup,
  )


@bot.callback_query_handler(
    func=lambda call: call.data.startswith(("pay_dc_", "pay_alif_"))
)
def payment_method_selected(call):
  user_id = call.from_user.id
  user_data = get_user_data(user_id)

  parts = call.data.split("_")
  method_code = parts[1]
  game_name = "_".join(parts[2:])

  method_name = (
      "Dushanbe City" if method_code == "dc" else "Алиф Карта (Alif)"
  )

  user_data["state"]["method"] = method_name
  user_data["state"]["awaiting_id"] = True

  bot.answer_callback_query(call.id)
  bot.send_message(
      call.message.chat.id,
      f"💳 Выбран способ оплаты: **{method_name}** ({game_name}).\n\n"
      f"Пожалуйста, введите ваш **Player ID** (ID игрока):",
      parse_mode="Markdown",
  )


# ==================== ВВОД PLAYER ID И ОФОРМЛЕНИЕ ЗАКАЗА ====================
@bot.message_handler(
    func=lambda message: get_user_data(message.from_user.id)
    .get("state", {})
    .get("awaiting_id", False)
)
def process_player_id(message):
  user_id = message.from_user.id
  user_data = get_user_data(user_id)

  player_id = message.text.strip()
  user_data["state"]["player_id"] = player_id
  user_data["state"]["awaiting_id"] = False

  game = user_data["state"].get("game", "Игра")
  method = user_data["state"].get("method", "Карта")
  refs_count = user_data["referrals"]
  discount = 10 if refs_count >= 10 else 0

  summary_text = (
      f"📋 **Подтверждение заказа:**\n\n"
      f"🎮 Игра: **{game}**\n"
      f"🆔 Player ID: `{player_id}`\n"
      f"💳 Способ оплаты: **{method}**\n"
      f"📌 Наценка: **{MARKUP} TJS**\n"
      f"🎁 Ваша скидка: **{discount}%**\n\n"
      f"Для завершения переведите нужную сумму на карту **{method}** и свяжитесь с оператором."
  )

  bot.send_message(message.chat.id, summary_text, parse_mode="Markdown")

  # Уведомление администратору
  admin_notification = (
      f"🔔 **НОВАЯ ЗАЯВКА НА ПОПОЛНЕНИЕ!**\n\n"
      f"👤 Пользователь: @{message.from_user.username or 'без_юзернейма'} (ID: `{user_id}`)\n"
      f"🎮 Игра: **{game}**\n"
      f"🆔 Player ID: `{player_id}`\n"
      f"💳 Оплата: **{method}**\n"
      f"🎁 Скидка пользователя: **{discount}%**"
  )
  bot.send_message(ADMIN_ID, admin_notification, parse_mode="Markdown")


# ==================== ПАНЕЛЬ АДМИНИСТРАТОРА ====================
@bot.message_handler(commands=["admin"])
def admin_panel(message):
  if message.from_user.id != ADMIN_ID:
    bot.reply_to(message, "⛔ У вас нет доступа к панели администратора.")
    return

  active_users = len(users_db)
  bot.send_message(
      message.chat.id,
      f"👑 **Панель администратора:**\n\n"
      f"📊 Зарегистрировано пользователей: **{active_users}**\n"
      f"🟢 Статус сервера: **Активен (24/7)**",
      parse_mode="Markdown",
  )


# ==================== ЗАПУСК ПРИЛОЖЕНИЯ ====================
if __name__ == "__main__":
  # Запуск Flask веб-сервера в отдельном фоновом потоке
  web_thread = threading.Thread(target=run_web)
  web_thread.daemon = True
  web_thread.start()

  # Запуск Telegram-бота
  bot.infinity_polling()
