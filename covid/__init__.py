from .covid import Covid
from .report import Report

def setup(bot):
    bot.add_cog(Covid())
    bot.add_cog(Report())