import os
import sqlite3
import threading
from flask import Flask
from telebot import TeleBot

# تنظیم وب‌سرویس کوچک برای رایگان ماندن در Render
app = Flask(__name__)


@app.route("/")
def home():
    return "Bot is alive!"


def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


# توکن ربات
BOT_TOKEN = "8989339741:AAFy6Oi7mrSviQrfZGumbXonjUbVAcevZ14"
bot = TeleBot(BOT_TOKEN)

# دیتابیس
conn = sqlite3.connect("badwords.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute(
    "CREATE TABLE IF NOT EXISTS words (word TEXT UNIQUE)"
)
conn.commit()


def get_words():
    cursor.execute("SELECT word FROM words")
    return [row[0] for row in cursor.fetchall()]


def add_word(word):
    try:
        cursor.execute(
            "INSERT INTO words (word) VALUES (?)", (word.lower(),)
        )
        conn.commit()
        return True
    except:
        return False


def remove_word(word):
    cursor.execute("DELETE FROM words WHERE word = ?", (word.lower(),))
    conn.commit()
    return cursor.rowcount > 0


# دستورات
@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    help_text = (
        "سلام! 👋\n"
        "ربات مدیریت گروه فعال است.\n\n"
        "• افزودن کلمه: `افزودن کلمه` (مثال: `افزودن فحش1`)\n"
        "• حذف کلمه: `حذف کلمه`\n"
        "• مشاهده لیست: `لیست کلمات`"
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
        bot.reply_to(message, "⚠️ کلمه تکراری است یا نامعتبر.")


@bot.message_handler(func=lambda m: m.text and m.text.startswith("حذف "))
def handle_remove_word(message):
    word = message.text.replace("حذف ", "").strip()
    if word and remove_word(word):
        bot.reply_to(
            message, f"🗑 کلمه «{word}» از لیست کلمات غیرمجاز حذف شد."
        )
    else:
        bot.reply_to(message, "⚠️ کلمه یافت نشد.")


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
        bot.reply_to(message, "📜 لیست خالی است.")


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
            print(f"خطا در حذف: {e}")


# اجرای هم‌زمان وب‌سرویس و ربات
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.infinity_polling()
        
