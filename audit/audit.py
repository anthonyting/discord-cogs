from redbot.core import commands, bot, Config
from discord import AuditLogEntry, abc, Embed, TextChannel


# TODO: fix representations of extra and diffs (e.g permissions)
class Audit(commands.Cog):
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

        before = self.get_key_value_representation(dict(changes.before))
        after = self.get_key_value_representation(dict(changes.after))

        max_length = 400

        embed = Embed(
            title=f"{entry.user.display_name} ({entry.user.name})"
        ).set_thumbnail(url=avatar_url)

        embed.add_field(name="Action", value=action.name)
        if entry.target:
            embed.add_field(name="Target", value=entry.target)
        embed.add_field(name="User", value=entry.user.mention)

        if len(changes.before):
            embed.add_field(
                name="Before",
                value=before[0:max_length]
                + ("..." if len(before) > max_length else ""),
            )
        if len(changes.after):
            embed.add_field(
                name="After",
                value=after[0:max_length] + ("..." if len(after) > max_length else ""),
            )
        if entry.extra:
            extra = (
                vars(entry.extra) if hasattr(entry.extra, "__dict__") else entry.extra
            )
            if isinstance(extra, dict):
                for key, value in extra.items():
                    message_channel = extra.get("channel")
                    if key == "message_id" and isinstance(message_channel, TextChannel):
                        try:
                            message = await message_channel.fetch_message(value)
                            embed.add_field(
                                name=key.capitalize(), value={message.jump_url}
                            )
                        except Exception as e:
                            print("error fetching message", e)
                            embed.add_field(name=key.capitalize(), value={value})
                            pass
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
