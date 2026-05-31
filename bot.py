import os
import io
import requests
import base64
from PIL import Image
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
STABILITY_KEY = os.getenv("STABILITY_API_KEY")
REPLICATE_KEY = os.getenv("REPLICATE_API_KEY")
ADMIN_ID = 7860734994

users = {}

def compress_image(img_bytes, max_size=9*1024*1024):
    img = Image.open(io.BytesIO(img_bytes))
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    output = io.BytesIO()
    quality = 90
    img.save(output, format="JPEG", quality=quality)
    while output.tell() > max_size and quality > 30:
        output = io.BytesIO()
        quality -= 10
        img.save(output, format="JPEG", quality=quality)
    output.seek(0)
    output.name = "result.jpg"
    return output

async def delete_prev(context, chat_id):
    msg_id = context.user_data.get("last_bot_msg")
    if msg_id:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except:
            pass

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📸 Upscale", callback_data="upscale"),
         InlineKeyboardButton("🎨 AI Generate", callback_data="generate")],
        [InlineKeyboardButton("📊 Statistika", callback_data="stats"),
         InlineKeyboardButton("ℹ️ Bot haqida", callback_data="about")]
    ])

def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Menyuga qaytish", callback_data="back")]
    ])

def result_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📸 Upscale", callback_data="upscale"),
         InlineKeyboardButton("🎨 AI Generate", callback_data="generate")],
        [InlineKeyboardButton("🔙 Menyu", callback_data="back")]
    ])

