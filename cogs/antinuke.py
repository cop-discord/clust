import discord, datetime
from discord.ext import commands
from extensions.control import Perms
from extensions.utilities import Whitelist


def is_antinuke():
    async def predicate(ctx: commands.Context):
        check = await ctx.bot.db.fetchrow(
            "SELECT * FROM antinuke_toggle WHERE guild_id = $1", ctx.guild.id
        )
        if not check:
            await ctx.send_warning("The antinuke is **not** enabled")
        return check is not None

    return commands.check(predicate)


def can_manage():
    async def predicate(ctx: commands.Context):
        if ctx.author.id == ctx.guild.owner_id:
            return True
        if ctx.author.top_role.position <= ctx.guild.me.top_role.position:
            await ctx.send_warning("You cannot **manage** the antinuke module")
            return False
        else:
            if not Perms.has_perms(ctx, "administrator"):
                await ctx.send_warning(
                    "You need **administrator** permission to manage antinuke"
                )
                return False
        return True

    return commands.check(predicate)


class AntiNuke(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self.ban_cache = {}
        self.kick_cache = {}
        self.channel_delete_cache = {}

    async def sendlogs(self, action: str, member: discord.Member, punishment: str):
        check = await self.bot.db.fetchrow(
            "SELECT logs FROM antinuke_toggle WHERE guild_id = $1", member.guild.id
        )
        embed = discord.Embed(
            color=self.bot.color,
            title=f"{member} punished",
            description="Was clust fast? If yes, please give us a review in https://discord.gg/clust",
        )
        embed.set_thumbnail(url=member.guild.icon)
        embed.add_field(name="Server", value=member.guild.name)
        embed.add_field(name="Punishment", value=punishment)
        embed.add_field(name="Action", value=action)
        if check[0] is None:
            try:
                await member.guild.owner.send(embed=embed)
            except:
                return
        else:
            channel = member.guild.get_channel(int(check["logs"]))
            if channel:
                await channel.send(embed=embed)

    @commands.Cog.listener("on_audit_log_entry_create")
    async def channel_delete(self, entry: discord.AuditLogEntry):
        if entry.action == discord.AuditLogAction.channel_delete:
            if entry.guild.owner.id == entry.user.id:
                return
            if entry.user.top_role.position >= entry.guild.me.top_role.position:
                return
            check = await self.bot.db.fetchrow(
                "SELECT punishment FROM antinuke WHERE guild_id = $1 AND module = $2",
                entry.guild.id,
                "channel",
            )
            if not check:
                return
            res3 = await self.bot.db.fetchrow(
                "SELECT * FROM whitelist WHERE guild_id = $1 AND module = $2 AND object_id = $3 AND mode = $4",
                entry.guild.id,
                "antinuke",
                entry.user.id,
                "user",
            )
            if res3:
                return
            if not self.channel_delete_cache.get(str(entry.guild.id)):
                self.channel_delete_cache[str(entry.guild.id)] = {}
            if not self.channel_delete_cache[str(entry.guild.id)].get(
                str(entry.user.id)
            ):
                self.channel_delete_cache[str(entry.guild.id)][str(entry.user.id)] = []
            self.channel_delete_cache[str(entry.guild.id)][str(entry.user.id)].append(
                datetime.datetime.now()
            )
            expired_cache = [
                c
                for c in self.channel_delete_cache[str(entry.guild.id)][
                    str(entry.user.id)
                ]
                if (datetime.datetime.now() - c).total_seconds() > 60
            ]
            for b in expired_cache:
                self.channel_delete_cache[str(entry.guild.id)][
                    str(entry.user.id)
                ].remove(b)
            if (
                len(self.channel_delete_cache[str(entry.guild.id)][str(entry.user.id)])
                >= check["threshold"]
            ):
                self.channel_delete_cache[str(entry.guild.id)][str(entry.user.id)] = []
                punishment = check["punishment"]
                if punishment == "ban":
                    return await entry.user.ban(reason="AntiNuke: Deleting channels")
                elif punishment == "kick":
                    return await entry.user.kick(reason="AntiNuke: Deleting channels")
                else:
                    await entry.user.edit(
                        roles=[
                            role
                            for role in entry.user.roles
                            if not role.is_assignable()
                            or not self.bot.is_dangerous(role)
                            or role.is_premium_subscriber()
                        ],
                        reason="AntiNuke: Deleting channels",
                    )
                    if entry.user.bot:
                        for role in [r for r in entry.user.roles if r.is_bot_managed()]:
                            await role.edit(
                                permissions=discord.Permissions.none(),
                                reason="AntiNuke: Deleting channels",
                            )
                await self.sendlogs("Deleting channels", entry.user, punishment)

    @commands.Cog.listener("on_audit_log_entry_create")
    async def antibot_join(self, entry: discord.AuditLogEntry):
        if entry.action == discord.AuditLogAction.bot_add:
            check = await self.bot.db.fetchrow(
                "SELECT punishment FROM antinuke WHERE guild_id = $1 AND module = $2",
                entry.guild.id,
                "antibot",
            )
            if not check:
                return
            if not entry.target.bot:
                return
            res1 = await self.bot.db.fetchrow(
                "SELECT * FROM whitelist WHERE guild_id = $1 AND module = $2 AND object_id = $3 AND mode = $4",
                entry.guild.id,
                "antibot",
                entry.target.id,
                "user",
            )
            if res1:
                return
            res3 = await self.bot.db.fetchrow(
                "SELECT * FROM whitelist WHERE guild_id = $1 AND module = $2 AND object_id = $3 AND mode = $4",
                entry.guild.id,
                "antinuke",
                entry.user.id,
                "user",
            )
            if res3:
                return
            punishment = check["punishment"]
            await entry.guild.kick(
                user=entry.target, reason="AntiNuke: Unwhitelisted bot added"
            )
            if entry.guild.owner.id == entry.user.id:
                return
            if entry.user.top_role.position >= entry.guild.me.top_role.position:
                return
            if punishment == "ban":
                return await entry.user.ban(reason="AntiNuke: Added Bots")
            elif punishment == "kick":
                return await entry.user.kick(reason="AntiNuke: Added Bots")
            else:
                await entry.user.edit(
                    roles=[
                        role
                        for role in entry.user.roles
                        if not role.is_assignable()
                        or not self.bot.is_dangerous(role)
                        or role.is_premium_subscriber()
                    ],
                    reason="AntiNuke: Added Bots",
                )
            await self.sendlogs("Adding Bots", entry.user, punishment)

    @commands.Cog.listener("on_audit_log_entry_create")
    async def on_ban(self, entry: discord.AuditLogEntry):
        if entry.action == discord.AuditLogAction.ban:
            check = await self.bot.db.fetchrow(
                "SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2",
                entry.guild.id,
                "ban",
            )
            if not check:
                return
            res3 = await self.bot.db.fetchrow(
                "SELECT * FROM whitelist WHERE guild_id = $1 AND module = $2 AND object_id = $3 AND mode = $4",
                entry.guild.id,
                "antinuke",
                entry.user.id,
                "user",
            )
            if res3:
                return
            if entry.guild.owner.id == entry.user.id:
                return
            if entry.user.top_role.position >= entry.guild.me.top_role.position:
                return
            if not self.ban_cache.get(str(entry.guild.id)):
                self.ban_cache[str(entry.guild.id)] = {}
            if not self.ban_cache[str(entry.guild.id)].get(str(entry.user.id)):
                self.ban_cache[str(entry.guild.id)][str(entry.user.id)] = []
            self.ban_cache[str(entry.guild.id)][str(entry.user.id)].append(
                datetime.datetime.now()
            )
            expired_bans = [
                ban
                for ban in self.ban_cache[str(entry.guild.id)][str(entry.user.id)]
                if (datetime.datetime.now() - ban).total_seconds() > 60
            ]
            for b in expired_bans:
                self.ban_cache[str(entry.guild.id)][str(entry.user.id)].remove(b)
            if (
                len(self.ban_cache[str(entry.guild.id)][str(entry.user.id)])
                >= check["threshold"]
            ):
                self.ban_cache[str(entry.guild.id)][str(entry.user.id)] = []
                punishment = check["punishment"]
                if punishment == "ban":
                    return await entry.user.ban(reason="AntiNuke: Banning Members")
                elif punishment == "kick":
                    return await entry.user.kick(reason="AntiNuke: Banning Members")
                else:
                    await entry.user.edit(
                        roles=[
                            role
                            for role in entry.user.roles
                            if not role.is_assignable()
                            or not self.bot.is_dangerous(role)
                            or role.is_premium_subscriber()
                        ],
                        reason="AntiNuke: Banning Members",
                    )
                    if entry.user.bot:
                        for role in [r for r in entry.user.roles if r.is_bot_managed()]:
                            await role.edit(
                                permissions=discord.Permissions.none(),
                                reason="AntiNuke: Banning Members",
                            )
                await self.sendlogs("Banning Members", entry.user, punishment)

    @commands.Cog.listener("on_audit_log_entry_create")
    async def on_kick(self, entry: discord.AuditLogEntry):
        if entry.action == discord.AuditLogAction.kick:
            check = await self.bot.db.fetchrow(
                "SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2",
                entry.guild.id,
                "kick",
            )
            if not check:
                return
            res3 = await self.bot.db.fetchrow(
                "SELECT * FROM whitelist WHERE guild_id = $1 AND module = $2 AND object_id = $3 AND mode = $4",
                entry.guild.id,
                "antinuke",
                entry.user.id,
                "ban",
            )
            if res3:
                return
            if entry.guild.owner.id == entry.user.id:
                return
            if entry.user.top_role.position >= entry.guild.me.top_role.position:
                return
            if not self.kick_cache.get(str(entry.guild.id)):
                self.kick_cache[str(entry.guild.id)] = {}
            if not self.kick_cache[str(entry.guild.id)].get(str(entry.user.id)):
                self.kick_cache[str(entry.guild.id)][str(entry.user.id)] = []
            self.kick_cache[str(entry.guild.id)][str(entry.user.id)].append(
                datetime.datetime.now()
            )
            expired_bans = [
                ban
                for ban in self.kick_cache[str(entry.guild.id)][str(entry.user.id)]
                if (datetime.datetime.now() - ban).total_seconds() > 60
            ]
            for b in expired_bans:
                self.kick_cache[str(entry.guild.id)][str(entry.user.id)].remove(b)
            if (
                len(self.kick_cache[str(entry.guild.id)][str(entry.user.id)])
                >= check["threshold"]
            ):
                self.kick_cache[str(entry.guild.id)][str(entry.user.id)] = []
                punishment = check["punishment"]
                if punishment == "ban":
                    return await entry.user.ban(reason="AntiNuke: Kicking Members")
                elif punishment == "kick":
                    return await entry.user.kick(reason="AntiNuke: Kicking Members")
                else:
                    await entry.user.edit(
                        roles=[
                            role
                            for role in entry.user.roles
                            if not role.is_assignable()
                            or not self.bot.is_dangerous(role)
                            or role.is_premium_subscriber()
                        ],
                        reason="AntiNuke: Kicking Members",
                    )
                    if entry.user.bot:
                        for role in [r for r in entry.user.roles if r.is_bot_managed()]:
                            await role.edit(
                                permissions=discord.Permissions.none(),
                                reason="AntiNuke: Kicking Members",
                            )
                await self.sendlogs("Kicking Members", entry.user, punishment)

    @commands.hybrid_group(
        invoke_without_command=True,
        name="antinuke",
        help="protect your server against nukes",
        aliases=["an"],
    )
    async def antinuke(self, ctx: commands.Context):
        return await ctx.create_pages()

    @antinuke.command(
        name="logs",
        help="configure the logs antinuke channel",
        brief="antinuke admin",
        usage="[channel]",
    )
    @Perms.check_whitelist("antinuke")
    @is_antinuke()
    async def antinuke_logs(
        self, ctx: commands.Context, *, channel: discord.TextChannel = None
    ):
        if not channel:
            await self.bot.db.execute(
                "UPDATE antinuke_toggle SET logs = $1 WHERE guild_id = $2",
                None,
                ctx.guild.id,
            )
            return await ctx.send_success("Antinuke logging channel -> **owner's dms**")
        await self.bot.db.execute(
            "UPDATE antinuke_toggle SET logs = $1 WHERE guild_id = $2",
            channel.id,
            ctx.guild.id,
        )
        return await ctx.send_success(f"Antinuke logging channel -> {channel.mention}")

    @antinuke.command(
        name="enable",
        aliases=["e", "on"],
        help="enable antinuke in your server",
        brief="server owner",
    )
    @can_manage()
    async def antinuke_enable(self, ctx: commands.Context):
        check = await self.bot.db.fetchrow(
            "SELECT * FROM antinuke_toggle WHERE guild_id = $1", ctx.guild.id
        )
        if check:
            return await ctx.send_warning("AntiNuke is **already** enabled")
        await self.bot.db.execute(
            "INSERT INTO antinuke_toggle (guild_id) VALUES ($1)", ctx.guild.id
        )
        return await ctx.send_success("AntiNuke is now **enabled**")

    @antinuke.command(
        name="disable",
        aliases=["d", "off"],
        help="disable antinuke in your server",
        brief="server owner",
    )
    @can_manage()
    @is_antinuke()
    async def antinuke_disable(self, ctx: commands.Context):
        await self.bot.db.execute(
            "DELETE FROM antinuke_toggle WHERE guild_id = $1", ctx.guild.id
        )
        return await ctx.send_success("AntiNuke is now **disabled**")

    @antinuke.group(
        name="admin", invoke_without_command=True, help="manage antinuke admins"
    )
    async def antinuke_admin(self, ctx):
        return await ctx.create_pages()

    @antinuke_admin.command(
        name="add",
        brief="server owner",
        help="add an antinuke admin",
        usage="[member]",
    )
    @can_manage()
    @is_antinuke()
    async def antinuke_admin_add(
        self, ctx: commands.Context, *, member: discord.Member
    ):
        return await Whitelist.whitelist_things(ctx, "antinuke", member)

    @antinuke_admin.command(
        name="remove",
        brief="server owner",
        help="remove an antinuke admin",
        usage="[member]",
    )
    @can_manage()
    @is_antinuke()
    async def antinuke_admin_remove(
        self, ctx: commands.Context, *, member: discord.Member
    ):
        return await Whitelist.unwhitelist_things(ctx, "antinuke", member)

    @antinuke_admin.command(name="list", help="returns antinuke admins")
    @is_antinuke()
    async def antinuke_admin_list(self, ctx: commands.Context):
        return await Whitelist.whitelisted_things(ctx, "antinuke", "user")

    @antinuke.command(name="admins", help="returns antinuke admins")
    @is_antinuke()
    async def antinuke_admins(self, ctx: commands.Context):
        return await Whitelist.whitelisted_things(ctx, "antinuke", "user")

    @antinuke.command(
        name="settings", aliases=["stats"], help="check antinuke settings"
    )
    @is_antinuke()
    async def an_settings(self, ctx: commands.Context):
        settings_enabled = {
            "antibot": self.bot.no,
            "ban": self.bot.no,
            "kick": self.bot.no,
            "channel": self.bot.no,
        }
        results = await self.bot.db.fetch(
            "SELECT * FROM antinuke WHERE guild_id = $1", ctx.guild.id
        )
        for result in results:
            if settings_enabled.get(result["module"]):
                settings_enabled[result["module"]] = self.bot.yes
        embed = discord.Embed(
            color=self.bot.color,
            description="\n".join(
                [
                    f"**{m}:** {settings_enabled.get(m)}"
                    for m in ["antibot", "ban", "kick", "channel"]
                ]
            ),
        )
        embed.set_author(name=f"antinuke settings for {ctx.guild.name}")
        embed.set_thumbnail(url=ctx.guild.icon)
        await ctx.reply(embed=embed)

    @antinuke.group(
        name="channel",
        invoke_without_command=True,
        help="prevent members from deleting the server's channels",
    )
    async def an_channels(self, ctx):
        return await ctx.create_pages()

    @an_channels.command(
        name="enable",
        aliases=["e"],
        help="enable channel delete protection",
        usage="[punishment]",
        brief="antinuke admin",
    )
    @Perms.check_whitelist("antinuke")
    @is_antinuke()
    async def an_channels_enable(self, ctx: commands.Context, *, punishment: str):
        if not punishment in ["ban", "kick", "strip"]:
            return await ctx.send_warning(
                f"Punishment should be either **kick**, **ban** or **strip**, not **{punishment}**"
            )
        check = await self.bot.db.fetchrow(
            "SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2",
            ctx.guild.id,
            "channel",
        )
        if not check:
            await self.bot.db.execute(
                "INSERT INTO antinuke VALUES ($1,$2,$3,$4)",
                ctx.guild.id,
                "channel",
                punishment,
                0,
            )
        else:
            await self.bot.db.execute(
                "UPDATE antinuke SET punishment = $1 WHERE guild_id = $2 AND module = $3",
                punishment,
                ctx.guild.id,
                "channel",
            )
        return await ctx.send_success(
            f"**Anti channel delete** enabled\npunishment: {punishment}\nThreshold: 1 channel deletion per 1 minute"
        )

    @an_channels.command(
        name="disable",
        aliases=["dis"],
        help="disable channel delete protection",
        brief="antinuke admin",
    )
    @Perms.check_whitelist("antinuke")
    @is_antinuke()
    async def an_channels_disable(self, ctx: commands.Context):
        check = await self.bot.db.fetchrow(
            "SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2",
            ctx.guild.id,
            "channel",
        )
        if not check:
            return await ctx.send_warning("Antinuke channel delete **not** enabled")
        await self.bot.db.execute(
            "DELETE FROM antinuke WHERE guild_id = $1 AND module = $2",
            ctx.guild.id,
            "channel",
        )
        return await ctx.send_success("Antinuke channel delete succesfully disabled")

    @an_channels.command(
        name="threshold",
        usage="[number]",
        aliases=["limit", "count"],
        help="change the number of allowed channel deletions per 1 minute",
        brief="antinuke admin",
    )
    @Perms.check_whitelist("antinuke")
    @is_antinuke()
    async def an_channels_threshold(self, ctx: commands.Context, number: int):
        if number < 0:
            return await ctx.send_warning("The limit can't be lower than 0")
        check = await self.bot.db.fetchrow(
            "SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2",
            ctx.guild.id,
            "channel",
        )
        if not check:
            return await ctx.send_warning("Antinuke channel delete **not** enabled")
        await self.bot.db.execute(
            "UPDATE antinuke SET threshold = $1 WHERE guild_id = $2 AND module = $3",
            number,
            ctx.guild.id,
            "channel",
        )
        return await ctx.send_success(
            f"Antinuke channel delete threshold changed to **{number}** channels per **60** seconds"
        )

    @antinuke.group(
        name="kick",
        invoke_without_command=True,
        help="prevent members from mass kicking other members",
    )
    async def an_kick(self, ctx):
        return await ctx.create_pages()

    @an_kick.command(
        name="enable",
        aliases=["e"],
        help="enable kick members protection",
        usage="[punishment]",
        brief="antinuke admin",
    )
    @Perms.check_whitelist("antinuke")
    @is_antinuke()
    async def an_kick_enable(self, ctx: commands.Context, *, punishment: str):
        if not punishment in ["ban", "kick", "strip"]:
            return await ctx.send_warning(
                f"Punishment should be either **kick**, **ban** or **strip**, not **{punishment}**"
            )
        check = await self.bot.db.fetchrow(
            "SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2",
            ctx.guild.id,
            "kick",
        )
        if not check:
            await self.bot.db.execute(
                "INSERT INTO antinuke VALUES ($1,$2,$3,$4)",
                ctx.guild.id,
                "kick",
                punishment,
                0,
            )
        else:
            await self.bot.db.execute(
                "UPDATE antinuke SET punishment = $1 WHERE guild_id = $2 AND module = $3",
                punishment,
                ctx.guild.id,
                "kick",
            )
        return await ctx.send_success(
            f"**Anti kick** enabled\npunishment: {punishment}\nThreshold: 1 kick per 1 minute"
        )

    @an_kick.command(
        name="disable",
        aliases=["dis"],
        help="disable kick protection",
        brief="antinuke admin",
    )
    @Perms.check_whitelist("antinuke")
    @is_antinuke()
    async def an_kick_disable(self, ctx: commands.Context):
        check = await self.bot.db.fetchrow(
            "SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2",
            ctx.guild.id,
            "kick",
        )
        if not check:
            return await ctx.send_warning("Antinuke kick **not** enabled")
        await self.bot.db.execute(
            "DELETE FROM antinuke WHERE guild_id = $1 AND module = $2",
            ctx.guild.id,
            "kick",
        )
        return await ctx.send_success("Antinuke kick succesfully disabled")

    @an_kick.command(
        name="threshold",
        usage="[number]",
        aliases=["limit", "count"],
        help="change the number of allowed kicks per 1 minute",
        brief="antinuke admin",
    )
    @Perms.check_whitelist("antinuke")
    @is_antinuke()
    async def an_kick_threshold(self, ctx: commands.Context, number: int):
        if number < 0:
            return await ctx.send_warning("The limit can't be lower than 0")
        check = await self.bot.db.fetchrow(
            "SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2",
            ctx.guild.id,
            "kick",
        )
        if not check:
            return await ctx.send_warning("Antinuke kick **not** enabled")
        await self.bot.db.execute(
            "UPDATE antinuke SET threshold = $1 WHERE guild_id = $2 AND module = $3",
            number,
            ctx.guild.id,
            "kick",
        )
        return await ctx.send_success(
            f"Antinuke kicks threshold changed to **{number}** kicks per **60** seconds"
        )

    @antinuke.group(
        name="ban",
        invoke_without_command=True,
        help="prevent members from mass banning other members",
    )
    async def an_ban(self, ctx):
        return await ctx.create_pages()

    @an_ban.command(
        name="enable",
        aliases=["e"],
        help="enable ban members protection",
        usage="[punishment]",
        brief="antinuke admin",
    )
    @Perms.check_whitelist("antinuke")
    @is_antinuke()
    async def an_ban_enable(self, ctx: commands.Context, *, punishment: str):
        if not punishment in ["ban", "kick", "strip"]:
            return await ctx.send_warning(
                f"Punishment should be either **kick**, **ban** or **strip**, not **{punishment}**"
            )
        check = await self.bot.db.fetchrow(
            "SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2",
            ctx.guild.id,
            "ban",
        )
        if not check:
            await self.bot.db.execute(
                "INSERT INTO antinuke VALUES ($1,$2,$3,$4)",
                ctx.guild.id,
                "ban",
                punishment,
                0,
            )
        else:
            await self.bot.db.execute(
                "UPDATE antinuke SET punishment = $1 WHERE guild_id = $2 AND module = $3",
                punishment,
                ctx.guild.id,
                "ban",
            )
        return await ctx.send_success(
            f"**Anti Ban** enabled\npunishment: {punishment}\nThreshold: 1 ban per 1 minute"
        )

    @an_ban.command(
        name="disable",
        aliases=["dis"],
        help="disable ban protection",
        brief="antinuke admin",
    )
    @Perms.check_whitelist("antinuke")
    @is_antinuke()
    async def an_ban_disable(self, ctx: commands.Context):
        check = await self.bot.db.fetchrow(
            "SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2",
            ctx.guild.id,
            "ban",
        )
        if not check:
            return await ctx.send_warning("Antinuke ban **not** enabled")
        await self.bot.db.execute(
            "DELETE FROM antinuke WHERE guild_id = $1 AND module = $2",
            ctx.guild.id,
            "ban",
        )
        return await ctx.send_success("Antinuke ban succesfully disabled")

    @an_ban.command(
        name="threshold",
        usage="[number]",
        aliases=["limit", "count"],
        help="change the number of allowed bans per one minute",
        brief="antinuke admin",
    )
    @Perms.check_whitelist("antinuke")
    @is_antinuke()
    async def an_ban_threshold(self, ctx: commands.Context, number: int):
        if number < 0:
            return await ctx.send_warning("The limit can't be lower than 0")
        check = await self.bot.db.fetchrow(
            "SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2",
            ctx.guild.id,
            "ban",
        )
        if not check:
            return await ctx.send_warning("Antinuke ban **not** enabled")
        await self.bot.db.execute(
            "UPDATE antinuke SET threshold = $1 WHERE guild_id = $2 AND module = $3",
            number,
            ctx.guild.id,
            "ban",
        )
        return await ctx.send_success(
            f"Antinuke bans threshold changed to **{number}** bans per **60** seconds"
        )

    @antinuke.group(
        name="botadd",
        aliases=["antibot"],
        invoke_without_command=True,
        help="prevent bots from joining your server",
    )
    async def botadd(self, ctx):
        return await ctx.create_pages()

    @botadd.command(
        name="whitelist",
        aliases=["wl"],
        brief="antinuke admin",
        help="whitelist a bot so it can join the server ",
        usage="[member]",
    )
    @Perms.check_whitelist("antinuke")
    @is_antinuke()
    async def botadd_whitelist(self, ctx: commands.Context, *, member: discord.User):
        return await Whitelist.whitelist_things(ctx, "antibot", member)

    @botadd.command(
        name="unwhitelist",
        brief="antinuke admin",
        aliases=["uwl"],
        help="remove an antibot whitelisted member",
        usage="[member]",
    )
    @Perms.check_whitelist("antinuke")
    @is_antinuke()
    async def botadd_unwhitelist(self, ctx: commands.Context, *, member: discord.User):
        return await Whitelist.unwhitelist_things(ctx, "antibot", member)

    @botadd.command(name="whitelisted", help="returns antinuke admins")
    @is_antinuke()
    async def botadd_whitelisted(self, ctx: commands.Context):
        return await Whitelist.whitelisted_things(ctx, "antibot", "user")

    @botadd.command(
        name="enable",
        aliases=["e"],
        help="enable bot adding protection",
        usage="[punishment]",
        brief="antinuke admin",
    )
    @Perms.check_whitelist("antinuke")
    @is_antinuke()
    async def botadd_enable(self, ctx: commands.Context, punishment: str):
        if not punishment in ["ban", "kick", "strip"]:
            return await ctx.send_warning(
                f"Punishment should be either **kick**, **ban** or **strip**, not **{punishment}**"
            )
        check = await self.bot.db.fetchrow(
            "SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2",
            ctx.guild.id,
            "antibot",
        )
        if not check:
            await self.bot.db.execute(
                "INSERT INTO antinuke VALUES ($1,$2,$3,$4)",
                ctx.guild.id,
                "antibot",
                punishment,
                0,
            )
        else:
            await self.bot.db.execute(
                "UPDATE antinuke SET punishment = $1 WHERE guild_id = $2 AND module = $3",
                punishment,
                ctx.guild.id,
                "antibot",
            )
        return await ctx.send_success(f"**Botadd** enabled\npunishment: {punishment}")

    @botadd.command(
        name="disable",
        aliases=["dis"],
        help="disable antibot",
        brief="antinuke admin",
    )
    @Perms.check_whitelist("antinuke")
    @is_antinuke()
    async def botadd_disable(self, ctx: commands.Context):
        check = await self.bot.db.fetchrow(
            "SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2",
            ctx.guild.id,
            "antibot",
        )
        if not check:
            return await ctx.send_warning("Antinuke botadd **not** enabled")
        await self.bot.db.execute(
            "DELETE FROM antinuke WHERE guild_id = $1 AND module = $2",
            ctx.guild.id,
            "antibot",
        )
        return await ctx.send_success("Antinuke botadd succesfully disabled")


async def setup(bot: commands.AutoShardedBot) -> None:
    return await bot.add_cog(AntiNuke(bot))
