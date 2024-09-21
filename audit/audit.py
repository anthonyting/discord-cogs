from redbot.core import commands, bot, Config
from discord import AuditLogEntry, abc


class Audit(commands.Cog):
    def __init__(self, bot: bot.Red):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=1217560653, force_registration=True
        )
        default_guild = {"channel_id": None}
        self.config.register_guild(**default_guild)

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

        # TODO: make a nicer message with user photo
        await channel.send(str(entry))

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
