from redbot.core import commands
import discord
from .crawler import CustomBingCrawler
from .googlecrawler import CustomGoogleCrawler, CustomGoogleParser, CustomGoogleFeeder
from .downloader import CustomDownloader
import os
import io
from PIL import Image
from pathlib import Path
import logging
import typing
import random
import math
import glob

root_dir = './CustomCogs/quarter/temp'
running = False
dailyLimit = 100


class Quarter(commands.Cog):
    """Quarter"""

    def __init__(self):
        self.queue = []
        self.count = 0

    @commands.command()
    @commands.is_owner()
    async def quarterdata(self, ctx):
        global dailyLimit
        await ctx.send(f"Count: {self.count}, Limit: {dailyLimit}, Queue: {self.queue}")

    @commands.command()
    @commands.guild_only()
    async def quarter(self, ctx, something: str, someone: typing.Optional[discord.Member] = None):
        """
        Examples:
        - !quarter trout
        - !quarter "elvis rodriguez"
        """
        global running, dailyLimit

        if (dailyLimit <= self.count):
            await ctx.send(f"{ctx.message.author.mention} QuarterLimit was reached {self.count}/{dailyLimit}, Quarter{something.title()} not retrieved.")
            return

        if (len(os.listdir(root_dir)) >= 100):
            files = glob.glob(root_dir)
            for f, i in enumerate(files):
                os.remove(f)
                if (i >= 50):
                    break

        self.queue.append(something)
        self.count += 1
        if (running):
            return
        running = True

        async with ctx.typing():
            # create a new one every time because otherwise it's broken
            self.crawler = CustomGoogleCrawler(
                storage={'root_dir': root_dir},
                log_level=20,
                downloader_cls=CustomDownloader,
                parser_cls=CustomGoogleParser,
                feeder_cls=CustomGoogleFeeder
            )
            while (self.queue):
                word = self.queue.pop()
                print(f"Getting {word}")
                imagePath = os.path.join(root_dir, word.lower())
                quarter = Path(imagePath)
                if (quarter.exists()):
                    print(f"Cached {word}")
                else:
                    self.crawler.crawl(keyword=word, max_num=1)

                filename = f"{word.title().replace(' ', '')}"

                if (not quarter.exists()):
                    await ctx.send(f"{ctx.message.author.mention} Quarter{filename} does not exist sorry")
                    continue

                im = Image.open(imagePath)
                width, height = im.size

                getRegion = bool(random.getrandbits(1))

                topLimit = 0
                bottomLimit = height
                if (getRegion):  # random square region with quarter area
                    region = width * height
                    quarterRegion = math.floor((region/4) ** (1/2))
                    leftLimit = random.randint(0, width - quarterRegion)
                    rightLimit = leftLimit + quarterRegion
                    topLimit = random.randint(0, height - quarterRegion)
                    bottomLimit = topLimit + quarterRegion
                else:  # either left middle or right middle
                    moved = random.randint(1, 2)
                    leftLimit = moved * width/4
                    rightLimit = (1 + moved) * width/4
                cropped = im.convert('RGB').crop(
                    (leftLimit, topLimit, rightLimit, bottomLimit))
                cropped.thumbnail((800, 800), Image.ANTIALIAS)
                with io.BytesIO() as image_binary:
                    cropped.save(image_binary, 'PNG')
                    image_binary.seek(0)

                    print(f"Sending Quarter{filename}")
                    replyTo = ctx.message.author.mention
                    if (someone):
                        replyTo = someone.mention

                    print(f"QuarterLimit: {self.count}/{dailyLimit}")
                    message = f"{replyTo} Quarter{filename} "
                    await ctx.send(message, file=discord.File(fp=image_binary, filename=f"Quarter{filename}.png"))

            running = False
