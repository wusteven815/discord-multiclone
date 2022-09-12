from logging import getLogger

from discord import Colour
from discord import Embed
from discord import Forbidden
from discord import Interaction
from discord import Role
from discord.app_commands import AppCommandError
from discord.app_commands import command
from discord.app_commands.errors import CommandInvokeError
from discord.app_commands.errors import MissingPermissions
from discord.channel import TextChannel
from discord.ext.commands import GroupCog

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

        # Paste
        embed = Embed(title="Pasted the following features", colour=Colour.light_grey())

        if "overwrites" in channel:
            try:
                await interaction.channel.edit(overwrites=channel["overwrites"])
            except Forbidden:
                embed.add_field(
                    name="Permissions",
                    value="Failed because the bot is missing permissions. The bot needs the `Manage server` and "
                          "`Manage roles` permissions to paste permissions.",
                    inline=False)
            else:
                embed.add_field(
                    name="Permissions",
                    value="\n".join([f" - <@&{obj.id}>" if type(obj) == Role else f" - <@{obj.id}>"
                                     for obj in channel['overwrites']]),
                    inline=False)

        if "threads" in channel:

            created_threads = []
            did_not_create = False

            for thread in channel["threads"]:

                if thread.archived or thread.locked or thread.is_private():
                    did_not_create = True
                    continue

                try:
                    message = await interaction.channel.send(f"Copy pasted thread - **{thread.name}**")
                    await interaction.channel.create_thread(
                        name=thread.name,
                        message=message,
                        auto_archive_duration=thread.auto_archive_duration,
                        reason=f"Copy pasted thread by {interaction.user}",
                        invitable=thread.invitable,
                        slowmode_delay=thread.slowmode_delay)
                except Forbidden:
                    created_threads.append(f" - ⚠ {thread.name}")
                    did_not_create = True
                else:
                    created_threads.append(f" - {thread.name}")

            if did_not_create:
                created_threads.append("\nDid not create archived, locked, or private thread(s). ⚠ Warning threads "
                                       "were not created because they are missing  the `Create public thread`, or "
                                       "`Send message` permission (in this channel).")

            embed.add_field(name="Threads", value="\n".join(created_threads), inline=False)

        await reply(embed=embed)

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
