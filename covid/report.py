from asyncio.tasks import Task
from redbot.core import commands
import discord
import bs4
from urllib.request import urlopen
import re
from bs4.element import PageElement, Tag
import pyteaser
from datetime import datetime, timedelta
import asyncio


class Report(commands.Cog):
    """Start report"""

    def __init__(self):
        self.foundToday = False
        self.firstRun = True
        self.task: Task = None
        self.count = 0

    def stopTask(self):
        if (self.task):
            self.task.cancel()
            self.task = None
            print("report.py: stopped task succesfully")
        else:
            print("report.py: no task to stop")

    @commands.command(pass_context=True)
    @commands.is_owner()
    async def covidreset(self, ctx: commands.Context = None):
        if (not self.task):
            await ctx.send("Task not started")

        self.foundToday = False
        self.firstRun = True
        self.count = 0
        self.stopTask()
        await ctx.send("Task reset success")

    @commands.command(pass_context=True)
    @commands.guild_only()
    @commands.is_owner()
    async def covidstart(self, ctx: commands.Context):
        if (self.task):
            await ctx.send("Already started")
            return

        await ctx.send("Starting task in this channel")
        self.task = asyncio.create_task(self.run(ctx))
        await self.task
        print(self.task.exception())

    async def run(self, ctx: commands.Context):
        while(self.task is not None):
            print(f"Loop task count: {self.count}. Time: {datetime.now()}")
            self.count += 1
            # temporarily wait to prevent untested infinite loops
            await asyncio.sleep(10)
            now: datetime = datetime.now()
            noon: datetime = now.replace(
                hour=12, minute=0, second=0, microsecond=0)
            night: datetime = now.replace(
                hour=22, minute=0, second=0, microsecond=0)
            if (now > noon):
                if (self.foundToday or now > night):
                    # wait for tomorrow if we have today or if it's too late
                    noonTomorrow: datetime = noon + timedelta(days=1)
                    timeUntilNextCheck: float = (
                        noonTomorrow - now).total_seconds()
                    self.foundToday = False  # since next check is tomorrow, next today is false
                else:  # otherwise check every 15 minutes
                    timeUntilNextCheck: float = 750  # 15 minutes
            else:
                timeUntilNextCheck: float = (noon - now).total_seconds()
            if (not self.firstRun):
                print(f"Checking again in: {timeUntilNextCheck} seconds")
                await asyncio.sleep(timeUntilNextCheck)
            self.firstRun = False
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
                                    embed.set_author(
                                        name=f"Source", url=statement['href'], icon_url=r'https://cdn.discordapp.com/attachments/360564259316301836/747043112043544617/BCGov_-_Horizontal_AGOL_Logo_-_White_-_Sun.png')

                                    self.count = 0
                                    await ctx.send(embed=embed)
