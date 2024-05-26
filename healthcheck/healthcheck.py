from redbot.core import commands, bot
from discord import Message


class HealthCheck(commands.Cog):
    def __init__(self, bot: bot.Red):
        self.bot = bot

    @commands.Cog.listener(name="on_message_without_command")
    async def on_message_without_command(self, message: Message):
        if message.content == "!healthcheck":
            await message.reply("OK")
