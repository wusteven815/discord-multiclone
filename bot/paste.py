from logging import getLogger

from discord import Colour
from discord import Embed
from discord import Forbidden
from discord import Interaction
from discord import Role
from discord.app_commands import AppCommandError
from discord.app_commands import command
from discord.app_commands.checks import has_permissions
from discord.app_commands.errors import CommandInvokeError
from discord.app_commands.errors import MissingPermissions
from discord.ext.commands import GroupCog
from discord.channel import TextChannel

from bot.utils import get_log_decorator

log_as = get_log_decorator(getLogger(__name__))


async def setup(bot):
    await bot.add_cog(Paste(bot))


class ChannelTypeError(Exception):
    pass


class GuildError(Exception):
    pass


class Paste(GroupCog, name="paste", description="Copy a Discord feature"):

    def __init__(self, bot):

        self.bot = bot

    @command(name="channel", description="Paste channel data")
    @log_as("/paste channel")
    async def paste_channel(self, interaction: Interaction):

        reply = interaction.response.send_message

        # Check if correct channel type
        if type(interaction.channel) != TextChannel:
            raise ChannelTypeError

        # Check permissions
        permissions = interaction.channel.permissions_for(interaction.user)
        if not permissions.manage_guild or not permissions.manage_roles:
            raise MissingPermissions(["manage_server", "manage_roles"])

        # Check if key exists
        key = self.bot.user_key[str(interaction.user.id)]
        if not key.startswith("c"):
            raise KeyError

        # Check if channel exists
        channel = self.bot.key_channel[key]
        if channel["guild"] != interaction.guild_id:
            raise GuildError

        # Run
        await interaction.channel.edit(overwrites=channel["overwrites"])
        await reply("Successfully pasted channel permissions.",
                    embed=Embed(
                        title="Changed permissions:",
                        description="\n".join([f" - <@&{obj.id}>" if type(obj) == Role else f" - <@{obj.id}>"
                                               for obj in channel['overwrites']]),
                        colour=Colour.light_grey()))

    @paste_channel.error
    async def paste_channel_error(self, interaction: Interaction, err: AppCommandError):

        async def reply(message):
            await interaction.response.send_message(message, ephemeral=True)

        if isinstance(err, MissingPermissions):
            await reply("You must need the `Manage server` and `Manage roles` permission to use this command")

        elif isinstance(err, CommandInvokeError):

            if isinstance(err.original, ChannelTypeError):
                await reply("This command can only be run in server text channels.")
            elif isinstance(err.original, Forbidden):
                await reply("Missing permissions to change permissions. The bot needs the `Manage server` and `Manage "
                            "roles` permission to paste.")
            elif isinstance(err.original, GuildError):
                await reply("You must paste the channel permission in the same server you copied in.")
            elif isinstance(err.original, KeyError):
                await reply("You don't have a channel permission data saved in the last 10 minutes.")

            else:
                await reply("Something went wrong.")
        else:
            await reply("Something went wrong.")
