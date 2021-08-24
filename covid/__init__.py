from .covid import Covid
from .report import Report

covidInstance = Covid()


def setup(bot):
    bot.add_cog(covidInstance)


def teardown(bot):
    covidInstance.stop_report_task()
