from hashlib import md5
from logging import getLogger
from time import time

from discord import Interaction
from discord.app_commands import Group
from discord.ext.commands import GroupCog
from discord.ext.tasks import loop

from bot.utils import get_log_decorator
from env import TOKEN

log_as = get_log_decorator(getLogger(__name__))


async def setup(bot):
    await bot.add_cog(Copy(bot))


class Copy(GroupCog, name="copy", description="Copy a Discord feature"):

    def __init__(self, bot):

        self.bot = bot
        self.clear_cache.start()

    @loop(minutes=1.0)
    async def clear_cache(self):

        for expiry in self.bot.expiry_key.copy():
            if int(expiry) < time():

                key = self.bot.expiry_key[expiry]
                user = self.bot.key_user[key]

                # Clean cache
                self.bot.expiry_key.pop(expiry)
                self.bot.user_key.pop(user)
                self.bot.key_user.pop(key)
                if key.startswith("c"):
                    self.bot.key_channel.pop(key)
                else:
                    self.bot.key_server.pop(key)

    channel = Group(name="channel", description="Copy channel related features")

    @channel.command(name="permissions", description="Copy channel permissions")
    @log_as("/copy channel permissions")
    async def copy_channel_permissions(self, interaction: Interaction):

        key = "c" + md5(f"{TOKEN}{interaction.user.id}{interaction.channel_id}{time()}".encode("utf-8")).hexdigest()
        expiry = round(time()) + 600

        self.bot.key_channel[key] = dict(guild=interaction.guild_id, overwrites=interaction.channel.overwrites)
        self.bot.user_key[str(interaction.user.id)] = key
        self.bot.key_user[key] = str(interaction.user.id)
        self.bot.expiry_key[str(expiry)] = key

        await interaction.response.send_message(
            f"Copied <#{interaction.channel_id}>'s permissions. You can paste the permissions by doing `/paste "
            f"channel`. The copied data will expire at <t:{expiry}:t> (<t:{expiry}:R>)",
            ephemeral=True)
