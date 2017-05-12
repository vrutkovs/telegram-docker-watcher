FROM fedora:25

RUN dnf update -y && \
    dnf install -y python3-pip git && \
    dnf clean all

ADD . /telegram-docker-watcher

RUN cd /telegram-docker-watcher && \
    pip3 install -r requirements.txt

WORKDIR /telegram-docker-watcher

CMD ["python3", "telegram_bot.py"]
