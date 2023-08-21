from .sportsday import SportsDay
from .tictactoe import TicTacToe

async def setup(bot):
    await bot.add_cog(SportsDay())
    await bot.add_cog(TicTacToe())
