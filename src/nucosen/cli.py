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

from logging import INFO, StreamHandler, Formatter, WARNING, root

from nucosen import nucosen
from nucosen.discordHandler import DiscordHandler


def execute():
    stdErr = StreamHandler()
    oneLineFormat = Formatter("{asctime} [{levelname:4}] {message}", style="{")
    stdErr.setLevel(INFO)
    stdErr.setFormatter(oneLineFormat)

    discordErr = DiscordHandler()
    twoLineFormat = Formatter('**{levelname}** @ ``{name}`` ({funcName})\n{message}', style="{")
    discordErr.setLevel(WARNING)
    discordErr.setFormatter(twoLineFormat)

    root.addHandler(stdErr)
    root.addHandler(discordErr)
    root.setLevel(INFO)

    nucosen.run()