MAIN_TEXT = (
    "⚡️ *Stability AI Bot* ga xush kelibsiz!\n\n"
    "━━━━━━━━━━━━━━━\n"
    "📸 *Upscale* — Rasmni tiniq qilish\n"
    "🎨 *AI Generate* — img2img Stable Diffusion\n"
    "━━━━━━━━━━━━━━━\n\n"
    "👇 Xizmatni tanlang:"
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in users:
        users[user.id] = {
            "name": user.first_name,
            "upscale": 0,
            "generate": 0,
            "count": 0,
            "blocked": False
        }
    await delete_prev(context, update.effective_chat.id)
    msg = await update.message.reply_text(
        MAIN_TEXT, parse_mode="Markdown", reply_markup=main_keyboard()
    )
    context.user_data["last_bot_msg"] = msg.message_id
    context.user_data["mode"] = None

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    chat_id = query.message.chat_id

    if user_id not in users:
        users[user_id] = {
            "name": query.from_user.first_name,
            "upscale": 0, "generate": 0,
            "count": 0, "blocked": False
        }

    async def edit(text, kb=None):
        try:
            await query.message.edit_text(
                text, parse_mode="Markdown", reply_markup=kb
            )
            context.user_data["last_bot_msg"] = query.message.message_id
        except:
            msg = await context.bot.send_message(
                chat_id, text, parse_mode="Markdown", reply_markup=kb
            )
            context.user_data["last_bot_msg"] = msg.message_id

    if query.data == "back":
        context.user_data["mode"] = None
        await edit(MAIN_TEXT, main_keyboard())

    elif query.data == "upscale":
        context.user_data["mode"] = "upscale"
        await edit(
            "📸 *Upscale*\n\nRasmingizni yuboring!\n_Yuqori sifatga ko'taraman_ ✨",
            back_keyboard()
        )

    elif query.data == "generate":
        context.user_data["mode"] = "generate_ratio"
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬜ 1:1 Kvadrat", callback_data="ratio_1:1")],
            [InlineKeyboardButton("📱 9:16 Vertikal", callback_data="ratio_9:16")],
            [InlineKeyboardButton("🖥️ 16:9 Gorizontal", callback_data="ratio_16:9")],
            [InlineKeyboardButton("🔙 Menyuga qaytish", callback_data="back")]
        ])
        await edit("🎨 *AI Generate*\n\nRasm o'lchamini tanlang:", kb)

    elif query.data.startswith("ratio_"):
        ratio = query.data.replace("ratio_", "")
        context.user_data["ratio"] = ratio
        context.user_data["mode"] = "generate"
        await edit(
            f"🎨 *AI Generate* | O'lcham: *{ratio}*\n\n"
            "Rasmingizni yuboring — AI qayta yaratadi! 🎨",
            back_keyboard()
        )

    elif query.data == "stats":
        u = users.get(user_id, {})
        await edit(
            f"📊 *Statistika*\n\n"
            f"📸 Upscale: *{u.get('upscale', 0)} ta*\n"
            f"🎨 Generate: *{u.get('generate', 0)} ta*\n"
            f"📦 Jami: *{u.get('count', 0)} ta*",
            back_keyboard()
        )

    elif query.data == "about":
        await edit(
            "ℹ️ *Bot haqida*\n\n"
            "🤖 *Stability AI Bot*\n\n"
            "• 📸 Upscale — rasmni tiniqlashtirish\n"
            "• 🎨 AI Generate — img2img\n\n"
            "🛠 *Texnologiya:* Replicate + Stability AI\n"
            "━━━━━━━━━━━━━━━\n"
            "👤 *Yaratuvchi:* @EHENCEADS",
            back_keyboard()
        )

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Ruxsat yo'q!")
        return
    text = "👥 *Foydalanuvchilar:*\n\n"
    for uid, data in users.items():
        status = "🚫" if data.get("blocked") else "✅"
        text += f"{status} *{data['name']}* | `{uid}` | 📸{data.get('upscale',0)} 🎨{data.get('generate',0)}\n"
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
    else:
        await update.message.reply_text("Foydalanuvchi topilmadi!")

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
    else:
        await update.message.reply_text("Foydalanuvchi topilmadi!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id

    if user.id not in users:
        users[user.id] = {
            "name": user.first_name,
            "upscale": 0, "generate": 0,
            "count": 0, "blocked": False
        }

    if users[user.id].get("blocked"):
        await update.message.reply_text("🚫 Siz admin tomonidan bloklandingiz!")
        return

    if not update.message.photo:
        msg = await update.message.reply_text(
            "📸 Rasm yuboring yoki /start bosing!"
        )
        context.user_data["last_bot_msg"] = msg.message_id
        return

    mode = context.user_data.get("mode")
    if not mode:
        msg = await update.message.reply_text(
            "👆 Avval xizmatni tanlang!",
            reply_markup=main_keyboard()
        )
        context.user_data["last_bot_msg"] = msg.message_id
        return

    await delete_prev(context, chat_id)
    proc_msg = await context.bot.send_message(
        chat_id, "⏳ *Qayta ishlanmoqda...*", parse_mode="Markdown"
    )
    context.user_data["last_bot_msg"] = proc_msg.message_id

    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    img_bytes = bytes(await file.download_as_bytearray())

    try:
        if mode == "generate":
            ratio = context.user_data.get("ratio", "16:9")
            img_b64 = "data:image/png;base64," + base64.b64encode(img_bytes).decode()

            response = requests.post(
                "https://api.replicate.com/v1/models/stability-ai/stable-diffusion/versions/ac732df83cea7fff18b8472768c88ad041fa750ff7682a21affe81863cbe77e4/predictions",
                headers={
                    "Authorization": f"Token {REPLICATE_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "input": {
                        "image": img_b64,
                        "prompt": "high quality, cinematic, professional, sharp, detailed",
                        "strength": 0.6,
                        "guidance_scale": 7.5,
                        "num_inference_steps": 30
                    }
                }
            )

            if response.status_code in [200, 201]:
                prediction = response.json()
                prediction_id = prediction.get("id")
                import time
                result_url = None
                for _ in range(60):
                    time.sleep(2)
                    check = requests.get(
                        f"https://api.replicate.com/v1/predictions/{prediction_id}",
                        headers={"Authorization": f"Token {REPLICATE_KEY}"}
                    )
                    check_data = check.json()
                    if check_data.get("status") == "succeeded":
                        output = check_data.get("output")
                        result_url = output[0] if isinstance(output, list) else output
                        break
                    elif check_data.get("status") == "failed":
                        break

                if result_url:
                    img_response = requests.get(result_url)
                    photo_io = compress_image(img_response.content)
                    users[user.id]["generate"] += 1
                    users[user.id]["count"] += 1
                    try:
                        await proc_msg.delete()
                    except:
                        pass
                    await update.message.reply_photo(
                        photo=photo_io,
                        caption="✅ *AI Generate tayyor!* 🎨",
                        parse_mode="Markdown",
                        reply_markup=result_keyboard()
                    )
                else:
                    try:
                        await proc_msg.delete()
                    except:
                        pass
                    msg = await context.bot.send_message(
                        chat_id, "❌ AI Generate muvaffaqiyatsiz. Qayta urinib ko'ring!"
                    )
                    context.user_data["last_bot_msg"] = msg.message_id
            else:
                try:
                    await proc_msg.delete()
                except:
                    pass
                msg = await context.bot.send_message(
                    chat_id, f"❌ Xatolik: `{response.status_code}`", parse_mode="Markdown"
                )
                context.user_data["last_bot_msg"] = msg.message_id

        else:
            response = requests.post(
                "https://api.stability.ai/v2beta/stable-image/upscale/fast",
                headers={
                    "authorization": f"Bearer {STABILITY_KEY}",
                    "accept": "image/*"
                },
                files={"image": ("image.png", img_bytes, "image/png")},
                data={"output_format": "png"}
            )

            try:
                await proc_msg.delete()
            except:
                pass

            if response.status_code == 200:
                photo_io = compress_image(response.content)
                users[user.id]["upscale"] += 1
                users[user.id]["count"] += 1
                await update.message.reply_photo(
                    photo=photo_io,
                    caption="✅ *Upscale tayyor!* 📸",
                    parse_mode="Markdown",
                    reply_markup=result_keyboard()
                )
            else:
                msg = await context.bot.send_message(
                    chat_id,
                    f"❌ Upscale xatolik: `{response.status_code}`\n"
                    f"`{response.text[:100]}`",
                    parse_mode="Markdown"
                )
                context.user_data["last_bot_msg"] = msg.message_id

    except Exception as e:
        try:
            await proc_msg.delete()
        except:
            pass
        msg = await context.bot.send_message(
            chat_id, f"❌ Xatolik: `{str(e)[:200]}`", parse_mode="Markdown"
        )
        context.user_data["last_bot_msg"] = msg.message_id

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin_panel))
app.add_handler(CommandHandler("block", block_user))
app.add_handler(CommandHandler("unblock", unblock_user))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.ALL, handle_message))
app.run_polling()
