import logging
from os import getcwd

import requests
from decouple import AutoConfig


class DiscordHandler(logging.StreamHandler):
    def __init__(self):
        super().__init__()
        config = AutoConfig(search_path=getcwd())
        self.url: str = str(
            config("LOGGING_DISCORD_WEBHOOK", "http://example.com")
        )

    def emit(self, record):
        msg = self.format(record)
        self.send_message(msg)

    def send_message(self, text):
        message = {
            'content': text
        }
        requests.post(self.url, json=message)
