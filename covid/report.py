from redbot.core import commands
import discord
import bs4
from urllib.request import urlopen
import re
from bs4.element import PageElement, Tag
import pyteaser
from datetime import datetime
import asyncio


class Report(commands.Cog):
    """Start report"""

    def __init__(self):
        self.running = False
        self.today = None
        self.foundToday = False
        self.firstRun = True

    @commands.command(pass_context=True)
    @commands.guild_only()
    @commands.is_owner()
    async def report(self, ctx: commands.Context):
        if (self.running):
            await ctx.send("Already reporting")
            return

        self.running = True

        await ctx.send("Reporting in this channel")
        while(not self.foundToday):
            if (not self.firstRun):
                await asyncio.sleep(3600.0)
            self.firstRun = False
            if (self.today != datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)):
                with urlopen('https://news.gov.bc.ca/ministries/health') as directoryUrl:
                    directory = bs4.BeautifulSoup(
                        directoryUrl, features="html.parser")

                    todayString = datetime.now().strftime(r"%B %#d, %Y")
                    dates = directory.find_all(
                        name='span', attrs={"class": "item-date"}, text=re.compile(f"{todayString}.*"))
                    statement: PageElement = None
                    for date in dates:
                        located: PageElement = date.parent.parent.find(
                            name='a', href=True, text=re.compile(f"Joint statement.*COVID-19.*"))
                        if (located):
                            statement = located
                            break

                    if (statement and statement['href']):
                        with urlopen(statement['href']) as jointStatementUrl:
                            jointStatement = bs4.BeautifulSoup(
                                jointStatementUrl, features="html.parser")
                            textElement: Tag = jointStatement.select_one(
                                selector=".story-expander article")
                            if (textElement):
                                text: str = textElement.getText()
                                intro: str = "Dr. Bonnie Henry, B.C.’s provincial health officer, and Adrian Dix, Minister of Health, have issued the following joint statement regarding updates on the novel coronavirus (COVID-19) response in British Columbia:"
                                concatenateStart: int = text.find(intro)
                                if (concatenateStart > -1):
                                    concatenateStart += len(intro)
                                    concatenateEnd: int = text.rfind(
                                        "Learn More:")
                                    if (concatenateStart > -1 and concatenateEnd > -1):
                                        text = text[concatenateStart:concatenateEnd]
                                        text = re.sub(re.compile('”'), '', re.sub(
                                            re.compile('“'), ' ', text)).strip()
                                        self.foundToday = True
                                        embed = discord.Embed(
                                            title="BC COVID-19 Joint Statement",
                                            description=" ".join(
                                                pyteaser.Summarize(statement.getText(), text)),
                                            colour=discord.Colour.blue()
                                        )
                                        embed.set_author(name=f"Source", url=statement['href'], icon_url=r'https://cdn.discordapp.com/attachments/360564259316301836/747043112043544617/BCGov_-_Horizontal_AGOL_Logo_-_White_-_Sun.png')

                                        await ctx.send(embed=embed)
                                        continue