from asyncio.tasks import Task
from redbot.core import commands
import discord
import bs4
from urllib.request import urlopen
import re
from bs4.element import PageElement, Tag
from markdownify import markdownify as md
from datetime import datetime, timedelta
import asyncio
import traceback


class pyteaser:
    @staticmethod
    def Summarize(text):
        return text


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
    async def covidreset(self, ctx: commands.Context):
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
            timeUntilNextCheck: float
            if (now > noon):
                if (self.foundToday or now > night or noon.date().weekday() in [6, 7]):
                    # wait for tomorrow if we have today or if it's too late
                    nextCheck: datetime = noon + timedelta(days=1)
                    timeUntilNextCheck = (
                        nextCheck - now).total_seconds()
                    self.foundToday = False  # since next check is tomorrow, next today is false
                else:
                    timeUntilNextCheck = 750  # 15 minutes
            else:
                timeUntilNextCheck = (noon - now).total_seconds()
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
                        name='a', href=True, text=re.compile(f".*COVID-19.*update"))
                    if (located):
                        statement = located
                        break

                if (statement and statement['href']):
                    nums = {
                        "no": 0,
                        "zero": 0,
                        "one": 1,
                        "two": 2,
                        "three": 3,
                        "four": 4,
                        "five": 5,
                        "six": 6,
                        "seven": 7,
                        "eight": 8,
                        "nine": 9
                    }
                    with urlopen(statement['href']) as infoUrl:
                        info = bs4.BeautifulSoup(
                            infoUrl, features="html.parser")
                        textElement: Tag = info.select(
                            selector=".story-expander > article > *")

                        if (textElement):
                            elms1: Tag = info.new_tag('div')
                            elms2: Tag = info.new_tag('div')
                            ul: Tag = None
                            for elm in textElement:
                                if (elm.name == 'ul'):
                                    if (ul is None):
                                        ul = elm
                                    else:
                                        elms2.append(elm)
                                else:
                                    if (ul is None):
                                        elms1.append(elm)
                                        pass
                                    else:
                                        elms2.append(elm)
                            caseCount = 0
                            for elm in ul.find_all('li', recursive=False):
                                cases = next(elm.stripped_strings)
                                split = cases.split(' ')
                                if (len(split)):
                                    try:
                                        caseCount += int(split[0])
                                    except ValueError:
                                        caseCount += nums.get(split[0]) or 0
                            caseCountSection = f"```md\n{md(str(ul))}\nTotal new: {caseCount}```\n"
                            text: str = f"{md(str(elms1))}{caseCountSection}{md(str(elms2))}"
                            concatenateEnd: int = text.rfind(
                                "**Learn More:")
                            if (concatenateEnd > -1):
                                text = text[:concatenateEnd].strip()
                                self.foundToday = True
                                embed = discord.Embed(
                                    title="BC COVID-19 Pandemic Update",
                                    description=caseCountSection,
                                    colour=discord.Colour.blue()
                                )
                                embed.set_author(
                                    name=f"Source", url=statement['href'], icon_url=r'https://cdn.discordapp.com/attachments/360564259316301836/747043112043544617/BCGov_-_Horizontal_AGOL_Logo_-_White_-_Sun.png')

                                self.count = 0
                                await ctx.send(embed=embed)
