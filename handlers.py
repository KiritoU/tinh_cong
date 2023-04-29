import asyncio
import json
import os
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from time import sleep

from dotenv import dotenv_values, load_dotenv
from telegram import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MessageEntity,
    Update,
)
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

DB_FILE = "db.json"


def add_this_year() -> str:
    now = datetime.now()
    return "/" + str(now.year)


def get_db() -> dict:
    try:
        return json.loads(open(DB_FILE, "r").read())
    except:
        return {}


def write_db(db_dict: dict) -> None:
    with open(DB_FILE, "w") as f:
        f.write(json.dumps(db_dict, indent=4, ensure_ascii=False))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Hello {update.message.from_user.first_name}",
        parse_mode="HTML",
    )


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(text="Pong!", parse_mode="HTML")


async def getchat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id

    await update.message.reply_text(text="Chat ID: %s" % chat_id)


async def batdau(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text(
            text="""Nhập ngày bắt đầu tính công
Ví dụ: /batdau 15/4""",
            parse_mode="HTML",
        )
        return

    try:
        input_date_str = context.args[0] + add_this_year()
        input_date = datetime.strptime(input_date_str, "%d/%m/%Y")

        db_dict = get_db()
        db_dict["batdau"] = input_date_str
        db_dict["nghi"] = {}

        write_db(db_dict)
        await update.message.reply_text(
            text=f"Đã cài đặt ngày bắt đầu là: {input_date_str}"
        )
    except:
        await update.message.reply_text(
            text="Có lỗi xảy ra, liên hệ với Chồng boé nhé bà chủ"
        )


async def nghi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text(
            text="""Nhập thêm ngày nghỉ
Ví dụ:  /nghi 25/4
        /nghi 30/4 le""",
            parse_mode="HTML",
        )
        return

    try:
        input_date_str = context.args[0] + add_this_year()
        is_holiday = True if len(context.args) >= 2 else False
        input_date = datetime.strptime(input_date_str, "%d/%m/%Y")
        db_dict = get_db()

        db_dict_nghi = db_dict.get("nghi", {})
        db_dict_nghi[input_date_str] = is_holiday
        db_dict["nghi"] = db_dict_nghi

        write_db(db_dict)

        await update.message.reply_text(
            text=f"Đã thêm ngày nghỉ {'LỄ' if is_holiday else ''} là: {input_date_str}"
        )
    except:
        await update.message.reply_text(
            text="Có lỗi xảy ra, liên hệ với Chồng boé nhé vợ iu"
        )


async def xoa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text(
            text="""Nhập ngày để xoá khỏi ngày nghỉ
Ví dụ: /xoa 25/4""",
            parse_mode="HTML",
        )
        return

    try:
        input_date_str = context.args[0] + add_this_year()
        input_date = datetime.strptime(input_date_str, "%d/%m/%Y")
        db_dict = get_db()

        db_dict_nghi = db_dict.get("nghi", {})
        db_dict_nghi.pop(input_date_str, None)
        db_dict["nghi"] = db_dict_nghi

        write_db(db_dict)

        await update.message.reply_text(text=f"Đã xoá ngày nghỉ: {input_date_str}")
    except:
        await update.message.reply_text(
            text="Có lỗi xảy ra, liên hệ với Chồng boé nhé vợ iu"
        )


async def tinh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        db_dict = get_db()
        sorted_days_off_dict = sorted(
            db_dict.get("nghi", {}).items(),
            key=lambda x: (x[1], datetime.strptime(x[0], "%d/%m/%Y")),
        )
        start_day_str = db_dict.get("batdau", "")
        start_day = datetime.strptime(start_day_str, "%d/%m/%Y")
        msg = f"Ngày bắt đầu tính công: {start_day_str}"
        if sorted_days_off_dict:
            msg += f"\nDanh sách ngày nghỉ:"
        for day in sorted_days_off_dict:
            day_off, is_holiday = day
            msg += f"\nNghỉ {'LỄ ' if is_holiday else ''}ngày: {day_off}"

        days_off = sum(1 for day in sorted_days_off_dict if not day[-1])
        _29days = start_day + timedelta(days=29 + days_off)

        msg += f"\nNgày đủ 29 công: {_29days.strftime('%d/%m/%Y')}"
        await update.message.reply_text(text=msg)

    except Exception as e:
        print(e)
        await update.message.reply_text(
            text="Có lỗi xảy ra, liên hệ với Chồng boé nhé vợ iu"
        )


async def debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db_dict = get_db()
    await update.message.reply_text(text=json.dumps(db_dict))


strategyPatterns = {
    "ping": ping,
    "start": start,
    "getchat": getchat,
    "batdau": batdau,
    "nghi": nghi,
    "xoa": xoa,
    "tinh": tinh,
    "debug": debug,
}

handlers = []

for key, value in strategyPatterns.items():
    handlers.append(CommandHandler(key, value))
