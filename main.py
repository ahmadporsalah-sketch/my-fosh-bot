import os
import sqlite3
from threading import Thread
from flask import Flask
from telebot import TeleBot

# ----------------- وب‌سرویس برای Render -----------------
app = Flask(__name__)


@app.route("/")
def home():
    return "Bot is active!"


def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


# ----------------- ربات تلگرام -----------------
BOT_TOKEN = "8989339741:AAFy60i7mrSviQrfZGumbXonjUbVAcevZ14"
bot = TeleBot(BOT_TOKEN)


# ----------------- دیتابیس -----------------
def get_db():
    return sqlite3.connect("badwords.db")


def init_db():
    with get_db() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS words (word TEXT UNIQUE)"
        )


init_db()


def get_words():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT word FROM words")
        return [row[0] for row in cursor.fetchall()]


def add_word(word):
    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO words (word) VALUES (?)", (word.lower(),)
            )
        return True
    except:
        return False


def remove_word(word):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM words WHERE word = ?", (word.lower(),))
        return cursor.rowcount > 0


# ----------------- دستورات ربات -----------------
@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    help_text = (
        "سلام! 👋\n"
        "ربات مدیریت گروه ۲۴ ساعته فعال است.\n\n"
        "• برای افزودن کلمه: `افزودن کلمه` (مثال: `افزودن فحش1`)\n"
        "• برای حذف کلمه: `حذف کلمه`\n"
        "• برای مشاهده لیست: `لیست کلمات`"
    )
    bot.reply_to(message, help_text, parse_mode="Markdown")


@bot.message_handler(
    func=lambda m: m.text and m.text.startswith("افزودن ")
)
def handle_add_word(message):
    word = message.text.replace("افزودن ", "").strip()
    if word and add_word(word):
        bot.reply_to(
            message, f"✅ کلمه «{word}» به لیست کلمات غیرمجاز اضافه شد."
        )
    else:
        bot.reply_to(message, "⚠️ این کلمه از قبل وجود دارد یا نامعتبر است.")


@bot.message_handler(func=lambda m: m.text and m.text.startswith("حذف "))
def handle_remove_word(message):
    word = message.text.replace("حذف ", "").strip()
    if word and remove_word(word):
        bot.reply_to(
            message, f"🗑 کلمه «{word}» از لیست کلمات غیرمجاز حذف شد."
        )
    else:
        bot.reply_to(message, "⚠️ این کلمه در لیست یافت نشد.")


@bot.message_handler(
    func=lambda m: m.text and m.text in ["لیست کلمات", "لیست"]
)
def handle_list_words(message):
    words = get_words()
    if words:
        text = "📋 **لیست کلمات غیرمجاز:**\n\n" + "\n".join(
            [f"• {w}" for w in words]
        )
        bot.reply_to(message, text, parse_mode="Markdown")
    else:
        bot.reply_to(message, "📜 لیست کلمات غیرمجاز خالی است.")


@bot.message_handler(
    func=lambda message: message.chat.type in ["group", "supergroup"]
)
def check_and_delete_messages(message):
    if not message.text:
        return
    text = message.text.lower()
    forbidden_words = get_words()
    if any(word in text for word in forbidden_words if word):
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except Exception as e:
            print(f"خطا در حذف پیام: {e}")


# ----------------- اجرای برنامه -----------------
if __name__ == "__main__":
    server_thread = Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()

    bot.infinity_polling(timeout=10, long_polling_timeout=5)
    
