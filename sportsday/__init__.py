from .sportsday import SportsDay
from .tictactoe import TicTacToe

def setup(bot):
    bot.add_cog(SportsDay())
    bot.add_cog(TicTacToe())
