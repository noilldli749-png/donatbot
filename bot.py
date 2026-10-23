import os
import threading
from flask import Flask
import telebot
from telebot import types

# ==================== НАСТРОЙКИ И КОНФИГУРАЦИЯ ====================
TOKEN = "8983343058:AAH35u-bqLnEFHWKK52yKwq1lc0Nx9BtUbc"
ADMIN_ID = 6738122971

# ВАШ НОМЕР ДЛЯ ОПЛАТЫ (Dushanbe City / Alif)
WALLET_NUMBER = "+992006443155"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# База данных пользователей (в памяти)
users_db = {}
# Временное хранилище активных заказов, ожидающих проверки чека
# Формат: user_id: {"game": ..., "package": ..., "price": ..., "method": ..., "player_id": ...}
pending_orders = {}

# ==================== ПРАЙС-ЛИСТ ====================
PRICES = {
    "🎮 PUBG Mobile": {
        "325 UC": 51,
        "355 UC": 56,
        "385 UC": 61,
        "660 UC": 93,
        "720 UC": 103,
        "985 UC": 141,
        "1045 UC": 156,
        "1320 UC": 191,
        "1800 UC": 226,
        "2125 UC": 291,
        "2460 UC": 331,
        "3850 UC": 451,
        "4175 UC": 501,
        "5650 UC": 681,
        "8100 UC": 851,
        "9900 UC": 1101,
        "11950 UC": 1281,
        "16200 UC": 1751,
    },
    "🔥 Free Fire": {
        "100 Алмазов": 11,
        "210 Алмазов": 22,
        "530 Алмазов": 53,
        "1080 Алмазов": 106,
        "2200 Алмазов": 211,
    },
}


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
        "has_contributed": False,
        "discounts_available": 0,
        "state": {},
    }
  return users_db[user_id]


def main_keyboard():
  markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
  markup.add(
      types.KeyboardButton("🛍 Сделать заказ"),
      types.KeyboardButton("👤 Мой профиль"),
  )
  markup.add(
      types.KeyboardButton("ℹ️ Помощь и правила"),
      types.KeyboardButton("📞 Контакты"),
  )
  return markup


# ==================== ОБРАБОТЧИКИ КОМАНД ====================
@bot.message_handler(commands=["start"])
def send_welcome(message):
  user_id = message.from_user.id
  user_data = get_user_data(user_id)
  args = message.text.split()

  if len(args) > 1 and user_data["referred_by"] is None:
    try:
      referrer_id = int(args[1])
      if referrer_id != user_id and referrer_id in users_db:
        user_data["referred_by"] = referrer_id
        bot.send_message(
            message.chat.id,
            "Вы успешно зарегистрировались по приглашению! Как только вы"
            " совершите первую покупку, вашему другу засчитается реферал.",
        )
        bot.send_message(
            referrer_id,
            "По вашей ссылке зарегистрировался новый игрок! Реферал"
            " засчитается после того, как он совершит покупку.",
        )
    except ValueError:
      pass

  user_data["state"] = {}

  welcome_text = (
      f"Салом, {message.from_user.first_name}!\n\n"
      "Добро пожаловать в официальный бот моментального пополнения игр! 🚀\n\n"
      "• PUBG Mobile UC & Free Fire Алмазы по выгодным ценам.\n"
      "• Быстрое зачисление по ID (в течение 2–3 минут).\n"
      "• Удобная оплата через Dushanbe City и Alif.\n"
      "• Приглашайте друзей и получайте скидки!\n\n"
      "Воспользуйтесь меню ниже для управления:"
  )

  bot.send_message(message.chat.id, welcome_text, reply_markup=main_keyboard())


# ==================== КНОПКИ ГЛАВНОГО МЕНЮ ====================
@bot.message_handler(func=lambda message: message.text == "🛍 Сделать заказ")
def menu_order(message):
  markup = types.InlineKeyboardMarkup(row_width=2)
  markup.add(
      types.InlineKeyboardButton(
          "🎮 PUBG Mobile", callback_data="game_PUBG Mobile"
      ),
      types.InlineKeyboardButton("🔥 Free Fire", callback_data="game_Free Fire"),
  )
  bot.send_message(
      message.chat.id,
      "🎮 Выберите нужную игру для пополнения:",
      reply_markup=markup,
  )


