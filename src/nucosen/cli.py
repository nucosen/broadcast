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
