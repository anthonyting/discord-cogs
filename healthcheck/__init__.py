from redbot.core import bot
from .healthcheck import HealthCheck


async def setup(bot: bot.Red):
    await bot.add_cog(HealthCheck(bot))
