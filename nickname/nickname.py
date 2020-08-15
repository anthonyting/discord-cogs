from redbot.core import commands
import discord

class Nickname(commands.Cog):
    """Rename a user"""

    @commands.command(pass_context=True)
    @commands.is_owner()
    @commands.guild_only()
    async def nickname(self, ctx, member: discord.Member, nick):
        """Set a user's nickname"""
        # Your code will go here
        await member.edit(nick=nick)
        await ctx.send(f'Nickname was changed for {member.mention} ')