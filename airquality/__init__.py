from dotenv import load_dotenv
load_dotenv()
from .airquality import AirQuality
from .aqhi import AQHI

aqhiInstance = AQHI()

async def setup(bot):
    await bot.add_cog(AirQuality())
    await bot.add_cog(aqhiInstance)

async def teardown(bot):
    aqhiInstance.teardown()
