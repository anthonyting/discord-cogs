from redbot.core import commands
import os
import discord
from dotenv import load_dotenv
from urllib.request import urlopen
import json
import traceback
from datetime import datetime

API_KEY = os.getenv('IQR_API_KEY')

class AirQuality(commands.Cog):
    """Get air quality"""

    @commands.command(pass_context=True)
    @commands.guild_only()
    async def air(self, ctx):
        """Get air quality"""

        url = f"https://api.airvisual.com/v2/nearest_city?key={API_KEY}"

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

            pollutionData = data['history']['pollution'][0]
            time = pollutionData['ts']
            aqi = pollutionData['aqius']
            location = data['city']
            formattedTime = datetime.fromisoformat(time).strftime("%Y/%m/%d %I:%M%p")

            await ctx.send(f'{aqi} as of {formattedTime} in {location}')
