import asyncio

try:
    asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
import asyncio
import logging
import random
from pyrogram import Client, filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

logging.basicConfig(level=logging.INFO)

# ------------------------------------
# تنظیمات اولیه
# ------------------------------------
API_ID = 20473518
API_HASH = "d2832a6a81a16a8a4e96807c50b380c8"
BOT_TOKEN = "8301053372:AAHtczCUDA0iDJ8iEZd3ioW9N6ISp61uUow"
ADMIN_ID = 5579683966

# ساخت کلاینت‌ها بدون جاگذاری مستقیم توکن
userbot = Client("my_userbot", api_id=API_ID, api_hash=API_HASH)
bot = Client("management_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

config = {
    "groups": [],
    "text": "بنر پیش‌فرض",
    "media_type": None,
    "media_file_id": None,
    "media_caption": "",
    "delay": 10,  # زمان پایه (ثانیه)
    "running": False,
    "state": None,
}


def get_main_markup():
    status = "🟢 روشن" if config["running"] else "🔴 خاموش"
    keyboard = [
        [
            InlineKeyboardButton("➕ افزودن گروه", callback_data="add_group"),
            InlineKeyboardButton(
                "🗑️ پاک‌سازی گروه‌ها", callback_data="clear_groups"
            ),
        ],
        [
            InlineKeyboardButton("📝 بنر متنی", callback_data="set_text"),
            InlineKeyboardButton("🖼️ بنر رسانه‌ای", callback_data="set_media"),
        ],
        [
            InlineKeyboardButton(
                "⏱️ تنظیم زمان پایه", callback_data="set_delay"
            )
        ],
        [InlineKeyboardButton(f"حالت ارسال: {status}", callback_data="toggle")],
        [
            InlineKeyboardButton(
                "📊 وضعیت و لیست گروه‌ها", callback_data="status"
            )
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


# ------------------------------------
# هندلرهای ربات مدیریتی
# ------------------------------------
@bot.on_message(filters.user(ADMIN_ID) & filters.command("start"))
async def start_cmd(client: Client, message: Message):
    config["state"] = None
    await message.reply_text(
        "👋 پنل مدیریت ارسال چندگانه بنر:", reply_markup=get_main_markup()
    )


@bot.on_callback_query(filters.user(ADMIN_ID))
async def callback_handler(client: Client, query: CallbackQuery):
    data = query.data
    await query.answer()

    if data == "add_group":
        config["state"] = "await_group"
        await query.edit_message_text(
            "لطفاً آیدی یا لینک گروه جدید را ارسال کنید (مثلاً group@):"
        )

    elif data == "clear_groups":
        config["groups"].clear()
        await query.edit_message_text(
            "🗑️ تمام گروه‌ها از لیست حذف شدند.", reply_markup=get_main_markup()
        )

    elif data == "set_delay":
        config["state"] = "await_delay"
        await query.edit_message_text(
            "لطفاً حداقل زمان پایه را به ثانیه وارد کنید (مثلاً 10):\n"
            "نکته: سیستم تا ۱۰ ثانیه اضافه تر به صورت رندوم صبر خواهد کرد."
        )

    elif data == "set_text":
        config["state"] = "await_text"
        await query.edit_message_text("لطفاً متن جدید بنر را بفرستید:")

    elif data == "set_media":
        config["state"] = "await_media"
        await query.edit_message_text(
            "لطفاً عکس یا ویدیو بنر را همراه با زیرنویس ارسال کنید:"
        )

    elif data == "toggle":
        if not config["groups"]:
            await query.edit_message_text(
                "❌ حداقل باید یک گروه اضافه کرده باشید!",
                reply_markup=get_main_markup(),
            )
            return

        config["running"] = not config["running"]
        if config["running"]:
            asyncio.create_task(send_worker())
            await query.edit_message_text(
                "▶️ ارسال مداوم با زمان‌بندی تصادفی شروع شد!",
                reply_markup=get_main_markup(),
            )
        else:
            await query.edit_message_text(
                "⏹️ ارسال بنر متوقف شد.", reply_markup=get_main_markup()
            )

    elif data == "status":
        groups_list = (
            "\n".join([f"• `{g}`" for g in config["groups"]])
            if config["groups"]
            else "هیچ گروهی ثبت نشده"
        )
        msg = (
            f"📌 **وضعیت سیستم:**\n\n"
            f"👥 **تعداد گروه‌ها:** {len(config['groups'])}\n"
            f"📜 **لیست گروه‌ها:**\n{groups_list}\n\n"
            f"⏱️ **زمان پایه:** {config['delay']} ثانیه (با بازه تصادفی)\n"
            f"⚙️ **حالت:** {'در حال ارسال...' if config['running'] else 'متوقف'}"
        )
        await query.edit_message_text(msg, reply_markup=get_main_markup())


@bot.on_message(filters.user(ADMIN_ID) & ~filters.command("start"))
async def input_handler(client: Client, message: Message):
    state = config.get("state")

    if state == "await_group":
        group_input = message.text.strip()
        if group_input not in config["groups"]:
            config["groups"].append(group_input)
            await message.reply_text(
                f"✅ گروه `{group_input}` اضافه شد.",
                reply_markup=get_main_markup(),
            )
        else:
            await message.reply_text(
                "⚠️ این گروه از قبل وجود دارد.", reply_markup=get_main_markup()
            )
        config["state"] = None

    elif state == "await_delay":
        if message.text.isdigit():
            config["delay"] = int(message.text)
            config["state"] = None
            await message.reply_text(
                f"✅ زمان پایه به {message.text} ثانیه تغییر یافت.",
                reply_markup=get_main_markup(),
            )
        else:
            await message.reply_text("❌ لطفاً یک عدد معتبر وارد کنید.")

    elif state == "await_text":
        config["text"] = message.text
        config["media_file_id"] = None
        config["state"] = None
        await message.reply_text(
            "✅ بنر متنی ذخیره شد.", reply_markup=get_main_markup()
        )

    elif state == "await_media":
        if message.photo:
            config["media_type"] = "photo"
            config["media_file_id"] = message.photo.file_id
        elif message.video:
            config["media_type"] = "video"
            config["media_file_id"] = message.video.file_id
        elif message.document:
            config["media_type"] = "document"
            config["media_file_id"] = message.document.file_id

        config["media_caption"] = message.caption or ""
        config["state"] = None
        await message.reply_text(
            "✅ بنر رسانه‌ای ذخیره شد.", reply_markup=get_main_markup()
        )


# ------------------------------------
# موتور ارسال یوزربات با زمان‌بندی رندوم
# ------------------------------------
async def send_worker():
    while config["running"]:
        for group in list(config["groups"]):
            if not config["running"]:
                break

            try:
                try:
                    await userbot.join_chat(group)
                except Exception:
                    pass

                if config["media_file_id"]:
                    if config["media_type"] == "photo":
                        await userbot.send_photo(
                            chat_id=group,
                            photo=config["media_file_id"],
                            caption=config["media_caption"],
                        )
                    elif config["media_type"] == "video":
                        await userbot.send_video(
                            chat_id=group,
                            video=config["media_file_id"],
                            caption=config["media_caption"],
                        )
                    elif config["media_type"] == "document":
                        await userbot.send_document(
                            chat_id=group,
                            document=config["media_file_id"],
                            caption=config["media_caption"],
                        )
                else:
                    await userbot.send_message(
                        chat_id=group, text=config["text"]
                    )

            except Exception as e:
                logging.error(f"خطا در ارسال به {group}: {e}")

            # مکث رندوم بین ارسال به گروه‌ها (۲ تا ۵ ثانیه)
            await asyncio.sleep(random.randint(2, 5))

        # زمان انتظار رندوم (بین زمان پایه تا ۱۰ ثانیه بیشتر)
        base_delay = config["delay"]
        random_delay = random.randint(base_delay, base_delay + 10)
        logging.info(f"زمان انتظار تا دوره بعدی: {random_delay} ثانیه")

        await asyncio.sleep(random_delay)


# ------------------------------------
# اجرای برنامه
# ------------------------------------
async def main():
    await userbot.start()
    await bot.start()
    print("ربات چندگانه آنلاین شد.")
    await asyncio.Event().wait()
    
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Userbot is running!")

def run_web_server():
    server = HTTPServer(('0.0.0.0', 10000), SimpleHTTPRequestHandler)
    server.serve_forever()

# اجرا در وب‌سرور در پس‌زمینه
threading.Thread(target=run_web_server, daemon=True).start()
        

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