@bot.message_handler(func=lambda message: message.text == "👤 Мой профиль")
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
      "👤 ВАШ ПРОФИЛЬ\n"
      "-----------------------------------\n"
      f"Ваш ID: {user_id}\n"
      f"Активных рефералов (купивших товар): {refs_count}\n"
      f"До следующей скидки: {next_target} рефералов\n"
      f"Доступно одноразовых скидок (10%): {discounts} шт.\n"
      "-----------------------------------\n\n"
      "Ваша персональная реферальная ссылка:\n"
      f"{ref_link}\n\n"
      "Делитесь ссылкой с друзьями! Когда друг покупает UC или алмазы,"
      " вам засчитывается 1 реферал. За каждые 10 таких рефералов вы получаете"
      " скидку 10% на следующую покупку."
  )

  bot.send_message(
      message.chat.id, profile_text, reply_markup=main_keyboard()
  )


@bot.message_handler(func=lambda message: message.text == "ℹ️ Помощь и правила")
def show_help(message):
  help_text = (
      "ℹ️ КАК ПОПОЛНИТЬ ИГРУ?\n"
      "-----------------------------------\n"
      "1. Нажмите кнопку «🛍 Сделать заказ».\n"
      "2. Выберите игру (PUBG Mobile или Free Fire).\n"
      "3. Выберите нужный пакет UC или алмазов.\n"
      "4. Выберите удобный способ оплаты (Dushanbe City или Alif).\n"
      "5. Отправьте ваш Player ID (числовой ID).\n"
      "6. Переведите сумму на указанный номер и отправьте чек (фото/скриншот) в этот чат.\n\n"
      "⏱ Время зачисления: обычно от 2 до 5 минут после проверки чека."
  )
  bot.send_message(
      message.chat.id, help_text, reply_markup=main_keyboard()
  )


@bot.message_handler(func=lambda message: message.text == "📞 Контакты")
def show_contacts(message):
  contacts_text = (
      "📞 КОНТАКТЫ И ПОДДЕРЖКА\n"
      "-----------------------------------\n"
      "По всем вопросам обращайтесь к администратору:\n"
      f"Связь: @MNG_STABBY\n"
      f"Официальный кошелек: {WALLET_NUMBER}"
  )
  bot.send_message(
      message.chat.id, contacts_text, reply_markup=main_keyboard()
  )


# ==================== ВЫБОР ИГРЫ И ПАКЕТОВ ====================
@bot.callback_query_handler(func=lambda call: call.data.startswith("game_"))
def callback_choose_game(call):
  game_name = call.data.replace("game_", "")
  if game_name == "PUBG Mobile":
    game_key = "🎮 PUBG Mobile"
  else:
    game_key = "🔥 Free Fire"

  user_id = call.from_user.id
  get_user_data(user_id)["state"] = {"game": game_key}

  markup = types.InlineKeyboardMarkup(row_width=1)
  game_packages = PRICES.get(game_key, {})
  for item_name, price in game_packages.items():
    markup.add(
        types.InlineKeyboardButton(
            f"💎 {item_name} — {price} TJS", callback_data=f"pkg_{item_name}"
        )
    )

  markup.add(
      types.InlineKeyboardButton("⬅️ Назад к играм", callback_data="back_to_games")
  )

  bot.answer_callback_query(call.id)
  bot.edit_message_text(
      f"🎯 Вы выбрали: {game_key}\n\n📦 Выберите пакет пополнения:",
      call.message.chat.id,
      call.message.message_id,
      reply_markup=markup,
  )


@bot.callback_query_handler(func=lambda call: call.data == "back_to_games")
def callback_back_to_games(call):
  markup = types.InlineKeyboardMarkup(row_width=2)
  markup.add(
      types.InlineKeyboardButton(
          "🎮 PUBG Mobile", callback_data="game_PUBG Mobile"
      ),
      types.InlineKeyboardButton("🔥 Free Fire", callback_data="game_Free Fire"),
  )
  bot.answer_callback_query(call.id)
  bot.edit_message_text(
      "🎮 Выберите нужную игру для пополнения:",
      call.message.chat.id,
      call.message.message_id,
      reply_markup=markup,
  )


@bot.callback_query_handler(func=lambda call: call.data.startswith("pkg_"))
def package_selected(call):
  user_id = call.from_user.id
  user_data = get_user_data(user_id)

  package_name = call.data.replace("pkg_", "")
  game_name = user_data["state"].get("game", "🎮 PUBG Mobile")

  price = PRICES.get(game_name, {}).get(package_name, 0)

  user_data["state"]["package"] = package_name
  user_data["state"]["price"] = price

  markup = types.InlineKeyboardMarkup(row_width=1)
  markup.add(
      types.InlineKeyboardButton("🦅 Dushanbe City", callback_data="pay_dc"),
      types.InlineKeyboardButton(
          "🟢 Алиф Карта (Alif)", callback_data="pay_alif"
      ),
      types.InlineKeyboardButton(
          "⬅️ Назад к пакетам",
          callback_data=f"game_{game_name.replace('🎮 ', '').replace('🔥 ', '')}",
      ),
  )

  bot.answer_callback_query(call.id)
  bot.edit_message_text(
      f"📦 Выбран пакет: {package_name}\n💵 Стоимость: {price} TJS\n\n💳 Выберите"
      " способ оплаты:",
      call.message.chat.id,
      call.message.message_id,
      reply_markup=markup,
  )


