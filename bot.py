import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler, ContextTypes
)

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Bosqichlar
ASK_PAGES, ASK_SIZE, ASK_COLOR, ASK_COPIES, ASK_FILE, CONFIRM_ORDER = range(6)

# User ma'lumotlarini vaqtincha saqlash
user_data = {}

# Start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Assalomu alaykum! Kitob sahifa sonini kiriting:")
    return ASK_PAGES

# Sahifa soni so'rash
async def ask_pages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id] = {'pages': int(update.message.text)}
    keyboard = [
        [InlineKeyboardButton("A4", callback_data='A4'), InlineKeyboardButton("A5", callback_data='A5')]
    ]
    await update.message.reply_text('Kitob o\'lchamini tanlang:', reply_markup=InlineKeyboardMarkup(keyboard))
    return ASK_SIZE

# O'lcham tanlash
async def ask_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_data[query.from_user.id]['size'] = query.data
    keyboard = [
        [InlineKeyboardButton("Oq qora", callback_data='black_white'), InlineKeyboardButton("Rangli", callback_data='color')]
    ]
    await query.edit_message_text('Chop etish turini tanlang:', reply_markup=InlineKeyboardMarkup(keyboard))
    return ASK_COLOR

# Rang tanlash
async def ask_color(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_data[query.from_user.id]['color'] = query.data
    await query.edit_message_text('Nechta nusxa kerak? Sonini yozib yuboring:')
    return ASK_COPIES

# Nusxa sonini so'rash
async def ask_copies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]['copies'] = int(update.message.text)
    await update.message.reply_text('Kitobning PDF faylini yuboring:')
    return ASK_FILE

# Faylni qabul qilish va narx hisoblash
async def ask_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    user_data[update.effective_user.id]['file'] = document

    info = user_data[update.effective_user.id]
    pages = info['pages']
    size = info['size']
    color = info['color']
    copies = info['copies']

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
    user_data[update.effective_user.id]['total_price'] = total_price

    msg = (
        f"📄 Sahifalar soni: {pages}\n"
        f"📐 O'lcham: {size}\n"
        f"🎨 Chop turi: {'Rangli' if color == 'color' else 'Oq qora'}\n"
        f"📚 Nusxalar soni: {copies}\n"
        f"💰 Umumiy narx: {total_price} so'm\n\n"
        "Buyurtma berishni xohlaysizmi?"
    )

    keyboard = [
        [InlineKeyboardButton("✅ Buyurtma berish", callback_data='confirm')],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data='cancel')]
    ]
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

    return CONFIRM_ORDER

# Buyurtmani tasdiqlash yoki bekor qilish
async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'confirm':
        info = user_data[query.from_user.id]
        file = info['file']

        text = (
            f"✅ Yangi buyurtma!\n\n"
            f"👤 Foydalanuvchi: @{query.from_user.username}\n"
            f"📄 Sahifa: {info['pages']}\n"
            f"📐 O'lcham: {info['size']}\n"
            f"🎨 Chop turi: {'Rangli' if info['color'] == 'color' else 'Oq qora'}\n"
            f"📚 Nusxa soni: {info['copies']}\n"
            f"💵 Umumiy narx: {info['total_price']} so'm"
        )

        await context.bot.send_message(chat_id='@xurshid3221', text=text)
        await context.bot.send_document(chat_id='@xurshid3221', document=file.file_id, caption="📎 Kitob PDF fayli")
        await query.edit_message_text('Buyurtmangiz qabul qilindi! ✅')

    else:
        await query.edit_message_text('Buyurtma bekor qilindi.')

    return ConversationHandler.END

# Cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Buyurtma bekor qilindi.')
    return ConversationHandler.END

# Main
async def main():
    app = Application.builder().token("7591946515:AAFFMEgpPLkwRxADRCTlztIh0GxDdc1qLC8").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASK_PAGES: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_pages)],
            ASK_SIZE: [CallbackQueryHandler(ask_size)],
            ASK_COLOR: [CallbackQueryHandler(ask_color)],
            ASK_COPIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_copies)],
            ASK_FILE: [MessageHandler(filters.Document.PDF, ask_file)],
            CONFIRM_ORDER: [CallbackQueryHandler(confirm_order)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(conv_handler)
    await app.run_polling()

if __name__ == '__main__':
    import nest_asyncio
    nest_asyncio.apply()

    try:
        asyncio.get_running_loop().run_until_complete(main())
    except RuntimeError:
        asyncio.run(main())