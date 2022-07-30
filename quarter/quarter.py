from time import time
from redbot.core import commands
import discord
from .crawler import CustomBingCrawler
from .googlecrawler import CustomDownloader, CustomGoogleCrawler, CustomGoogleParser, CustomGoogleFeeder, CustomGoogleFeederSafe
import os
import io
from PIL import Image
from pathlib import Path
import logging
import typing
import random
import math
import glob
import re
import urllib.request
import urllib.parse
import posixpath

root_dir = './CustomCogs/quarter/temp'
running = False
dailyLimit = 100
validURL = re.compile( # https://stackoverflow.com/a/7160778
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)


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
    async def quarter(self, ctx, something: typing.Optional[str] = None, someone: typing.Optional[discord.Member] = None):
        """
        Examples:
        - !quarter trout
        - !quarter "elvis rodriguez"
        """
        global running, dailyLimit

        if (dailyLimit <= self.count):
            await ctx.send(f"{ctx.message.author.mention} QuarterLimit was reached {self.count}/{dailyLimit}, Quarter{something} not retrieved.")
            return

        if (something and len(something) >= 150):
            await ctx.send(f"{ctx.message.author.mention} Your quarter request is too long")
            return

        mention = ctx.message.author.mention
        if (someone):
            mention = someone.mention

        if (not os.path.exists(root_dir)):
            os.makedirs(root_dir)

        if (len(os.listdir(root_dir)) >= 100):
            files = glob.glob(root_dir)
            for i, f in enumerate(files):
                os.remove(f)
                if (i >= 50):
                    break

        if (ctx.message.attachments and not something):
            attachment = ctx.message.attachments[0]
            try:
                self.queue.append((os.path.splitext(attachment.filename)[0], mention, ctx.message.author.mention, 'attachment', await attachment.read(use_cached=True), False, ctx))
            except Exception as e:
                print("Error getting attachment: ", e)
                self.queue.append((os.path.splitext(attachment.filename)[0], mention, ctx.message.author.mention, 'attachment', None, True, ctx))
        elif (not something):
            await ctx.send(f"{ctx.message.author.mention} Usage: !quarter <thing>")
            return
        elif (re.match(validURL, something) is not None):
            try:
                user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
                image_formats = ("image/png", "image/jpeg", "image/gif")

                request = urllib.request.Request(something, headers={'User-Agent': user_agent})
                with urllib.request.urlopen(request) as response:
                    if (response.info()["content-type"] not in image_formats):
                        await ctx.send(f"{ctx.message.author.mention} That wasn't an image")
                        return
                    filename = os.path.splitext(posixpath.basename(urllib.parse.urlsplit(something).path))[0]
                    self.queue.append((filename, mention, ctx.message.author.mention, 'attachment', response.read(), False, ctx))
            except Exception as e:
                print("Error getting url: ", e)
                self.queue.append(('something', mention, ctx.message.author.mention, 'attachment', None, True, ctx))
        else:
            self.queue.append(
                (something, mention, ctx.message.author.mention, 'search', None, False, ctx))
        self.count += 1
        if (running):
            return
        running = True

        async with ctx.typing():
            # create a new one every time because otherwise it's broken

            caller = None
            displayName = None
            try:
                while (self.queue):
                    originalWord, replyTo, caller, queueType, data, error, realCtx = self.queue.pop()
                    self.crawler = CustomGoogleCrawler(
                        storage={'root_dir': root_dir},
                        log_level=20,
                        downloader_cls=CustomDownloader,
                        parser_cls=CustomGoogleParser,
                        feeder_cls=CustomGoogleFeeder if realCtx.channel.is_nsfw() else CustomGoogleFeederSafe
                    )

                    if (error):
                        await realCtx.send(f"{caller} Error getting Quarter{originalWord}")
                        return

                    print(f"Getting {originalWord}")

                    displayName = f"{originalWord.title().replace(' ', '').strip()}"

                    escapedFilename = urllib.parse.quote(
                        originalWord.lower().strip())[0:150]

                    imagePath = os.path.join(root_dir, escapedFilename)
                    if (queueType != 'attachment'):
                        quarter = Path(imagePath)
                        refetch = False
                        if (quarter.exists()):
                            print(f"Cached {originalWord}")
                            last_modification_time = os.stat(quarter).st_mtime
                            current_time = time()
                            if (current_time - last_modification_time > 300):
                                refetch = True
                        else:
                            refetch = True

                        if (refetch):
                            # must download with escaped name so it saves properly
                            self.crawler.crawl(
                                keyword=escapedFilename, max_num=1)

                        if (not quarter.exists()):
                            await realCtx.send(f"{caller} Quarter{displayName} does not exist sorry")
                            continue

                        im = Image.open(imagePath)
                    else:
                        im = Image.open(io.BytesIO(data))

                    width, height = im.size

                    getRegion = bool(random.getrandbits(1))

                    topLimit = 0
                    bottomLimit = height
                    if (getRegion):  # random square region with quarter area
                        region = width * height
                        quarterRegion = math.floor((region/4) ** (1/2))
                        leftRegion = width - quarterRegion
                        leftLimit = random.randint(0, leftRegion if (leftRegion >= 0) else 0)
                        rightLimit = leftLimit + quarterRegion
                        rightRegion = height - quarterRegion
                        topLimit = random.randint(0, rightRegion if (rightRegion >= 0) else 0)
                        bottomLimit = topLimit + quarterRegion
                    else:  # either left middle or right middle
                        moved = random.randint(1, 2)
                        leftLimit = moved * width/4
                        rightLimit = (1 + moved) * width/4
                    cropped = im.convert('RGB').crop(
                        tuple([int(x) for x in [leftLimit, topLimit, rightLimit, bottomLimit]]))
                    cropped.thumbnail((800, 800), Image.ANTIALIAS)
                    with io.BytesIO() as image_binary:
                        cropped.save(image_binary, 'PNG')
                        image_binary.seek(0)

                        print(f"Sending Quarter{displayName}")

                        print(f"QuarterLimit: {self.count}/{dailyLimit}")
                        if (queueType != 'attachment'):
                            link = f"https://goo.gl/search?{urllib.parse.quote(originalWord)}&tbm=isch"
                            if (not realCtx.channel.is_nsfw()):
                                link += "&safe=active"
                        else:
                            link = ""
                        message = f"{replyTo} Quarter{displayName}\n{link}"
                        await ctx.send(message, file=discord.File(fp=image_binary, filename=f"Quarter{escapedFilename}.png"))

                        if (realCtx.channel.is_nsfw()):
                            os.remove(imagePath)
            except Exception as e:
                print("Error getting and serving: ", e)
                await ctx.send(f"{caller} Error getting Quarter{displayName}")

            running = False
