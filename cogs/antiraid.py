import humanfriendly, datetime, discord
from discord.ext import commands
from extensions.control import Perms
from extensions.utilities import Whitelist


class AntiRaid(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self.massjoin_cooldown = 10
        self.massjoin_cache = {}

    @commands.Cog.listener("on_member_join")
    async def no_avatar(self, member: discord.Member):
        if not member.avatar:
            check = await self.bot.db.fetchrow(
                "SELECT * FROM antiraid WHERE command = $1 AND guild_id = $2",
                "defaultavatar",
                member.guild.id,
            )
            if check is not None:
                res1 = await self.bot.db.fetchrow(
                    "SELECT * FROM whitelist WHERE guild_id = $1 AND module = $2 AND object_id = $3 AND mode = $4",
                    member.guild.id,
                    "defaultavatar",
                    member.id,
                    "user",
                )
                if res1:
                    return
                if check["punishment"] == "kick":
                    return await member.kick(
                        reason="AntiRaid: No avatar triggered for this user"
                    )
                elif check["punishment"] == "ban":
                    return await member.ban(
                        reason="AntiRaid: No avatar triggered for this user"
                    )

    @commands.Cog.listener("on_member_join")
    async def alt_joined(self, member: discord.Member):
        check = await self.bot.db.fetchrow(
            "SELECT * FROM antiraid WHERE command = $1 AND guild_id = $2",
            "newaccounts",
            member.guild.id,
        )
        if check is not None:
            res1 = await self.bot.db.fetchrow(
                "SELECT * FROM whitelist WHERE guild_id = $1 AND module = $2 AND object_id = $3 AND mode = $4",
                member.guild.id,
                "newaccounts",
                member.id,
                "user",
            )
            if res1:
                return
            if (
                datetime.datetime.now() - member.created_at.replace(tzinfo=None)
            ).total_seconds() <= int(check["seconds"]):
                if check["punishment"] == "kick":
                    return await member.kick(
                        reason="AntiRaid: Account too young to be allowed"
                    )
                elif check["punishment"] == "ban":
                    return await member.ban(
                        reason="AntiRaid: Account too young to be allowed"
                    )

    @commands.Cog.listener("on_member_join")
    async def mass_joins(self, member: discord.Member):
        check = await self.bot.db.fetchrow(
            "SELECT * FROM antiraid WHERE command = $1 AND guild_id = $2",
            "massjoin",
            member.guild.id,
        )
        if check:
            if not self.massjoin_cache.get(str(member.guild.id)):
                self.massjoin_cache[str(member.guild.id)] = []
            self.massjoin_cache[str(member.guild.id)].append(
                tuple([datetime.datetime.now(), member.id])
            )
            expired = [
                mem
                for mem in self.massjoin_cache[str(member.guild.id)]
                if (datetime.datetime.now() - mem[0]).total_seconds()
                > self.massjoin_cooldown
            ]
            for m in expired:
                self.massjoin_cache[str(member.guild.id)].remove(m)
            if len(self.massjoin_cache[str(member.guild.id)]) > check["seconds"]:
                members = [me[1] for me in self.massjoin_cache[str(member.guild.id)]]
                for mem in members:
                    if check["punishment"] == "ban":
                        try:
                            await member.guild.ban(
                                user=self.bot.get_user(mem),
                                reason="AntiRaid: Join raid triggered",
                            )
                        except:
                            continue
                    else:
                        try:
                            await member.guild.kick(
                                user=member.guild.get_member(mem),
                                reason="AntiRaid: Join raid triggered",
                            )
                        except:
                            continue

    @commands.hybrid_group(invoke_without_command=True)
    async def antiraid(self, ctx: commands.Context):
        await ctx.create_pages()

    @antiraid.command(
        aliases=["stats"],
        help="check antiraid settings",
        name="settings",
    )
    async def antiraid_settings(self, ctx: commands.Context):
        settings_enabled = {
            "massjoin": self.bot.no,
            "defaultavatar": self.bot.no,
            "newaccounts": self.bot.no,
        }
        results = await self.bot.db.fetch(
            "SELECT command FROM antiraid WHERE guild_id = $1", ctx.guild.id
        )
        for result in results:
            if settings_enabled.get(result[0]):
                settings_enabled[result[0]] = self.bot.yes
        embed = discord.Embed(
            color=self.bot.color,
            description="\n".join(
                [
                    f"**{m}:** {settings_enabled.get(m)}"
                    for m in ["massjoin", "defaultavatar", "newaccounts"]
                ]
            ),
        )
        embed.set_author(name=f"antiraid settings for {ctx.guild.name}")
        embed.set_thumbnail(url=ctx.guild.icon)
        await ctx.reply(embed=embed)

    @antiraid.command(
        brief="server owner",
        aliases=["wl"],
        help="whitelist an user so they can use antiraid commands",
        usage="[member]",
    )
    @Perms.server_owner()
    async def whitelist(self, ctx: commands.Context, *, member: discord.Member):
        check = await self.bot.db.fetchrow(
            "SELECT * FROM whitelist WHERE guild_id = $1 AND object_id = $2 AND module = $3 AND mode = $4",
            ctx.guild.id,
            member.id,
            "antiraid",
            "user",
        )
        if check:
            return await ctx.send_warning(
                f"**{member}** is already whitelisted for **anti raid**"
            )
        await self.bot.db.execute(
            "INSERT INTO whitelist VALUES ($1,$2,$3,$4)",
            ctx.guild.id,
            "antiraid",
            member.id,
            "user",
        )
        return await ctx.send_success(
            f"**{member}** is now whitelisted and can use **antiraid** commands"
        )

    @antiraid.command(
        brief="server owner",
        aliases=["uwl"],
        help="unwhitelist an user from antiraid commands",
        usage="[member]",
    )
    @Perms.server_owner()
    async def unwhitelist(self, ctx: commands.Context, *, member: discord.User):
        check = await self.bot.db.fetchrow(
            "SELECT * FROM whitelist WHERE guild_id = $1 AND object_id = $2 AND module = $3 AND mode = $4",
            ctx.guild.id,
            member.id,
            "antiraid",
            "user",
        )
        if not check:
            return await ctx.send_warning(
                f"**{member}** is not whitelisted for **anti raid**"
            )
        await self.bot.db.execute(
            "DELETE FROM whitelist WHERE guild_id = $1 AND object_id = $2 AND module = $3",
            ctx.guild.id,
            member.id,
            "antiraid",
        )
        return await ctx.send_success(
            f"**{member}** can no longer use **antiraid** commands"
        )

    @antiraid.command(help="check whitelisted users of antiraid commands")
    async def whitelisted(self, ctx: commands.Context):
        i = 0
        k = 1
        l = 0
        mes = ""
        number = []
        messages = []
        results = await self.bot.db.fetch(
            "SELECT * FROM whitelist WHERE guild_id = $1 AND module = $2 AND mode = $3",
            ctx.guild.id,
            "antiraid",
            "user",
        )
        if len(results) == 0:
            return await ctx.send_warning("No **whitelisted** members found")
        for result in results:
            mes = f"{mes}`{k}` {await self.bot.fetch_user(result['object_id'])}\n"
            k += 1
            l += 1
            if l == 10:
                messages.append(mes)
                number.append(
                    discord.Embed(
                        color=self.bot.color,
                        title=f"antiraid whitelisted ({len(results)})",
                        description=messages[i],
                    )
                )
                i += 1
                mes = ""
                l = 0

        messages.append(mes)
        number.append(
            discord.Embed(
                color=self.bot.color,
                title=f"antiraid whitelisted ({len(results)})",
                description=messages[i],
            )
        )
        await ctx.paginator(number)

    @antiraid.group(
        invoke_without_command=True,
        help="prevend join raids",
        usage="[status (enable/disable)] [punishment] [joins per 10 seconds]\nexample: antiraid massjoin enable 10",
    )
    async def massjoin(self, ctx: commands.Context):
        return await ctx.create_pages()

    @massjoin.command(
        brief="antiraid whitelisted",
        name="enable",
        help="prevent join raids",
        usage="[punishment] [joins per 10 seconds]\nexample: antiraid massjoin enable ban 10",
    )
    @Perms.check_whitelist("antiraid")
    async def massjoin_enable(self, ctx: commands.Context, punishment: str, joins: int):
        check = await self.bot.db.fetchrow(
            "SELECT * FROM antiraid WHERE guild_id = $1 AND command = $2",
            ctx.guild.id,
            "massjoin",
        )
        if check:
            return await ctx.send_warning("Massjoin protection is **already** enabled")
        await self.bot.db.execute(
            "INSERT INTO antiraid VALUES ($1,$2,$3,$4)",
            ctx.guild.id,
            "massjoin",
            punishment,
            joins,
        )
        return await ctx.send_success(
            f"Massjoin protection enabled. This will be triggered only if there are more than **{joins}** joins under **10 seconds**\npunishment: **{punishment}**"
        )

    @massjoin.command(
        brief="antiraid whitelisted",
        name="disable",
        help="disable massjoin protection",
    )
    @Perms.check_whitelist("antiraid")
    async def massjoin_disable(self, ctx: commands.Context):
        check = await self.bot.db.fetchrow(
            "SELECT * FROM antiraid WHERE guild_id = $1 AND command = $2",
            ctx.guild.id,
            "massjoin",
        )
        if not check:
            return await ctx.send_warning("Massjoin protection is **not** enabled")
        await self.bot.db.execute(
            "DELETE FROM antiraid WHERE command = $1 AND guild_id = $2",
            "massjoin",
            ctx.guild.id,
        )
        return await ctx.send_success(f"Massjoin protection disabled")

    @antiraid.group(
        invoke_without_command=True,
        help="prevent alt accounts from joining your server",
        usage="[subcommand] [time] [punishment]\nantiraid newaccounts on 2d ban",
    )
    async def newaccounts(self, ctx: commands.Context):
        return await ctx.create_pages()

    @newaccounts.command(
        brief="antiraid whitelisted",
        name="whitelist",
        help="let a young account join",
        usage="[user]",
        aliases=["wl"],
    )
    @Perms.check_whitelist("antiraid")
    async def newaccounts_whitelist(
        self, ctx: commands.Context, *, member: discord.User
    ):
        check = await ctx.bot.db.fetchrow(
            "SELECT * FROM whitelist WHERE guild_id = $1 AND module = $2 AND object_id = $3 AND mode = $4",
            ctx.guild.id,
            "newaccounts",
            member.id,
            "user",
        )
        if check:
            return await ctx.send_warning(
                f"**{member}** is **already** whitelisted for **antiraid newaccounts**"
            )
        await ctx.bot.db.execute(
            "INSERT INTO whitelist VALUES ($1,$2,$3,$4)",
            ctx.guild.id,
            "newaccounts",
            member.id,
            "user",
        )
        return await ctx.send_success(
            f"**{member}** is now whitelisted for **antiraid newaccounts** and can join"
        )

    @newaccounts.command(
        brief="antiraid whitelisted",
        name="unwhitelist",
        help="remove the whitelist of a new account",
        usage="[member]",
        aliases=["uwl"],
    )
    @Perms.check_whitelist("antiraid")
    async def newaccounts_unwhitelist(
        self, ctx: commands.Context, *, member: discord.User
    ):
        check = await ctx.bot.db.fetchrow(
            "SELECT * FROM whitelist WHERE guild_id = $1 AND module = $2 AND object_id = $3 AND mode = $4",
            ctx.guild.id,
            "newaccounts",
            member.id,
            "user",
        )
        if not check:
            return await ctx.send_warning(
                f"**{member}** is **not** whitelisted for **antiraid newaccounts**"
            )
        await ctx.bot.db.execute(
            "DELETE FROM whitelist WHERE guild_id = $1 AND module = $2 AND object_id = $3 AND mode = $4",
            ctx.guild.id,
            "newaccounts",
            member.id,
            "user",
        )
        return await ctx.send_success(
            f"**{member}** is not whitelisted for **antiraid newaccounts** anymore"
        )

    @newaccounts.command(
        name="whitelisted",
        aliases=["list"],
        help="returns the whitelisted members from the newaccounts antiraid system",
    )
    async def newaccounts_whitelisted(self, ctx: commands.Context):
        return await Whitelist.whitelisted_things(ctx, "newaccounts", "user")

    @newaccounts.command(
        brief="antiraid whitelisted",
        name="on",
        help="turn on newaccounts",
        usage="[time] [punishment]\nexample: antiraid newaccounts on 2d ban",
    )
    @Perms.check_whitelist("antiraid")
    async def newaccounts_on(self, ctx: commands.Context, time: str, punishment: str):
        try:
            if not punishment in ["kick", "ban"]:
                return await ctx.send_error(
                    "Punishment is not either **kick** or **ban**"
                )
            time = humanfriendly.parse_timespan(time)
            check = await self.bot.db.fetchrow(
                "SELECT * FROM antiraid WHERE guild_id = $1 AND command = $2",
                ctx.guild.id,
                "newaccounts",
            )
            if check:
                return await ctx.send_warning("Newaccounts is **already** enabled")
            await self.bot.db.execute(
                "INSERT INTO antiraid VALUES ($1,$2,$3,$4)",
                ctx.guild.id,
                "newaccounts",
                punishment,
                int(time),
            )
            return await ctx.send_success(
                f"Newaccounts antiraid enabled ({humanfriendly.format_timespan(time)}) | punishment: {punishment}"
            )
        except humanfriendly.InvalidTimespan:
            return await ctx.send_warning(
                f"**{time}** couldn't be converted in **seconds**"
            )

    @newaccounts.command(
        brief="antiraid whitelisted",
        name="off",
        help="turn off newaccounts",
    )
    @Perms.check_whitelist("antiraid")
    async def newaccounts_off(self, ctx: commands.Context):
        check = await self.bot.db.fetchrow(
            "SELECT * FROM antiraid WHERE guild_id = $1 AND command = $2",
            ctx.guild.id,
            "newaccounts",
        )
        if check is None:
            return await ctx.send_warning("Newaccounts is **not** enabled")
        await self.bot.db.execute(
            "DELETE FROM antiraid WHERE command = $1 AND guild_id = $2",
            "newaccounts",
            ctx.guild.id,
        )
        return await ctx.send_success("Newaccounts antiraid disabled")

    @antiraid.group(
        invoke_without_command=True,
        help="prevent members with no avatar from joining your server",
        aliases=["noavatar", "defaultpfp"],
    )
    async def defaultavatar(self, ctx: commands.Context):
        return await ctx.create_pages()

    @defaultavatar.command(
        brief="antiraid whitelisted",
        name="on",
        help="turn on defaultavatar",
    )
    @Perms.check_whitelist("antiraid")
    async def defaultpfp_on(self, ctx: commands.Context, punishment: str):
        if not punishment in ["kick", "ban"]:
            return await ctx.send_warning(
                "Punishment can be either **ban** or **kick**"
            )
        check = await self.bot.db.fetchrow(
            "SELECT * FROM antiraid WHERE guild_id = $1 AND command = $2",
            ctx.guild.id,
            "defaultavatar",
        )
        if check:
            return await ctx.send_warning("Defaultavatar is **already** enabled")
        await self.bot.db.execute(
            "INSERT INTO antiraid VALUES ($1,$2,$3,$4)",
            ctx.guild.id,
            "defaultavatar",
            punishment,
            None,
        )
        return await ctx.send_success(f"Defaultavatar enabled")

    @defaultavatar.command(
        brief="antiraid whitelisted",
        name="off",
        help="turn off defaultavatar",
    )
    @Perms.check_whitelist("antiraid")
    async def defaultpfp_off(self, ctx: commands.Context):
        check = await self.bot.db.fetchrow(
            "SELECT * FROM antiraid WHERE guild_id = $1 AND command = $2",
            ctx.guild.id,
            "defaultavatar",
        )
        if not check:
            return await ctx.send_warning("Defaultavatar is **not** enabled")
        await self.bot.db.execute(
            "DELETE FROM antiraid WHERE guild_id = $1 AND command = $2",
            ctx.guild.id,
            "defaultavatar",
        )
        return await ctx.send_success("Defaultavatar disabled")

    @defaultavatar.command(
        brief="antiraid whitelisted",
        name="whitelist",
        help="let a person with no avatar",
        usage="[user]",
        aliases=["wl"],
    )
    @Perms.check_whitelist("antiraid")
    async def defaultavatar_whitelist(
        self, ctx: commands.Context, *, member: discord.User
    ):
        check = await ctx.bot.db.fetchrow(
            "SELECT * FROM whitelist WHERE guild_id = $1 AND module = $2 AND object_id = $3 AND mode = $4",
            ctx.guild.id,
            "defaultavatar",
            member.id,
            "user",
        )
        if check:
            return await ctx.send_warning(
                f"**{member}** is **already** whitelisted for **antiraid defaultavatar**"
            )
        await ctx.bot.db.execute(
            "INSERT INTO whitelist VALUES ($1,$2,$3,$4)",
            ctx.guild.id,
            "defaultavatar",
            member.id,
            "user",
        )
        return await ctx.send_success(
            f"**{member}**is now whitelisted for **antiraid defaultavatar** and can join"
        )

    @defaultavatar.command(
        brief="antiraid whitelisted",
        name="unwhitelist",
        help="remove the whitelist of a no avatar member",
        usage="[member]",
        aliases=["uwl"],
    )
    @Perms.check_whitelist("antiraid")
    async def defaultavatar_unwhitelist(
        self, ctx: commands.Context, *, member: discord.User
    ):
        check = await ctx.bot.db.fetchrow(
            "SELECT * FROM whitelist WHERE guild_id = $1 AND module = $2 AND object_id = $3 AND mode = $4",
            ctx.guild.id,
            "defaultavatar",
            member.id,
            "user",
        )
        if not check:
            return await ctx.send_warning(
                f"**{member}** is **not** whitelisted for **antiraid defaultavatar**"
            )
        await ctx.bot.db.execute(
            "DELETE FROM whitelist WHERE guild_id = $1 AND module = $2 AND object_id = $3 AND mode = $4",
            ctx.guild.id,
            "defaultavatar",
            member.id,
            "user",
        )
        return await ctx.send_success(
            f"**{member}**is not whitelisted for **antiraid defaultavatar** anymore"
        )

    @defaultavatar.command(
        name="whitelisted",
        aliases=["list"],
        help="returns the whitelisted members from the defaultavatar antiraid system",
    )
    async def defaultavatar_whitelisted(self, ctx: commands.Context):
        return await Whitelist.whitelisted_things(ctx, "defaultavatar", "user")


async def setup(bot):
    await bot.add_cog(AntiRaid(bot))
