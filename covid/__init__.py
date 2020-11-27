from .covid import Covid
from .report import Report

covidInstance = Covid()
reportInstance = Report()

def setup(bot):
    bot.add_cog(covidInstance)
    bot.add_cog(reportInstance)

def teardown(bot):
    reportInstance.stopTask()