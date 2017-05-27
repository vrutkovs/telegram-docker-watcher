#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os
import logging
import re

from telegram import ChatAction
from telegram.ext import Updater, CommandHandler
from ahab import Ahab
from threading import Thread
from docker import Client

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

if 'TOKEN' not in os.environ:
    raise RuntimeError("Put bot token in TOKEN env var")

if 'USER' not in os.environ:
    raise RuntimeError("Put intended user name in USER env var")

if 'HOST' not in os.environ:
    raise RuntimeError("Put intended hostname in HOST env var")

TOKEN = os.environ['TOKEN']
USER = os.environ['USER']
HOST = os.environ['HOST']

NAME_REGEX = os.environ.get("NAME_REGEX")
IMAGE_REGEX = os.environ.get("IMAGE_REGEX")

listener_thread = None
docker_client = Client(base_url='unix://var/run/docker.sock')


class DockerWatcher(Ahab):
    def set_bot_details(self, bot, chat_id):
        self.bot = bot
        self.chat_id = chat_id

    def handle(self, event, data):
        logger.info("docker event {}".format(event))
        message_tmpl = 'host {hostname}: {action} "{container}" (id {shortid} image "{image}")'
        if event.get('Action') and event.get('Actor', {}).get('Attributes', {}).get('image'):
            container_name = event.get('Actor', {}).get('Attributes', {}).get('name')
            image_name = event.get('Actor', {}).get('Attributes', {}).get('image')
            message = message_tmpl.format(
                hostname=HOST,
                container=container_name,
                shortid=event.get('Actor', {}).get('ID', '')[:8],
                image=image_name,
                action=event.get('Action', '')
            )

            show_message = True
            if container_name and NAME_REGEX:
                if re.match(NAME_REGEX, container_name):
                    show_message = False

            if image_name and IMAGE_REGEX:
                if re.match(IMAGE_REGEX, image_name):
                    show_message = False

            if show_message:
                self.bot.sendMessage(chat_id=self.chat_id, text=message)


def setup_docker_watcher(bot, update):
    logger.info("setup_docker_watcher")
    docker_watcher = DockerWatcher()
    docker_watcher.set_bot_details(bot, update.message.chat_id)
    docker_watcher.listen()


def cmd_start(bot, update):
    global listener_thread
    bot.sendChatAction(chat_id=update.message.chat_id,
                       action=ChatAction.TYPING)
    logger.info("start")
    if update.message.from_user.username != USER:
        return

    if listener_thread:
        message = 'Listener has already started on host {host}'.format(host=HOST)
        bot.sendMessage(chat_id=update.message.chat_id, text=message)
        return

    try:
        listener_thread = Thread(target=setup_docker_watcher,
                                 args=(bot, update))
        listener_thread.start()
        message = 'Docker events listener started on host {host}'.format(host=HOST)
        bot.sendMessage(chat_id=update.message.chat_id, text=message)

    except Exception as e:
        message = 'Exception occurred: %r' % e
        bot.sendMessage(chat_id=update.message.chat_id, text=message)


def cmd_list(bot, update):
    global docker_client
    logger.info("list")

    container_lines = []
    for x in docker_client.containers():
        line = '{name} - {status}'.format(
            name=x['Names'][0],
            status=x['Status']
        )
        container_lines.append(line)
    message = 'My containers: {}'.format('\n'.join(container_lines))
    bot.sendMessage(chat_id=update.message.chat_id, text=message)


def cmd_ping(bot, update, args):
    logger.info("ping args={}".format(args))
    if update.message.from_user.username != USER:
        return

    try:
        message = 'Host {host} reporting in'.format(host=HOST)
        bot.sendMessage(chat_id=update.message.chat_id, text=message)

    except Exception as e:
        message = 'Exception occurred: %r' % e
        bot.sendMessage(chat_id=update.message.chat_id, text=message)


updater = Updater(token=TOKEN)
updater.dispatcher.add_handler(CommandHandler('start', cmd_start))
updater.dispatcher.add_handler(CommandHandler('ping', cmd_ping, pass_args=True))
updater.dispatcher.add_handler(CommandHandler('list', cmd_list))
updater.start_polling()
