from redbot.core import commands
from redbot.core.utils.predicates import MessagePredicate, ReactionPredicate
import discord
import random
import asyncio


class TicTacToe(commands.Cog):
    """Sports Day"""

    def __init__(self):
        self.playing = False
        self.bj = ""
        self.bjPlayer = None
        self.vk = ""
        self.vkPlayer = None
        self.sportsdaybj = None
        self.sportsdayvk = None
        self.board = [0 for _ in range(9)]
        self.options = (('1'), ('2'), ('3'), ('4'),
                        ('5'), ('6'), ('7'), ('8'), ('9'))
        self.players = {}

    @commands.group(autohelp=True)
    @commands.guild_only()
    async def tic(self, ctx: commands.Context):
        """Tic Tac Sports Day"""
        pass

    @tic.command()
    async def start(self, ctx: commands.Context):
        if (not self.sportsdaybj or not self.sportsdayvr):
            self.sportsdaybj = str(discord.utils.get(
                ctx.guild.emojis, name='sportsdaybj'))
            self.sportsdayvk = str(discord.utils.get(
                ctx.guild.emojis, name='sportsdayvik'))

        if (self.playing):
            return await ctx.send(f"{self.bj} is playing with {self.vk} right now")

        if (bool(random.getrandbits(1))):
            self.bj = ctx.message.author.display_name
            self.bjPlayer = ctx.message.author
            await ctx.send(f"{ctx.message.author.display_name} is {self.sportsdaybj}. Waiting for {self.sportsdayvk} with [p]tic join.")
        else:
            self.vk = ctx.message.author.display_name
            self.vkPlayer = ctx.message.author
            await ctx.send(f"{ctx.message.author.display_name} is {self.sportsdayvk}. Waiting for {self.sportsdaybj} with [p]tic join.")

    @tic.command()
    async def join(self, ctx: commands.Context):
        if (not self.bj and not self.vk):
            return await ctx.send(f"[p]tic start to start a game")
        elif (ctx.author == self.bjPlayer):
            return await ctx.send(f"You're already in the race as {self.sportsdaybj}")
        elif (ctx.author == self.vkPlayer):
            return await ctx.send(f"You're already in the race as {self.sportsdayvk}")

        if (self.vk):
            self.bj = ctx.message.author.display_name
            self.bjPlayer = ctx.message.author
            await ctx.send(f"{ctx.message.author.display_name} is {self.sportsdaybj}.")
        else:
            self.vk = ctx.message.author.display_name
            self.vkPlayer = ctx.message.author
            await ctx.send(f"{ctx.message.author.display_name} is {self.sportsdayvk}.")

        self.playing = True
        await self.startGame(ctx)

    async def printBoard(self, ctx: commands.Context):
        output = ""
        counter = 0
        for i, item in enumerate(self.board):
            if item:
                output += item
            else:
                output += f"{ReactionPredicate.NUMBER_EMOJIS[i + 1]}"
            if (i in [2, 5]):
                output += "\n"
        await ctx.send(output)

    async def getInput(self, ctx: commands.Context, turn):
        position = MessagePredicate.contained_in(
            self.options, channel=ctx.channel, user=turn)
        print(turn)
        try:
            choice = await ctx.bot.wait_for("message", check=position, timeout=35.0)
        except asyncio.TimeoutError:
            return None

        return int(choice.content)

    async def startGame(self, ctx: commands.Context):
        self.players['current'] = self.sportsdayvk
        self.players['other'] = self.sportsdaybj
        currentPlayer = self.vkPlayer
        while True:
            await self.printBoard(ctx)
            if (currentPlayer == self.bjPlayer):
                self.players['current'] = self.sportsdayvk
                self.players['other'] = self.sportsdaybj
                currentPlayer = self.vkPlayer
                await ctx.send(f"{self.sportsdayvk}'s turn")
            else:
                self.players['current'] = self.sportsdaybj
                self.players['other'] = self.sportsdayvk
                currentPlayer = self.bjPlayer
                await ctx.send(f"{self.sportsdaybj}'s turn")
            taken = True
            while(taken):
                response = await self.getInput(ctx, currentPlayer)
                if (response):
                    if (not self.board[response - 1]):
                        taken = False
                        self.board[response - 1] = self.players['current']
                    else:
                        await ctx.send("That position is taken, try again")
                else:
                    return await ctx.send(f"{self.players['current']} took too long, {self.players['other']} wins")
