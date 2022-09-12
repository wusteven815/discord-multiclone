from logging import getLogger
from time import time

from discord import Interaction
from discord import TextChannel
from discord.app_commands import Group
from discord.ext.commands import GroupCog
from discord.ext.tasks import loop

from bot.utils import get_expiry
from bot.utils import get_key
from bot.utils import get_log_decorator

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

    async def _copy_channel_item(self, interaction: Interaction, item_name, item_value, public_name):

        async def reply(message):
            await interaction.response.send_message(message, ephemeral=True)

        # Check if correct channel type
        if type(interaction.channel) != TextChannel:
            await reply("This command can only be run in server text channels.")
            return

        key = "c" + get_key(interaction)
        expiry = get_expiry()

        self.bot.key_channel[key] = {
            "guild": interaction.guild_id,
            item_name: item_value}
        self.bot.user_key[str(interaction.user.id)] = key
        self.bot.key_user[key] = str(interaction.user.id)
        self.bot.expiry_key[str(expiry)] = key

        await reply(f"Copied <#{interaction.channel_id}>'s {public_name}. You can paste the {public_name} by doing "
                    f"`/paste channel`. The copied data will expire at <t:{expiry}:t> (<t:{expiry}:R>)")

    @channel.command(name="permissions", description="Copy channel permissions")
    @log_as("/copy channel permissions")
    async def copy_channel_permissions(self, interaction: Interaction):
        if len(interaction.channel.overwrites) == 0:
            await interaction.response.send_message(
                "This channel doesn't have any special permissions.",
                ephemeral=True)
        else:
            await self._copy_channel_item(interaction, "overwrites", interaction.channel.overwrites, "permissions")

    @channel.command(name="threads", description="Copy channel threads")
    @log_as("/copy channel threads")
    async def copy_channel_threads(self, interaction: Interaction):
        if len(interaction.channel.threads) == 0:
            await interaction.response.send_message(
                "This channel doesn't have any non archived/locked/private threads, and/or can't see any threads.",
                ephemeral=True)
        else:
            await self._copy_channel_item(interaction, "threads", interaction.channel.threads, "threads")

    server = Group(name="server", description="Copy server related features")

    # @server.command(name="")
