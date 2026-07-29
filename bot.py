import os
from pathlib import Path
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

def load_env_file():
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url=os.environ.get("MINI_APP_URL","http://127.0.0.1:8000/")
    await update.message.reply_text("Ariza.uz orqali murojaat yuboring:",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Ariza yuborish",web_app=WebAppInfo(url=url))]]))

if __name__=="__main__":
    load_env_file()
    token=os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token: raise RuntimeError("TELEGRAM_BOT_TOKEN belgilanmagan.")
    app=Application.builder().token(token).build();app.add_handler(CommandHandler("start",start));app.run_polling()
