#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os
import logging
import sys
import socket

from telegram.ext import Updater, CommandHandler
from ahab import Ahab

log = logging.getLogger('telegram_bot')
log.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)

if 'TOKEN' not in os.environ:
    raise RuntimeError("Put bot token in TOKEN env var")

if 'USER' not in os.environ:
    raise RuntimeError("Put intended user name in USER env var")

TOKEN = os.environ['TOKEN']
USER = os.environ['USER']
HOSTNAME = socket.gethostname()


class DockerWatcher(Ahab):
    def set_bot_details(self, bot, chat_id):
        self.bot = bot
        self.chat_id = chat_id

    def handle(self, event, data):
        message_tmpl = 'host {hostname}: {action} "{container}" (id {shortid} image "{image}")'
        if event.get('Action') and event.get('Actor', {}).get('Attributes', {}).get('image'):
            message = message_tmpl.format(
                hostname=HOSTNAME,
                container=event.get('Actor', {}).get('Attributes', {}).get('name'),
                shortid=event.get('Actor', {}).get('ID', '')[:8],
                image=event.get('Actor', {}).get('Attributes', {}).get('image'),
                action=event.get('Action', '')
            )
            self.bot.sendMessage(chat_id=self.chat_id, text=message)


def start(bot, update):
    if update.message.chat.username != USER:
        return

    try:
        message = 'Bot has started on host {host}'.format(host=HOSTNAME)
        bot.sendMessage(chat_id=update.message.chat_id, text=message)

        docker_watcher = DockerWatcher()
        docker_watcher.set_bot_details(bot, update.message.chat_id)
        docker_watcher.listen()

    except Exception as e:
        message = 'Exception ocurred: %r' % e
        bot.sendMessage(chat_id=update.message.chat_id, text=message)


updater = Updater(token=TOKEN)
updater.dispatcher.add_handler(CommandHandler('start', start))
updater.start_polling()
