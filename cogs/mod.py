import discord, datetime, humanfriendly, json, asyncio
from discord.ext import commands
from typing import Union
from extensions.control import Mod
from cogs.config import InvokeClass
from extensions.utilities import EmbedBuilder, GoodRole, NoStaff
from extensions.control import Perms
from extensions import utils
from discord import Embed


class ClearMod(discord.ui.View):
    def __init__(self, ctx: commands.Context):
        super().__init__()
        self.ctx = ctx
        self.status = False

    @discord.ui.button(emoji="<:approve:1121826853678747710>")
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.client.ext.send_warning(
                interaction, "You are not the author of this embed"
            )
        check = await interaction.client.db.fetchrow(
            "SELECT * FROM mod WHERE guild_id = $1", interaction.guild.id
        )
        channelid = check["channel_id"]
        roleid = check["role_id"]
        logsid = check["jail_id"]
        channel = interaction.guild.get_channel(channelid)
        role = interaction.guild.get_role(roleid)
        logs = interaction.guild.get_channel(logsid)
        try:
            await channel.delete()
        except:
            pass
        try:
            await role.delete()
        except:
            pass
        try:
            await logs.delete()
        except:
            pass
        await interaction.client.db.execute(
            "DELETE FROM mod WHERE guild_id = $1", interaction.guild.id
        )
        self.status = True
        return await interaction.response.edit_message(
            view=None,
            embed=discord.Embed(
                color=interaction.client.color,
                description=f"{interaction.client.yes} {interaction.user.mention}: Disabled moderation",
            ),
        )

    @discord.ui.button(emoji="<:deny:1121826907739144412>")
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.client.ext.send_warning(
                interaction, "You are not the author of this embed"
            )
        await interaction.response.edit_message(
            embed=discord.Embed(color=interaction.client.color, help="aborting action"),
            view=None,
        )
        self.status = True

    async def on_timeout(self) -> None:
        if self.status == False:
            for item in self.children:
                item.disabled = True

            await self.message.edit(view=self)


class ModConfig:
    async def sendlogs(
        bot: commands.AutoShardedBot,
        action: str,
        author: discord.Member,
        victim: Union[discord.Member, discord.User],
        reason: str,
    ):
        check = await bot.db.fetchrow(
            "SELECT channel_id FROM mod WHERE guild_id = $1", author.guild.id
        )
        if check:
            res = await bot.db.fetchrow(
                "SELECT count FROM cases WHERE guild_id = $1", author.guild.id
            )
            case = int(res["count"]) + 1
            await bot.db.execute(
                "UPDATE cases SET count = $1 WHERE guild_id = $2", case, author.guild.id
            )
            embed = discord.Embed(
                color=bot.color,
                title=f"case #{case} ➜ {action}",
                timestamp=datetime.datetime.now(),
            )
            embed.add_field(name="user", value=f"{victim}\n({victim.id})")
            embed.add_field(name="mod", value=f"{author}\n({author.id})")
            embed.add_field(name="reason", value=reason, inline=False)
            try:
                await author.guild.get_channel(int(check["channel_id"])).send(
                    embed=embed
                )
            except:
                pass

    async def send_dm(
        ctx: commands.Context, member: discord.Member, action: str, reason: str
    ):
        results = await ctx.bot.db.fetchrow(
            "SELECT * FROM authorize WHERE guild_id = $1", ctx.guild.id
        )
        if results or ctx.guild.id in ctx.bot.main_guilds:
            res = await ctx.bot.db.fetchrow(
                "SELECT embed FROM dm WHERE guild_id = $1 AND command = $2",
                ctx.guild.id,
                ctx.command.name,
            )
            if res:
                name = res[0]
                if name.lower() == "off":
                    return
                view = discord.ui.View()
                view.add_item(
                    discord.ui.Button(
                        label=f"sent from {ctx.guild.name}", disabled=True
                    )
                )
                try:
                    x = await EmbedBuilder.to_object(
                        EmbedBuilder.embed_replacement(
                            ctx.author, InvokeClass.invoke_replacement(member, name)
                        ).replace("{reason}", reason)
                    )
                    try:
                        return await member.send(content=x[0], embed=x[1], view=view)
                    except:
                        pass
                except Exception as e:
                    print(e)
                    try:
                        return await member.send(
                            content=InvokeClass.invoke_replacement(
                                member, EmbedBuilder.embed_replacement(ctx.author, name)
                            ).replace("{reason}", reason),
                            embed=None,
                            view=view,
                        )
                    except:
                        pass
            else:
                embed = discord.Embed(
                    color=ctx.bot.color,
                    description=f"You have been **{action}** in {ctx.guild.name}\n{f'reason: {reason}' if reason != 'No reason provided' else ''}",
                )
                try:
                    await member.send(embed=embed)
                except:
                    pass
        else:
            embed = discord.Embed(
                color=ctx.bot.color,
                description=f"You have been **{action}** in {ctx.guild.name}\n{f'reason: {reason}' if reason != 'No reason provided' else ''}",
            )
            try:
                await member.send(embed=embed)
            except:
                pass


