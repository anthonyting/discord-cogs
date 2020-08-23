from redbot.core import commands
import discord
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import json
import traceback

from datetime import datetime, timedelta


class Covid(commands.Cog):
    """Gets BC COVID-19 data"""

    def __init__(self):
        self.sinceLastGotData = None
        self.cachedResponse = None

    @commands.command()
    @commands.guild_only()
    async def covid(self, ctx):
        """Get latest BC COVID data"""

        if (self.cachedResponse and self.sinceLastGotData and datetime.now() - self.sinceLastGotData < timedelta(seconds=30)):
            await ctx.send(embed=await self.parseData(self.cachedResponse))
            return

        queries = {
            "where": "1=1",
            "time": f"\'{datetime.now().strftime('%m/%d/%Y')}\'",
            "outFields": "HA_Name, NewCases, Date_Updat, ActiveCases",
            "returnGeometry": "false",
            "returnCentroid": "false",
            "f": "json"
        }
        url = r"https://services1.arcgis.com/xeMpV7tU1t4KD3Ei/ArcGIS/rest/services/COVID19_Cases_by_BC_Health_Authority/FeatureServer/0/query?"
        url += urlencode(queries)

        request = Request(url)
        with urlopen(request) as response:
            print("Requesting covid data at " + datetime.now().isoformat())
            try:
                data = json.load(response)
                self.cachedResponse = data
                self.sinceLastGotData = datetime.now()
                await ctx.send(embed=await self.parseData(data))
            except Exception as e:
                traceback.print_exc()
                print(url)
                print(data)
                await ctx.send(f"{ctx.message.author.mention} Sorry, there was an error getting the data.")

    async def parseData(self, data):
        totalNew = 0
        totalActive = 0
        date = 0
        regionString, newCasesString, activeCasesString = ("", "", "")
        for element in data['features']:
            attr = element['attributes']
            newCasesToday = attr['NewCases']
            activeCasesToday = attr['ActiveCases']
            totalNew += newCasesToday
            totalActive += activeCasesToday
            date = max(date, int(attr['Date_Updat']))

            regionString += attr['HA_Name'] + '\n'
            newCasesString += str(newCasesToday) + '\n'
            activeCasesString += str(activeCasesToday) + '\n'

        dateString = datetime.utcfromtimestamp(
            date // 1000).strftime("%Y/%m/%d %I:%M%p")

        embed = discord.Embed(
            title="BC COVID-19 Case Numbers",
            description="Most recent BC COVID-19 data. Last Updated: " + dateString,
            colour=discord.Colour.blue()
        )

        totalNew = 0
        totalActive = 0
        date = 0
        regionString, newCasesString, activeCasesString = ("", "", "")
        regions, newCases, activeCases = ([], [], [])
        for element in data['features']:
            attr = element['attributes']
            newCasesToday = attr['NewCases']
            activeCasesToday = attr['ActiveCases']
            region = attr['HA_Name']
            totalNew += newCasesToday
            totalActive += activeCasesToday
            date = max(date, int(attr['Date_Updat']))

            regions.append(region)
            newCases.append(newCasesToday)
            activeCases.append(activeCasesToday)

            if (region == 'Vancouver Coastal'):
                regionString += f"**{region}**"
                newCasesString += f"**{newCasesToday}**"
                activeCasesString += f"**{activeCasesToday}**"
            else:
                regionString += region
                newCasesString += str(newCasesToday)
                activeCasesString += str(activeCasesToday)
            regionString += '\n'
            newCasesString += '\n'
            activeCasesString += '\n'

        newCasesString += f"**{totalNew}**"
        activeCasesString += f"**{totalActive}**"

        embed.add_field(name="Region", value=regionString, inline=True)
        embed.add_field(name="New Cases (24h)", value=newCasesString, inline=True)
        embed.add_field(name="Active Cases", value=activeCasesString, inline=True)
        embed.set_author(name=f"Source", url=r"https://experience.arcgis.com/experience/a6f23959a8b14bfa989e3cda29297ded", icon_url=r"https://cdn.discordapp.com/attachments/360564259316301836/747043112043544617/BCGov_-_Horizontal_AGOL_Logo_-_White_-_Sun.png")
        # API: https://services1.arcgis.com/xeMpV7tU1t4KD3Ei/ArcGIS/rest/services/COVID19_Cases_by_BC_Health_Authority/FeatureServer/0
        return embed