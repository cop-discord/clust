import discord, random, string, asyncio
from discord.ext import commands
from extensions.control import Perms, Mod
from extensions.utilities import EmbedBuilder
from typing import Union
from extensions.control import Perms as utils


def is_detention():
    async def predicate(ctx: commands.Context):
        check = await ctx.bot.db.fetchrow(
            "SELECT * FROM naughtycorner WHERE guild_id = $1", ctx.guild.id
        )
        if not check:
            await ctx.send_warning("Naughty corner is not configured")
        return check is not None

    return commands.check(predicate)


class Misc(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot

    async def webhook_channel(self, url) -> discord.TextChannel | None:
        r = await self.bot.session.get(url)
        data = (await r.json())["channel_id"]
        return self.bot.get_channel(int(data))

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        naughty = await self.bot.db.fetchrow(
            "SELECT * FROM naughtycorner_members WHERE guild_id = $1 AND user_id = $2",
            member.guild.id,
            member.id,
        )
        if naughty:
            check = await self.bot.db.fetchrow(
                "SELECT * FROM naughtycorner WHERE guild_id = $1", member.guild.id
            )
            if check:
                channel = member.guild.get_channel(int(check["channel_id"]))
                if after.channel.id != channel.id:
                    await member.move_to(
                        channel=channel, reason=f"Moved to the naughty corner"
                    )

    @commands.group(aliases=["detention", "nc"], invoke_without_command=True)
    async def naughtycorner(
        self, ctx: commands.Context, *, member: discord.Member = None
    ):
        if member is None:
            return await ctx.create_pages()
        return await ctx.invoke(
            self.bot.get_command("naughtycorner add"), member=member
        )

    @naughtycorner.command(
        aliases=["configure", "set"],
        brief="manage server",
        usage="[voice channel]",
        name="setup",
        help="configure naughty corner voice channel",
    )
    @Perms.get_perms("manage_guild")
    async def nc_setup(self, ctx: commands.Context, *, channel: discord.VoiceChannel):
        check = await self.bot.db.fetchrow(
            "SELECT * FROM naughtycorner WHERE guild_id = $1", ctx.guild.id
        )
        if check:
            await self.bot.db.execute(
                "UPDATE naughtycorner SET channel_id = $1 WHERE guild_id = $2",
                channel.id,
                ctx.guild.id,
            )
        else:
            await self.bot.db.execute(
                "INSERT INTO naughtycorner VALUES ($1,$2)", ctx.guild.id, channel.id
            )
        return await ctx.send_success(
            f"Naughty corner voice channel configured -> {channel.mention}"
        )

    @naughtycorner.command(
        name="unsetup",
        brief="manage server",
        help="disable naughty corner feature in the server",
    )
    @Perms.get_perms("manage_guild")
    @is_detention()
    async def nc_unsetup(self, ctx: commands.Context):
        await self.bot.db.execute(
            "DELETE FROM naughtycorner WHERE guild_id = $1", ctx.guild.id
        )
        return await ctx.send_success("Naughty corner is now disabled")

    @naughtycorner.command(
        name="add",
        brief="timeout members",
        help="add a member to the naughty corner",
        usage="[member]",
    )
    @Perms.get_perms("moderate_members")
    @is_detention()
    async def nc_add(self, ctx: commands.Context, *, member: discord.Member):
        if await Mod.check_hieracy(ctx, member):
            check = await self.bot.db.fetchrow(
                "SELECT * FROM naughtycorner_members WHERE guild_id = $1 AND user_id = $2",
                ctx.guild.id,
                member.id,
            )
            if check:
                return await ctx.send_warning(
                    "This member is **already** in the naughty corner"
                )
            await self.bot.db.execute(
                "INSERT INTO naughtycorner_members VALUES ($1,$2)",
                ctx.guild.id,
                member.id,
            )
            res = await self.bot.db.fetchrow(
                "SELECT channel_id FROM naughtycorner WHERE guild_id = $1", ctx.guild.id
            )
            channel = ctx.guild.get_channel(int(res["channel_id"]))
            await member.move_to(
                channel=channel, reason=f"Moved to the naughty corner by {ctx.author}"
            )
            return await ctx.send_success(
                f"Moved **{member}** to {channel.mention if channel else '**Naughty Corner**'}"
            )

    @naughtycorner.command(
        name="remove",
        brief="timeout emmbers",
        help="remove a member from the naughty corner",
        usage="[member]",
    )
    @Perms.get_perms("moderate_members")
    @is_detention()
    async def nc_remove(self, ctx: commands.Context, *, member: discord.Member):
        if await Mod.check_hieracy(ctx, member):
            check = await self.bot.db.fetchrow(
                "SELECT * FROM naughtycorner_members WHERE guild_id = $1 AND user_id = $2",
                ctx.guild.id,
                member.id,
            )
            if not check:
                return await ctx.send_warning(
                    "This member is **not** in the naughty corner"
                )
            await self.bot.db.execute(
                "DELETE FROM naughtycorner_members WHERE guild_id = $1 AND user_id = $2",
                ctx.guild.id,
                member.id,
            )
            return await ctx.send_success(
                f"Removed **{member}** from **Naughty Corner**"
            )

    @naughtycorner.command(
        name="members",
        aliases=["list"],
        help="returns members from the naughty corner",
    )
    @is_detention()
    async def nc_list(self, ctx: commands.Context):
        results = await self.bot.db.fetch(
            "SELECT user_id FROM naughtycorner_members WHERE guild_id = $1",
            ctx.guild.id,
        )
        if len(results) == 0:
            return await ctx.send_warning(
                "There are no **naughty** members in this server"
            )
        i = 0
        k = 1
        l = 0
        mes = ""
        number = []
        messages = []
        for result in results:
            mes = f"{mes}`{k}` <@!{result['user_id']}>\n"
            k += 1
            l += 1
            if l == 10:
                messages.append(mes)
                number.append(
                    discord.Embed(
                        color=self.bot.color,
                        title=f"naughty members in {ctx.guild.name} ({len(results)})",
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
                title=f"naughty members in {ctx.guild.name} ({len(results)})",
                description=messages[i],
            )
        )
        await ctx.paginator(number)

    @commands.group(name="webhook", invoke_without_command=True)
    async def webhook(self, ctx):
        await ctx.create_pages()

    @webhook.group(name="edit", invoke_without_command=True, help="edit a webhook")
    async def webhook_edit(self, ctx):
        return await ctx.create_pages()

    @webhook_edit.command(
        name="name",
        help="edit a webhook's name",
        usage="[code] [name]",
        brief="manage server",
    )
    @Perms.get_perms("manage_guild")
    async def webhook_name(self, ctx: commands.Context, code: str, *, name: str):
        check = await self.bot.db.fetchrow(
            "SELECT * FROM webhook WHERE code = $1 AND guild_id = $2",
            code,
            ctx.guild.id,
        )
        if not check:
            return ctx.send_error("No **webhook** associated with this code")
        webhook = discord.Webhook.from_url(check["url"], session=self.bot.session)
        if webhook:
            await webhook.edit(name=name, reason=f"webhook edited by {ctx.author}")
            return await ctx.send_success(f"Webhook name changed in **{name}**")
        else:
            return ctx.send_error(f"No **webhook** found")

    @webhook_edit.command(
        name="avatar",
        aliases=["icon"],
        help="edit a webhook's avatar",
        usage="[code] [image url / attachment]",
        brief="manage server",
    )
    @Perms.get_perms("manage_guild")
    async def webhook_avatar(self, ctx: commands.Context, code: str, link: str = None):
        check = await self.bot.db.fetchrow(
            "SELECT * FROM webhook WHERE code = $1 AND guild_id = $2",
            code,
            ctx.guild.id,
        )
        if not check:
            return ctx.send_error("No **webhook** associated with this code")
        webhook = discord.Webhook.from_url(check["url"], session=self.bot.session)
        if webhook:
            if link is None and len(ctx.message.attachments) == 0:
                return await self.bot.help_command.send_command_help(ctx.command)
            if link:
                link = link
            elif not link and ctx.message.attachments:
                link = ctx.message.attachments[0].url
            try:
                avatar = (await self.bot.getbyte(link)).getvalue()
                await webhook.edit(
                    avatar=avatar, reason=f"webhook avatar changed by {ctx.author}"
                )
                return await ctx.send_success(f"Webhook avatar changed")
            except:
                return await ctx.send_warning(
                    "Unable to change the **webhook's** avatar"
                )
        else:
            return ctx.send_error(f"No **webhook** found")

    ""

    @webhook.command(
        name="create",
        aliases=["add"],
        help="create a webhook in a channel",
        usage="[channel] <name>",
        brief="manage server",
    )
    @Perms.get_perms("manage_guild")
    async def webhook_create(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel,
        *,
        name: str = "clust",
    ):
        avatar_response = await self.bot.session.get(ctx.guild.me.display_avatar.url)
        avatar = await avatar_response.read()

        webhook = await channel.create_webhook(
            name=name,
            avatar=avatar,
            reason=f"webhook created by {ctx.author}",
        )
        code = "".join(
            random.choice(string.ascii_letters + string.digits) for _ in range(5)
        )
        await self.bot.db.execute(
            "INSERT INTO webhook VALUES ($1,$2,$3,$4)",
            ctx.guild.id,
            channel.id,
            code,
            webhook.url,
        )
        return await ctx.send_success(
            f"Webhook created in {channel.mention} with the code `{code}`"
        )

    @webhook.command(
        name="delete",
        aliases=["remove"],
        brief="manage server",
        help="delete a webhook from a channel",
        usage="[code]",
    )
    @Perms.get_perms("manage_guild")
    async def webhook_delete(self, ctx: commands.Context, code: str):
        check = await self.bot.db.fetchrow(
            "SELECT * FROM webhook WHERE code = $1 AND guild_id = $2",
            code,
            ctx.guild.id,
        )
        if not check:
            return ctx.send_error("No **webhook** associated with this code")
        webhook = discord.Webhook.from_url(check["url"], session=self.bot.session)
        if webhook:
            try:
                await webhook.delete(reason=f"webhook deleted by {ctx.author}")
            except:
                pass
        await self.bot.db.execute(
            "DELETE FROM webhook WHERE code = $1 AND guild_id = $2", code, ctx.guild.id
        )
        await ctx.send_success("Deleted the webhook")

    @webhook.command(
        name="send",
        aliases=["post"],
        help="send a message via a webhook using a code",
        brief="manage server",
    )
    @Perms.get_perms("manage_guild")
    async def webhook_send(self, ctx: commands.Context, code: str, *, message: str):
        check = await self.bot.db.fetchrow(
            "SELECT * FROM webhook WHERE code = $1 AND guild_id = $2",
            code,
            ctx.guild.id,
        )
        if not check:
            return ctx.send_error("No **webhook** associated with this code")
        webhook = discord.Webhook.from_url(check["url"], session=self.bot.session)
        if not webhook:
            return ctx.send_error(f"No **webhook** found")
        channel = await self.webhook_channel(check["url"])
        webhooks = [w for w in await channel.webhooks() if w.url == webhook.url][0]
        try:
            x = await EmbedBuilder.to_object(
                EmbedBuilder.embed_replacement(ctx.author, message)
            )
            await webhooks.send(content=x[0], embed=x[1], view=x[2])
        except Exception as e:
            await webhook.send(message)
            print(e)
        await ctx.message.add_reaction("<:blue_guy_thumbs_up:1126833290867908660>")

    @webhook.command(
        name="list",
        help="shows a list of available webhooks in the server",
        aliases=["view"],
    )
    async def webhook_list(self, ctx: commands.Context):
        results = await self.bot.db.fetch(
            "SELECT * FROM webhook WHERE guild_id = $1", ctx.guild.id
        )
        if len(results) == 0:
            return await ctx.send_warning(
                "There are no **webhooks** created by the bot in this server"
            )
        i = 0
        k = 1
        l = 0
        mes = ""
        number = []
        messages = []
        for result in results:
            mes = f"{mes}`{k}` <#{result['channel_id']}> - `{result['code']}`\n"
            k += 1
            l += 1
            if l == 10:
                messages.append(mes)
                number.append(
                    discord.Embed(
                        color=self.bot.color,
                        title=f"webhooks in {ctx.guild.name} ({len(results)})",
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
                title=f"webhooks in {ctx.guild.name} ({len(results)})",
                description=messages[i],
            )
        )
        await ctx.paginator(number)

    @commands.command(
        aliases=["downloademoji", "e", "jumbo"],
        help="gets an image version of your emoji",
        usage="[emoji]",
    )
    async def enlarge(
        self, ctx: commands.Context, emoj: Union[discord.PartialEmoji, str]
    ):
        if isinstance(emoj, discord.PartialEmoji):
            return await ctx.reply(
                file=await emoj.to_file(
                    filename=f"{emoj.name}{'.gif' if emoj.animated else '.png'}"
                )
            )
        elif isinstance(emoj, str):
            return await ctx.reply(
                file=discord.File(
                    fp=await self.bot.getbyte(
                        f"https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/72x72/{ord(emoj):x}.png"
                    ),
                    filename="emoji.png",
                )
            )

    @commands.command(aliases=["ei"], help="show emoji info", usage="[emoji]")
    async def emojiinfo(
        self,
        ctx: commands.Context,
        *,
        emoji: Union[discord.Emoji, discord.PartialEmoji],
    ):
        embed = discord.Embed(
            color=self.bot.color, title=emoji.name, timestamp=emoji.created_at
        ).set_footer(text=f"id: {emoji.id}")
        embed.set_thumbnail(url=emoji.url)
        embed.add_field(name="Animated", value=emoji.animated)
        embed.add_field(name="Link", value=f"[emoji]({emoji.url})")
        if isinstance(emoji, discord.Emoji):
            embed.add_field(name="Guild", value=emoji.guild.name)
            embed.add_field(name="Usable", value=emoji.is_usable())
            embed.add_field(name="Available", value=emoji.available)
            emo = await emoji.guild.fetch_emoji(emoji.id)
            embed.add_field(name="Created by", value=str(emo.user))
        return await ctx.reply(embed=embed)

    @commands.command(
        help="returns a list of server's emojis",
        aliases=["emojis"],
    )
    async def emojilist(self, ctx: commands.Context):
        i = 0
        k = 1
        l = 0
        mes = ""
        number = []
        messages = []
        for emoji in ctx.guild.emojis:
            mes = f"{mes}`{k}` {emoji} - ({emoji.name})\n"
            k += 1
            l += 1
            if l == 10:
                messages.append(mes)
                number.append(
                    discord.Embed(
                        color=self.bot.color,
                        title=f"emojis in {ctx.guild.name} [{len(ctx.guild.emojis)}]",
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
                title=f"emojis in {ctx.guild.name} [{len(ctx.guild.emojis)}]",
                description=messages[i],
            )
        )
        await ctx.paginator(number)

    @commands.command(
        name="delete",
        help="delete a sticker",
        usage="[attach sticker]",
        brief="manage emojis",
    )
    @utils.get_perms("manage_emojis")
    async def sticker_delete(self, ctx: commands.Context):
        if ctx.message.stickers:
            sticker = ctx.message.stickers[0]
            sticker = await sticker.fetch()
            if sticker.guild.id != ctx.guild.id:
                return await ctx.send_warning("This sticker is not from this server")
            await sticker.delete(reason=f"sticker deleted by {ctx.author}")
            return await ctx.send_success("Deleted the sticker")
        async for message in ctx.channel.history(limit=10):
            if message.stickers:
                sticker = message.stickers[0]
                s = await sticker.fetch()
                if s.guild_id == ctx.guild.id:
                    embed = discord.Embed(
                        color=self.bot.color,
                        description=f"Are you sure you want to delete `{s.name}`?",
                    ).set_image(url=s.url)
                    button1 = discord.ui.Button(emoji="<:approve:1121826853678747710>")
                    button2 = discord.ui.Button(emoji="<:deny:1121826907739144412>")

                    async def button1_callback(interaction: discord.Interaction):
                        if ctx.author.id != interaction.user.id:
                            return await self.bot.ext.send_warning(
                                interaction, "You are not the author of this embed"
                            )
                        await s.delete()
                        return await interaction.response.edit_message(
                            embed=discord.Embed(
                                color=self.bot.color,
                                description=f"{self.bot.yes} {interaction.user.mention}: Deleted sticker",
                            ),
                            view=None,
                        )

                    async def button2_callback(interaction: discord.Interaction):
                        if ctx.author.id != interaction.user.id:
                            return await self.bot.ext.send_warning(
                                interaction, "You are not the author of this embed"
                            )
                        return await interaction.response.edit_message(
                            embed=discord.Embed(
                                color=self.bot.color,
                                description=f"{interaction.user.mention}",
                            )
                        )

                    button1.callback = button1_callback
                    button2.callback = button2_callback
                    view = discord.ui.View()
                    view.add_item(button1)
                    view.add_item(button2)
                    return await ctx.reply(embed=embed, view=view)

    @commands.command(
        help="delete an emoji",
        usage="[emoji]",
        brief="manage emojis",
        aliases=["delemoji"],
    )
    @utils.get_perms("manage_emojis")
    async def deleteemoji(self, ctx: commands.Context, emoji: discord.Emoji):
        await emoji.delete()
        await ctx.send_success("Deleted the emoji")

    @commands.command(
        help="add an emoji",
        usage="[emoji] <name>",
        brief="manage emojis",
        aliases=["steal"],
    )
    @utils.get_perms("manage_emojis")
    async def addemoji(
        self,
        ctx: commands.Context,
        emoji: Union[discord.Emoji, discord.PartialEmoji],
        *,
        name: str = None,
    ):
        if not name:
            name = emoji.name
        try:
            emoji = await ctx.guild.create_custom_emoji(
                image=await emoji.read(), name=name
            )
            await ctx.send_success(f"added emoji `{name}` | {emoji}".capitalize())
        except discord.HTTPException as e:
            return await ctx.send_error(ctx, f"Unable to add the emoji | {e}")

    @commands.command(
        help="add multiple emojis",
        usage="[emojis]",
        aliases=["am"],
        brief="manage emojis",
    )
    @utils.get_perms("manage_emojis")
    async def addmultiple(
        self, ctx: commands.Context, *emoji: Union[discord.Emoji, discord.PartialEmoji]
    ):
        if len(emoji) == 0:
            return await ctx.send_warning("Please provide some emojis to add")
        emojis = []
        await ctx.channel.typing()
        for emo in emoji:
            try:
                emoj = await ctx.guild.create_custom_emoji(
                    image=await emo.read(), name=emo.name
                )
                emojis.append(f"{emoj}")
                await asyncio.sleep(0.5)
            except discord.HTTPException as e:
                return await ctx.send_error(ctx, f"Unable to add the emoji | {e}")

        embed = discord.Embed(color=self.bot.color, title=f"added {len(emoji)} emojis")
        embed.description = "".join(map(str, emojis))
        return await ctx.reply(embed=embed)

    @commands.command(
        name="stickerenlarge",
        aliases=["stickere", "stickerjumbo"],
        help="returns a sticker as a file",
        usage="[attach sticker]",
    )
    async def stickerenlarge(self, ctx: commands.Context):
        if ctx.message.stickers:
            stick = ctx.message.stickers[0]
        else:
            messages = [m async for m in ctx.channel.history(limit=20) if m.stickers]
            if len(messages) == 0:
                return await ctx.send_warning("No sticker found")
            stick = messages[0].stickers[0]
        return await ctx.reply(file=await stick.to_file(filename=f"{stick.name}.png"))


async def setup(bot: commands.AutoShardedBot) -> None:
    await bot.add_cog(Misc(bot))
