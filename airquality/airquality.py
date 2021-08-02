import urllib.parse
import urllib.error
import dateutil.parser
from datetime import datetime, timezone
import traceback
import json
from urllib.request import urlopen
from redbot.core import commands
import os
import discord

API_KEY = os.getenv('IQR_API_KEY')
CITY = os.getenv('CITY')
COUNTRY = os.getenv('COUNTRY')
STATE = os.getenv('STATE')


class AirQuality(commands.Cog):
    """Get air quality"""

    @commands.command(pass_context=True)
    @commands.guild_only()
    async def airquality(self, ctx):
        """Get air quality"""
        await self.air(ctx)

    @commands.command(pass_context=True)
    @commands.guild_only()
    async def aqi(self, ctx):
        """Get air quality"""
        await self.air(ctx)

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
                formattedTime = dateutil.parser.isoparse(time).replace(
                    tzinfo=timezone.utc).astimezone(tz=None).strftime("%Y/%m/%d %#I:%M%p")

                color: discord.Colour
                risk: str
                if (0 <= aqi <= 33):
                    color = discord.Colour.green()
                    risk = "Very Good"
                elif (34 <= aqi <= 66):
                    color = discord.Colour.dark_green()
                    risk = "Good"
                elif (67 <= aqi <= 99):
                    color = discord.Colour.dark_gold()
                    risk = "Fair"
                elif (100 <= aqi <= 149):
                    color = discord.Colour.dark_orange()
                    risk = "Poor"
                elif (150 <= aqi <= 200):
                    color = discord.Colour.dark_red()
                    risk = "Very Poor"
                elif (201 <= aqi <= 300):
                    color = discord.Colour.purple()
                    risk = "Hazardous"
                else:
                    color = discord.Colour.dark_purple()
                    risk = "Very Hazardous"

                embed = discord.Embed(
                    title=f'AQI of **{aqi}** in {location} ({risk})',
                    color=color
                )
                embed.set_author(name=f"Updated at {formattedTime}", url=f"https://www.iqair.com/{COUNTRY.lower()}/{STATE.lower().replace(' ', '-')}/{CITY.lower()}")

                await ctx.send(embed=embed)
        except urllib.error.HTTPError as e:
            print(e.read())
            return await ctx.send("Error getting air quality.")
