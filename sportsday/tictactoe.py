from redbot.core import commands, bank
from redbot.core.utils.predicates import MessagePredicate, ReactionPredicate
import discord
import random
import asyncio


class TicTacToe(commands.Cog):
    """Sports Day"""

    def __init__(self):
        self.options = (('1'), ('2'), ('3'), ('4'),
                        ('5'), ('6'), ('7'), ('8'), ('9'))
        self.extraMessage = None
        self.gameMessage = None
        self.playing = False
        self.bjPlayerName = ""
        self.bjPlayer = None
        self.vkPlayerName = ""
        self.vkPlayer = None
        self.sportsdaybj = None
        self.sportsdayvk = None
        self.players = {}
        self.waiting = False
        self.filledSquares = 0
        self.board = [0 for _ in range(9)]
        self.channel = None
        self.wager = 0
        self.gameMessage = None
        self.extraMessage = None
        self.contentMessage = None
        self.resetGame()

    @commands.group(autohelp=True)
    @commands.guild_only()
    async def tic(self, ctx: commands.Context):
        """Tic Tac Sports Day"""
        pass

    @tic.command()
    async def start(self, ctx: commands.Context, wager: int = 0):
        if (self.channel and ctx.channel != self.channel):
            return await ctx.send(f"TicTacToe is being played in {self.channel.name}")

        self.channel = ctx.channel

        if (not self.sportsdaybj or not self.sportsdayvk):
            self.sportsdaybj = str(discord.utils.get(
                ctx.guild.emojis, name='sportsdaybj'))
            self.sportsdayvk = str(discord.utils.get(
                ctx.guild.emojis, name='sportsdayvik'))

        if (self.playing):
            return await ctx.send(f"{self.bjPlayerName} is playing with {self.vkPlayerName} right now")

        if (self.waiting):
            if (self.wager):
                return await ctx.send(f"{self.bjPlayerName if self.bjPlayerName else self.vkPlayerName} is waiting for a player willing to wager {self.wager} credits. Type !tic join to join.")
            return await ctx.send(f"{self.bjPlayerName if self.bjPlayerName else self.vkPlayerName} is waiting for a player. Type !tic join to join.")

        minwager = 10
        maxwager = 1000
        if (wager and not (minwager <= wager <= maxwager)):
            return await ctx.send(f"Minimum wager is {minwager} and maximum wager is {maxwager}")
        else:
            try:
                await bank.withdraw_credits(member=ctx.message.author, amount=wager)
            except ValueError:
                return await ctx.send(f"{ctx.message.author.mention} You do not have enough credits")

        self.waiting = True
        self.wager = wager

        if (bool(random.getrandbits(1))):
            self.bjPlayerName = ctx.message.author.display_name
            self.bjPlayer = ctx.message.author
            if (self.wager):
                await ctx.send(f"{ctx.message.author.display_name} is {self.sportsdaybj} wagering {self.wager} credits. Waiting for {self.sportsdayvk} with !tic join.")
            else:
                await ctx.send(f"{ctx.message.author.display_name} is {self.sportsdaybj}. Waiting for {self.sportsdayvk} with !tic join.")
        else:
            self.vkPlayerName = ctx.message.author.display_name
            self.vkPlayer = ctx.message.author
            if (self.wager):
                await ctx.send(f"{ctx.message.author.display_name} is {self.sportsdayvk} wagering {self.wager} credits. Waiting for {self.sportsdaybj} with !tic join.")
            else:
                await ctx.send(f"{ctx.message.author.display_name} is {self.sportsdayvk}. Waiting for {self.sportsdaybj} with !tic join.")

        self.cancellationTask = asyncio.create_task(self.timeoutJoin(ctx))

    async def timeoutJoin(self, ctx: commands.Context):
        await asyncio.sleep(25.0)
        await ctx.send(f"{ctx.author.mention} nobody joined")
        if (self.wager):
            await bank.deposit_credits(member=ctx.author, amount=self.wager)
        return self.resetGame()

    @tic.command()
    async def join(self, ctx: commands.Context):
        if (self.channel and ctx.channel != self.channel):
            return await ctx.send(f"TicTacToe is being played in {self.channel.name}")

        if (not self.bjPlayerName and not self.vkPlayerName):
            return await ctx.send(f"!tic start to start a game")
        elif (ctx.author == self.bjPlayer):
            return await ctx.send(f"You're already in the race as {self.sportsdaybj}")
        elif (ctx.author == self.vkPlayer):
            return await ctx.send(f"You're already in the race as {self.sportsdayvk}")

        try:
            await bank.withdraw_credits(member=ctx.message.author, amount=self.wager)
        except ValueError:
            return await ctx.send(f"{ctx.message.author.mention} You do not have enough credits")

        self.cancellationTask.cancel()
        if (self.vkPlayerName):
            self.bjPlayerName = ctx.message.author.display_name
            self.bjPlayer = ctx.message.author
            await ctx.send(f"{ctx.message.author.display_name} is {self.sportsdaybj}.")
        else:
            self.vkPlayerName = ctx.message.author.display_name
            self.vkPlayer = ctx.message.author
            await ctx.send(f"{ctx.message.author.display_name} is {self.sportsdayvk}.")

        self.playing = True
        await self.startGame(ctx)

    async def printBoard(self, ctx: commands.Context, extraText: str = 'GAME OVER'):
        output = ""
        for i, item in enumerate(self.board):
            if item:
                output += item
            else:
                output += f"{ReactionPredicate.NUMBER_EMOJIS[i + 1]}"
            if (i in [2, 5]):
                output += "\n"

        if (self.extraMessage and self.contentMessage):
            await self.extraMessage.edit(content=extraText)
            await self.contentMessage.edit(content=output)
        else:
            self.extraMessage = await ctx.send(extraText)
            self.contentMessage = await ctx.send(output)


    async def getInput(self, ctx: commands.Context, turn):
        position = MessagePredicate.contained_in(
            self.options, channel=ctx.channel, user=turn)
        try:
            choice = await ctx.bot.wait_for("message", check=position, timeout=5.0)
        except asyncio.TimeoutError:
            return None

        return int(choice.content)

    def resetGame(self):
        self.__init__()

    def checkWin(self):
        for i in range(0, 9, 3):
            if (self.board[i] == self.board[i + 1] and self.board[i] == self.board[i + 2]):
                return self.board[i]

        for i in range(3):
            if (self.board[i] == self.board[i + 3] and self.board[i] == self.board[i + 6]):
                return self.board[i]

        if (self.board[0] == self.board[4] and self.board[0] == self.board[8]):
            return self.board[0]

        if (self.board[2] == self.board[4] and self.board[2] == self.board[6]):
            return self.board[2]

        return None

    async def startGame(self, ctx: commands.Context):
        self.players['current'] = self.sportsdayvk
        self.players['other'] = self.sportsdaybj
        currentPlayer = self.vkPlayer
        while True:
            extraText = ""
            if (currentPlayer == self.bjPlayer):
                self.players['current'] = self.sportsdayvk
                self.players['other'] = self.sportsdaybj
                currentPlayer = self.vkPlayer
                extraText = f"{self.sportsdayvk}'s turn"
            else:
                self.players['current'] = self.sportsdaybj
                self.players['other'] = self.sportsdayvk
                currentPlayer = self.bjPlayer
                extraText = f"{self.sportsdaybj}'s turn"
            await self.printBoard(ctx, extraText)
            taken = True
            while(taken):
                response = await self.getInput(ctx, currentPlayer)
                if (response):
                    if (not self.board[response - 1]):
                        taken = False
                        self.board[response - 1] = self.players['current']
                        self.filledSquares += 1
                        winner = self.checkWin()

                        if (winner):
                            await self.printBoard(ctx)
                            winnerPlayer, loserPlayer = None, None
                            if (winner == self.sportsdaybj):
                                await ctx.send(f"WINNER! {winner} {self.bjPlayerName}")
                                winnerPlayer = self.bjPlayer
                            else:
                                await ctx.send(f"WINNER! {winner} {self.vkPlayerName}")
                                winnerPlayer = self.vkPlayer
                            if (self.wager):
                                amountWon = int(self.wager * 2 * 0.97)
                                await bank.deposit_credits(member=winnerPlayer, amount=amountWon)
                                await ctx.send(f"{winnerPlayer.mention} wins {amountWon}")
                            return self.resetGame()
                        elif (self.filledSquares == 9):
                            await self.printBoard(ctx)

                            if (self.wager):
                                await bank.deposit_credits(member=self.vkPlayer, amount=self.wager)
                                await bank.deposit_credits(member=self.bjPlayer, amount=self.wager)
                                await ctx.send(f"DRAW! Credits refunded")
                            else:
                                await ctx.send(f"DRAW!")
                            return self.resetGame()
                    else:
                        await ctx.send("That position is taken, try again")
                else:
                    reply = f"{self.players['current']} took too long\n"
                    winner = self.players['other']
                    if (winner == self.sportsdaybj):
                        await ctx.send(reply + f"WINNER! {winner} {self.bjPlayerName}")
                        winnerPlayer = self.bjPlayer
                    else:
                        await ctx.send(reply + f"WINNER! {winner} {self.vkPlayerName}")
                        winnerPlayer = self.vkPlayer
                    if (self.wager):
                        amountWon = int(self.wager * 2 * 0.97)
                        await bank.deposit_credits(member=winnerPlayer, amount=amountWon)
                        await ctx.send(f"{winnerPlayer.mention} wins {amountWon}")
                    return self.resetGame()
