import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url=os.environ.get("MINI_APP_URL","http://127.0.0.1:8000/")
    await update.message.reply_text("Ariza.uz orqali murojaat yuboring:",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Ariza yuborish",web_app=WebAppInfo(url=url))]]))

if __name__=="__main__":
    token=os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token: raise RuntimeError("TELEGRAM_BOT_TOKEN belgilanmagan.")
    app=Application.builder().token(token).build();app.add_handler(CommandHandler("start",start));app.run_polling()
