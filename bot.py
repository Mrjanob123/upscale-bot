import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7860734994

users = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if user.id not in users:
        users[user.id] = {
            "name": user.first_name,
            "count": 0,
            "blocked": False,
            "api_key": None,
            "upscale": 0,
            "generate": 0
        }

    keyboard = [
        [
            InlineKeyboardButton("📸 Upscale", callback_data="upscale"),
            InlineKeyboardButton("🎨 AI Generate", callback_data="generate")
        ],
        [
            InlineKeyboardButton("🔑 API Key kiriting", callback_data="setkey")
        ],
        [
            InlineKeyboardButton("📊 Statistika", callback_data="stats"),
            InlineKeyboardButton("ℹ️ Bot haqida", callback_data="about")
        ]
    ]

    await update.message.reply_text(
        "⚡️ *Stability AI Bot* ga xush kelibsiz!\n\n"
        "━━━━━━━━━━━━━━━\n"
        "📸 *Upscale* — Rasmni tiniq qilish _(1 kredit)_\n"
        "🎨 *AI Generate* — AI style _(3 kredit)_\n"
        "━━━━━━━━━━━━━━━\n\n"
        "⚠️ Avval 🔑 *API Key* kiriting!\n"
        "👇 Xizmatni tanlang:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if user_id not in users:
        users[user_id] = {
            "name": query.from_user.first_name,
            "count": 0,
            "blocked": False,
            "api_key": None,
            "upscale": 0,
            "generate": 0
        }

    if query.data == "setkey":

        context.user_data["waiting_key"] = True

        await query.message.reply_text(
            "🔑 *API Key kiriting*\n\n"
            "https://platform.stability.ai/account/keys\n\n"
            "Misol:\n"
            "`sk-xxxxxxxxxxxxxxxx`",
            parse_mode="Markdown"
        )

    elif query.data == "upscale":

        if not users[user_id].get("api_key"):
            await query.message.reply_text(
                "⚠️ Avval API Key kiriting!"
            )
            return

        context.user_data["mode"] = "upscale"

        await query.message.reply_text(
            "📸 Upscale uchun rasm yuboring!",
            parse_mode="Markdown"
        )

    elif query.data == "generate":

        if not users[user_id].get("api_key"):
            await query.message.reply_text(
                "⚠️ Avval API Key kiriting!"
            )
            return

        context.user_data["mode"] = "generate"

        await query.message.reply_text(
            "🎨 AI Generate uchun rasm yuboring!",
            parse_mode="Markdown"
        )

    elif query.data == "stats":

        api_key = users[user_id].get("api_key")

        if not api_key:
            await query.message.reply_text(
                "⚠️ API Key yo'q!"
            )
            return

        try:

            r = requests.get(
                "https://api.stability.ai/v1/user/balance",
                headers={
                    "Authorization": f"Bearer {api_key}"
                }
            )

            if r.status_code == 200:

                credits = r.json().get("credits", 0)

                u = users[user_id]

                await query.message.reply_text(
                    f"📊 *Statistika*\n\n"
                    f"💰 Kredit: *{credits:.1f}*\n\n"
                    f"📸 Upscale: *{u['upscale']}*\n"
                    f"🎨 Generate: *{u['generate']}*\n"
                    f"📦 Jami: *{u['count']}*",
                    parse_mode="Markdown"
                )

            else:
                await query.message.reply_text(
                    "❌ Kreditni olishda xato!"
                )

        except Exception as e:
            await query.message.reply_text(
                f"❌ Xato:\n{e}"
            )

    elif query.data == "about":

        await query.message.reply_text(
            "🤖 Stability AI Bot\n\n"
            "📸 Upscale\n"
            "🎨 AI Generate\n"
            "📊 Kredit statistikasi\n\n"
            "👤 Creator: @EHENCEADS",
            parse_mode="Markdown"
        )


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    text = "👥 *Foydalanuvchilar*\n\n"

    for uid, data in users.items():

        text += (
            f"👤 {data['name']}\n"
            f"🆔 `{uid}`\n"
            f"📸 {data['upscale']} | 🎨 {data['generate']}\n\n"
        )

    await update.message.reply_text(
        text,
        parse_mode="Markdown"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if user.id not in users:
        users[user.id] = {
            "name": user.first_name,
            "count": 0,
            "blocked": False,
            "api_key": None,
            "upscale": 0,
            "generate": 0
        }

    if context.user_data.get("waiting_key"):

        api_key = update.message.text.strip()

        if len(api_key) > 20:

            users[user.id]["api_key"] = api_key
            context.user_data["waiting_key"] = False

            await update.message.reply_text(
                "✅ API Key saqlandi!"
            )

        else:

            await update.message.reply_text(
                "❌ API Key noto'g'ri!"
            )

        return

    if not update.message.photo:

        await update.message.reply_text(
            "📸 Rasm yuboring!"
        )

        return

    api_key = users[user.id].get("api_key")

    if not api_key:

        await update.message.reply_text(
            "⚠️ Avval API Key kiriting!"
        )

        return

    mode = context.user_data.get("mode", "upscale")

    await update.message.reply_text(
        "⏳ Ishlanmoqda..."
    )

    photo = update.message.photo[-1]

    file = await context.bot.get_file(photo.file_id)

    img_bytes = await file.download_as_bytearray()

    # GENERATE
    if mode == "generate":

        response = requests.post(
            "https://api.stability.ai/v2beta/stable-image/control/sketch",

            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "image/*"
            },

            files={
                "image": (
                    "image.png",
                    bytes(img_bytes),
                    "image/png"
                )
            },

            data={
                "prompt": "high quality detailed image",
                "control_strength": 0.7,
                "output_format": "png"
            }
        )

    # UPSCALE
    else:

        response = requests.post(
            "https://api.stability.ai/v2beta/stable-image/upscale/fast",

            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "image/*"
            },

            files={
                "image": (
                    "image.png",
                    bytes(img_bytes),
                    "image/png"
                )
            },

            data={
                "output_format": "png"
            }
        )

    if response.status_code == 200:

        if mode == "generate":
            users[user.id]["generate"] += 1
        else:
            users[user.id]["upscale"] += 1

        users[user.id]["count"] += 1

        caption = (
            "✅ AI Generate tayyor!"
            if mode == "generate"
            else "✅ Upscale tayyor!"
        )

        await update.message.reply_photo(
            photo=response.content,
            caption=caption
        )

    else:

        print(response.status_code)
        print(response.text)

        await update.message.reply_text(
            f"{response.status_code}\n\n{response.text}"
        )


app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin_panel))

app.add_handler(CallbackQueryHandler(button))

app.add_handler(
    MessageHandler(filters.ALL, handle_message)
)

app.run_polling()
