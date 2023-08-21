from .covid import Covid

covidInstance = Covid()


async def setup(bot):
    await bot.add_cog(covidInstance)


async def teardown(bot):
    covidInstance.stop_report_task()
