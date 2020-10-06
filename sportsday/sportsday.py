from redbot.core import commands
import discord
import random


class SportsDay(commands.Cog):
    """Sports Day"""

    def __init__(self):
        self.sportsdaybj = None
        self.sportsdayvk = None

    @commands.command(pass_context=True)
    @commands.guild_only()
    async def sportsday(self, ctx: commands.Context):
        """Sport Day"""
        await ctx.trigger_typing()
        
        if (not self.sportsdaybj):
            self.sportsdaybj = discord.utils.get(ctx.guild.emojis, name='sportsdaybj')
        if (not self.sportsdayvk):
            self.sportsdayvk = discord.utils.get(ctx.guild.emojis, name='sportsdayvik')

        isbj = random.randint(0, 100)

        sportsday = self.sportsdaybj if (isbj < 60) else self.sportsdayvk

        rows = random.randint(1, 6)
        cols = random.randint(1, 6)

        message = await ctx.send(((str(sportsday) * cols + "\n") * rows))
        # await message.add_reaction(sportsday)
