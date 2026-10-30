# Telegram Price Alert Bot

A Telegram bot that watches product prices and sends you a message when a price changes.

Demo target: books.toscrape.com (a public practice site). The same structure can be adapted to other shops.

## Features

- Track any number of products per user
- Automatic price checks on a schedule
- Instant Telegram alert when a price drops or rises
- Simple commands, no setup needed for the end user
- Retry-safe: network errors never crash the bot
- Bot token stays in a local `.env` file (never uploaded)

## Commands

| Command | What it does |
|---|---|
| `/track <url>` | Start tracking a book |
| `/list` | Show tracked books |
| `/untrack <number>` | Stop tracking |
| `/check` | Check prices now |
| `/simulate <number>` | Demo: fake an old price to test alerts |

## Setup

1. Create a bot with @BotFather in Telegram and copy the token.
2. Install dependencies:

       pip install -r requirements.txt

3. Create a `.env` file:

       BOT_TOKEN=your_token_here

4. Run:

       python bot.py

Optional: change the check interval (seconds):

       CHECK_INTERVAL=60 python bot.py

## Need something similar?

I build custom Python bots, scrapers and automation tools: price monitoring, data collection, reports and alerts.
Contact: Telegram @amir0_418
