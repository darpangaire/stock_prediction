import os
import logging
from datetime import datetime

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from django.core.exceptions import ObjectDoesNotExist

from api.models import TelegramUser, Prediction
from api.utils import run_prediction
from payment.models import UserProfile

User = get_user_model()

# Logging config
logger = logging.getLogger("telegrambot")
logging.basicConfig(level=logging.INFO)


async def get_linked_user(chat_id):
    try:
        tg_user = await sync_to_async(TelegramUser.objects.select_related("user").get)(chat_id=chat_id)
        return tg_user.user, tg_user
    except TelegramUser.DoesNotExist:
        return None, None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "Please provide your email and password:\n/start your_email@example.com your_password"
        )
        return

    email = args[0]
    password = args[1]

    try:
        user = await sync_to_async(User.objects.get)(email=email)
        is_valid = await sync_to_async(user.check_password)(password)
        if not is_valid:
            await update.message.reply_text(" Incorrect password. Please try again.")
            return

        # Check if TelegramUser already exists for this user
        try:
            telegram_user_obj = await sync_to_async(TelegramUser.objects.get)(user=user)
            if telegram_user_obj.chat_id != chat_id:
                telegram_user_obj.chat_id = chat_id
                await sync_to_async(telegram_user_obj.save)()
        except TelegramUser.DoesNotExist:
            try:
                existing_by_chat = await sync_to_async(TelegramUser.objects.get)(chat_id=chat_id)
                existing_by_chat.user = user
                await sync_to_async(existing_by_chat.save)()
            except TelegramUser.DoesNotExist:
                await sync_to_async(TelegramUser.objects.create)(
                    user=user,
                    chat_id=chat_id
                )

        await update.message.reply_text(
            " Your account is successfully linked to this Telegram chat!\n"
            "You can now use /predict and /latest."
        )

    except ObjectDoesNotExist:
        await update.message.reply_text(" No account found with that email. Please register first.")


async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    user, tg_user = await get_linked_user(chat_id)
    if not user:
        await update.message.reply_text(" You need to link your account first. Use /start <email> <password>.")
        return

    # Get UserProfile
    try:
        profile = await sync_to_async(UserProfile.objects.get)(user=tg_user)
    except UserProfile.DoesNotExist:
        # If profile doesn't exist, create it
        profile = await sync_to_async(UserProfile.objects.create)(user=tg_user)

    # Reset count if new day
    await sync_to_async(profile.reset_count_if_new_day)()

    # Check limit for non-pro users
    if not profile.is_pro and profile.daily_prediction_count >= 5:
        await update.message.reply_text(
            " You have used your 5 free predictions for today.\n"
            "Upgrade to Pro to get unlimited predictions! 💎"
        )
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

        price_str = f"{next_day_price:.2f}" if next_day_price is not None else "N/A"

        msg = (
            f"Prediction for {ticker}\n\n"
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

        # Increment daily_prediction_count
        profile.daily_prediction_count += 1
        await sync_to_async(profile.save)()

        # Send plot images
        with open(plot_history_path, "rb") as hist_img:
            await update.message.reply_photo(hist_img)
        with open(plot_pred_path, "rb") as pred_img:
            await update.message.reply_photo(pred_img)

        logger.info(f" Prediction sent to user_id={user.id}, ticker={ticker}")

    except Exception as e:
        logger.exception(f" Prediction error for user_id={user.id}, ticker={ticker}: {str(e)}")
        try:
            await update.message.reply_text(f" Error during prediction: {str(e)}")
        except Exception as e2:
            logger.exception(f" Also failed to send error message: {str(e2)}")


async def latest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    user, tg_user = await get_linked_user(chat_id)
    if not user:
        await update.message.reply_text("You need to link your account first. Use /start <email> <password>.")
        return

    latest_pred = await sync_to_async(
        lambda: Prediction.objects.filter(user=user).order_by("-created_at").first()
    )()

    if not latest_pred:
        await update.message.reply_text(" No predictions found. Use /predict <TICKER> to get started.")
        return

    price = latest_pred.next_day_price if latest_pred.next_day_price is not None else "N/A"

    msg = (
        f"Latest prediction for {latest_pred.ticker}\n\n"
        f"Next-day price: {price:.2f}\n"
        f"Created at: {latest_pred.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    await update.message.reply_text(msg)

    try:
        if latest_pred.plot_history_path and latest_pred.plot_pred_path:
            with open(latest_pred.plot_history_path, "rb") as hist_img:
                await update.message.reply_photo(hist_img)
            with open(latest_pred.plot_pred_path, "rb") as pred_img:
                await update.message.reply_photo(pred_img)
    except Exception as e:
        await update.message.reply_text(f" Could not send plot images: {str(e)}")


async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    user, tg_user = await get_linked_user(chat_id)
    if not user:
        await update.message.reply_text("You need to link your account first. Use /start <email> <password>.")
        return

    # Get latest prediction
    predictions = await sync_to_async(
        lambda: Prediction.objects.filter(user=user).order_by("-created_at")
    )()

    if not predictions:
        await update.message.reply_text("No predictions found. Use /predict <TICKER> to get started.")
        return

    # Prepare message
    msg = "Your predictions:\n\n"
    for p in predictions:
        price = f"{p.next_day_price:.2f}" if p.next_day_price is not None else "N/A"
        msg += (
            f"Ticker: {p.ticker}\n"
            f"Next-day price: {price}\n"
            f"Created at: {p.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )

    # Telegram message size limit workaround
    if len(msg) > 4000:
        # Split into smaller chunks
        for i in range(0, len(msg), 4000):
            await update.message.reply_text(msg[i:i+4000])
    else:
        await update.message.reply_text(msg)






async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Available commands:\n"
        "Login From Web\n"
        "/start <email> <password> — Link your Telegram account\n"
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
        app.add_handler(CommandHandler("history", history))

        logger.info("Telegram bot started using long polling...")

        app.run_polling()
