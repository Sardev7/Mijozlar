cat > /mnt/user-data/outputs/bot.py << 'EOF'
import os
import json
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

TOKEN = os.environ.get("BOT_TOKEN")
DATA_FILE = "mijozlar.json"
ISM, TELEFON, VAQT = range(3)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main_keyboard():
    return ReplyKeyboardMarkup(
        [["➕ Mijoz qo'shish", "📋 Ro'yxat"]],
        resize_keyboard=True
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salom! Mijozlar ro'yxati boti.",
        reply_markup=main_keyboard()
    )

async def show_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not data:
        await update.message.reply_text("📋 Ro'yxat bo'sh.", reply_markup=main_keyboard())
        return
    now = datetime.now()
    msg = f"📋 Mijozlar ({len(data)} ta):\n\n"
    for i, m in enumerate(data, 1):
        vaqt = datetime.strptime(m["vaqt"], "%d.%m.%Y %H:%M")
        belgi = "✅" if vaqt < now else "⏳"
        msg += f"{belgi} {i}. {m['ism']}\n📞 {m['telefon']}\n🕐 {m['vaqt']}\n\n"
    await update.message.reply_text(msg, reply_markup=main_keyboard())

async def start_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👤 Mijoz ismini kiriting:")
    return ISM

async def get_ism(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ism"] = update.message.text
    await update.message.reply_text("📞 Telefon raqamini kiriting:")
    return TELEFON

async def get_telefon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["telefon"] = update.message.text
    await update.message.reply_text("🕐 Kelish vaqtini kiriting:\nMasalan: 15.06.2025 14:30")
    return VAQT

async def get_vaqt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        vaqt = datetime.strptime(update.message.text, "%d.%m.%Y %H:%M")
    except ValueError:
        await update.message.reply_text("❌ Format noto'g'ri. Masalan: 15.06.2025 14:30")
        return VAQT

    mijoz = {
        "id": int(datetime.now().timestamp()),
        "ism": context.user_data["ism"],
        "telefon": context.user_data["telefon"],
        "vaqt": vaqt.strftime("%d.%m.%Y %H:%M"),
        "qoshgan": update.effective_user.first_name or "Noma'lum"
    }
    data = load_data()
    data.append(mijoz)
    data.sort(key=lambda x: datetime.strptime(x["vaqt"], "%d.%m.%Y %H:%M"))
    save_data(data)

    await update.message.reply_text(
        f"✅ Qo'shildi!\n👤 {mijoz['ism']}\n📞 {mijoz['telefon']}\n🕐 {mijoz['vaqt']}",
        reply_markup=main_keyboard()
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Bekor qilindi.", reply_markup=main_keyboard())
    return ConversationHandler.END

async def ochir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not data:
        await update.message.reply_text("Ro'yxat bo'sh.")
        return
    if not context.args:
        msg = "O'chirish: /ochir <raqam>\n\n"
        for i, m in enumerate(data, 1):
            msg += f"{i}. {m['ism']} — {m['vaqt']}\n"
        await update.message.reply_text(msg)
        return
    try:
        n = int(context.args[0]) - 1
        if 0 <= n < len(data):
            o = data.pop(n)
            save_data(data)
            await update.message.reply_text(f"✅ O'chirildi: {o['ism']} — {o['vaqt']}")
        else:
            await update.message.reply_text("❌ Bunday raqam yo'q.")
    except ValueError:
        await update.message.reply_text("❌ Masalan: /ochir 2")

def main():
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ Mijoz qo'shish$"), start_add)],
        states={
            ISM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ism)],
            TELEFON: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_telefon)],
            VAQT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_vaqt)],
        },
        fallbacks=[CommandHandler("bekor", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("royxat", show_list))
    app.add_handler(CommandHandler("ochir", ochir))
    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.Regex("^📋 Ro'yxat$"), show_list))

    print("Bot ishga tushdi!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
EOF
echo "Done"
