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

    if users[user.id].get("blocked"):
        await update.message.reply_text("🚫 Siz admin tomonidan bloklandingiz!")
        return

    # API KEY KIRITISH
    if context.user_data.get("waiting_key"):
        api_key = update.message.text.strip()

        if api_key.startswith("sk-"):
            users[user.id]["api_key"] = api_key
            context.user_data["waiting_key"] = False

            await update.message.reply_text(
                "✅ *API Key saqlandi!* Endi xizmatni tanlang!",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "❌ Noto'g'ri API Key!\n\n`sk-` bilan boshlanishi kerak!",
                parse_mode="Markdown"
            )
        return

    # FAQAT RASM QABUL QILISH
    if not update.message.photo:
        await update.message.reply_text(
            "📸 Rasm yuboring yoki /start bosing!"
        )
        return

    api_key = users[user.id].get("api_key")

    if not api_key:
        await update.message.reply_text(
            "⚠️ Avval /start bosib API Key kiriting!"
        )
        return

    mode = context.user_data.get("mode", "upscale")
    ratio = context.user_data.get("ratio", "16:9")

    await update.message.reply_text(
        "⏳ Rasm qayta ishlanmoqda...\nIltimos kuting."
    )

    try:
        photo = update.message.photo[-1]

        file = await context.bot.get_file(photo.file_id)

        img_bytes = await file.download_as_bytearray()

        # =========================
        # AI GENERATE
        # =========================
        if mode == "generate":

            response = requests.post(
                "https://api.stability.ai/v2beta/stable-image/generate/core",

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
                    "prompt": "cinematic digital art",
                    "output_format": "png",
                    "aspect_ratio": ratio
                },

                timeout=120
            )

        # =========================
        # UPSCALE
        # =========================
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
                },

                timeout=120
            )

        # =========================
        # SUCCESS
        # =========================
        if response.status_code == 200:

            if mode == "generate":
                users[user.id]["generate"] += 1
                caption = "✅ *AI Generate tayyor!* _(3 kredit)_"

            else:
                users[user.id]["upscale"] += 1
                caption = "✅ *Upscale tayyor!* _(1 kredit)_"

            users[user.id]["count"] += 1

            await update.message.reply_photo(
                photo=response.content,
                caption=caption,
                parse_mode="Markdown"
            )

        # =========================
        # ERROR
        # =========================
        else:

            print("STATUS:", response.status_code)
            print("ERROR:", response.text)

            await update.message.reply_text(
                f"❌ Xatolik: {response.status_code}\n\n{response.text}"
            )

    except Exception as e:

        print("SYSTEM ERROR:", str(e))

        await update.message.reply_text(
            f"❌ Tizim xatosi:\n{str(e)}"
            )
