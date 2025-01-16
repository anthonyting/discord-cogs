from redbot.core import commands, bot, Config
from discord import AuditLogEntry, abc, Embed, TextChannel, Permissions
from typing import Any, Tuple


# TODO: fix representations of extra and diffs (e.g permissions)
class Audit(commands.Cog):
    MAX_LENGTH = 500

    def __init__(self, bot: bot.Red):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=1217560653, force_registration=True
        )
        default_guild = {"channel_id": None}
        self.config.register_guild(**default_guild)

    def get_key_value_representation(self, obj: dict):
        result = ""
        for key, value in obj.items():
            value_string = value.mention if hasattr(value, "mention") else value
            result += f"__{key}__ - {value_string}\n"
        return result

    @staticmethod
    def trim_text(text: str) -> str:
        return text[: Audit.MAX_LENGTH] + (
            "..." if len(text) > Audit.MAX_LENGTH else ""
        )

    async def handle_message_id(self, embed: Embed, value: Any, extra: dict[str, Any]):
        message_channel = extra.get("channel")
        if isinstance(message_channel, TextChannel):
            try:
                message = await message_channel.fetch_message(value)
                embed.add_field(name="Message", value=message.jump_url)
                if message.content:
                    embed.add_field(
                        name="Content", value=self.trim_text(message.content)
                    )
                return
            except Exception as e:
                print("error fetching message", e)
        embed.add_field(name="Message", value=value)

    # todo: show permissions better
    # def handle_permission_values(
    #     self, key: str, embed: Embed, before: Permissions, after: Permissions
    # ):
    #     difference = before ^ after

    #     result_before = ""
    #     for perm, value in before:
    #         if difference[perm] != value:
    #             result_before += f"__{perm}__ - {value}\n"

    #     result_after = ""
    #     for perm, value in after:
    #         if difference[perm] != value:
    #             result_after += f"__{perm}__ - {value}\n"

    #     embed.add_field(name=f"{key} (before)", value=result_before)
    #     embed.add_field(name=f"{key} (after)", value=result_after)

    @commands.Cog.listener(name="on_audit_log_entry_create")
    async def on_audit_log_entry_create(self, entry: AuditLogEntry):
        config = self.config.guild(entry.guild)
        channel_id_value = config.channel_id
        channel_id = await channel_id_value()
        if not channel_id:
            return

        channel = self.bot.get_channel(channel_id)
        if not channel or not isinstance(channel, abc.Messageable):
            return

        if not entry.user:
            return

        avatar_url = entry.user.display_avatar.url
        action = entry.action
        changes = entry.changes

        before_dict = dict(changes.before)
        after_dict = dict(changes.after)

        embed = Embed(
            title=f"{entry.user.display_name} ({entry.user.name})"
        ).set_thumbnail(url=avatar_url)

        embed.add_field(name="Action", value=action.name)
        if entry.target:
            embed.add_field(name="Target", value=entry.target)
        embed.add_field(name="User", value=entry.user.mention)

        # to_delete = []
        # for key, before_value in before_dict.items():
        #     after_value = after_dict.get(key)
        #     if isinstance(before_value, Permissions) and isinstance(
        #         after_value, Permissions
        #     ):
        #         self.handle_permission_values(key, embed, before_value, after_value)
        #         to_delete.append(key)

        # for key in to_delete:
        #     del before_dict[key]
        #     del after_dict[key]

        before = self.get_key_value_representation(before_dict)
        after = self.get_key_value_representation(after_dict)

        if len(before_dict):
            embed.add_field(name="Before", value=self.trim_text(before))
        if len(after_dict):
            embed.add_field(name="After", value=self.trim_text(after))
        if entry.extra:
            extra = (
                vars(entry.extra) if hasattr(entry.extra, "__dict__") else entry.extra
            )
            if isinstance(extra, dict):
                for key, value in extra.items():
                    if key == "message_id":
                        await self.handle_message_id(embed, value, extra)
                    else:
                        embed.add_field(
                            name=key.capitalize(),
                            value=(
                                f"{value.name} - {value.mention}"
                                if hasattr(value, "mention") and hasattr(value, "name")
                                else value
                            ),
                        )
            else:
                embed.add_field(name="Extra", value=extra)
        if entry.reason:
            embed.add_field(name="Reason", value=entry.reason)

        await channel.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def set_audit_channel_id(self, ctx: commands.Context, channel_id: int):
        if not ctx.guild:
            await ctx.send(f"No guild available")
            return

        channel = ctx.guild.get_channel(channel_id)
        if not channel or not isinstance(channel, abc.Messageable):
            await ctx.send(f"No valid channel found with id {channel_id}")
            return

        await self.config.guild(ctx.guild).channel_id.set(channel_id)
        await ctx.send(f"Successfully set audit channel to {channel}")
