import telebot
from telebot import types
import urllib.parse

# === НАСТРОЙКИ БОТА ===
TOKEN = '8983343058:AAH35u-bqLnEFHWKK52yKwq1lc0Nx9BtUbc'  # Ваш новый актуальный токен
ADMIN_ID = 6738122971            # Ваш ID администратора
BOT_USERNAME = "ucdonat_tj_bot"  # Юзернейм вашего бота

bot = telebot.TeleBot(TOKEN)

# Хранилища в памяти
orders = {}
order_counter = 1
all_users = set()

# Реферальная система
referred_by = {}
successful_referrals = {}
user_bonuses = {}

PUBG_PACKS = [
    {"uc": "60 UC", "price": 11},
    {"uc": "325 UC", "price": 53},
    {"uc": "660 UC", "price": 105},
    {"uc": "1800 UC", "price": 275}
]

FREEFIRE_PACKS = [
    {"diamonds": "100 Алмазов", "price": 12},
    {"diamonds": "310 Алмазов", "price": 34},
    {"diamonds": "520 Алмазов", "price": 56},
    {"diamonds": "1060 Алмазов", "price": 110}
]

# === КРАСИВОЕ ГЛАВНОЕ МЕНЮ ===
def main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_pubg = types.InlineKeyboardButton("🎮 PUBG Mobile", callback_data="game_pubg")
    btn_ff = types.InlineKeyboardButton("🔥 Free Fire", callback_data="game_ff")
    btn_profile = types.InlineKeyboardButton("👤 Мой профиль", callback_data="user_profile")
    btn_history = types.InlineKeyboardButton("📜 История заказов", callback_data="user_history")
    btn_ref = types.InlineKeyboardButton("🎁 Акция: 10% Скидка", callback_data="ref_menu")
    
    btn_help = types.InlineKeyboardButton("💬 Поддержка", url="https://t.me/ucdonat_admin")
    
    share_text = urllib.parse.quote("💎 Самое быстрое и выгодное пополнение UC и Алмазов в Таджикистане!")
    share_url = f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}&text={share_text}"
    btn_share = types.InlineKeyboardButton("📲 Поделиться ботом", url=share_url)

    markup.add(btn_pubg, btn_ff)
    markup.add(btn_profile, btn_history)
    markup.add(btn_ref)
    markup.add(btn_share)
    markup.add(btn_help)
    return markup

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    all_users.add(user_id)
    
    if user_id not in user_bonuses:
        user_bonuses[user_id] = {'has_discount': False}

    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referrer_id = int(args[1].replace("ref_", ""))
            if referrer_id != user_id and user_id not in referred_by:
                referred_by[user_id] = referrer_id
        except ValueError:
            pass

    welcome_text = (
        f"👋 **Здравствуйте, {message.from_user.first_name}!**\n\n"
        f"💎 **UC & Diamond Store TJ** — ваш надежный сервис пополнения игровых валют.\n\n"
        f"⚡ **Наши преимущества:**\n"
        f"└ 🚀 Зачисление от 5 до 15 минут\n"
        f"└ 💳 Оплата через **Dushanbe City**\n"
        f"└ 🔒 100% гарантия безопасности аккаунта\n\n"
        f"👇 **Выберите нужную игру в меню ниже:**"
    )

    bot.send_message(
        message.chat.id,
        welcome_text,
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

# === КОМАНДА РАССЫЛКИ (ТОЛЬКО ДЛЯ ВАС) ===
@bot.message_handler(commands=['send', 'broadcast'])
def broadcast_cmd(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ У вас нет доступа к этой команде.")
        return

    text_to_send = message.text.partition(' ')[2].strip()
    if not text_to_send:
        bot.send_message(message.chat.id, "⚠️ Использование: `/send Ваш текст новости`", parse_mode="Markdown")
        return

    bot.send_message(message.chat.id, f"⏳ Запуск рассылки на {len(all_users)} пользователей...")
    success_count, error_count = 0, 0

    for u_id in list(all_users):
        try:
            bot.send_message(u_id, text_to_send, parse_mode="Markdown")
            success_count += 1
        except Exception:
            error_count += 1

    bot.send_message(
        message.chat.id,
        f"📢 **Итоги рассылки:**\n\n"
        f"✅ Доставлено: **{success_count}**\n"
        f"❌ Не доставлено: **{error_count}**",
        parse_mode="Markdown"
    )

# === ОБРАБОТКА ИНТЕРАКТИВА ===
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    global order_counter
    user_id = call.from_user.id
    all_users.add(user_id)

    if user_id not in user_bonuses:
        user_bonuses[user_id] = {'has_discount': False}

    if call.data == "main_menu":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="🏠 **Главное меню**\n\nВыберите категорию для покупки:",
            reply_markup=main_keyboard(),
            parse_mode="Markdown"
        )

    # Профиль пользователя
    elif call.data == "user_profile":
        paid_count = len(successful_referrals.get(user_id, set()))
        has_disc = user_bonuses[user_id]['has_discount']
        disc_text = "🔥 **Активирована (10%)**" if has_disc else "❌ Отсутствует"

        profile_text = (
            f"👤 **Кабинет покупателя**\n\n"
            f"🆔 Ваш ID: `{user_id}`\n"
            f"🏷 Ваша персональная скидка: {disc_text}\n"
            f"👥 Приглашено покупателей: **{paid_count} / 10**\n\n"
            f"💡 *Приглашайте друзей и получайте скидку 10% на каждый 10-й выполненный заказ!*"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⬅️ Назад в меню", callback_data="main_menu"))

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=profile_text,
            reply_markup=markup,
            parse_mode="Markdown"
        )

    # Меню рефералов
    elif call.data == "ref_menu":
        paid_count = len(successful_referrals.get(user_id, set()))
        has_disc = user_bonuses[user_id]['has_discount']
        ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"
        
        status_info = "✅ **Скидка 10% готова к использованию!**" if has_disc else f"⏳ Осталось пригласить покупателей: **{max(0, 10 - paid_count)}**"

        ref_text = (
            f"🎁 **Реферальная система «Приведи 10 друзей»**\n\n"
            f"Приглашайте друзей по вашей ссылке! Когда **10 человек** сделают по 1 покупке, вы получите **скидку 10%** на свой следующий заказ.\n\n"
            f"📈 **Ваш прогресс:**\n"
            f"└ Друзей с покупками: **{paid_count} / 10**\n"
            f"└ Статус: {status_info}\n\n"
            f"🔗 **Ваша реферальная ссылка:**\n`{ref_link}`\n\n"
            f"👇 *Нажмите на ссылку, чтобы скопировать её и отправить друзьям!*"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="main_menu"))

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=ref_text,
            reply_markup=markup,
            parse_mode="Markdown"
        )

    # Выбор PUBG Mobile
    elif call.data == "game_pubg":
        markup = types.InlineKeyboardMarkup(row_width=1)
        has_disc = user_bonuses[user_id]['has_discount']

        for item in PUBG_PACKS:
            price = item['price']
            if has_disc:
                price = round(price * 0.9, 1)
                btn_text = f"🔥 {item['uc']} — {price} TJS (Скидка 10%!)"
            else:
                btn_text = f"🔹 {item['uc']} — {price} TJS"
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"buy_pubg_{price}_{item['uc']}"))

        markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="main_menu"))
        
        header_text = "🎮 **Пополнение PUBG Mobile**\n\nВыберите желаемый пакет Unknown Cash (UC):"
        if has_disc:
            header_text = "🎮 **PUBG Mobile**\n✨ *Вам доступна бонусная скидка 10%! Цены снижены:*"

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=header_text,
            reply_markup=markup,
            parse_mode="Markdown"
        )

    # Выбор Free Fire
    elif call.data == "game_ff":
        markup = types.InlineKeyboardMarkup(row_width=1)
        has_disc = user_bonuses[user_id]['has_discount']

        for item in FREEFIRE_PACKS:
            price = item['price']
            if has_disc:
                price = round(price * 0.9, 1)
                btn_text = f"🔥 {item['diamonds']} — {price} TJS (Скидка 10%!)"
            else:
                btn_text = f"🔹 {item['diamonds']} — {price} TJS"
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"buy_ff_{price}_{item['diamonds']}"))

        markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="main_menu"))

        header_text = "🔥 **Пополнение Free Fire**\n\nВыберите желаемый пакет Алмазов:"
        if has_disc:
            header_text = "🔥 **Free Fire**\n✨ *Вам доступна бонусная скидка 10%! Цены снижены:*"

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=header_text,
            reply_markup=markup,
            parse_mode="Markdown"
        )

    # Оформление покупки
    elif call.data.startswith("buy_"):
        parts = call.data.split("_")
        game_type = "PUBG Mobile" if parts[1] == "pubg" else "Free Fire"
        price = parts[2]
        pack_name = parts[3]

        order_id = order_counter
        order_counter += 1

        orders[order_id] = {
            'user_id': user_id,
            'game': game_type,
            'pack': pack_name,
            'price': price,
            'status': 'Ожидает чека'
        }

        if user_bonuses[user_id]['has_discount']:
            user_bonuses[user_id]['has_discount'] = False

        pay_text = (
            f"💳 **Оформление заказа #{order_id}**\n\n"
            f"🎮 Игра: **{game_type}**\n"
            f"📦 Комплект: **{pack_name}**\n"
            f"💵 Итого к оплате: **{price} TJS**\n\n"
            f"═══════════════════\n"
            f"📌 **Реквизиты для оплаты:**\n"
            f"Банк: **Dushanbe City**\n"
            f"Номер: `+992006443155`\n"
            f"═══════════════════\n\n"
            f"📸 **Отправьте скриншот чека об оплате прямо в этот чат!**"
        )

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("❌ Отменить заказ", callback_data="main_menu"))

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=pay_text,
            reply_markup=markup,
            parse_mode="Markdown"
        )

    # История заказов
    elif call.data == "user_history":
        user_orders = [
            f"🧾 **Заказ #{oid}**\n└ {data['game']} | {data['pack']}\n└ Сумма: **{data['price']} TJS**\n└ Статус: `{data['status']}`"
            for oid, data in orders.items() if data['user_id'] == user_id
        ]

        if user_orders:
            history_text = "📜 **Ваша история заказов:**\n\n" + "\n\n".join(user_orders[-5:])
        else:
            history_text = "📜 **История пуста.** Вы еще не совершали заказов."

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="main_menu"))

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=history_text,
            reply_markup=markup,
            parse_mode="Markdown"
        )

    # --- АДМИН-ДЕЙСТВИЯ ---
    elif call.data.startswith("adm_approve_"):
        order_id = int(call.data.split("_")[2])
        if order_id in orders:
            orders[order_id]['status'] = '✅ Выполнен'
            target_user_id = orders[order_id]['user_id']

            bot.send_message(
                target_user_id,
                f"🎉 **Ваш заказ #{order_id} успешно выполнен!**\n\n"
                f"Игровая валюта зачислена на ваш аккаунт. Приятной игры! 🎮"
            )

            if target_user_id in referred_by:
                referrer_id = referred_by[target_user_id]
                if referrer_id not in successful_referrals:
                    successful_referrals[referrer_id] = set()

                if target_user_id not in successful_referrals[referrer_id]:
                    successful_referrals[referrer_id].add(target_user_id)
                    current_count = len(successful_referrals[referrer_id])

                    if referrer_id not in user_bonuses:
                        user_bonuses[referrer_id] = {'has_discount': False}

                    if current_count >= 10 and not user_bonuses[referrer_id]['has_discount']:
                        user_bonuses[referrer_id]['has_discount'] = True
                        successful_referrals[referrer_id].clear()
                        try:
                            bot.send_message(
                                referrer_id,
                                "🎉 **Поздравляем!** 10 ваших рефералов сделали покупки!\n\n"
                                "✨ Вам активирована **скидка 10%** на следующий заказ!"
                            )
                        except:
                            pass
                    else:
                        try:
                            bot.send_message(
                                referrer_id,
                                f"🔔 Ваш реферал сделал заказ!\nПрогресс: **{current_count} / 10**"
                            )
                        except:
                            pass

            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=call.message.caption + "\n\n✅ **СТАТУС: ВЫПОЛНЕН**"
            )

    elif call.data.startswith("adm_reject_"):
        order_id = int(call.data.split("_")[2])
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("❌ Неверная сумма", callback_data=f"adm_reason_{order_id}_sum"),
            types.InlineKeyboardButton("❌ Нечеткий чек", callback_data=f"adm_reason_{order_id}_blur"),
            types.InlineKeyboardButton("❌ Чек уже использован", callback_data=f"adm_reason_{order_id}_used")
        )
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup
        )

    elif call.data.startswith("adm_reason_"):
        parts = call.data.split("_")
        order_id, reason_code = int(parts[2]), parts[3]

        reasons = {
            "sum": "Сумма в чеке не соответствует стоимости заказа.",
            "blur": "Скриншот чека нечеткий или не разборчив.",
            "used": "Данный чек был использован ранее."
        }
        reason_text = reasons.get(reason_code, "Чек не прошёл проверку.")

        if order_id in orders:
            orders[order_id]['status'] = f"❌ Отклонен ({reason_text})"
            target_user_id = orders[order_id]['user_id']

            bot.send_message(
                target_user_id,
                f"⚠️ **Ваш заказ #{order_id} был отклонен.**\n\n"
                f"**Причина:** {reason_text}\n\n"
                f"Если произошла ошибка, напишите в поддержку."
            )

            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=call.message.caption + f"\n\n❌ **СТАТУС: ОТКЛОНЕН ({reason_text})**"
            )

