from redbot.core import commands
import os
import discord
from ftplib import FTP
import csv
from typing import Dict, List, cast
import datetime

AQHI_REGION = os.getenv('AQHI_REGION')


class AQHI(commands.Cog):
    """Get BC AQHI"""

    def __init__(self):
        self.cache = None
        self.cache_time = None
        self.ftp = None

    def teardown(self):
        if (self.ftp):
            self.ftp.close()

    @commands.command(pass_context=True)
    @commands.guild_only()
    async def airquality(self, ctx):
        """Get air quality"""
        await self.air(ctx)

    @commands.command(pass_context=True)
    @commands.guild_only()
    async def aqhi(self, ctx):
        """Get air quality"""
        await self.air(ctx)       

    @commands.command(pass_context=True)
    @commands.guild_only()
    async def air(self, ctx: commands.Context):
        """Get BC AQHI"""

        async with ctx.typing():
            MINIMUM_CACHE_TIME = datetime.timedelta(minutes=5)
            if (self.cache and datetime.datetime.now() - self.cache_time < MINIMUM_CACHE_TIME):
                await ctx.send(embed=self.cache)
                return

            if (self.ftp):
                self.ftp.close()
            self.ftp = FTP('ftp.env.gov.bc.ca')
            print(self.ftp.login())
            self.ftp.cwd('pub/outgoing/AIR/Hourly_Raw_Air_Data/Station/')

            lines = []
            print(self.ftp.retrlines(f'RETR AQHI-{AQHI_REGION}.csv',
                                    callback=lambda x: lines.append(str(x))))

            self.ftp.close()

            output: List[Dict] = []
            reader = csv.DictReader(lines)
            for elm in reader:
                date = datetime.datetime.strptime(
                    elm['DATE_PST'], '%Y-%m-%d %H:%M')
                output.append({
                    **elm,
                    "DATE_PST": date,
                })

            sortedOutput = sorted(output, key=lambda x: cast(
                datetime.date, x['DATE_PST']))
            latest = sortedOutput[-1]

            aqhi_char = latest['AQHI_CHAR']

            color: discord.Colour
            risk: str
            if (aqhi_char == '1'):
                color = discord.Colour.from_rgb(0, 204, 255)
                risk = 'Low'
            elif (aqhi_char == '2'):
                color = discord.Colour.from_rgb(0, 153, 204)
                risk = 'Low'
            elif (aqhi_char == '3'):
                color = discord.Colour.from_rgb(0, 102, 153)
                risk = 'Low'
            elif (aqhi_char == '4'):
                color = discord.Colour.from_rgb(255, 255, 0)
                risk = 'Moderate'
            elif (aqhi_char == '5'):
                color = discord.Colour.from_rgb(255, 204, 0)
                risk = 'Moderate'
            elif (aqhi_char == '6'):
                color = discord.Colour.from_rgb(255, 153, 51)
                risk = 'Moderate'
            elif (aqhi_char == '7'):
                color = discord.Colour.from_rgb(255, 102, 102)
                risk = 'High'
            elif (aqhi_char == '8'):
                color = discord.Colour.from_rgb(255, 0, 0)
                risk = 'High'
            elif (aqhi_char == '9'):
                color = discord.Colour.from_rgb(204, 0, 0)
                risk = 'High'
            elif (aqhi_char == '10'):
                color = discord.Colour.from_rgb(153, 0, 0)
                risk = 'High'
            else:
                color = discord.Colour.from_rgb(102, 0, 0)
                risk = 'Very High'

            formattedTime = latest['DATE_PST'].strftime("%Y/%m/%d %#I:%M%p")

            embed = discord.Embed(
                title=f"{risk} Risk ({latest['AQHI_CHAR']}/10)",
                color=color
            ) \
            .set_author(name=f"Updated at {formattedTime}",
                            url="https://www.env.gov.bc.ca/epd/bcairquality/data/aqhi-table.html") \
            .set_footer(text=f"{latest['AQHI_AREA']}")
            self.cache = embed
            self.cache_time = datetime.datetime.now()
            await ctx.send(embed=embed)
