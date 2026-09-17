import sqlite3
import time
from telebot import TeleBot

BOT_TOKEN = "8989339741:AAFy6Oi7mrSviQrfZGumbXonjUbVAcevZ14"
bot = TeleBot(BOT_TOKEN)

# ----------------- تنظیمات دیتابیس -----------------
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


# ----------------- دستور استارت -----------------
@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    help_text = (
        "سلام! 👋\n"
        "من ربات مدیریت گروه و حذف کلمات غیرمجاز هستم.\n\n"
        "📌 **راهنمای استفاده:**\n"
        "• برای افزودن کلمه: عبارت `افزودن کلمه` را بفرستید (مثال: `افزودن فحش1`)\n"
        "• برای حذف کلمه: عبارت `حذف کلمه` را بفرستید (مثال: `حذف فحش1`)\n"
        "• برای مشاهده لیست: عبارت `لیست کلمات` را بفرستید"
    )
    bot.reply_to(message, help_text, parse_mode="Markdown")


# ----------------- دستورات مدیریت کلمات -----------------
@bot.message_handler(
    func=lambda m: m.text and m.text.startswith("افزودن ")
)
def handle_add_word(message):
    word = message.text.replace("افزودن ", "").strip()
    if word:
        if add_word(word):
            bot.reply_to(
                message, f"✅ کلمه «{word}» به لیست کلمات غیرمجاز اضافه شد."
            )
        else:
            bot.reply_to(message, "⚠️ این کلمه از قبل در لیست وجود دارد.")


@bot.message_handler(func=lambda m: m.text and m.text.startswith("حذف "))
def handle_remove_word(message):
    word = message.text.replace("حذف ", "").strip()
    if word:
        if remove_word(word):
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


# ----------------- بررسی پیام‌های گروه -----------------
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
            print(f"پیام غیرمجاز حذف شد: {message.text}")
        except Exception as e:
            print(f"خطا در حذف پیام: {e}")


print("ربات با موفقیت روشن شد...")
bot.infinity_polling()
