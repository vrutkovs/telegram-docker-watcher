# telegram-docker-watcher

This script will create a bot, which would report docker events (started and stopped containers)

## Config

* Set the following env vars:
  * `TOKEN` - Telegram bot token
  * `USER` - Telegram user name, requests from other users will be ignored
  * `HOSTNAME` - hostname description

* Set optional env vars:
  * `NAME_REGEX` - ignore events from containers with names matching the regex
  * `IMAGE_REGEX` - ignore events from containers with images matching the regex

* Run `python3 telegram_bot.py`

