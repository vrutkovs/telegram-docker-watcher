# telegram-docker-watcher

This script will create a bot, which would report docker events (started and stopped containers)

## Config

* Set the following env vars:
  * `TOKEN` - Telegram bot token
  * `USER` - Telegram user name, requests from other users will be ignored

* Run `python3 telegram_bot.py`

