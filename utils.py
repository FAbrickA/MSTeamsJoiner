import datetime as dt
import random

from discord import SyncWebhook, Embed

from settings import settings

random_session_color = random.randint(0, 16777215)


def limit_str(string: str, max_length: int = 100) -> str:
    """
    Make string no longer than max_length.

    Example:
    ("string_very_very_long", 6) => "strin…"
    """

    ending = "…"
    if len(string) > max_length:
        return string[:max_length - len(ending)] + ending
    return string


def notify_in_discord(title: str, description: str):
    """
    Make discord notification using given webhook
    """
    if not settings["discord_webhook_url"]:
        return

    webhook = SyncWebhook.from_url(settings["discord_webhook_url"])

    embed = Embed(title=title, description=description, colour=random_session_color)
    embed.set_author(name="MsTeamsJoiner")
    embed.set_footer(text=f"\nTime: [{dt.datetime.now():%d/%m/%Y-%H:%M:%S}]\nLogin: {settings['email']}")

    try:
        webhook.send(embed=embed)
    except Exception as e:
        print("Failed to send discord notification.")
