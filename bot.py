import os
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
STABILITY_KEY = os.getenv("STABILITY_API_KEY")

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("📸 Menga rasm yuboring, men uni upscale qilaman!")
        return
    await update.message.reply_text("⏳ Rasm qayta ishlanmoqda, biroz kuting...")
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
app.add_handler(MessageHandler(filters.ALL, handle_image))
app.run_polling()
