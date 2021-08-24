from .covid import Covid

covidInstance = Covid()


def setup(bot):
    bot.add_cog(covidInstance)


def teardown(bot):
    covidInstance.stop_report_task()
