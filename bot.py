import os
import json
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

TOKEN = os.environ.get("BOT_TOKEN")

DATA_FILE = "mijozlar.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Conversation states
ISM, TELEFON, VAQT = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["➕ Mijoz qo'shish", "📋 Ro'yxat ko'rish"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "👋 Salom! Mijozlar ro'yxati boti.\n\nNima qilmoqchisiz?",
        reply_markup=reply_markup
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "➕ Mijoz qo'shish":
        await update.message.reply_text("👤 Mijozning ismini kiriting:")
        return ISM
    elif text == "📋 Ro'yxat ko'rish":
        await show_list(update, context)

async def get_ism(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ism"] = update.message.text
    await update.message.reply_text("📞 Telefon raqamini kiriting (masalan: +998901234567):")
    return TELEFON

async def get_telefon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["telefon"] = update.message.text
    await update.message.reply_text(
        "🕐 Kelish vaqtini kiriting:\nFormat: KK.OO.YYYY SS:MM\nMasalan: 15.06.2025 14:30"
    )
    return VAQT

async def get_vaqt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    vaqt_str = update.message.text
    try:
        vaqt = datetime.strptime(vaqt_str, "%d.%m.%Y %H:%M")
    except ValueError:
        await update.message.reply_text("❌ Vaqt formati noto'g'ri. Qaytadan kiriting:\nMasalan: 15.06.2025 14:30")
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

    keyboard = [["➕ Mijoz qo'shish", "📋 Ro'yxat ko'rish"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"✅ Mijoz qo'shildi!\n\n"
        f"👤 Ism: {mijoz['ism']}\n"
        f"📞 Telefon: {mijoz['telefon']}\n"
        f"🕐 Vaqt: {mijoz['vaqt']}",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["➕ Mijoz qo'shish", "📋 Ro'yxat ko'rish"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("❌ Bekor qilindi.", reply_markup=reply_markup)
    return ConversationHandler.END

async def show_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not data:
        await update.message.reply_text("📋 Ro'yxat bo'sh.")
        return

    now = datetime.now()
    msg = f"📋 *Mijozlar ro'yxati* ({len(data)} ta)\n\n"
    for i, m in enumerate(data, 1):
        vaqt = datetime.strptime(m["vaqt"], "%d.%m.%Y %H:%M")
        utdi = "✓" if vaqt < now else "⏳"
        msg += f"{utdi} *{i}. {m['ism']}*\n"
        msg += f"   📞 {m['telefon']}\n"
        msg += f"   🕐 {m['vaqt']}\n"
        msg += f"   👤 Qo'shgan: {m['qoshgan']}\n\n"

    await update.message.reply_text(msg, parse_mode="Markdown")

async def delete_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not data:
        await update.message.reply_text("Ro'yxat bo'sh.")
        return
    if not context.args:
        msg = "O'chirish uchun: /ochir <raqam>\n\nRo'yxat:\n"
        for i, m in enumerate(data, 1):
            msg += f"{i}. {m['ism']} — {m['vaqt']}\n"
        await update.message.reply_text(msg)
        return
    try:
        n = int(context.args[0]) - 1
        if 0 <= n < len(data):
            ochirilgan = data.pop(n)
            save_data(data)
            await update.message.reply_text(f"✅ O'chirildi: {ochirilgan['ism']} — {ochirilgan['vaqt']}")
        else:
            await update.message.reply_text("❌ Bunday raqam yo'q.")
    except ValueError:
        await update.message.reply_text("❌ Raqam kiriting. Masalan: /ochir 2")

def main():
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ Mijoz qo'shish$"), menu)],
        states={
            ISM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ism)],
            TELEFON: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_telefon)],
            VAQT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_vaqt)],
        },
        fallbacks=[CommandHandler("bekor", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("royxat", show_list))
    app.add_handler(CommandHandler("ochir", delete_cmd))
    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.Regex("^📋 Ro'yxat ko'rish$"), show_list))

    print("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
