from redbot.core import commands
import discord
import random


class SportsDay(commands.Cog):
    """Sports Day"""

    @commands.command(pass_context=True)
    @commands.guild_only()
    async def sportsday(self, ctx: commands.Context):
        """Sport Day"""
        ctx.trigger_typing()

        sportsdaybj = discord.utils.get(ctx.guild.emojis, name='sportsdaybj')
        sportsdayvr = discord.utils.get(ctx.guild.emojis, name='sportsdayvik')

        isbj = random.randint(0, 100)

        sportsday = sportsdaybj if (isbj < 60) else sportsdayvr

        rows = random.randint(1, 6)
        cols = random.randint(1, 6)

        message = await ctx.send(((str(sportsday) * cols + "\n") * rows))
        await message.add_reaction(sportsday)
