import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7860734994

users = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in users:
        users[user.id] = {"name": user.first_name, "count": 0, "blocked": False, "api_key": None}
    keyboard = [
        [InlineKeyboardButton("📸 Upscale", callback_data="upscale"),
         InlineKeyboardButton("🎨 AI Generate", callback_data="generate")],
        [InlineKeyboardButton("🔑 API Key kiriting", callback_data="setkey")],
        [InlineKeyboardButton("ℹ️ Bot haqida", callback_data="about")]
    ]
    await update.message.reply_text(
        "⚡️ *Stability AI Bot* ga xush kelibsiz!\n\n"
        "🤖 Bu bot sun'iy intellekt yordamida:\n"
        "━━━━━━━━━━━━━━━\n"
        "📸 *Upscale* — Rasmni yuqori sifatga ko'tarish\n"
        "🎨 *AI Generate* — Stable Diffusion AI orqali qayta yaratish\n"
        "━━━━━━━━━━━━━━━\n\n"
        "⚠️ Ishlatish uchun *API Key* kiriting!\n"
        "👇 Xizmatni tanlang:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if query.data == "setkey":
        context.user_data["waiting_key"] = True
        await query.message.reply_text(
            "🔑 *API Key kiriting*\n\n"
            "platform.stability.ai dan API Key oling va yuboring:\n\n"
            "Misol: `sk-xxxxxxxxxxxxxxxx`",
            parse_mode="Markdown"
        )
    elif query.data == "upscale":
        if not users.get(user_id, {}).get("api_key"):
            await query.message.reply_text("⚠️ Avval 🔑 API Key kiriting!")
            return
        context.user_data["mode"] = "upscale"
        await query.message.reply_text("📸 Upscale uchun rasm yuboring!")
    elif query.data == "generate":
        if not users.get(user_id, {}).get("api_key"):
            await query.message.reply_text("⚠️ Avval 🔑 API Key kiriting!")
            return
        context.user_data["mode"] = "generate"
        await query.message.reply_text("🎨 AI Generate uchun rasm yuboring!")
    elif query.data == "about":
        await query.message.reply_text(
            "ℹ️ *Bot haqida*\n\n"
            "🤖 *Stability AI Bot*\n\n"
            "⚡️ *Imkoniyatlar:*\n"
            "• 📸 Rasmni yuqori sifatga ko'tarish\n"
            "• 🎨 AI orqali professional dizayn\n\n"
            "🛠 *Texnologiya:* Stability AI\n"
            "━━━━━━━━━━━━━━━\n"
            "👤 *Yaratuvchi:* @EHENCEADS",
            parse_mode="Markdown"
        )

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Ruxsat yo'q!")
        return
    text = "👥 *Foydalanuvchilar:*\n\n"
    for uid, data in users.items():
        status = "🚫" if data.get("blocked") else "✅"
        key = "✅ Bor" if data.get("api_key") else "❌ Yo'q"
        text += f"{status} *{data['name']}* | ID: `{uid}` | Rasm: {data['count']} | Key: {key}\n"
    if not users:
        text = "Hali foydalanuvchi yo'q"
    await update.message.reply_text(text, parse_mode="Markdown")

async def block_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Ruxsat yo'q!")
        return
    if not context.args:
        await update.message.reply_text("Ishlatish: /block 123456789")
        return
    uid = int(context.args[0])
    if uid in users:
        users[uid]["blocked"] = True
        await update.message.reply_text(f"🚫 {users[uid]['name']} bloklandi!")
    else:
        await update.message.reply_text("Foydalanuvchi topilmadi!")

async def unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Ruxsat yo'q!")
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
    if user.id not in users:
        users[user.id] = {"name": user.first_name, "count": 0, "blocked": False, "api_key": None}
    if users[user.id].get("blocked"):
        await update.message.reply_text("🚫 Siz admin tomonidan bloklandingiz!")
        return
    if context.user_data.get("waiting_key"):
        api_key = update.message.text.strip()
        if api_key.startswith("sk-"):
            users[user.id]["api_key"] = api_key
            context.user_data["waiting_key"] = False
            await update.message.reply_text("✅ API Key saqlandi! Endi rasm yuboring!")
        else:
            await update.message.reply_text("❌ Noto'g'ri key! sk- bilan boshlanishi kerak!")
        return
    if not update.message.photo:
        await update.message.reply_text("📸 Iltimos rasm yuboring yoki /start bosing!")
        return
    api_key = users[user.id].get("api_key")
    if not api_key:
        await update.message.reply_text("⚠️ Avval /start bosib API Key kiriting!")
        return
    mode = context.user_data.get("mode", "upscale")
    await update.message.reply_text("⏳ Qayta ishlanmoqda, kuting...")
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    img_bytes = await file.download_as_bytearray()
    if mode == "generate":
        response = requests.post(
            "https://api.stability.ai/v2beta/stable-image/generate/core",
            headers={"authorization": f"Bearer {api_key}", "accept": "image/*"},
            data={"prompt": "high quality cinematic professional detailed", "output_format": "png"},
            files={"none": ""}
        )
    else:
        response = requests.post(
            "https://api.stability.ai/v2beta/stable-image/upscale/fast",
            headers={"authorization": f"Bearer {api_key}", "accept": "image/*"},
            files={"image": ("image.png", bytes(img_bytes), "image/png")},
            data={"output_format": "png"}
        )
    users[user.id]["count"] += 1
    if response.status_code == 200:
        caption = "✅ *AI Generate tayyor!*" if mode == "generate" else "✅ *Upscale tayyor!*"
        await update.message.reply_photo(photo=response.content, caption=caption, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Xatolik! API Key noto'g'ri yoki kredit tugagan!")

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin_panel))
app.add_handler(CommandHandler("block", block_user))
app.add_handler(CommandHandler("unblock", unblock_user))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.ALL, handle_message))
app.run_polling()