class Mod(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot

    @commands.Cog.listener("on_member_remove")
    async def on_restore(self, member: discord.Member):
        check = await self.bot.db.fetchrow(
            "SELECT * FROM nodata WHERE user_id = $1 AND state = $2", member.id, "false"
        )
        if check:
            return
        list = [role.id for role in member.roles if role.is_assignable()]
        sql_as_text = json.dumps(list)
        ch = await self.bot.db.fetchrow(
            "SELECT * FROM restore WHERE user_id = {} AND guild_id = {}".format(
                member.id, member.guild.id
            )
        )
        if ch:
            return await self.bot.db.execute(
                "UPDATE restore SET roles = $1 WHERE guild_id = $2 AND user_id = $3",
                sql_as_text,
                member.guild.id,
                member.id,
            )
        return await self.bot.db.execute(
            "INSERT INTO restore VALUES ($1,$2,$3)",
            member.guild.id,
            member.id,
            sql_as_text,
        )

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        check = await self.bot.db.fetchrow(
            "SELECT * FROM mod WHERE guild_id = {}".format(channel.guild.id)
        )
        if check:
            await channel.set_permissions(
                channel.guild.get_role(int(check["role_id"])),
                view_channel=False,
                reason="overwriting permissions for jail role",
            )

    @commands.command(help="disable the moderation features in your server")
    @Perms.get_perms("administrator")
    async def unsetmod(self, ctx: commands.Context):
        check = await self.bot.db.fetchrow(
            "SELECT * FROM mod WHERE guild_id = $1", ctx.guild.id
        )
        if not check:
            return await ctx.send_warning(
                "Moderation is **not** enabled in this server"
            )
        view = ClearMod(ctx)
        view.message = await ctx.reply(
            view=view,
            embed=discord.Embed(
                color=self.bot.color,
                description=f"{ctx.author.mention} Are you sure you want to disable moderation?",
            ),
        )

    @commands.command(help="enable the moderation features in your server")
    @Perms.get_perms("administrator")
    async def setmod(self, ctx: commands.Context):
        check = await self.bot.db.fetchrow(
            "SELECT * FROM mod WHERE guild_id = $1", ctx.guild.id
        )
        if check:
            return await ctx.send_warning(
                "Moderation is **already** enabled in this server"
            )
        await ctx.typing()
        role = await ctx.guild.create_role(name="clust-jail")
        for channel in ctx.guild.channels:
            await channel.set_permissions(role, view_channel=False)
        overwrite = {
            role: discord.PermissionOverwrite(view_channel=True),
            ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
        }
        over = {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False)}
        category = await ctx.guild.create_category(name="clust mod", overwrites=over)
        text = await ctx.guild.create_text_channel(
            name="mod-logs", overwrites=over, category=category
        )
        jai = await ctx.guild.create_text_channel(
            name="jail", overwrites=overwrite, category=category
        )
        await self.bot.db.execute(
            "INSERT INTO mod VALUES ($1,$2,$3,$4)",
            ctx.guild.id,
            text.id,
            jai.id,
            role.id,
        )
        await self.bot.db.execute("INSERT INTO cases VALUES ($1,$2)", ctx.guild.id, 0)
        return await ctx.send_success("Enabled **moderation** for this server")

    @commands.command(help="clone a channel", brief="server owner")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    @Perms.server_owner()
    @Mod.is_mod_configured()
    async def nuke(self, ctx: commands.Context):
        embed = discord.Embed(
            color=self.bot.color, description=f"Do you want to **nuke** this channel?"
        )
        yes = discord.ui.Button(emoji=self.bot.yes)
        no = discord.ui.Button(emoji=self.bot.no)

        async def yes_callback(interaction: discord.Interaction):
            if not interaction.user == ctx.guild.owner:
                return await self.bot.ext.send_warning(
                    interaction,
                    "You are not the **author** of this embed",
                    ephemeral=True,
                )
            c = await interaction.channel.clone()
            await c.edit(position=ctx.channel.position)
            await ctx.channel.delete()
            file = discord.File(
                fp=await self.bot.getbyte(
                    "https://cdn.discordapp.com/attachments/769749773401849896/776951922295963648/giphy-downsized-large.gif"
                ),
                filename="nuke.gif",
            )
            await c.send(file=file)

        async def no_callback(interaction: discord.Interaction):
            if not interaction.user == ctx.guild.owner:
                return await self.bot.ext.send_warning(
                    interaction,
                    "You are not the **author** of this embed",
                    ephemeral=True,
                )
            await interaction.response.edit_message(
                embed=discord.Embed(color=self.bot.color, help="aborting action"),
                view=None,
            )

        yes.callback = yes_callback
        no.callback = no_callback
        view = discord.ui.View()
        view.add_item(yes)
        view.add_item(no)
        await ctx.reply(embed=embed, view=view)

    @commands.hybrid_command(
        help="restore member's roles",
        brief="manage roles",
        usage="[member]",
    )
    @Perms.get_perms("manage_roles")
    @Mod.is_mod_configured()
    async def restore(self, ctx: commands.Context, *, member: discord.Member):
        async with ctx.message.channel.typing():
            result = await self.bot.db.fetchrow(
                f"SELECT * FROM restore WHERE user_id = {member.id} AND guild_id = {ctx.guild.id}"
            )
            if result is None:
                return await ctx.send_warning(
                    f"Unable to find saved roles for **{member}**"
                )
            to_dump = json.loads(result["roles"])
            roles = [
                ctx.guild.get_role(r)
                for r in to_dump
                if ctx.guild.get_role(r) is not None
            ]
            succeed = ", ".join([f"{r.mention}" for r in roles if r.is_assignable()])
            failed = ", ".join([f"<@&{r.id}>" for r in roles if not r.is_assignable()])
            await member.edit(
                roles=[
                    r
                    for r in roles
                    if r.position
                    < ctx.guild.get_member(self.bot.user.id).top_role.position
                    and r != ctx.guild.premium_subscriber_role
                    and r != "@everyone"
                ]
            )
            await self.bot.db.execute(
                f"DELETE FROM restore WHERE user_id = {member.id} AND guild_id = {ctx.guild.id}"
            )
            embed = discord.Embed(
                color=self.bot.color,
                title="roles restored",
                description=f"target: **{member}**",
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(
                name="added",
                value="none" if succeed == ", " else succeed or "none",
                inline=False,
            )
            embed.add_field(
                name="failed",
                value="none" if failed == ", " else failed or "none",
                inline=False,
            )
            return await ctx.reply(embed=embed)

    @commands.hybrid_command(
        aliases=["setnick", "nick"],
        help="change an user's nickname",
        usage="[member] <nickname>",
    )
    @Perms.get_perms("manage_nicknames")
    @Mod.is_mod_configured()
    async def nickname(self, ctx, member: NoStaff, *, nick: str = None):
        if nick == None or nick.lower() == "none":
            return await ctx.send_success(f"Cleared **{member.name}'s** nickname")
        await member.edit(nick=nick)
        return await ctx.send_success(
            f"Changed **{member.name}'s** nickname to **{nick}**"
        )

    @commands.command(
        help="kick members from your server",
        brief="kick members",
        usage="[member] <reason>",
    )
    @Perms.get_perms("kick_members")
    @Mod.is_mod_configured()
    async def kick(
        self,
        ctx: commands.Context,
        member: NoStaff,
        *,
        reason: str = "No reason provided",
    ):
        await ctx.guild.kick(user=member, reason=reason + " | {}".format(ctx.author))
        await ModConfig.send_dm(ctx, member, "kicked", reason)
        await ModConfig.sendlogs(
            self.bot, "kick", ctx.author, member, reason + " | " + str(ctx.author)
        )
        if not await InvokeClass.invoke_send(ctx, member, reason):
            await ctx.send_success(f"**{member}** has been kicked | {reason}")

    @commands.hybrid_command(
        help="ban members from your server",
        brief="ban members",
        usage="[member] <reason>",
    )
    @Perms.get_perms("ban_members")
    @Mod.is_mod_configured()
    async def ban(
        self,
        ctx: commands.Context,
        member: NoStaff,
        *,
        reason: str = "No reason provided",
    ):
        await ctx.guild.ban(user=member, reason=reason + " | {}".format(ctx.author))
        await ModConfig.send_dm(ctx, member, "banned", reason)
        await ModConfig.sendlogs(
            self.bot, "ban", ctx.author, member, reason + " | " + str(ctx.author)
        )
        if not await InvokeClass.invoke_send(ctx, member, reason):
            await ctx.send_success(f"**{member}** has been banned | {reason}")

    @commands.hybrid_command(
        help="mute members in your server",
        brief="moderate members",
        usage="[member] [time] <reason>",
        aliases=["timeout"],
    )
    @Perms.get_perms("moderate_members")
    @Mod.is_mod_configured()
    async def mute(
        self,
        ctx: commands.Context,
        member: NoStaff,
        time: str = "60s",
        *,
        reason="No reason provided",
    ):
        tim = humanfriendly.parse_timespan(time)
        until = discord.utils.utcnow() + datetime.timedelta(seconds=tim)
        await member.timeout(until, reason=reason + " | {}".format(ctx.author))
        if not await InvokeClass.invoke_send(ctx, member, reason):
            await ctx.send_success(
                f"**{member}** has been muted for {humanfriendly.format_timespan(tim)} | {reason}"
            )
        await ModConfig.sendlogs(
            self.bot,
            "mute",
            ctx.author,
            member,
            reason + " | " + humanfriendly.format_timespan(tim),
        )
        await ModConfig.send_dm(
            ctx, member, "muted", reason + " | " + humanfriendly.format_timespan(tim)
        )

    @commands.command(help="unban an user", usage="[member] [reason]")
    @Perms.get_perms("ban_members")
    @Mod.is_mod_configured()
    async def unban(
        self,
        ctx: commands.Context,
        member: discord.User,
        *,
        reason: str = "No reason provided",
    ):
        try:
            await ctx.guild.unban(
                user=member, reason=reason + f" | unbanned by {ctx.author}"
            )
            if not await InvokeClass.invoke_send(ctx, member, reason):
                await ctx.send_success(f"**{member}** has been unbanned")
        except discord.NotFound:
            return await ctx.send_warning(f"Couldn't find ban for **{member}**")

    @commands.command(
        help="ban an user then immediately unban them",
        usage="[member] [reason]",
    )
    @Perms.get_perms("ban_members")
    @Mod.is_mod_configured()
    async def softban(
        self,
        ctx: commands.Context,
        member: NoStaff,
        *,
        reason: str = "No reason provided",
    ):
        await member.ban(
            delete_message_days=7, reason=reason + f" | banned by {ctx.author}"
        )
        await ctx.guild.unban(user=member)
        await ctx.send_success(f"Softbanned **{member}**")

    @commands.hybrid_command(
        help="unmute a member in your server",
        brief="moderate members",
        usage="[member] <reason>",
        aliases=["untimeout"],
    )
    @Perms.get_perms("moderate_members")
    @Mod.is_mod_configured()
    async def unmute(
        self,
        ctx: commands.Context,
        member: NoStaff,
        *,
        reason: str = "No reason provided",
    ):
        if not member.is_timed_out():
            return await ctx.send_warning(f"**{member}** is not muted")
        await member.edit(
            timed_out_until=None, reason=reason + " | {}".format(ctx.author)
        )
        if not await InvokeClass.invoke_send(ctx, member, reason):
            await ctx.send_success(f"**{member}** has been unmuted")
        await ModConfig.sendlogs(self.bot, "unmute", ctx.author, member, reason)

    @commands.group(name="clear", invoke_without_command=True)
    async def mata_clear(self, ctx):
        return await ctx.create_pages()

    @mata_clear.command(
        help="clear messages that contain a certain word",
        usage="[word]",
        brief="manage messages",
    )
    async def contains(self, ctx: commands.Context, *, word: str):
        messages = [
            message
            async for message in ctx.channel.history(limit=300)
            if word in message.content
        ]
        if len(messages) == 0:
            return await ctx.send_warning(
                f"No messages containing **{word}** in this channel"
            )
        await ctx.channel.delete_messages(messages)

    @commands.command(
        aliases=["p"],
        help="bulk delete messages",
        brief="manage messages",
        usage="[messages]",
    )
    @Perms.get_perms("manage_messages")
    async def purge(
        self, ctx: commands.Context, amount: int, *, member: NoStaff = None
    ):
        if member is None:
            await ctx.channel.purge(
                limit=amount + 1, bulk=True, reason=f"purge invoked by {ctx.author}"
            )
            return await ctx.send(f"purged `{amount}` messages", delete_after=2)
        messages = []
        async for m in ctx.channel.history():
            if m.author.id == member.id:
                messages.append(m)
            if len(messages) == amount:
                break
        messages.append(ctx.message)
        await ctx.channel.delete_messages(messages)
        return await ctx.send(
            f"purged `{amount}` messages sent by `{member}`", delete_after=2
        )

    @commands.command(
        help="bulk delete messages sent by bots",
        usage="[amount]",
        aliases=["bc", "botclear"],
    )
    @Perms.get_perms("manage_messages")
    async def botpurge(self, ctx: commands.Context, amount: int):
        mes = []
        async for message in ctx.channel.history():
            if len(mes) == amount:
                break
            if message.author.bot:
                mes.append(message)

        mes.append(ctx.message)
        await ctx.channel.delete_messages(mes)
        await ctx.send("purged {} messages from bots".format(amount), delete_after=1)

    @commands.command(
        help="removes all staff roles from a member",
        usage="[member] [reason]",
    )
    @Perms.get_perms("administrator")
    @Mod.is_mod_configured()
    async def strip(
        self,
        ctx: commands.Context,
        member: NoStaff,
        *,
        reason: str = "No reason provided",
    ):
        await ctx.channel.typing()
        await member.edit(
            roles=[
                role
                for role in member.roles
                if not role.is_assignable()
                or not self.bot.is_dangerous(role)
                or role.is_premium_subscriber()
            ],
            reason=reason + " | Moderator: {}".format(ctx.author),
        )
        await ctx.send_success(f"Removed **{member}'s** roles")
        await ModConfig.sendlogs(self.bot, "strip", ctx.author, member, reason)

    @commands.group(invoke_without_command=True)
    @Perms.get_perms("manage_messages")
    @Mod.is_mod_configured()
    async def warn(
        self,
        ctx: commands.Context,
        member: NoStaff = None,
        *,
        reason: str = "No reason provided",
    ):
        if member is None:
            return await ctx.create_pages()
        date = datetime.datetime.now()
        await self.bot.db.execute(
            "INSERT INTO warns VALUES ($1,$2,$3,$4,$5)",
            ctx.guild.id,
            member.id,
            ctx.author.id,
            f"{date.day}/{f'0{date.month}' if date.month < 10 else date.month}/{str(date.year)[-2:]} at {datetime.datetime.strptime(f'{date.hour}:{date.minute}', '%H:%M').strftime('%I:%M %p')}",
            reason,
        )
        if not await InvokeClass.invoke_send(ctx, member, reason):
            await ctx.send_success(f"Warned **{member}** | {reason}")
        await ModConfig.sendlogs(self.bot, "warn", ctx.author, member, reason)
        await ModConfig.send_dm(ctx, member, "warned", reason)

    @warn.command(
        help="clear all warns from an user",
        usage="[member]",
        brief="manage messages",
    )
    @Perms.get_perms("manage_messages")
    @Mod.is_mod_configured()
    async def clear(self, ctx: commands.Context, *, member: NoStaff):
        check = await self.bot.db.fetch(
            "SELECT * FROM warns WHERE guild_id = $1 AND user_id = $2",
            ctx.guild.id,
            member.id,
        )
        if len(check) == 0:
            return await ctx.send_warning("this user has no warnings".capitalize())
        await self.bot.db.execute(
            "DELETE FROM warns WHERE guild_id = $1 AND user_id = $2",
            ctx.guild.id,
            member.id,
        )
        await ctx.send_success(f"Removed **{member.name}'s** warns")

    @warn.command(
        name="list",
        help="shows all warns of an user",
        usage="[member]",
    )
    @Mod.is_mod_configured()
    async def list(self, ctx: commands.Context, *, member: discord.Member):
        check = await self.bot.db.fetch(
            "SELECT * FROM warns WHERE guild_id = $1 AND user_id = $2",
            ctx.guild.id,
            member.id,
        )
        if len(check) == 0:
            return await ctx.send_warning("this user has no warnings".capitalize())
        i = 0
        k = 1
        l = 0
        mes = ""
        number = []
        messages = []
        for result in check:
            mes = f"{mes}`{k}` {result['time']} by **{await self.bot.fetch_user(result['author_id'])}** - {result['reason']}\n"
            k += 1
            l += 1
            if l == 10:
                messages.append(mes)
                number.append(
                    discord.Embed(
                        color=self.bot.color,
                        title=f"warns ({len(check)})",
                        description=messages[i],
                    )
                )
                i += 1
                mes = ""
                l = 0

        messages.append(mes)
        embed = discord.Embed(
            color=self.bot.color, title=f"warns ({len(check)})", description=messages[i]
        ).set_footer(text="All times are GMT")
        number.append(embed)
        await ctx.paginator(number)

    @commands.command(help="shows all warns of an user", usage="[member]")
    @Mod.is_mod_configured()
    async def warns(self, ctx: commands.Context, *, member: discord.Member):
        return await ctx.invoke(self.bot.get_command("warn list"), member=member)

    @commands.command(
        help="jail a member",
        usage="[member]",
        brief="manage channels",
    )
    @Perms.get_perms("manage_channels")
    @Mod.is_mod_configured()
    async def jail(
        self,
        ctx: commands.Context,
        member: NoStaff,
        *,
        reason: str = "No reason provided",
    ):
        check = await self.bot.db.fetchrow(
            "SELECT * FROM jail WHERE guild_id = $1 AND user_id = $2",
            ctx.guild.id,
            member.id,
        )
        if check:
            return await ctx.send_warning(f"**{member}** is already jailed")
        if reason == None:
            reason = "No reason provided"
        roles = [
            r.id for r in member.roles if r.name != "@everyone" and r.is_assignable()
        ]
        sql_as_text = json.dumps(roles)
        await self.bot.db.execute(
            "INSERT INTO jail VALUES ($1,$2,$3)", ctx.guild.id, member.id, sql_as_text
        )
        chec = await self.bot.db.fetchrow(
            "SELECT * FROM mod WHERE guild_id = $1", ctx.guild.id
        )
        roleid = chec["role_id"]
        try:
            jail = ctx.guild.get_role(roleid)
            new = [r for r in member.roles if not r.is_assignable()]
            new.append(jail)
            if not await InvokeClass.invoke_send(ctx, member, reason):
                await member.edit(
                    roles=new, reason=f"jailed by {ctx.author} - {reason}"
                )
            await ctx.send_success(f"**{member}** got jailed - {reason}")
            await ModConfig.sendlogs(self.bot, "jail", ctx.author, member, reason)
            await ModConfig.send_dm(ctx, member, "jailed", reason)
            c = ctx.guild.get_channel(int(chec["jail_id"]))
            if c:
                await c.send(
                    f"{member.mention}, you have been jailed! Wait for a staff member to unjail you and check dm's if you have received one!"
                )
        except:
            return await ctx.send_error(f"There was a problem jailing **{member}**")

    @commands.command(
        help="unjail a member",
        usage="[member] [reason]",
        brief="manage channels",
    )
    @Perms.get_perms("manage_channels")
    @Mod.is_mod_configured()
    async def unjail(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "No reason provided",
    ):
        check = await self.bot.db.fetchrow(
            "SELECT * FROM jail WHERE guild_id = $1 AND user_id = $2",
            ctx.guild.id,
            member.id,
        )
        if not check:
            return await ctx.send_warning(f"**{member}** is not jailed")
        sq = check["roles"]
        roles = json.loads(sq)
        try:
            await member.edit(
                roles=[
                    ctx.guild.get_role(role)
                    for role in roles
                    if ctx.guild.get_role(role)
                ],
                reason=f"unjailed by {ctx.author}",
            )
        except:
            pass
        await self.bot.db.execute(
            "DELETE FROM jail WHERE user_id = {} AND guild_id = {}".format(
                member.id, ctx.guild.id
            )
        )
        if not await InvokeClass.invoke_send(ctx, member, reason):
            await ctx.send_success(f"Unjailed **{member}**")
        await ModConfig.sendlogs(self.bot, "unjail", ctx.author, member, reason)

    @commands.command(
        aliases=["sm"],
        help="add slowmode to a channel",
        usage="[seconds] <channel>",
        brief="manage channelss",
    )
    @Perms.get_perms("manage_channels")
    @Mod.is_mod_configured()
    async def slowmode(
        self, ctx: commands.Context, seconds: str, channel: discord.TextChannel = None
    ):
        if not channel:
            channel = ctx.channel

        tim = humanfriendly.parse_timespan(seconds)
        await channel.edit(
            slowmode_delay=tim, reason=f"Slowmode invoked by {ctx.author}"
        )
        return await ctx.send_success(
            f"Slowmode for {channel.mention} set to **{humanfriendly.format_timespan(tim)}**"
        )

    @commands.command(
        help="lock a channel",
        usage="<channel>",
        brief="manage channels",
    )
    @Perms.get_perms("manage_channels")
    @Mod.is_mod_configured()
    async def lock(self, ctx: commands.Context, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        return await ctx.send_success(f"Locked {channel.mention}")

    @commands.command(
        help="unlock a channel",
        usage="<channel>",
        brief="manage channels",
    )
    @Perms.get_perms("manage_channels")
    @Mod.is_mod_configured()
    async def unlock(self, ctx: commands.Context, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = True
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        return await ctx.send_success(f"Unlocked {channel.mention}")

    @commands.group(
        invoke_without_command=True,
        help="manage roles in your server",
    )
    @Perms.get_perms("manage_roles")
    async def role(
        self,
        ctx: commands.Context,
        user: discord.Member = None,
        *,
        role: GoodRole = None,
    ):
        if role == None or user == None:
            return await ctx.create_pages()
        if role in user.roles:
            await user.remove_roles(role)
            return await ctx.send_success(
                f"Removed {role.mention} from **{user.name}**"
            )
        else:
            await user.add_roles(role)
            return await ctx.send_success(f"Added {role.mention} to **{user.name}**")

    @role.command(
        help="add a role to an user",
        usage="[user] [role]",
        name="add",
        brief="manage roles",
    )
    @Perms.get_perms("manage_roles")
    async def role_add(
        self, ctx: commands.Context, user: discord.Member, *, role: GoodRole
    ):
        if role in user.roles:
            return await ctx.send_error(f"**{user}** has this role already")
        await user.add_roles(role)
        return await ctx.send_success(f"Added {role.mention} to **{user.name}**")

    @role.command(
        name="remove",
        brief="manage roles",
        help="remove a role from a member",
    )
    @Perms.get_perms("manage_roles")
    async def role_remove(
        self, ctx: commands.Context, user: discord.Member, *, role: GoodRole
    ):
        if not role in user.roles:
            return await ctx.send_error(f"**{user}** doesn't this role")
        await user.remove_roles(role)
        return await ctx.send_success(f"Removed {role.mention} from **{user.name}**")

    @role.command(
        help="create a role",
        usage="[name]",
        brief="manage roles",
    )
    @Perms.get_perms("manage_roles")
    async def create(self, ctx: commands.Context, *, name: str):
        role = await ctx.guild.create_role(
            name=name, reason=f"changed role name by {ctx.author}"
        )
        return await ctx.send_success(f"Created role {role.mention}")

    @role.command(
        help="delete a role",
        usage="[role]",
        brief="manage roles",
    )
    @Perms.get_perms("manage_roles")
    async def delete(self, ctx: commands.Context, *, role: GoodRole):
        await role.delete()
        return await ctx.send_success("Deleted the role")

    @role.group(invoke_without_command=True, help="edit a role")
    async def edit(self, ctx: commands.Context):
        return await ctx.create_pages()

    @edit.command(
        help="make a role visible separately.. or not",
        brief="manage roles",
        usage="[role] [bool <true or false>]",
    )
    @Perms.get_perms("manage_roles")
    async def hoist(self, ctx: commands.Context, role: GoodRole, state: str):
        if not state.lower() in ["true", "false"]:
            return await ctx.send_error(
                f"**{state}** can be only **true** or **false**"
            )
        await role.edit(hoist=bool(state.lower() == "true"))
        return await ctx.send_success(
            f"{f'The role is now hoisted' if role.hoist is True else 'The role is not hoisted anymore'}"
        )

    @edit.command(
        aliases=["pos"],
        help="change a role's position",
        usage="[role] [base role]",
        brief="manage roles",
    )
    @Perms.get_perms("manage_roles")
    async def position(self, ctx: commands.Context, role: GoodRole, position: GoodRole):
        await role.edit(position=position.position)
        return await ctx.send_success(f"Role position changed to `{position.position}`")

    @edit.command(
        help="change a role's icon",
        brief="manage roles",
        usage="[role] <emoji>",
    )
    @Perms.get_perms("manage_roles")
    async def icon(
        self,
        ctx: commands.Context,
        role: GoodRole,
        emoji: Union[discord.PartialEmoji, str],
    ):
        if isinstance(emoji, discord.PartialEmoji):
            by = await emoji.read()
            await role.edit(display_icon=by)
        elif isinstance(emoji, str):
            await role.edit(display_icon=str(emoji))
        return await ctx.send_success("Changed role icon")

    @edit.command(
        brief="manage roles",
        help="change a role's name",
        usage="[role] [name]",
    )
    @Perms.get_perms("manage_roles")
    async def name(self, ctx: commands.Context, role: GoodRole, *, name: str):
        await role.edit(name=name, reason=f"role edited by {ctx.author}")
        return await ctx.send_success(f"Edited the role's name in **{name}**")

    @edit.command(help="change a role's color", usage="[role] [color]")
    @Perms.get_perms("manage_roles")
    async def color(self, ctx: commands.Context, role: GoodRole, *, color: str):
        try:
            color = color.replace("#", "")
            await role.edit(color=int(color, 16), reason=f"role edited by {ctx.author}")
            return await ctx.reply(
                embed=discord.Embed(
                    color=role.color,
                    description=f"{self.bot.yes} {ctx.author.mention}: Changed role's color",
                )
            )
        except:
            return await ctx.send_error("Unable to change the role's color")

    @role.group(
        invoke_without_command=True,
        name="humans",
        help="mass add or remove roles from members",
    )
    async def rolehumans(self, ctx: commands.Context):
        return await ctx.create_pages()

    @rolehumans.command(
        name="remove",
        help="remove a role from all members in this server",
        usage="[role]",
        brief="manage_roles",
    )
    @Perms.get_perms("manage_roles")
    async def rolehumansremove(self, ctx: commands.Context, *, role: GoodRole):
        embed = discord.Embed(
            color=self.bot.color,
            description=f"{ctx.author.mention} Removing {role.mention} from all humans....",
        )
        message = await ctx.reply(embed=embed)
        try:
            for member in [m for m in ctx.guild.members if not m.bot]:
                if not role in member.roles:
                    continue
                await member.remove_roles(role)

            await message.edit(
                embed=discord.Embed(
                    color=self.bot.color,
                    description=f"{self.bot.yes} {ctx.author.mention}: Removed {role.mention} from all humans",
                )
            )
        except Exception:
            await message.edit(
                embed=discord.Embed(
                    color=self.bot.color,
                    description=f"{self.bot.no} {ctx.author.mention}: Unable to remove {role.mention} from all humans",
                )
            )

    @rolehumans.command(
        name="add",
        help="add a role to all humans in this server",
        usage="[role]",
        brief="manage_roles",
    )
    @Perms.get_perms("manage_roles")
    async def rolehumansadd(self, ctx: commands.Context, *, role: GoodRole):
        embed = discord.Embed(
            color=self.bot.color,
            description=f"{ctx.author.mention}: Adding {role.mention} to all humans....",
        )
        message = await ctx.reply(embed=embed)
        try:
            for member in [m for m in ctx.guild.members if not m.bot]:
                if role in member.roles:
                    continue
                await member.add_roles(role)

            await message.edit(
                embed=discord.Embed(
                    color=self.bot.color,
                    description=f"{self.bot.yes} {ctx.author.mention}: Added {role.mention} to all humans",
                )
            )
        except Exception:
            await message.edit(
                embed=discord.Embed(
                    color=self.bot.color,
                    description=f"{self.bot.no} {ctx.author.mention}: Unable to add {role.mention} to all humans",
                )
            )

    @role.group(
        invoke_without_command=True,
        name="bots",
        help="mass add or remove roles from members",
    )
    async def rolebots(self, ctx: commands.Context):
        return await ctx.create_pages()

    @rolebots.command(
        name="remove",
        help="remove a role from all bots in this server",
        usage="[role]",
        brief="manage_roles",
    )
    @Perms.get_perms("manage_roles")
    async def rolebotsremove(self, ctx: commands.Context, *, role: GoodRole):
        embed = discord.Embed(
            color=self.bot.color,
            description=f"{ctx.author.mention} Removing {role.mention} from all bots....",
        )
        message = await ctx.reply(embed=embed)
        try:
            for member in [m for m in ctx.guild.members if m.bot]:
                if not role in member.roles:
                    continue
                await member.remove_roles(role)

            await message.edit(
                embed=discord.Embed(
                    color=self.bot.color,
                    description=f"{self.bot.yes} {ctx.author.mention}: Removed {role.mention} from all bots",
                )
            )
        except Exception:
            await message.edit(
                embed=discord.Embed(
                    color=self.bot.color,
                    description=f"{self.bot.no} {ctx.author.mention}: Unable to remove {role.mention} from all bots",
                )
            )

    @rolebots.command(
        name="add",
        help="add a role to all bots in this server",
        usage="[role]",
        brief="manage_roles",
    )
    @Perms.get_perms("manage_roles")
    async def rolebotsadd(self, ctx: commands.Context, *, role: GoodRole):
        embed = discord.Embed(
            color=self.bot.color,
            description=f"{ctx.author.mention}: Adding {role.mention} to all bots....",
        )
        message = await ctx.reply(embed=embed)
        try:
            for member in [m for m in ctx.guild.members if m.bot]:
                if role in member.roles:
                    continue
                await member.add_roles(role)

            await message.edit(
                embed=discord.Embed(
                    color=self.bot.color,
                    description=f"{self.bot.yes} {ctx.author.mention}: Added {role.mention} to all bots",
                )
            )
        except Exception:
            await message.edit(
                embed=discord.Embed(
                    color=self.bot.color,
                    description=f"{self.bot.no} {ctx.author.mention}: Unable to add {role.mention} to all bots",
                )
            )

    @role.group(
        invoke_without_command=True,
        name="all",
        help="mass add or remove roles from members",
    )
    async def roleall(self, ctx: commands.Context):
        return await ctx.create_pages()

    @roleall.command(
        name="remove",
        help="remove a role from all members in this server",
        usage="[role]",
        brief="manage_roles",
    )
    @Perms.get_perms("manage_roles")
    async def roleallremove(self, ctx: commands.Context, *, role: GoodRole):
        embed = discord.Embed(
            color=self.bot.color,
            description=f"{ctx.author.mention} Removing {role.mention} from all members....",
        )
        message = await ctx.reply(embed=embed)
        try:
            for member in ctx.guild.members:
                if not role in member.roles:
                    continue
                await member.remove_roles(role)

            await message.edit(
                embed=discord.Embed(
                    color=self.bot.color,
                    description=f"{self.bot.yes} {ctx.author.mention}: Removed {role.mention} from all members",
                )
            )
        except Exception:
            await message.edit(
                embed=discord.Embed(
                    color=self.bot.color,
                    description=f"{self.bot.no} {ctx.author.mention}: Unable to remove {role.mention} from all members",
                )
            )

    @roleall.command(
        name="add",
        help="add a role to all members in this server",
        usage="[role]",
        brief="manage_roles",
    )
    @Perms.get_perms("manage_roles")
    async def rolealladd(self, ctx: commands.Context, *, role: GoodRole):
        embed = discord.Embed(
            color=self.bot.color,
            description=f"{ctx.author.mention}: Adding {role.mention} to all members....",
        )
        message = await ctx.reply(embed=embed)
        try:
            for member in ctx.guild.members:
                if role in member.roles:
                    continue
                await member.add_roles(role)

            await message.edit(
                embed=discord.Embed(
                    color=self.bot.color,
                    description=f"{self.bot.yes} {ctx.author.mention}: Added {role.mention} to all members",
                )
            )
        except Exception:
            await message.edit(
                embed=discord.Embed(
                    color=self.bot.color,
                    description=f"{self.bot.no} {ctx.author.mention}: Unable to add {role.mention} to all members",
                )
            )

    @commands.command(
        help="ban a user and instanly unban",
        usage="<user>",
        brief="ban members",
    )
    @Perms.get_perms("ban_members")
    async def softban(self, ctx, member: discord.Member):
        try:
            await ctx.guild.ban(member)
            await ctx.guild.unban(member)
            embed = discord.Embed(
                title="Softban",
                description=f"{member.name} has been softbanned.",
                color=self.bot.color,
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(
                title="Error",
                help="I don't have the permission to softban members.",
                color=self.bot.color,
            )
            await ctx.send(embed=embed)

    @commands.command(
        help="clear all invites in guild",
        usage="",
        brief="administrator",
    )
    @Perms.get_perms("administrator")
    async def clearinvites(self, ctx):
        invites = await ctx.guild.invites()

        for invite in invites:
            await invite.delete()

        embed = discord.Embed(
            title="Clear Invites",
            help="All existing invites have been removed.",
            color=self.bot.color,
        )
        await ctx.send(embed=embed)

    @commands.command(
        name="hide",
        help="Make clust hide a text channel",
        aliases=["hc", "hidechan", "hchannel", "hidechannel"],
        usage="",
        brief="manage channels",
    )
    @Perms.get_perms("manage_channels")
    async def hide(ctx: commands.Context, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        perms = ctx.channel.overwrites_for(ctx.guild.default_role)
        perms.view_channel = False
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=perms)
        await ctx.send(
            embed=discord.Embed(
                help="<:approve:1121826853678747710> {}: successfully hid channel".format(
                    ctx.author.mention
                ),
                color=0x2B2D31,
            )
        )

    @commands.command(
        name="unhide",
        help="Make clust unhide a text channel",
        aliases=["uhc", "unhidechan", "uhchannel", "unhidechannel"],
        usage="",
        brief="manage channels",
    )
    @Perms.get_perms("manage_channels")
    async def unhide(self, ctx: commands.Context, channel: discord.TextChannel = None):
        try:
            channel = channel or ctx.channel
            perms = ctx.channel.overwrites_for(ctx.guild.default_role)
            perms.view_channel = True
            await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=perms)
            await ctx.send(
                embed=discord.Embed(
                    help="<:approve:1121826853678747710> {}: successfully unhid channel".format(
                        ctx.author.mention
                    ),
                    color=0x2B2D31,
                )
            )
        except discord.Forbidden:
            await ctx.send(
                embed=discord.Embed(
                    help="<:watttt:1139317517408546816> {}: I don't have permission to unhide the channel.".format(
                        ctx.author.mention
                    ),
                    color=0x2B2D31,
                )
            )
        except Exception as e:
            await ctx.send(
                embed=discord.Embed(
                    help="<:deny:1121826907739144412> {}: An error occurred while unhiding the channel.".format(
                        ctx.author.mention
                    ),
                    color=0x2B2D31,
                )
            )
            print(e)

    @commands.command(
        name="setname",
        help="Make clust set the servername",
        aliases=["sname", "servername"],
        usage="[name]",
        brief="administrator",
    )
    @Perms.get_perms("administrator")
    async def setname(self, ctx, *, name=None):
        try:
            if name is None:
                raise ValueError("Specify a name for me to set")

            await ctx.guild.edit(name=name)
            await ctx.send(
                embed=discord.Embed(
                    help="<:approve:1121826853678747710>{}: Server name has been set to `{name}`".format(
                        ctx.author.mention
                    ),
                    color=0x2B2D31,
                )
            )
        except discord.Forbidden:
            await ctx.send(
                embed=discord.Embed(
                    help="<:watttt:1139317517408546816> {}: I don't have permission to change the server name.".format(
                        ctx.author.mention
                    ),
                    color=0x2B2D31,
                )
            )
        except ValueError as ve:
            await ctx.send(
                embed=discord.Embed(
                    description=f"<:deny:1121826907739144412> {ctx.author.mention}: {str(ve)}",
                    color=0x2B2D31,
                )
            )

    @commands.command(
        help="make the channel nsfw for 60 seconds",
        usage="[channel]",
        aliases=["nsfwc"],
        brief="manage channels",
    )
    @commands.has_permissions(manage_channels=True)
    async def tempnsfw(self, ctx, channel: discord.TextChannel):
        if not ctx.message.author.guild_permissions.manage_channels:
            return await ctx.send(
                "You don't have the required permissions to manage channels."
            )

        if channel.is_nsfw():
            return await ctx.send("The channel is already marked as NSFW.")

        await ctx.message.delete()

        try:
            await channel.edit(nsfw=True)
            await ctx.send(
                f"The channel {channel.mention} has been marked as NSFW for 60 seconds."
            )
            await asyncio.sleep(60)
            await channel.edit(nsfw=False)
            await ctx.send(
                f"The channel {channel.mention} is no longer marked as NSFW."
            )
        except discord.Forbidden:
            await ctx.send("I don't have the required permissions to manage channels.")

    @commands.command(
        name="setnsfw",
        help="Set the channel to NSFW",
        brief="manage guild",
        usage="",
        aliases=["nsfw", "nsfwchannel"],
    )
    @Perms.get_perms("manage_guild")
    async def set_nsfw(self, ctx):
        if not ctx.author.guild_permissions.manage_channels:
            return await ctx.send("You don't have the permission to manage channels.")

        if ctx.channel.is_nsfw():
            return await ctx.send("This channel is already marked as NSFW.")

        try:
            await ctx.channel.edit(nsfw=True)
            embed = discord.Embed(
                title="NSFW Channel",
                description=f"{ctx.channel.mention} has been set to NSFW.",
                color=self.bot.color,
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("I don't have the permission to set this channel to NSFW.")

    @commands.command(
        name="unsetnsfw",
        help="Set the channel to NSFW",
        brief="manage guild",
        aliases=["unnsfw", "unsfwchannel"],
    )
    @Perms.get_perms("manage_guild")
    async def unset_nsfw(self, ctx):
        if not ctx.author.guild_permissions.manage_channels:
            return await ctx.send("You don't have the permission to manage channels.")

        if not ctx.channel.is_nsfw():
            return await ctx.send("This channel is not marked as NSFW.")

        try:
            await ctx.channel.edit(nsfw=False)
            embed = discord.Embed(
                title="NSFW Channel Removed",
                description=f"{ctx.channel.mention} is no longer an NSFW channel.",
                color=self.bot.color,
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send(
                "I don't have the permission to remove NSFW status from this channel."
            )

    @commands.command(
        help="see all banned members",
    )
    async def bans(self, ctx):
        banned = [m async for m in ctx.guild.bans()]
        if len(banned) == 0:
            return await ctx.send_warning("There are no banned people in this server")
        i = 0
        k = 1
        l = 0
        mes = ""
        number = []
        messages = []
        for m in banned:
            mes = f"{mes}`{k}` **{m.user}** - `{m.reason or 'No reason provided'}` \n"
            k += 1
            l += 1
            if l == 10:
                messages.append(mes)
                number.append(
                    Embed(
                        color=self.bot.color,
                        title=f"banned ({len(banned)})",
                        description=messages[i],
                    )
                )
                i += 1
                mes = ""
                l = 0

        messages.append(mes)
        embed = Embed(
            color=self.bot.color,
            title=f"banned ({len(banned)})",
            description=messages[i],
        )
        number.append(embed)
        await ctx.paginator(number)


async def setup(bot: commands.Bot):
    await bot.add_cog(Mod(bot))