# === ПРИЕМ ЧЕКОВ ===
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    all_users.add(user_id)

    active_order_id = None
    for oid, data in reversed(list(orders.items())):
        if data['user_id'] == user_id and data['status'] == 'Ожидает чека':
            active_order_id = oid
            break

    if active_order_id:
        orders[active_order_id]['status'] = '⏳ На проверке'

        bot.send_message(
            user_id,
            "📩 **Чек принят и передан администратору!**\n\n"
            "Заказ будет обработан в течение 5-15 минут. Вы получите уведомление!"
        )

        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_approve = types.InlineKeyboardButton("✅ Выполнить", callback_data=f"adm_approve_{active_order_id}")
        btn_reject = types.InlineKeyboardButton("❌ Отклонить", callback_data=f"adm_reject_{active_order_id}")
        markup.add(btn_approve, btn_reject)

        order_info = orders[active_order_id]
        username = f"@{message.from_user.username}" if message.from_user.username else "нет"

        adm_caption = (
            f"📥 **НОВЫЙ ЧЕК К ЗАКАЗУ #{active_order_id}**\n\n"
            f"👤 Клиент: {username} (ID: `{user_id}`)\n"
            f"🎮 Игра: **{order_info['game']}**\n"
            f"📦 Пакет: **{order_info['pack']}**\n"
            f"💰 К оплате: **{order_info['price']} TJS**"
        )

        bot.send_photo(
            ADMIN_ID,
            message.photo[-1].file_id,
            caption=adm_caption,
            reply_markup=markup,
            parse_mode="Markdown"
        )
    else:
        bot.send_message(
            user_id,
            "❓ Вы прислали фото, но у вас нет активного заказа.\n"
            "Сначала выберите нужный товар в главном меню!"
        )

if __name__ == '__main__':
    print("Запуск приукрашенного бота...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
  
