from dotenv import load_dotenv
load_dotenv()
from .airquality import AirQuality
from .aqhi import AQHI

aqhiInstance = AQHI()

def setup(bot):
    bot.add_cog(AirQuality())
    bot.add_cog(aqhiInstance)

def teardown(bot):
    aqhiInstance.teardown()
