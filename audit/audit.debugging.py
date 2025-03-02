from redbot.core import bot, data_manager
from redbot.core._cli import parse_cli_flags
from discord import Embed, Permissions
from audit import Audit

data_manager.create_temp_config()

data_manager.load_basic_configuration("TestingBot")

cli_flags = parse_cli_flags([])

testing_bot = bot.Red(cli_flags=cli_flags)

audit_cog = Audit(bot=testing_bot)

embed = Embed()
audit_cog.handle_permission_values("allow", embed, Permissions(0), Permissions(1))
for field in embed.fields:
    print(field.name)
    print(field.value)
