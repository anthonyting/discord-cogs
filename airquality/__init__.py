from dotenv import load_dotenv
load_dotenv()
from .airquality import AirQuality
from .aqhi import AQHI

def setup(bot):
    bot.add_cog(AirQuality())
    bot.add_cog(AQHI())