@bot.callback_query_handler(
    func=lambda call: call.data in ["pay_dc", "pay_alif"]
)
def payment_method_selected(call):
  user_id = call.from_user.id
  user_data = get_user_data(user_id)

  method_name = (
      "Dushanbe City" if call.data == "pay_dc" else "Алиф Карта (Alif)"
  )

  user_data["state"]["method"] = method_name
  user_data["state"]["awaiting_id"] = True

  bot.answer_callback_query(call.id)

  cancel_markup = types.InlineKeyboardMarkup()
  cancel_markup.add(
      types.InlineKeyboardButton(
          "❌ Отмена заказа", callback_data="cancel_order"
      )
  )

  bot.send_message(
      call.message.chat.id,
      f"✅ Способ оплаты: {method_name}\n\n"
      "✏️ Отправьте ваш Player ID (числовой ID игрока):",
      reply_markup=cancel_markup,
  )


@bot.callback_query_handler(func=lambda call: call.data == "cancel_order")
def cancel_order(call):
  user_id = call.from_user.id
  get_user_data(user_id)["state"] = {}

  bot.answer_callback_query(call.id, "Заказ отменен")
  bot.send_message(
      call.message.chat.id,
      "🔄 Оформление заказа отменено. Воспользуйтесь меню ниже:",
      reply_markup=main_keyboard(),
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
  user_data["state"]["awaiting_receipt"] = True  # Ждем чек от пользователя

  game = user_data["state"].get("game", "Игра")
  package = user_data["state"].get("package", "Пакет")
  method = user_data["state"].get("method", "Карта")
  base_price = user_data["state"].get("price", 0)

  has_discount = user_data["discounts_available"] > 0
  if has_discount:
    user_data["discounts_available"] -= 1
    final_price = base_price * 0.9  # Скидка 10%
    discount_note = "Применена одноразовая скидка 10% 🎉"
  else:
    final_price = base_price
    discount_note = "Без скидки"

  user_data["state"]["final_price"] = final_price

  summary_text = (
      "🎉 Заявка создана!\n"
      "-----------------------------------\n"
      f"Игра: {game}\n"
      f"Товар: {package}\n"
      f"Player ID: {player_id}\n"
      f"Способ оплаты: {method}\n"
      f"Бонус: {discount_note}\n"
      f"Итого к оплате: {final_price:.1f} TJS\n"
      "-----------------------------------\n\n"
      "📌 Куда переводить деньги?\n"
      f"Переведите {final_price:.1f} TJS на номер {method}:\n"
      f"`{WALLET_NUMBER}`\n\n"
      "📲 **Отправьте скриншот или фото чека в этот чат прямо сейчас!**"
  )

  bot.send_message(
      message.chat.id, summary_text, parse_mode="Markdown", reply_markup=main_keyboard()
  )


# ==================== ОБРАБОТКА ЧЕКОВ (ФОТО) ====================
@bot.message_handler(
    content_types=["photo"],
    func=lambda message: get_user_data(message.from_user.id)
    .get("state", {})
    .get("awaiting_receipt", False),
)
def handle_receipt(message):
  user_id = message.from_user.id
  user_data = get_user_data(user_id)
  state = user_data["state"]

  state["awaiting_receipt"] = False

  game = state.get("game", "Игра")
  package = state.get("package", "Пакет")
  player_id = state.get("player_id", "N/A")
  method = state.get("method", "Карта")
  final_price = state.get("final_price", 0)

  # Сохраняем во временное хранилище для админа
  pending_orders[user_id] = {
      "user_id": user_id,
      "game": game,
      "package": package,
      "player_id": player_id,
      "final_price": final_price,
  }

  bot.reply_to(
      message,
      "⏳ **Чек принят!** Он отправлен администратору на проверку. Ожидайте"
      " зачисления в течение нескольких минут.",
      parse_mode="Markdown",
  )

  # Кнопки для администратора под чеком
  admin_markup = types.InlineKeyboardMarkup(row_width=2)
  admin_markup.add(
      types.InlineKeyboardButton(
          "✅ Одобрить", callback_data=f"approve_{user_id}"
      ),
      types.InlineKeyboardButton("❌ Отказать", callback_data=f"reject_{user_id}"),
  )

  caption_text = (
      "🚨 **НОВАЯ ОПЛАТА / ЧЕК НА ПРОВЕРКУ!**\n"
      "-----------------------------------\n"
      f"👤 Клиент: @{message.from_user.username or 'без_юзернейма'} (ID: `{user_id}`)\n"
      f"🎮 Игра: {game}\n"
      f"📦 Пакет: {package}\n"
      f"🆔 Player ID: `{player_id}`\n"
      f"💳 Оплата: {method}\n"
      f"💰 Сумма: **{final_price:.1f} TJS**\n"
      "-----------------------------------"
  )

  # Берем самое качественное фото чека
  photo_id = message.photo[-1].file_id
  bot.send_photo(
      ADMIN_ID,
      photo_id,
      caption=caption_text,
      parse_mode="Markdown",
      reply_markup=admin_markup,
  )


# ==================== КНОПКИ УПРАВЛЕНИЯ ДЛЯ АДМИНА ====================
@bot.callback_query_handler(func=lambda call: call.data.startswith(("approve_", "reject_")))
def admin_decision(call):
  if call.from_user.id != ADMIN_ID:
    bot.answer_callback_query(call.id, "⛔ У вас нет прав администратора.", show_alert=True)
    return

  action, target_user_id_str = call.data.split("_")
  target_user_id = int(target_user_id_str)

  bot.answer_callback_query(call.id)

  if action == "approve":
    # 1. Начисляем реферал (если клиент чей-то реферал и еще не покупал)
    target_data = get_user_data(target_user_id)
    if (
        target_data["referred_by"]
        and not target_data["has_contributed"]
    ):
      target_data["has_contributed"] = True
      ref_id = target_data["referred_by"]
      if ref_id in users_db:
        users_db[ref_id]["referrals"] += 1
        if users_db[ref_id]["referrals"] % 10 == 0:
          users_db[ref_id]["discounts_available"] += 1
          bot.send_message(
              ref_id,
              "🎉 Поздравляем! Один из ваших приглашенных друзей успешно"
              " оплатил заказ. Вы накопили 10 рефералов и получили одноразовую"
              " скидку 10%!",
          )
        else:
          bot.send_message(
              ref_id,
              "👥 Ваш приглашенный друг совершил и оплатил покупку! Вам"
              " зачислен 1 реферал.",
          )

    # 2. Уведомляем клиента об успешной оплате
    try:
      bot.send_message(
          target_user_id,
          "✅ **Оплата успешно подтверждена администратором!**\n\n"
          "Ваш заказ передан в обработку, UC / алмазы будут зачислены на ваш аккаунт в течение 2–3 минут. Спасибо, что выбрали нас! 🚀",
          parse_mode="Markdown",
      )
    except Exception:
      pass

    # Обновляем сообщение у админа
    bot.edit_message_caption(
        call.message.chat.id,
        call.message.message_id,
        caption=call.message.caption + "\n\n🟢 **СТАТУС: ОДОБРЕНО ✅**",
        parse_mode="Markdown",
        reply_markup=None,
    )

  elif action == "reject":
    # Уведомляем клиента об отказе
    try:
      bot.send_message(
          target_user_id,
          "❌ **К сожалению, ваша оплата была отклонена администратором.**\n\n"
          "Возникла проблема с чеком или переводом. Пожалуйста, обратитесь в поддержку: @MNG_STABBY",
          parse_mode="Markdown",
      )
    except Exception:
      pass

    # Обновляем сообщение у админа
    bot.edit_message_caption(
        call.message.chat.id,
        call.message.message_id,
        caption=call.message.caption + "\n\n🔴 **СТАТУС: ОТКЛОНЕНО ❌**",
        parse_mode="Markdown",
        reply_markup=None,
    )

  if target_user_id in pending_orders:
    del pending_orders[target_user_id]


# ==================== ПАНЕЛЬ АДМИНИСТРАТОРА ====================
@bot.message_handler(commands=["admin"])
def admin_panel(message):
  if message.from_user.id != ADMIN_ID:
    bot.reply_to(message, "⛔ У вас нет доступа к панели администратора.")
    return

  active_users = len(users_db)
  bot.send_message(
      message.chat.id,
      "👑 ПАНЕЛЬ АДМИНИСТРАТОРА\n"
      "-----------------------------------\n"
      f"Зарегистрировано пользователей: {active_users}\n"
      f"Номер кошелька: {WALLET_NUMBER}\n"
      "Статус сервера: Работает 24/7\n"
      "-----------------------------------",
  )


# ==================== ЗАПУСК ПРИЛОЖЕНИЯ ====================
if __name__ == "__main__":
  web_thread = threading.Thread(target=run_web)
  web_thread.daemon = True
  web_thread.start()

  bot.infinity_polling()
    
