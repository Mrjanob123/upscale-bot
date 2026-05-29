import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
STABILITY_KEY = os.getenv("STABILITY_API_KEY")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📸 Rasm yuborish", callback_data="send_image")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Salom! Men Upscale botman!\n\n"
        "📸 Menga rasm yuboring — men uni Stability AI orqali yuqori sifatga ko'taraman!\n\n"
        "⬇️ Bosing yoki rasm yuboring:",
        reply_markup=reply_markup
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("📸 Iltimos, upscale qilmoqchi bo'lgan rasmingizni yuboring!")

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("📸 Iltimos, rasm yuboring!")
        return
    await update.message.reply_text("⏳ Rasm qayta ishlanmoqda, 30 soniya kuting...")
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    img_bytes = await file.download_as_bytearray()
    response = requests.post(
        "https://api.stability.ai/v2beta/stable-image/upscale/fast",
        headers={"authorization": f"Bearer {STABILITY_KEY}", "accept": "image/*"},
        files={"image": ("image.png", bytes(img_bytes), "image/png")},
        data={"output_format": "png"}
    )
    if response.status_code == 200:
        await update.message.reply_photo(photo=response.content, caption="✅ Upscale tayyor!")
    else:
        await update.message.reply_text("❌ Xatolik yuz berdi. Qayta urinib ko'ring.")

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.ALL, handle_image))
app.run_polling()
