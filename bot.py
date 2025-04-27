import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    CallbackQueryHandler, ConversationHandler, ContextTypes
)

# Logging sozlash
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Bosqichlar
ASK_PAGES, ASK_SIZE, ASK_COLOR, ASK_COPIES, ASK_FILE, CONFIRM_ORDER = range(6)

# Start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Assalomu alaykum! 📚 Kitob sahifa sonini kiriting:")
    return ASK_PAGES

# Sahifa sonini olish
async def ask_pages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['pages'] = int(update.message.text)
    keyboard = [
        [InlineKeyboardButton("A4", callback_data='A4'), InlineKeyboardButton("A5", callback_data='A5')]
    ]
    await update.message.reply_text('Kitob o\'lchamini tanlang:', reply_markup=InlineKeyboardMarkup(keyboard))
    return ASK_SIZE

# O'lchamni olish
async def ask_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['size'] = query.data
    keyboard = [
        [InlineKeyboardButton("Oq qora", callback_data='black_white'), InlineKeyboardButton("Rangli", callback_data='color')]
    ]
    await query.edit_message_text('Chop etish turini tanlang:', reply_markup=InlineKeyboardMarkup(keyboard))
    return ASK_COLOR

# Rangni olish
async def ask_color(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['color'] = query.data
    await query.message.reply_text('Nechta nusxa kerak? Sonini yozib yuboring:')
    return ASK_COPIES

# Nusxa sonini olish
async def ask_copies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['copies'] = int(update.message.text)
    await update.message.reply_text('Endi kitobning PDF faylini yuboring 📄:')
    return ASK_FILE

# PDF faylni qabul qilish
async def ask_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document

    if document.mime_type != 'application/pdf':
        await update.message.reply_text('⚠️ Iltimos, faqat PDF formatdagi fayl yuboring.')
        return ASK_FILE

    context.user_data['file_id'] = document.file_id

    pages = context.user_data['pages']
    size = context.user_data['size']
    color = context.user_data['color']
    copies = context.user_data['copies']

    # Narx hisoblash
    if size == 'A5' and color == 'black_white':
        price = pages * 50 + 8000
    elif size == 'A5' and color == 'color':
        price = pages * 60 + 8000
    elif size == 'A4' and color == 'black_white':
        price = pages * 100 + 8000
    elif size == 'A4' and color == 'color':
        price = pages * 120 + 8000
    else:
        price = 0

    total_price = price * copies
    context.user_data['total_price'] = total_price

    msg = (
        f"📄 Sahifalar soni: {pages}\n"
        f"📐 O'lcham: {size}\n"
        f"🎨 Chop turi: {'Rangli' if color == 'color' else 'Oq qora'}\n"
        f"📚 Nusxalar soni: {copies}\n"
        f"💰 Umumiy narx: {total_price:,} so'm\n\n"
        "Buyurtmani tasdiqlaysizmi?"
    )

    keyboard = [
        [InlineKeyboardButton("✅ Ha, tasdiqlayman", callback_data='confirm')],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data='cancel')]
    ]
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

    return CONFIRM_ORDER

# Buyurtma tasdiqlash yoki bekor qilish
async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'confirm':
        file_id = context.user_data['file_id']
        pages = context.user_data['pages']
        size = context.user_data['size']
        color = context.user_data['color']
        copies = context.user_data['copies']
        total_price = context.user_data['total_price']

        text = (
            f"✅ Yangi buyurtma!\n\n"
            f"👤 Foydalanuvchi: @{query.from_user.username or query.from_user.id}\n"
            f"📄 Sahifa soni: {pages}\n"
            f"📐 O'lcham: {size}\n"
            f"🎨 Chop turi: {'Rangli' if color == 'color' else 'Oq qora'}\n"
            f"📚 Nusxa soni: {copies}\n"
            f"💰 Umumiy narx: {total_price:,} so'm"
        )

        # ADMIN CHAT ID NI TO'G'RI QO'Y!!
        admin_chat_id = -1002124583221  # Misol uchun, to'g'ri ID ber

        await context.bot.send_message(chat_id=admin_chat_id, text=text)
        await context.bot.send_document(chat_id=admin_chat_id, document=file_id, caption="📎 Kitob PDF fayli")
        await query.edit_message_text('✅ Buyurtmangiz qabul qilindi!')
    else:
        await query.edit_message_text('❌ Buyurtma bekor qilindi.')

    return ConversationHandler.END

# Bekor qilish
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Buyurtma bekor qilindi.')
    return ConversationHandler.END

# Main ishga tushirish
async def main():
    app = ApplicationBuilder().token("BOT_TOKENINGNI_SHU_YERGA_QO'Y").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASK_PAGES: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_pages)],
            ASK_SIZE: [CallbackQueryHandler(ask_size)],
            ASK_COLOR: [CallbackQueryHandler(ask_color)],
            ASK_COPIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_copies)],
            ASK_FILE: [MessageHandler(filters.Document.PDF, ask_file)],
            CONFIRM_ORDER: [CallbackQueryHandler(confirm_order)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(conv_handler)

    await app.run_polling()

if __name__ == '__main__':
    try:
        import nest_asyncio
        nest_asyncio.apply()
    except:
        pass

    asyncio.run(main())