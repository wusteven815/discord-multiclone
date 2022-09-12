from functools import wraps
from hashlib import md5
from inspect import signature
from time import time

from discord import Attachment
from discord import Member
from discord import Message
from discord import Role

from env import TOKEN


def get_expiry():
    return round(time()) + 600


def get_key(interaction):
    return md5(f"{TOKEN}{interaction.user.id}{interaction.channel_id}{round(time())}".encode("utf-8")).hexdigest()


def get_log_decorator(logger):
    def decorator(command_name):
        def inner(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):

                interaction = args[1]
                # For context menus:
                context_args = {}
                if len(args) > 2:
                    for arg in args[2:]:
                        if type(arg) == Message:
                            context_args["message"] = f"MSG={arg.id} TME={round(arg.created_at.timestamp())} " + \
                                                      f"AUT={arg.author.id}"

                # Create args formatting
                command_args = ""
                all_args = kwargs | context_args
                for key in all_args:
                    command_args += f" {signature(func).parameters[key].name}=" + "\""

                    # Slash command arg formatting
                    if all_args[key] is None:
                        command_args += "None"
                    elif type(all_args[key]) in (str, int, float):
                        command_args += str(all_args[key])
                    elif type(all_args[key]) == Attachment:
                        command_args += all_args[key].filename
                    elif type(all_args[key]) == Member:
                        command_args += str(all_args[key].id)
                    elif type(all_args[key]) == Role:
                        command_args += str(all_args[key].id)
                    else:
                        command_args += str(type(all_args[key]))
                    command_args += "\""

                logger.info(
                    f"[USRCMD] USR={interaction.user.id} GLD={interaction.guild_id} CNL={interaction.channel_id}: " +
                    f"`{command_name}{command_args}`")

                return await func(*args, **kwargs)
            return wrapper
        return inner
    return decorator