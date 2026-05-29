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
        users[user.id] = {"name": user.first_name, "count": 0, "blocked": False, "api_key": None, "upscale": 0, "generate": 0}
    keyboard = [
        [InlineKeyboardButton("📸 Upscale", callback_data="upscale"),
         InlineKeyboardButton("🎨 AI Generate", callback_data="generate")],
        [InlineKeyboardButton("🔑 API Key kiriting", callback_data="setkey")],
        [InlineKeyboardButton("📊 Statistika", callback_data="stats"),
         InlineKeyboardButton("ℹ️ Bot haqida", callback_data="about")]
    ]
    await update.message.reply_text(
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

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id not in users:
        users[user_id] = {"name": query.from_user.first_name, "count": 0, "blocked": False, "api_key": None, "upscale": 0, "generate": 0}

    if query.data == "setkey":
        context.user_data["waiting_key"] = True
        await query.message.reply_text(
            "🔑 *API Key kiriting*\n\n"
            "platform.stability.ai dan oling va yuboring:\n"
            "Misol: `sk-xxxxxxxxxxxxxxxx`",
            parse_mode="Markdown"
        )
    elif query.data == "upscale":
        if not users.get(user_id, {}).get("api_key"):
            await query.message.reply_text("⚠️ Avval 🔑 API Key kiriting!")
            return
        context.user_data["mode"] = "upscale"
        await query.message.reply_text("📸 *Upscale* uchun rasm yuboring!\n\n_1 kredit sarflanadi_", parse_mode="Markdown")

    elif query.data == "generate":
        if not users.get(user_id, {}).get("api_key"):
            await query.message.reply_text("⚠️ Avval 🔑 API Key kiriting!")
            return
        context.user_data["mode"] = "generate_wait"
        keyboard = [
            [InlineKeyboardButton("⬜ 1:1 Kvadrat", callback_data="ratio_1:1")],
            [InlineKeyboardButton("📱 9:16 Vertikal", callback_data="ratio_9:16")],
            [InlineKeyboardButton("🖥️ 16:9 Gorizontal", callback_data="ratio_16:9")],
        ]
        await query.message.reply_text(
            "🎨 *AI Generate*\n\nRasm o'lchamini tanlang:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data.startswith("ratio_"):
        ratio = query.data.replace("ratio_", "")
        context.user_data["ratio"] = ratio
        context.user_data["mode"] = "generate"
        await query.message.reply_text(
            f"✅ O'lcham: *{ratio}*\n\n🎨 Endi rasmingizni yuboring — AI uni shu uslubda qayta yaratadi!",
            parse_mode="Markdown"
        )

    elif query.data == "stats":
        api_key = users.get(user_id, {}).get("api_key")
        if not api_key:
            await query.message.reply_text("⚠️ Avval API Key kiriting!")
            return
        try:
            r = requests.get(
                "https://api.stability.ai/v1/user/balance",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            if r.status_code == 200:
                credits = r.json().get("credits", 0)
                u = users.get(user_id, {})
                await query.message.reply_text(
                    f"📊 *Statistika*\n\n"
                    f"💰 Qolgan kredit: *{credits:.1f}*\n\n"
                    f"📸 Upscale qilingan: *{u.get('upscale', 0)} ta*\n"
                    f"🎨 Generate qilingan: *{u.get('generate', 0)} ta*\n"
                    f"📦 Jami: *{u.get('count', 0)} ta*\n\n"
                    f"💡 Upscale = 1 kredit\n"
                    f"💡 Generate = 3 kredit",
                    parse_mode="Markdown"
                )
            else:
                await query.message.reply_text("❌ Kredit ma'lumotini olishda xatolik!")
        except:
            await query.message.reply_text("❌ Xatolik yuz berdi!")

    elif query.data == "about":
        await query.message.reply_text(
            "ℹ️ *Bot haqida*\n\n"
            "🤖 *Stability AI Bot*\n\n"
            "⚡️ *Imkoniyatlar:*\n"
            "• 📸 Upscale — 1 kredit\n"
            "• 🎨 AI Generate — 3 kredit\n"
            "• 📊 Kredit balansi\n\n"
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
    if user.id not in users:
        users[user.id] = {"name": user.first_name, "count": 0, "blocked": False, "api_key": None, "upscale": 0, "generate": 0}
    if users[user.id].get("blocked"):
        await update.message.reply_text("🚫 Siz admin tomonidan bloklandingiz!")
        return

    if context.user_data.get("waiting_key"):
        api_key = update.message.text.strip()
        if api_key.startswith("sk-"):
            users[user.id]["api_key"] = api_key
            context.user_data["waiting_key"] = False
            await update.message.reply_text("✅ *API Key saqlandi!* Endi xizmatni tanlang!", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Noto'g'ri! `sk-` bilan boshlanishi kerak!", parse_mode="Markdown")
        return

    if not update.message.photo:
        await update.message.reply_text("📸 Rasm yuboring yoki /start bosing!")
        return

    api_key = users[user.id].get("api_key")
    if not api_key:
        await update.message.reply_text("⚠️ Avval /start bosib API Key kiriting!")
        return

    mode = context.user_data.get("mode", "upscale")
    ratio = context.user_data.get("ratio", "16:9")

    await update.message.reply_text("⏳ Qayta ishlanmoqda, kuting...")

    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    img_bytes = await file.download_as_bytearray()

    if mode == "generate":
        response = requests.post
            "https://api.stability.ai/v2beta/stable-image/generate/core",
        headers={"Authorization": f"Bearer {api_key}", "Accept": "image/*"},
            files={"image": ("image.png", bytes(img_bytes), "image/png")},
            data={
                data={
    "prompt": "cinematic digital art",
    "output_format": "png",
    "aspect_ratio": ratio
            }
                
                
            }
        )
    else:
        response = requests.post(
            "https://api.stability.ai/v2beta/stable-image/upscale/fast",
            headers={"Authorization": f"Bearer {api_key}", "Accept": "image/*"},
            files={"image": ("image.png", bytes(img_bytes), "image/png")},
            data={"output_format": "png"}
        )

    if mode == "generate":
        users[user.id]["generate"] = users[user.id].get("generate", 0) + 1
    else:
        users[user.id]["upscale"] = users[user.id].get("upscale", 0) + 1
    users[user.id]["count"] = users[user.id].get("count", 0) + 1

    if response.status_code == 200:
        caption = "✅ *AI Generate tayyor!* _(3 kredit)_" if mode == "generate" else "✅ *Upscale tayyor!* _(1 kredit)_"
        await update.message.reply_photo(photo=response.content, caption=caption, parse_mode="Markdown")
    else:
        else:
    print(response.status_code)
    print(response.text)

    await update.message.reply_text(
        f"{response.status_code}\n\n{response.text}"
    )
        )

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin_panel))
app.add_handler(CommandHandler("block", block_user))
app.add_handler(CommandHandler("unblock", unblock_user))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.ALL, handle_message))
app.run_polling()
