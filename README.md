🚀 Stock Prediction Platform
This is a Django-based stock prediction web application integrated with a Telegram bot. It offers both free and Pro (paid) plans using Stripe, with Docker support for easy deployment.

✨ Features
📝 User Registration & Email Verification
Register on the website with your email and password.

After registration, you'll receive a verification email.

Click the activation link to verify and activate your account.

💰 Stripe Payment Integration
Upgrade to Pro in your profile section using Stripe.

Pro Users:

Lifetime unlimited predictions on both website and Telegram.

Free Users:

Limited to 5 predictions per day (shared between website and Telegram).

📊 Stock Prediction
Enter a stock ticker name and number of days to predict.

Instantly receive predicted prices and insights.

🤖 Telegram Bot Integration
Start the bot:

bash
Copy
Edit
python manage.py telegrambot.py
Telegram Commands
/start <email> <password>
Link your Telegram account to your website account (must register first).

/predict <ticker>
Get future price predictions for a given stock ticker.

/latest
Fetch your most recent prediction.

/help
Get help and see available commands.

⚖️ Limitations:

Free users: Up to 5 predictions per day (combined across website & Telegram).

Pro users: Unlimited predictions.

🐳 Docker Setup
Build the Docker image
bash
Copy
Edit
docker build . -t my-django-image
Run using Docker Compose
bash
Copy
Edit
docker compose up
⚙️ Additional Commands
Start the Telegram bot separately:

bash
Copy
Edit
python manage.py telegrambot.py
✅ Quick Flow
1️⃣ Register an account.
2️⃣ Verify your email.
3️⃣ Log in and optionally upgrade to Pro for unlimited predictions.
4️⃣ Predict stock prices on the website or via Telegram.
5️⃣ For Docker, build and run using the provided commands.

