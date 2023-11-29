from discord.ext import commands

owners = [236931919063941121, 825704399523282954]


def is_owner():
    async def predicate(ctx: commands.Context):
        return ctx.author.id in owners

    return commands.check(predicate)


class confirm(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot


async def setup(bot):
    await bot.add_cog(confirm(bot))
