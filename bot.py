import os
import threading
from flask import Flask
import telebot
from telebot import types

# ==================== НАСТРОЙКИ И КОНФИГУРАЦИЯ ====================
TOKEN = "8983343058:AAH35u-bqLnEFHWKK52yKwq1lc0Nx9BtUbc"
ADMIN_ID = 6738122971

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# База данных пользователей (в памяти)
# Формат: user_id: {"referrals": int, "referred_by": int/None, "discounts_available": int, "state": {}}
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
    users_db[user_id] = {
        "referrals": 0,
        "referred_by": None,
        "discounts_available": 0,
        "state": {},
    }
  return users_db[user_id]


def main_keyboard():
  markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
  markup.add(
      types.KeyboardButton("🎮 PUBG Mobile"),
      types.KeyboardButton("🔥 Free Fire"),
  )
  markup.add(types.KeyboardButton("👤 Мой профиль / Рефералка"))
  return markup


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
        ref_data = users_db[referrer_id]
        ref_data["referrals"] += 1

        # Каждые 10 рефералов дают +1 одноразовую скидку 10%
        if ref_data["referrals"] % 10 == 0:
          ref_data["discounts_available"] += 1
          bot.send_message(
              referrer_id,
              "🎉 *Поздравляем!*\nВы пригласили 10 друзей и получили **одноразовую скидку 10%** на следующую покупку!",
              parse_mode="Markdown",
          )
        else:
          bot.send_message(
              referrer_id,
              "🎉 *Отличные новости!* По вашей реферальной ссылке зарегистрировался новый игрок!",
              parse_mode="Markdown",
          )
    except ValueError:
      pass

  user_data["state"] = {}  # Сброс состояния

  welcome_text = (
      f"👋 **Салом, {message.from_user.first_name}!**\n\n"
      f"Добро пожаловать в сервис моментального пополнения игр! 🚀\n\n"
      f"⚡️ Быстрое зачисление\n"
      f"💳 Удобная оплата (Dushanbe City / Alif)\n"
      f"🎁 Бонусы за приглашение друзей\n\n"
      f"👇 **Выберите игру для пополнения:**"
  )

  bot.send_message(
      message.chat.id,
      welcome_text,
      parse_mode="Markdown",
      reply_markup=main_keyboard(),
  )


# ==================== ПРОФИЛЬ И РЕФЕРАЛКА ====================
@bot.message_handler(
    func=lambda message: message.text == "👤 Мой профиль / Рефералка"
)
def show_profile(message):
  user_id = message.from_user.id
  user_data = get_user_data(user_id)

  bot_username = bot.get_me().username
  ref_link = (
      f"https://t.me/{bot_username}?start={user_id}" if bot_username else "N/A"
  )
  refs_count = user_data["referrals"]
  next_target = 10 - (refs_count % 10)
  discounts = user_data["discounts_available"]

  profile_text = (
      f"👤 **ВАШ ПРОФИЛЬ**\n"
      f"━━━━━━━━━━━━━━━━━━━\n"
      f"🆔 Ваш ID: `{user_id}`\n"
      f"👥 Всего приглашено: **{refs_count}**\n"
      f"🎯 До следующей скидки: **{next_target} друзей**\n"
      f"🎁 Доступно скидок 10%: **{discounts} шт.**\n"
      f"━━━━━━━━━━━━━━━━━━━\n\n"
      f"🔗 **Ваша реферальная ссылка:**\n`{ref_link}`\n\n"
      f"💡 _За каждые 10 приглашенных друзей вы получаете 1 одноразовую скидку 10%!_"
  )

  bot.send_message(message.chat.id, profile_text, parse_mode="Markdown")


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
          "🦅 Dushanbe City", callback_data=f"pay_dc_{game_name}"
      ),
      types.InlineKeyboardButton(
          "🟢 Алиф Карта (Alif)", callback_data=f"pay_alif_{game_name}"
      ),
      types.InlineKeyboardButton("❌ Отмена", callback_data="cancel_order"),
  )

  bot.send_message(
      message.chat.id,
      f"🎯 Вы выбрали: **{game_name}**\n\n"
      f"💳 **Выберите удобный способ оплаты:**",
      parse_mode="Markdown",
      reply_markup=markup,
  )


@bot.callback_query_handler(func=lambda call: call.data == "cancel_order")
def cancel_order(call):
  user_id = call.from_user.id
  get_user_data(user_id)["state"] = {}

  bot.answer_callback_query(call.id, "Заказ отменен")
  bot.send_message(
      call.message.chat.id,
      "🔄 Операция отменена. Выберите действие в меню ниже:",
      reply_markup=main_keyboard(),
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

  cancel_markup = types.InlineKeyboardMarkup()
  cancel_markup.add(
      types.InlineKeyboardButton("❌ Отмена", callback_data="cancel_order")
  )

  bot.send_message(
      call.message.chat.id,
      f"✅ Способ оплаты: **{method_name}**\n"
      f"🎮 Игра: **{game_name}**\n\n"
      f"✏️ **Отправьте ваш Player ID (ID в игре):**",
      parse_mode="Markdown",
      reply_markup=cancel_markup,
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

  # Проверяем наличие одноразовой скидки
  has_discount = user_data["discounts_available"] > 0
  if has_discount:
    user_data["discounts_available"] -= 1  # Разовое списание скидки
    discount_text = "Применена одноразовая скидка 10% 🎉"
  else:
    discount_text = "Без скидки"

  summary_text = (
      f"🎉 **Заявка почти готова!**\n"
      f"━━━━━━━━━━━━━━━━━━━\n"
      f"🎮 Игра: **{game}**\n"
      f"🆔 Player ID: `{player_id}`\n"
      f"💳 Оплата через: **{method}**\n"
      f"🎁 Бонус: **{discount_text}**\n"
      f"━━━━━━━━━━━━━━━━━━━\n\n"
      f"📌 **Что делать дальше?**\n"
      f"Переведите необходимую сумму на карту **{method}** и отправьте чек оператору для зачисления!"
  )

  bot.send_message(
      message.chat.id,
      summary_text,
      parse_mode="Markdown",
      reply_markup=main_keyboard(),
  )

  # Уведомление администратору
  admin_notification = (
      f"🚨 **НОВАЯ ЗАЯВКА НА ПОПОЛНЕНИЕ!**\n"
      f"━━━━━━━━━━━━━━━━━━━\n"
      f"👤 Клиент: @{message.from_user.username or 'без_юзернейма'} (ID: `{user_id}`)\n"
      f"🎮 Игра: **{game}**\n"
      f"🆔 Player ID: `{player_id}`\n"
      f"💳 Оплата: **{method}**\n"
      f"🎁 Скидка: **{'Да (10% одноразовая)' if has_discount else 'Нет'}**\n"
      f"━━━━━━━━━━━━━━━━━━━"
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
      f"👑 **ПАНЕЛЬ АДМИНИСТРАТОРА**\n"
      f"━━━━━━━━━━━━━━━━━━━\n"
      f"📊 Зарегистрировано пользователей: **{active_users}**\n"
      f"🟢 Статус сервера: **Работает 24/7**\n"
      f"━━━━━━━━━━━━━━━━━━━",
      parse_mode="Markdown",
  )


# ==================== ЗАПУСК ПРИЛОЖЕНИЯ ====================
if __name__ == "__main__":
  web_thread = threading.Thread(target=run_web)
  web_thread.daemon = True
  web_thread.start()

  bot.infinity_polling()
  
