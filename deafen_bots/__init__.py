import discord
from redbot.core import commands

class Deafen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if (not after.deaf and member.bot):
            await member.edit(reason="Bots don't need to hear", deafen=True)

async def setup(bot):
    await bot.add_cog(Deafen(bot))


async def teardown(bot):
    pass
