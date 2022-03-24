from logging import basicConfig

from nucosen import nucosen
from nucosen.discordHandler import DiscordHandler


def execute():
    basicConfig(
        format='**{levelname}** @ ``{name}`` ({funcName})\n{message}',
        style='{',
        handlers=(DiscordHandler(),),
    )
    nucosen.run()
