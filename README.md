# 🚀 Stock Prediction Platform

1.COMMAND:
--> python manage.py runserver
---> python manage.py telegrambot.py {seperately)

## 📄 Setup Instructions

# ------------------------------------------
# User Registration & Email Verification
# ------------------------------------------
- ✅ Register on website
- ✅ Receive email verification link
- ✅ Click link to activate account

# ------------------------------------------
# Profile & Stripe Payment
# ------------------------------------------
- 💳 Profile page includes Stripe upgrade
- 🎖️ Pro User:
    - Unlimited predictions (website & Telegram)
    - Lifetime access
- 🆓 Free User:
    - 5 predictions per day (combined website & Telegram)

# ------------------------------------------
# Stock Prediction Feature
# ------------------------------------------
- 🔎 Predict ticker name
- 📅 Select number of days to forecast

# ------------------------------------------
# Telegram Bot Usage
# ------------------------------------------
$ python manage.py telegrambot.py

# Commands:
  /start <email> <password>     # Link Telegram to website account (must register first)
  /predict <ticker>             # Get future prediction
  /latest                       # Get your latest prediction
  /help                         # Show all commands

# User Limits:
  - Free: 5 predictions/day total
  - Pro: Unlimited

# ------------------------------------------
# Docker Deployment
# ------------------------------------------
# Build Docker image
$ docker build . -t my-django-image

# Run using Docker Compose
$ docker compose up

# ------------------------------------------
# Extra
# ------------------------------------------
- 🖥️ Web predictions + 📲 Telegram predictions = same daily count limit
- 💬 Friendly UI built with Tailwind
- 🔐 Secure authentication (email + JWT/session)

# ------------------------------------------
# Quick Start Flow
# ------------------------------------------
1️⃣ Register → Verify Email → Login  
2️⃣ Upgrade to Pro (optional)  
3️⃣ Predict on website or Telegram  
4️⃣ Enjoy 🎉

# ------------------------------------------
# License & Contribution
# ------------------------------------------
MIT License. PRs & issues welcome!
