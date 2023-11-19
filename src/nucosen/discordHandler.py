"""
Copyright 2022 NUCOSen運営会議

This file is part of NUCOSen Broadcast.

NUCOSen Broadcast is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

NUCOSen Broadcast is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with NUCOSen Broadcast.  If not, see <https://www.gnu.org/licenses/>.
"""

import logging
from os import getcwd

import requests
from decouple import AutoConfig


class DiscordHandler(logging.StreamHandler):
    def __init__(self):
        super().__init__()
        config = AutoConfig(search_path=getcwd())
        self.url: str = str(
            config("LOGGING_DISCORD_WEBHOOK", default="BAD_URL")
        )
        if self.url == "BAD_URL":
            raise Exception(
                "START UP ERROR : LOGGING_DISCORD_WEBHOOK is not available.")

    def emit(self, record):
        msg = self.format(record)
        self.send_message(msg)

    def send_message(self, text):
        message = {
            'content': text
        }
        requests.post(self.url, json=message)
