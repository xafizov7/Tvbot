import os
import requests
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)

# ========================
# SOZLAMALAR
# ========================
import os
BOT_TOKEN = os.environ.get("8687297980:AAE3yCz4K_5Xwt6NOfMXD68uGjUiGqrj0Yc")
M3U_URL = "http://f6f5887552dc.mylistbest.net/playlists/uplist/2bd18521192d3454473703b3daa265b2/playlist.m3u8"

# ========================
# M3U PARSE QILISH
# ========================
def parse_m3u(url):
    try:
        resp = requests.get(url, timeout=15)
        resp.encoding = 'utf-8'
        lines = resp.text.splitlines()
    except Exception as e:
        print(f"M3U yuklashda xato: {e}")
        return {}

    channels = {}
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF"):
            # Kanal nomini olish
            name_match = re.search(r',(.+)$', line)
            name = name_match.group(1).strip() if name_match else "Nomsiz"

            # Guruhni olish
            group_match = re.search(r'group-title="([^"]*)"', line)
            group = group_match.group(1).strip() if group_match else "Boshqa"

            # URL ni keyingi qatordan olish
            if i + 1 < len(lines):
                stream_url = lines[i + 1].strip()
                if stream_url and not stream_url.startswith("#"):
                    if group not in channels:
                        channels[group] = []
                    channels[group].append({"name": name, "url": stream_url})
            i += 2
        else:
            i += 1
    return channels

# Global kanallar ro'yxati
print("Kanallar yuklanmoqda...")
CHANNELS = parse_m3u(M3U_URL)
print(f"Jami {sum(len(v) for v in CHANNELS.values())} kanal, {len(CHANNELS)} kategoriya yuklandi.")

# ========================
# /start BUYRUG'I
# ========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    row = []
    categories = list(CHANNELS.keys())

    for i, cat in enumerate(categories):
        count = len(CHANNELS[cat])
        row.append(InlineKeyboardButton(f"📺 {cat} ({count})", callback_data=f"cat:{cat}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("🔍 Qidirish", callback_data="search")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🎬 *TV Online Botga Xush Kelibsiz!*\n\n"
        "📡 Quyidagi kategoriyalardan birini tanlang:\n\n"
        f"📊 Jami: *{sum(len(v) for v in CHANNELS.values())}* kanal",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

# ========================
# KATEGORIYA TANLASH
# ========================
async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("cat:"):
        cat_name = data[4:]
        channels = CHANNELS.get(cat_name, [])

        keyboard = []
        row = []
        for i, ch in enumerate(channels[:50]):  # max 50 kanal ko'rsatish
            row.append(InlineKeyboardButton(
                f"📺 {ch['name']}", callback_data=f"ch:{cat_name}:{i}"
            ))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        keyboard.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="back")])

        await query.edit_message_text(
            f"📂 *{cat_name}* kategoriyasi\n"
            f"📺 {len(channels)} ta kanal mavjud:\n\n"
            "Kanaldan birini tanlang:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("ch:"):
        parts = data.split(":", 2)
        cat_name = parts[1]
        ch_index = int(parts[2])
        channel = CHANNELS[cat_name][ch_index]

        keyboard = [
            [InlineKeyboardButton("▶️ Ochish (VLC)", url=channel['url'])],
            [InlineKeyboardButton("🔗 Link olish", callback_data=f"link:{cat_name}:{ch_index}")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data=f"cat:{cat_name}")]
        ]

        await query.edit_message_text(
            f"📺 *{channel['name']}*\n\n"
            f"📂 Kategoriya: {cat_name}\n\n"
            "▶️ Ko'rish uchun tugmani bosing:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("link:"):
        parts = data.split(":", 2)
        cat_name = parts[1]
        ch_index = int(parts[2])
        channel = CHANNELS[cat_name][ch_index]

        await query.answer()
        await query.message.reply_text(
            f"🔗 *{channel['name']}* stream linki:\n\n"
            f"`{channel['url']}`\n\n"
            "📱 VLC yoki MX Player da oching",
            parse_mode="Markdown"
        )

    elif data == "back":
        await start_from_callback(query, context)

    elif data == "search":
        context.user_data['searching'] = True
        await query.edit_message_text(
            "🔍 *Qidirish*\n\n"
            "Kanal nomini yozing (masalan: Uzbekistan, BBC, Sport):",
            parse_mode="Markdown"
        )

# ========================
# ORQAGA QAYTISH
# ========================
async def start_from_callback(query, context):
    keyboard = []
    row = []
    categories = list(CHANNELS.keys())

    for i, cat in enumerate(categories):
        count = len(CHANNELS[cat])
        row.append(InlineKeyboardButton(f"📺 {cat} ({count})", callback_data=f"cat:{cat}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("🔍 Qidirish", callback_data="search")])

    await query.edit_message_text(
        "🎬 *TV Online*\n\n"
        "📡 Kategoriya tanlang:\n\n"
        f"📊 Jami: *{sum(len(v) for v in CHANNELS.values())}* kanal",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ========================
# QIDIRISH
# ========================
async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('searching'):
        return

    query_text = update.message.text.lower()
    results = []

    for cat, channels in CHANNELS.items():
        for i, ch in enumerate(channels):
            if query_text in ch['name'].lower():
                results.append((cat, i, ch))

    if not results:
        await update.message.reply_text(
            f"❌ *'{update.message.text}'* bo'yicha hech narsa topilmadi.\n\n"
            "/start - Bosh menyu",
            parse_mode="Markdown"
        )
        context.user_data['searching'] = False
        return

    keyboard = []
    for cat, i, ch in results[:20]:
        keyboard.append([InlineKeyboardButton(
            f"📺 {ch['name']} [{cat}]",
            callback_data=f"ch:{cat}:{i}"
        )])

    keyboard.append([InlineKeyboardButton("🏠 Bosh menyu", callback_data="back")])

    await update.message.reply_text(
        f"🔍 *'{update.message.text}'* uchun {len(results)} ta natija:\n",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    context.user_data['searching'] = False

# ========================
# /help BUYRUG'I
# ========================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Yordam*\n\n"
        "🔹 /start - Bosh menyu\n"
        "🔹 /channels - Barcha kanallar\n"
        "🔹 /help - Yordam\n\n"
        "📺 Kanallarni ko'rish uchun:\n"
        "1. Kategoriya tanlang\n"
        "2. Kanal tanlang\n"
        "3. VLC yoki MX Player da oching",
        parse_mode="Markdown"
    )

# ========================
# ISHGA TUSHIRISH
# ========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(category_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_handler))

    print("Bot ishga tushdi! ✅")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
