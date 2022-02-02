from typing import NamedTuple
from redbot.core import commands
import discord
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import json
import traceback

from datetime import datetime, timedelta
from prettytable import PrettyTable

from asyncio.tasks import Task
from redbot.core import commands
import discord
import bs4
from urllib.request import urlopen
import re
from bs4.element import PageElement, ResultSet, Tag
from markdownify import markdownify as md
from datetime import datetime, timedelta
import asyncio

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
# from https://stackoverflow.com/a/1359152
possible_numbers = '|'.join(nums.keys()) + '|' + r'\d{1,3}(?:[,]\d{3})*'

hospitalization_icu_re = re.compile(f'Of the active cases, ({possible_numbers}) .* individuals .* hospital and ({possible_numbers}) .* intensive care.')

def case_count_text_to_number(text: str):
    if (text.isdigit()):
        return int(text)

    as_number_text = nums.get(text)
    if (as_number_text):
        return as_number_text

    searched = re.search(possible_numbers, text)

    if (searched):
        return nums.get(searched.group()) or 0
    
    return 0

def sum_case_counts(list_elements: ResultSet):
    case_count = 0
    active_case_count = 0
    for elm in list_elements:
        cases = next(elm.stripped_strings)
        split = cases.split(' ')
        if (len(split)):
            for (i, word) in enumerate(split):
                if (i + 1 < len(split) - 1 and split[i + 1 == 'new']):
                    case_count += case_count_text_to_number(word.replace(',', ''))
                elif (i > 1 and split[i - 1] == 'cases:'):
                    active_case_count += case_count_text_to_number(word.replace(',', ''))

    return (active_case_count, case_count)


def generate_case_count_section(info: bs4.BeautifulSoup, article: Tag):
    elms1: Tag = info.new_tag('div')
    elms2: Tag = info.new_tag('div')
    summary_ul: Tag = None
    general_case_counts: Tag = None
    article_iter = iter(article)
    for elm in article_iter:
        if (not summary_ul and re.match(r"Over a .* period,", elm.getText())):
            summary_ul = next(article_iter)
        else:
            if (elm.name == 'ul'):
                if (general_case_counts is None):
                    general_case_counts = elm
                else:
                    elms2.append(elm)
            else:
                if (general_case_counts is None):
                    elms1.append(elm)
                    pass
                else:
                    elms2.append(elm)
    list_elements = general_case_counts.find_all('li')
    active_case_count, case_count = sum_case_counts(list_elements)
    summary_string = f"{md(str(summary_ul))}\n" if summary_ul else ""
    case_count_string = f"Total new: {case_count}"
    active_case_count_string = f"Total active: {active_case_count}" if active_case_count > case_count else ""

    article_as_text = str(article)
    hospital_info = hospitalization_icu_re.search(article_as_text)
    hospital_string = ""
    icu_string = ""
    if (hospital_info):
        hospital_count, icu_count = hospital_info.group(1, 2)
        if (hospital_count and icu_count):
            hospital_count_removed_commas = hospital_count.replace(',', '')
            if (hospital_count_removed_commas.isdigit()):
                hospital_count = int(hospital_count_removed_commas)
            else:
                hospital_count = nums.get(hospital_count) or 0

            icu_count_removed_commas = icu_count.replace(',', '')
            if (icu_count_removed_commas.isdigit()):
                icu_count = int(icu_count_removed_commas)
            else:
                icu_count = nums.get(icu_count) or 0

            hospital_string = f"Total hospitalized: {hospital_count}\n"
            icu_string = f"Total intensive care: {icu_count}\n"

    return (
        elms1,
        f"```md\n{summary_string}{md(str(general_case_counts))}\n{case_count_string}\n{active_case_count_string}\n{hospital_string}{icu_string}```",
        elms2
    )

class Site(NamedTuple):
    info: bs4.BeautifulSoup
    article: ResultSet[Tag]
    locatedTime: Tag
    link: str

