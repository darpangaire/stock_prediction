import os
import logging
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from api.models import TelegramUser, Prediction
from api.utils import run_prediction
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

User = get_user_model()

# Logging config
logger = logging.getLogger("telegrambot")
logging.basicConfig(level=logging.INFO)

# Rate limit store (in-memory)
user_rate_limits = {}

PREDICTION_LIMIT_PER_MIN = 10


def is_rate_limited(user_id):
    now = datetime.utcnow()
    if user_id not in user_rate_limits:
        user_rate_limits[user_id] = []
    user_rate_limits[user_id] = [t for t in user_rate_limits[user_id] if now - t < timedelta(minutes=1)]
    if len(user_rate_limits[user_id]) >= PREDICTION_LIMIT_PER_MIN:
        return True
    user_rate_limits[user_id].append(now)
    return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_user = update.effective_user
    chat_id = update.effective_chat.id

    # Create or get Django user (wrapped in sync_to_async)
    django_user, created = await sync_to_async(User.objects.get_or_create)(
        username=f"tg_{telegram_user.id}",
        defaults={
            "first_name": telegram_user.first_name or "",
            "last_name": telegram_user.last_name or ""
        }
    )

    # Create or get TelegramUser (also wrapped)  # adjust import if needed
    await sync_to_async(TelegramUser.objects.get_or_create)(
        user=django_user,
        defaults={"chat_id": chat_id}
    )

    await update.message.reply_text(
        " Welcome! to our stock prediction bot\n"
        "You are able to use /predict tickername and /latest."
    )



async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    try:
        tg_user = await sync_to_async(TelegramUser.objects.get)(chat_id=chat_id)
        user = await sync_to_async(lambda: tg_user.user)()
        user_id = user.id
    except TelegramUser.DoesNotExist:
        await update.message.reply_text("❌ You need to link your account first on the web. Use /start for info.")
        return

    if is_rate_limited(user_id):
        await update.message.reply_text("⚠️ Rate limit exceeded (10 predictions per minute). Please wait.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage: /predict <TICKER>")
        return

    ticker = context.args[0].upper()
    await update.message.reply_text(f"🔎 Running prediction for {ticker}...")

    try:
        predicted_prices, actual_prices, metrics, plot_history_path, plot_pred_path = run_prediction(ticker, n_days=1)

        next_day_price = predicted_prices[0] if predicted_prices else None
        mse = metrics.get("mse", None)
        rmse = metrics.get("rmse", None)
        r2 = metrics.get("r2", None)

        if next_day_price is not None:
            price_str = f"{next_day_price:.2f}"
        else:
            price_str = "N/A"

        msg = (
            f"📈 Prediction for {ticker}\n\n"
            f"Next-day price: {price_str}\n"
            f"Actual Prices: {actual_prices}\n"
            f"MSE: {mse:.4f}\n"
            f"RMSE: {rmse:.4f}\n"
            f"R²: {r2:.4f}"
        )

        await update.message.reply_text(msg)

        # Save prediction to DB
        await sync_to_async(Prediction.objects.create)(
            user=user,
            ticker=ticker,
            next_day_price=next_day_price if next_day_price is not None else 0.0,
            metrics=metrics,
            plot_history_path=plot_history_path,
            plot_pred_path=plot_pred_path,
            telegramuser=tg_user
        )

        # Send plot images
        with open(plot_history_path, "rb") as hist_img:
            await update.message.reply_photo(hist_img)
        with open(plot_pred_path, "rb") as pred_img:
            await update.message.reply_photo(pred_img)

        logger.info(f"✅ Prediction sent to user_id={user_id}, ticker={ticker}")

    except Exception as e:
        logger.exception(f"❌ Prediction error for user_id={user_id}, ticker={ticker}: {str(e)}")
        try:
            await update.message.reply_text(f"⚠️ Error during prediction: {str(e)}")
        except Exception as e2:
            logger.exception(f"⚠️ Also failed to send error message: {str(e2)}")


async def latest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    try:
        tg_user = await sync_to_async(TelegramUser.objects.select_related("user").get)(chat_id=chat_id)
        user = tg_user.user
    except TelegramUser.DoesNotExist:
        await update.message.reply_text("❌ You need to link your account first on the web. Use /start for info.")
        return

    # Get latest prediction for this user
    latest_pred = await sync_to_async(
        lambda: Prediction.objects.filter(user=user).order_by("-created_at").first()
    )()

    if not latest_pred:
        await update.message.reply_text("⚠️ No predictions found. Use /predict <TICKER> to get started.")
        return

    # Use the next_day_price field directly
    price = latest_pred.next_day_price if latest_pred.next_day_price is not None else "N/A"

    msg = (
        f"📊 Latest prediction for {latest_pred.ticker}\n\n"
        f"Next-day price: {price:.2f}\n"
        f"Created at: {latest_pred.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    await update.message.reply_text(msg)

    # Send plots if available
    try:
        if latest_pred.plot_history_path and latest_pred.plot_pred_path:
            with open(latest_pred.plot_history_path, "rb") as hist_img:
                await update.message.reply_photo(hist_img)
            with open(latest_pred.plot_pred_path, "rb") as pred_img:
                await update.message.reply_photo(pred_img)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Could not send plot images: {str(e)}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Available commands:\n"
        "/start — Link your Telegram account\n"
        "/predict <TICKER> — Predict next-day price\n"
        "/latest — Show your latest prediction\n"
        "/help — Show this help message"
    )


class Command(BaseCommand):
    help = "Run Telegram bot with long polling"

    def handle(self, *args, **options):
        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            self.stdout.write(self.style.ERROR("BOT_TOKEN not set in environment"))
            return

        app = ApplicationBuilder().token(bot_token).build()

        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("predict", predict))
        app.add_handler(CommandHandler("latest", latest))

        logger.info(" Telegram bot started using long polling...")

        app.run_polling()
