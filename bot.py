import os
import logging
from datetime import time as dt_time

import pytz
from telegram import BotCommand, Update
from telegram.ext import Application, CommandHandler, ContextTypes

import database as db
from hiker_helper import get_my_profile, get_my_top_clips, collect_trend_digest
from digest_helper import (
    build_account_update_text,
    generate_trend_breakdown_and_scenarios,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
MOSCOW = pytz.timezone("Europe/Moscow")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    db.add_subscriber(chat_id)
    await update.message.reply_text(
        "👋 Привет! Это дайджест-бот для твоего Instagram-блога @future.dentt.\n\n"
        "Два раза в неделю (Пн и Чт, 10:00 МСК) буду присылать:\n"
        "📊 апдейт по твоему аккаунту\n"
        "🔥 разбор свежих вирусных Reels (реальные данные HikerAPI)\n"
        "🎬 готовые сценарии под тренды\n\n"
        "Открой меню команд (кнопка ☰ рядом со строкой ввода), чтобы посмотреть, что я умею.",
        parse_mode="HTML",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "<b>Команды</b>\n"
        "/start — подписаться на дайджест\n"
        "/digest_now — прислать дайджест прямо сейчас\n"
        "/help — это сообщение\n\n"
        "Автоматическая рассылка приходит по понедельникам и четвергам в 10:00 (МСК). "
        "Все цифры — реальные данные из HikerAPI, тексты идей пишет Groq на их основе.",
        parse_mode="HTML",
    )


async def send_digest(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    profile = get_my_profile()
    top_clips = get_my_top_clips(profile["pk"])
    prev = db.get_account_snapshot(profile["username"])

    account_text = build_account_update_text(profile, top_clips, prev)
    await context.bot.send_message(chat_id=chat_id, text=account_text, parse_mode="HTML")

    trend_items = collect_trend_digest(num_queries=5, per_query=3)
    if trend_items:
        breakdown_text, scenarios_text = generate_trend_breakdown_and_scenarios(trend_items)
        await context.bot.send_message(chat_id=chat_id, text=breakdown_text, parse_mode="HTML")
        if scenarios_text:
            await context.bot.send_message(chat_id=chat_id, text=scenarios_text, parse_mode="HTML")
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Сегодня не нашлось новых вирусных Reels по проверяемым темам — попробуем в следующий раз.",
        )

    best_play = top_clips[0]["play_count"] if top_clips else 0
    db.save_account_snapshot(profile["username"], profile["follower_count"], best_play)


async def digest_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text("Собираю дайджест по реальным данным, подожди немного...")
    try:
        await send_digest(context, chat_id)
    except Exception as e:
        logger.exception("digest_now failed")
        await update.message.reply_text(f"Не получилось собрать дайджест: {e}")


async def scheduled_digest(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in db.get_subscribers():
        try:
            await send_digest(context, chat_id)
        except Exception:
            logger.exception(f"scheduled digest failed for chat_id={chat_id}")


async def post_init(app: Application):
    await app.bot.set_my_commands([
        BotCommand("start", "Подписаться на дайджест"),
        BotCommand("digest_now", "Прислать дайджест сейчас"),
        BotCommand("help", "Что умеет этот бот"),
    ])


def main():
    db.init_db()
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("digest_now", digest_now))
    app.add_handler(CommandHandler("help", help_command))

    # В python-telegram-bot 20.x дни недели: 0=воскресенье, 1=понедельник, ..., 6=суббота
    jq = app.job_queue
    jq.run_daily(scheduled_digest, time=dt_time(10, 0, tzinfo=MOSCOW), days=(1,), name="digest_monday")
    jq.run_daily(scheduled_digest, time=dt_time(10, 0, tzinfo=MOSCOW), days=(4,), name="digest_thursday")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