def scrape_website(provided_date=None):
    with urlopen('https://news.gov.bc.ca/ministries/health') as directoryUrl:
        directory = bs4.BeautifulSoup(
            directoryUrl, features="html.parser")

        todayString = (provided_date or datetime.now()).strftime(r"%B %#d, %Y")
        dates = directory.find_all(
            name='span', attrs={"class": "item-date"}, text=re.compile(f"{todayString}.*"))
        statement: PageElement = None
        for date in dates:
            located: PageElement = date.parent.parent.find(
                name='a', href=True, text=re.compile(f".*COVID-19.*update"))
            if (located):
                located_time = date
                statement = located
                break

        if (statement and statement['href']):
            with urlopen(statement['href']) as infoUrl:
                info = bs4.BeautifulSoup(
                    infoUrl, features="html.parser")
                textElement: ResultSet[Tag] = info.select(
                    selector=".story-expander > article > *")

                if (textElement):
                    return Site(info, textElement, located_time, str(statement['href']))

    return None

def get_case_attr(attr, param):
    return int(attr.get(param) or 0)

class Covid(commands.Cog):
    """Gets BC COVID-19 data"""

    def __init__(self):
        self.since_last_got_data = None
        self.cached_data_response = None
        self.found_report_today = False
        self.is_first_report_run = True
        self.report_task: Task = None
        self.scrape_count = 0
        self.cached_report = None
        self.cached_report_time = None

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def covid(self, ctx: commands.Context, *args):
        """Get latest BC COVID data"""

        if (self.cached_data_response and self.since_last_got_data and datetime.now() - self.since_last_got_data < timedelta(seconds=30)):
            await ctx.send(embed=await self.parse_covid_data(self.cached_data_response))
            return

        queries = {
            "where": "1=1",
            "time": f"\'{datetime.now().strftime('%m/%d/%Y')}\'",
            "outFields": "HA_Name, NewCases, Date_Updat, ActiveCases, CurrentlyICU, CurrentlyHosp",
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
                self.cached_data_response = data
                self.since_last_got_data = datetime.now()
                await ctx.send(embed=await self.parse_covid_data(data))
            except Exception as e:
                traceback.print_exc()
                print(url)
                print(data)
                await ctx.send(f"{ctx.message.author.mention} Sorry, there was an error getting the data.")

    async def parse_covid_data(self, data):
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

        data_updated_at = datetime.fromtimestamp(date // 1000)

        # if self.cached_report_time and data_updated_at < self.cached_report_time:
            # return self.cached_report

        dateString = data_updated_at.strftime("%B %#d at %#I:%M%p")
        daysSince = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) -
                     data_updated_at.replace(hour=0, minute=0, second=0, microsecond=0)).days

        if (daysSince == 1):
            dateDiff = "Yesterday"
        elif (daysSince > 1):
            dateDiff = f"{daysSince} days ago"
        else:
            dateDiff = "Today"

        embed = discord.Embed(
            title="BC COVID-19 Case Numbers",
            colour=discord.Colour.blue()
        )

        totalNew = 0
        totalActive = 0
        totalICU = 0
        totalHospitalizations = 0
        date = 0

        regions, newCases, activeCases, icuCases, hospitalizedCases = ([], [], [], [], [])
        for element in data['features']:
            attr = element['attributes']

            newCasesToday = get_case_attr(attr, 'NewCases')
            activeCasesToday = get_case_attr(attr, 'ActiveCases')
            icuToday = get_case_attr(attr, 'CurrentlyICU')
            region = attr['HA_Name']
            hospToday = get_case_attr(attr, 'CurrentlyHosp')

            totalNew += newCasesToday
            totalActive += activeCasesToday
            totalICU += icuToday
            totalHospitalizations += hospToday

            date = max(date, int(attr['Date_Updat']))

            newCases.append(newCasesToday)
            activeCases.append(activeCasesToday)
            icuCases.append(icuToday)
            hospitalizedCases.append(hospToday)

            # if needed, this can be used to reduce the length of HA region names
            regionShort = {}
            thisRegionShort = regionShort.get(region) or region

            if (region == 'Vancouver Coastal'):
                regions.append(f"* {thisRegionShort}")
            else:
                regions.append(thisRegionShort)

        regions.append('# Total')
        newCases.append(totalNew)
        activeCases.append(totalActive)
        icuCases.append(totalICU)
        hospitalizedCases.append(totalHospitalizations)

        table = PrettyTable(
            field_names=["# Region", "New", "Active", "ICU", "Hospital"])
        table.add_rows(zip(regions, newCases, activeCases, icuCases, hospitalizedCases))
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

    @commands.is_owner()
    @covid.command()
    async def report_cancel(self, ctx: commands.Context):
        if (not self.report_task):
            return

        self.found_report_today = False
        self.is_first_report_run = True
        self.scrape_count = 0
        self.stop_report_task()
        await ctx.message.delete()
        print("covid report task canceled")

    @commands.is_owner()
    @covid.command()
    async def report_start(self, ctx: commands.Context):
        if (self.report_task):
            return

        self.report_task = asyncio.create_task(self.run_scrape_task(ctx))
        await ctx.message.delete()
        await self.report_task
        print(self.report_task.exception())

    def stop_report_task(self):
        if (self.report_task):
            self.report_task.cancel()
            self.report_task = None
            print("covid report: stopped task succesfully")
        else:
            print("covid report: no task to stop")

    async def run_scrape_task(self, ctx: commands.Context):
        while(self.report_task is not None):
            self.scrape_count += 1
            print(
                f"Loop task count: {self.scrape_count}. Time: {datetime.now()}")
            now: datetime = datetime.now()
            noon: datetime = now.replace(
                hour=12, minute=0, second=0, microsecond=0)
            night: datetime = now.replace(
                hour=22, minute=0, second=0, microsecond=0)
            timeUntilNextCheck: float
            if (now > noon):
                if (self.found_report_today or now > night or noon.date().weekday() in [6, 7]):
                    # wait for tomorrow if we have today or if it's too late
                    nextCheck: datetime = noon + timedelta(days=1)
                    timeUntilNextCheck = (
                        nextCheck - now).total_seconds()
                    self.found_report_today = False  # since next check is tomorrow, next today is false
                else:
                    timeUntilNextCheck = 750  # 15 minutes
            else:
                timeUntilNextCheck = (noon - now).total_seconds()
            if (not self.is_first_report_run):
                print(f"Checking again in: {timeUntilNextCheck} seconds")
                await asyncio.sleep(timeUntilNextCheck)
            self.is_first_report_run = False
            scrape_result = scrape_website()

            if (scrape_result):
                _, case_count_section, _ = generate_case_count_section(
                    scrape_result.info, scrape_result.article)

                # text: str = f"{md(str(elms1))}{case_count_section}{md(str(elms2))}"
                # concatenateEnd: int = text.rfind("**Learn More:")
                # if (concatenateEnd > -1):
                # text = text[:concatenateEnd].strip()
                self.found_report_today = True
                embed = discord.Embed(
                    title="BC COVID-19 Pandemic Update",
                    description=case_count_section,
                    colour=discord.Colour.blue()
                )

                embed.set_author(
                    name=f"Source", url=scrape_result.link, icon_url=r'https://cdn.discordapp.com/attachments/360564259316301836/747043112043544617/BCGov_-_Horizontal_AGOL_Logo_-_White_-_Sun.png')

                statement_updated_at = scrape_result.locatedTime.getText()

                try:
                    self.cached_report_time = datetime.strptime(
                        statement_updated_at, r"%A, %B %d, %Y %I:%M %p")
                except ValueError as e:
                    print(e)
                    self.cached_report_time = datetime.now()

                embed.set_footer(
                    text=f"Updated {statement_updated_at}")

                self.scrape_count = 0
                self.cached_report = embed

                await ctx.send(embed=embed)

            # prevent untested infinite loops
            await asyncio.sleep(10)
