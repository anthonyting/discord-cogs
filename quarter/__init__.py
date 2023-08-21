from .quarter import Quarter

async def setup(bot):
    await bot.add_cog(Quarter())