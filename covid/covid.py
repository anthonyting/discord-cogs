from prettytable.prettytable import HEADER, NONE
from redbot.core import commands
import discord
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import json
import traceback

from datetime import datetime, timedelta
from prettytable import PrettyTable


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
            "outFields": "HA_Name, NewCases, Date_Updat, ActiveCases, CurrentlyICU",
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
        totalICU = 0
        date = 0
        regionString, newCasesString, activeCasesString = ("", "", "")
        for element in data['features']:
            attr = element['attributes']
            newCasesToday = attr['NewCases']
            activeCasesToday = attr['ActiveCases']
            icuToday = attr['CurrentlyICU']
            totalNew += int(newCasesToday or 0)
            totalActive += int(activeCasesToday or 0)
            totalICU += int(icuToday or 0)
            date = max(date, int(attr['Date_Updat']))

            regionString += attr['HA_Name'] + '\n'
            newCasesString += str(newCasesToday) + '\n'
            activeCasesString += str(activeCasesToday) + '\n'

        updatedAt = datetime.fromtimestamp(date // 1000)

        dateString = updatedAt.strftime("%B %#d at %#I:%M%p")
        daysSince = (datetime.now().replace(hour=0,minute=0,second=0,microsecond=0) - updatedAt.replace(hour=0,minute=0,second=0,microsecond=0)).days

        if (daysSince == 1):
            dateDiff = "Yesterday"
        elif (daysSince > 1):
            dateDiff = f"{(datetime.now() - updatedAt).days} days ago"
        else:
            dateDiff = "Today"

        embed = discord.Embed(
            title="BC COVID-19 Case Numbers",
            colour=discord.Colour.blue()
        )

        totalNew = 0
        totalActive = 0
        totalICU = 0
        date = 0
        regionString, newCasesString, activeCasesString = ("", "", "")
        regions, newCases, activeCases, icuCases = ([], [], [], [])
        for element in data['features']:
            attr = element['attributes']
            newCasesToday = attr['NewCases']
            activeCasesToday = attr['ActiveCases']
            icuToday = attr['CurrentlyICU']
            region = attr['HA_Name']
            totalNew += int(newCasesToday or 0)
            totalActive += int(activeCasesToday or 0)
            totalICU += int(icuToday or 0)
            date = max(date, int(attr['Date_Updat']))

            newCases.append(newCasesToday)
            activeCases.append(activeCasesToday)
            icuCases.append(icuToday)

            if (region == 'Vancouver Coastal'):
                regionString += f"**{region}**"
                newCasesString += f"**{newCasesToday}**"
                activeCasesString += f"**{activeCasesToday}**"
                regions.append(f"* {region}")
            else:
                regionString += region
                newCasesString += str(newCasesToday)
                activeCasesString += str(activeCasesToday)
                regions.append(region)
            regionString += '\n'
            newCasesString += '\n'
            activeCasesString += '\n'

        regions.append('# Total')
        newCases.append(totalNew)
        activeCases.append(totalActive)
        icuCases.append(totalICU)

        newCasesString += f"**{totalNew}**"
        activeCasesString += f"**{totalActive}**"

        table = PrettyTable(
            field_names=["# Region", "New Cases", "Active", "ICU"])
        table.add_rows(zip(regions, newCases, activeCases, icuCases))
        table.border = False
        table.align = 'l'
        table.left_padding_width = 0

        embed.add_field(name=f"Last updated on {dateString} ({dateDiff})",
                        value=f"```md\n{table.get_string()}```", inline=True)
        embed.set_author(name=f"Source", url=r"https://experience.arcgis.com/experience/a6f23959a8b14bfa989e3cda29297ded",
                         icon_url=r"https://cdn.discordapp.com/attachments/360564259316301836/747043112043544617/BCGov_-_Horizontal_AGOL_Logo_-_White_-_Sun.png")
        embed.set_footer(text="Updates daily Monday through Friday at 5:00 pm")
        # API: https://services1.arcgis.com/xeMpV7tU1t4KD3Ei/ArcGIS/rest/services/COVID19_Cases_by_BC_Health_Authority/FeatureServer/0
        return embed
