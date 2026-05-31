import os
import io
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7860734994
users = {}

async def delete_prev(context, chat_id):
    msg_id = context.user_data.get("last_bot_msg")
    if msg_id:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except:
            pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in users:
        users[user.id] = {"name": user.first_name, "count": 0, "blocked": False, "api_key": None, "upscale": 0, "generate": 0}
    keyboard = [
        [InlineKeyboardButton("📸 Upscale", callback_data="upscale"),
         InlineKeyboardButton("🎨 AI Generate", callback_data="generate")],
        [InlineKeyboardButton("🔑 API Key", callback_data="setkey"),
         InlineKeyboardButton("📊 Statistika", callback_data="stats")],
        [InlineKeyboardButton("ℹ️ Bot haqida", callback_data="about")]
    ]
    await delete_prev(context, update.effective_chat.id)
    msg = await update.message.reply_text(
        "⚡️ *Stability AI Bot* ga xush kelibsiz!\n\n"
        "━━━━━━━━━━━━━━━\n"
        "📸 *Upscale* — Rasmni tiniq qilish _(1 kredit)_\n"
        "🎨 *AI Generate* — Stable Diffusion _(3 kredit)_\n"
        "━━━━━━━━━━━━━━━\n\n"
        "⚠️ Avval 🔑 *API Key* kiriting!\n"
        "👇 Xizmatni tanlang:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    context.user_data["last_bot_msg"] = msg.message_id

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    chat_id = query.message.chat_id

    if user_id not in users:
        users[user_id] = {"name": query.from_user.first_name, "count": 0, "blocked": False, "api_key": None, "upscale": 0, "generate": 0}

    async def edit_or_send(text, keyboard=None):
        try:
            await query.message.edit_text(
                text, parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None
            )
            context.user_data["last_bot_msg"] = query.message.message_id
        except:
            msg = await context.bot.send_message(chat_id, text, parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None)
            context.user_data["last_bot_msg"] = msg.message_id

    if query.data == "setkey":
        context.user_data["waiting_key"] = True
        context.user_data["mode"] = None
        await edit_or_send(
            "🔑 *API Key kiriting*\n\n"
            "platform.stability.ai dan oling va yuboring:\n"
            "Misol: `sk-xxxxxxxxxxxxxxxx`\n\n"
            "_/start — menyuga qaytish_"
        )

    elif query.data == "upscale":
        if not users.get(user_id, {}).get("api_key"):
            await edit_or_send("⚠️ Avval 🔑 *API Key* kiriting!\n\n_/start — menyuga qaytish_")
            return
        context.user_data["mode"] = "upscale"
        context.user_data["waiting_key"] = False
        await edit_or_send(
            "📸 *Upscale*\n\n"
            "Rasmingizni yuboring — men uni yuqori sifatga ko'taraman!\n"
            "💰 _1 kredit sarflanadi_\n\n"
            "_/start — menyuga qaytish_"
        )

    elif query.data == "generate":
        if not users.get(user_id, {}).get("api_key"):
            await edit_or_send("⚠️ Avval 🔑 *API Key* kiriting!\n\n_/start — menyuga qaytish_")
            return
        context.user_data["waiting_key"] = False
        keyboard = [
            [InlineKeyboardButton("⬜ 1:1 Kvadrat", callback_data="ratio_1:1")],
            [InlineKeyboardButton("📱 9:16 Vertikal", callback_data="ratio_9:16")],
            [InlineKeyboardButton("🖥️ 16:9 Gorizontal", callback_data="ratio_16:9")],
            [InlineKeyboardButton("🔙 Orqaga", callback_data="back")]
        ]
        await edit_or_send(
            "🎨 *AI Generate*\n\n"
            "Rasm o'lchamini tanlang:\n"
            "💰 _3 kredit sarflanadi_",
            keyboard
        )

    elif query.data.startswith("ratio_"):
        ratio = query.data.replace("ratio_", "")
        context.user_data["ratio"] = ratio
        context.user_data["mode"] = "generate"
        await edit_or_send(
            f"🎨 *AI Generate* | O'lcham: *{ratio}*\n\n"
            "Rasmingizni yuboring — AI uni qayta yaratadi!\n\n"
            "_/start — menyuga qaytish_"
        )

    elif query.data == "stats":
        api_key = users.get(user_id, {}).get("api_key")
        if not api_key:
            await edit_or_send("⚠️ Avval 🔑 *API Key* kiriting!")
            return
        try:
            r = requests.get(
                "https://api.stability.ai/v1/user/balance",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            if r.status_code == 200:
                credits = r.json().get("credits", 0)
                u = users.get(user_id, {})
                await edit_or_send(
                    f"📊 *Statistika*\n\n"
                    f"💰 Qolgan kredit: *{credits:.1f}*\n\n"
                    f"📸 Upscale: *{u.get('upscale', 0)} ta* _(1 kredit/ta)_\n"
                    f"🎨 Generate: *{u.get('generate', 0)} ta* _(3 kredit/ta)_\n"
                    f"📦 Jami: *{u.get('count', 0)} ta*\n\n"
                    f"_/start — menyuga qaytish_"
                )
            else:
                await edit_or_send("❌ Kredit ma'lumotini olishda xatolik!")
        except:
            await edit_or_send("❌ Xatolik yuz berdi!")

    elif query.data == "about":
        await edit_or_send(
            "ℹ️ *Bot haqida*\n\n"
            "🤖 *Stability AI Bot*\n\n"
            "⚡️ *Imkoniyatlar:*\n"
            "• 📸 Upscale — 1 kredit\n"
            "• 🎨 AI Generate — 3 kredit\n"
            "• 📊 Kredit balansi\n\n"
            "🛠 *Texnologiya:* Stability AI\n"
            "━━━━━━━━━━━━━━━\n"
            "👤 *Yaratuvchi:* @EHENCEADS\n\n"
            "_/start — menyuga qaytish_"
        )

    elif query.data == "back":
        keyboard = [
            [InlineKeyboardButton("📸 Upscale", callback_data="upscale"),
             InlineKeyboardButton("🎨 AI Generate", callback_data="generate")],
            [InlineKeyboardButton("🔑 API Key", callback_data="setkey"),
             InlineKeyboardButton("📊 Statistika", callback_data="stats")],
            [InlineKeyboardButton("ℹ️ Bot haqida", callback_data="about")]
        ]
        await edit_or_send(
            "⚡️ *Stability AI Bot*\n\n"
            "━━━━━━━━━━━━━━━\n"
            "📸 *Upscale* — 1 kredit\n"
            "🎨 *AI Generate* — 3 kredit\n"
            "━━━━━━━━━━━━━━━\n\n"
            "👇 Xizmatni tanlang:",
            keyboard
        )

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Ruxsat yo'q!")
        return
    text = "👥 *Foydalanuvchilar:*\n\n"
    for uid, data in users.items():
        status = "🚫" if data.get("blocked") else "✅"
        key = "✅" if data.get("api_key") else "❌"
        text += f"{status} *{data['name']}* | `{uid}` | 📸{data.get('upscale',0)} 🎨{data.get('generate',0)} | Key:{key}\n"
    if not users:
        text = "Hali foydalanuvchi yo'q"
    await update.message.reply_text(text, parse_mode="Markdown")

async def block_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Ishlatish: /block 123456789")
        return
    uid = int(context.args[0])
    if uid in users:
        users[uid]["blocked"] = True
        await update.message.reply_text(f"🚫 {users[uid]['name']} bloklandi!")

async def unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Ishlatish: /unblock 123456789")
        return
    uid = int(context.args[0])
    if uid in users:
        users[uid]["blocked"] = False
        await update.message.reply_text(f"✅ {users[uid]['name']} blokdan chiqarildi!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id

    if user.id not in users:
        users[user.id] = {"name": user.first_name, "count": 0, "blocked": False, "api_key": None, "upscale": 0, "generate": 0}

    if users[user.id].get("blocked"):
        await update.message.reply_text("🚫 Siz admin tomonidan bloklandingiz!")
        return

    # API key kutilayotgan bo'lsa
    if context.user_data.get("waiting_key") and update.message.text:
        api_key = update.message.text.strip()
        try:
            await update.message.delete()
        except:
            pass
        await delete_prev(context, chat_id)
        if api_key.startswith("sk-"):
            users[user.id]["api_key"] = api_key
            context.user_data["waiting_key"] = False
            keyboard = [
                [InlineKeyboardButton("📸 Upscale", callback_data="upscale"),
                 InlineKeyboardButton("🎨 AI Generate", callback_data="generate")],
                [InlineKeyboardButton("📊 Statistika", callback_data="stats")]
            ]
            msg = await context.bot.send_message(
                chat_id,
                "✅ *API Key saqlandi!*\n\nXizmatni tanlang:",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            context.user_data["last_bot_msg"] = msg.message_id
        else:
            msg = await context.bot.send_message(
                chat_id,
                "❌ *Noto'g'ri!* `sk-` bilan boshlanishi kerak!\n\nQayta yuboring:",
                parse_mode="Markdown"
            )
            context.user_data["last_bot_msg"] = msg.message_id
        return

    if not update.message.photo:
        await update.message.reply_text("📸 Rasm yuboring yoki /start bosing!")
        return

    api_key = users[user.id].get("api_key")
    if not api_key:
        await update.message.reply_text("⚠️ Avval /start bosib *API Key* kiriting!", parse_mode="Markdown")
        return

    mode = context.user_data.get("mode", "upscale")
    ratio = context.user_data.get("ratio", "16:9")

    await delete_prev(context, chat_id)
    processing_msg = await context.bot.send_message(
        chat_id,
        "⏳ *Qayta ishlanmoqda, kuting...*",
        parse_mode="Markdown"
    )
    context.user_data["last_bot_msg"] = processing_msg.message_id

    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    img_bytes = await file.download_as_bytearray()

    try:
        if mode == "generate":
            response = requests.post(
                "https://api.stability.ai/v2beta/stable-image/control/style",
                headers={"authorization": f"Bearer {api_key}", "accept": "image/*"},
                files={"image": ("image.png", bytes(img_bytes), "image/png")},
                data={"output_format": "png", "aspect_ratio": ratio, "fidelity": 0.9}
            )
        else:
            response = requests.post(
                "https://api.stability.ai/v2beta/stable-image/upscale/fast",
                headers={"authorization": f"Bearer {api_key}", "accept": "image/*"},
                files={"image": ("image.png", bytes(img_bytes), "image/png")},
                data={"output_format": "png"}
            )

        try:
            await processing_msg.delete()
        except:
            pass

        if response.status_code == 200:
            if mode == "generate":
                users[user.id]["generate"] = users[user.id].get("generate", 0) + 1
                caption = "✅ *AI Generate tayyor!* _(3 kredit sarflandi)_"
            else:
                users[user.id]["upscale"] = users[user.id].get("upscale", 0) + 1
                caption = "✅ *Upscale tayyor!* _(1 kredit sarflandi)_"
            users[user.id]["count"] = users[user.id].get("count", 0) + 1

            photo_io = io.BytesIO(response.content)
            photo_io.name = "result.png"

            keyboard = [
                [InlineKeyboardButton("📸 Upscale", callback_data="upscale"),
                 InlineKeyboardButton("🎨 AI Generate", callback_data="generate")],
                [InlineKeyboardButton("🔙 Menyu", callback_data="back")]
            ]
            await update.message.reply_photo(
                photo=photo_io,
                caption=caption,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        elif response.status_code == 202:
            msg = await context.bot.send_message(chat_id, "⏳ Server band, 1 daqiqa kutib qayta yuboring!")
            context.user_data["last_bot_msg"] = msg.message_id
        else:
            msg = await context.bot.send_message(
                chat_id,
                f"❌ *Xatolik:* `{response.status_code}`\n"
                f"API Key noto'g'ri yoki kredit tugagan!\n\n"
                f"_/start → 📊 Statistika_",
                parse_mode="Markdown"
            )
            context.user_data["last_bot_msg"] = msg.message_id

    except Exception as e:
        try:
            await processing_msg.delete()
        except:
            pass
        msg = await context.bot.send_message(chat_id, f"❌ Xatolik yuz berdi: {str(e)[:100]}")
        context.user_data["last_bot_msg"] = msg.message_id

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin_panel))
app.add_handler(CommandHandler("block", block_user))
app.add_handler(CommandHandler("unblock", unblock_user))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.ALL, handle_message))
app.run_polling()
