from redbot.core import bot
from .audit import Audit


async def setup(bot: bot.Red):
    audit_bot = Audit(bot)
    
    await bot.add_cog(audit_bot)
