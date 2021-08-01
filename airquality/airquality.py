from redbot.core import commands
import os
import discord
from dotenv import load_dotenv
load_dotenv()
from urllib.request import urlopen
import urllib.error, urllib.parse
import json
import traceback
from datetime import datetime, timezone
import dateutil.parser

API_KEY = os.getenv('IQR_API_KEY')
CITY = os.getenv('CITY')
COUNTRY = os.getenv('COUNTRY')
STATE = os.getenv('STATE')

class AirQuality(commands.Cog):
    """Get air quality"""

    @commands.command(pass_context=True)
    @commands.guild_only()
    async def air(self, ctx):
        """Get air quality"""

        args = {
            "city": CITY,
            "country": COUNTRY,
            "state": STATE,
            "key": API_KEY
        }

        url = f"https://api.airvisual.com/v2/city?{urllib.parse.urlencode(args)}"

        await ctx.trigger_typing()

        try:
            with urlopen(url) as airQuality:
                print("Requesting AQI data at " + datetime.now().isoformat())
                try:
                    data = json.load(airQuality)
                    if (data['status'] != 'success'):
                        raise Exception("API Error with data", data)
                    data = data['data']
                except Exception as e:
                    traceback.print_exc()
                    return await ctx.send("Error getting air quality.")

                pollutionData = data['current']['pollution']
                time = pollutionData['ts']
                aqi = pollutionData['aqius']
                location = data['city']
                formattedTime = dateutil.parser.isoparse(time).replace(tzinfo=timezone.utc).astimezone(tz=None).strftime("%Y/%m/%d %I:%M%p")

                await ctx.send(f'AQI of **{aqi}** at {formattedTime} in {location}')
        except urllib.error.HTTPError as e:
            print(e.read())
            return await ctx.send("Error getting air quality.")
