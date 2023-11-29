import discord
from discord.ext import commands
from discord.ui import Modal, Select, View
from extensions.control import Perms

unlockemoji = "<:unlck:1126829783590895748>"
lockemoji = "<:lck:1126829779346259978>"
plusemoji = "<:plus:1126829792755466300>"
minusemoji = "<:minus:1126829788007510197>"
channelemoji = "<:channel:1136343398350082099>"
unghostemoji = "<:unghost:1126829806303051847>"
ghostemoji = "<:ghxst:1126829801697722458>"
claimemoji = "<:claims:1126829797046226984>"
hammeremoji = "<:bxnhammer:1126829770928304178>"
manemoji = "<:manuser:1126829775122600016>"


async def check_owner(ctx: commands.Context):
    check = await ctx.bot.db.fetchrow(
        "SELECT * FROM vcs WHERE voice = $1 AND user_id = $2",
        ctx.author.voice.channel.id,
        ctx.author.id,
    )
    if check is None:
        await ctx.bot.ext.send_warning(
            ctx, "You are not the owner of this voice channel"
        )
        return True


async def check_voice(ctx: commands.Context):
    check = await ctx.bot.db.fetchrow(
        "SELECT * FROM voicemaster WHERE guild_id = $1", ctx.guild.id
    )
    if check is not None:
        channeid = check[1]
        voicechannel = ctx.guild.get_channel(channeid)
        category = voicechannel.category
        if ctx.author.voice is None:
            await ctx.bot.ext.send_warning(ctx, "You are not in a voice channel")
            return True
        elif ctx.author.voice is not None:
            if ctx.author.voice.channel.category != category:
                await ctx.bot.ext.send_warning(
                    ctx, "You are not in a voice channel created by the bot"
                )
                return True


async def check_vc(interaction: discord.Interaction, category: discord.CategoryChannel):
    if interaction.user.voice is None:
        await interaction.client.ext.send_warning(
            interaction, "You are not in a voice channel", ephemeral=True
        )
        return False
    elif interaction.user.voice is not None:
        if interaction.user.voice.channel.category != category:
            await interaction.client.ext.send_warning(
                interaction,
                "You are not in a voice channel created by the bot",
                ephemeral=True,
            )
            return False
        return True


def check_vc_owner():
    async def predicate(ctx: commands.Context):
        voice = await check_voice(ctx)
        owner = await check_owner(ctx)
        if voice is True or owner is True:
            return False
        return True

    return commands.check(predicate)


class vcModal(Modal, title="rename your voice channel"):
    name = discord.ui.TextInput(
        label="voice channel name",
        placeholder="give your channel a better name",
        required=True,
        style=discord.TextStyle.short,
    )

    async def on_submit(self, interaction: discord.Interaction):
        name = self.name.value
        try:
            await interaction.user.voice.channel.edit(name=name)
            await interaction.client.ext.send_success(
                interaction, f"voice channel renamed to **{name}**", ephemeral=True
            )
        except Exception as er:
            await interaction.client.send_error(
                interaction, f"an error occured -> {er}", ephemeral=True
            )


class vmbuttons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="",
        emoji=lockemoji,
        style=discord.ButtonStyle.gray,
        custom_id="persistent_view:lock",
    )
    async def lock(self, interaction: discord.Interaction, button: discord.ui.Button):
        check = await interaction.client.db.fetchrow(
            "SELECT * FROM voicemaster WHERE guild_id = $1", interaction.guild.id
        )
        if check is not None:
            channeid = check["channel_id"]
            voicechannel = interaction.guild.get_channel(channeid)
            category = voicechannel.category
            if await check_vc(interaction, category) is False:
                return
            che = await interaction.client.db.fetchrow(
                "SELECT * FROM vcs WHERE voice = $1 AND user_id = $2",
                interaction.user.voice.channel.id,
                interaction.user.id,
            )
            if che is None:
                return await interaction.client.ext.send_warning(
                    interaction,
                    "you don't own this voice channel".capitalize(),
                    ephemeral=True,
                )
            elif che is not None:
                await interaction.user.voice.channel.set_permissions(
                    interaction.guild.default_role, connect=False
                )
                await interaction.client.ext.send_success(
                    interaction,
                    f"locked <#{interaction.user.voice.channel.id}>",
                    ephemeral=True,
                )

    @discord.ui.button(
        label="",
        emoji=unlockemoji,
        style=discord.ButtonStyle.gray,
        custom_id="persistent_view:unlock",
    )
    async def unlock(self, interaction: discord.Interaction, button: discord.ui.Button):
        check = await interaction.client.db.fetchrow(
            "SELECT * FROM voicemaster WHERE guild_id = $1", interaction.guild.id
        )
        if check is not None:
            channeid = check["channel_id"]
            voicechannel = interaction.guild.get_channel(channeid)
            category = voicechannel.category
            if await check_vc(interaction, category) is False:
                return
            che = await interaction.client.db.fetchrow(
                "SELECT * FROM vcs WHERE voice = $1 AND user_id = $2",
                interaction.user.voice.channel.id,
                interaction.user.id,
            )
            if che is None:
                return await interaction.client.ext.send_warning(
                    interaction,
                    "you don't own this voice channel".capitalize(),
                    ephemeral=True,
                )
            elif che is not None:
                await interaction.user.voice.channel.set_permissions(
                    interaction.guild.default_role, connect=True
                )
                await interaction.client.ext.send_success(
                    interaction,
                    f"unlocked <#{interaction.user.voice.channel.id}>",
                    ephemeral=True,
                )

    @discord.ui.button(
        label="",
        emoji=unghostemoji,
        style=discord.ButtonStyle.gray,
        custom_id="persistent_view:reveal",
    )
    async def reveal(self, interaction: discord.Interaction, button: discord.ui.Button):
        check = await interaction.client.db.fetchrow(
            "SELECT * FROM voicemaster WHERE guild_id = $1", interaction.guild.id
        )
        if check is not None:
            channeid = check["channel_id"]
            voicechannel = interaction.guild.get_channel(channeid)
            category = voicechannel.category
            if await check_vc(interaction, category) is False:
                return
            if (
                not await interaction.client.db.fetchrow(
                    "SELECT * FROM authorize WHERE guild_id = $1", interaction.guild.id
                )
                and not await interaction.client.db.fetchrow(
                    "SELECT * FROM donor WHERE user_id = $1", interaction.user.id
                )
                and not interaction.guild.id in interaction.client.main_guilds
            ):
                return await interaction.client.ext.send_warning(
                    interaction,
                    "This server wasn't **upgraded** to **premium**. Join [here](https://discord.gg/clust) to upgrade!",
                    ephemeral=True,
                )
            che = await interaction.client.db.fetchrow(
                "SELECT * FROM vcs WHERE voice = $1 AND user_id = $2",
                interaction.user.voice.channel.id,
                interaction.user.id,
            )
            if che is None:
                return await interaction.client.ext.send_warning(
                    interaction,
                    "you don't own this voice channel".capitalize(),
                    ephemeral=True,
                )
            elif che is not None:
                await interaction.user.voice.channel.set_permissions(
                    interaction.guild.default_role, view_channel=True
                )
                await interaction.client.ext.send_success(
                    interaction,
                    f"revealed <#{interaction.user.voice.channel.id}>",
                    ephemeral=True,
                )

    @discord.ui.button(
        label="",
        emoji=ghostemoji,
        style=discord.ButtonStyle.gray,
        custom_id="persistent_view:hide",
    )
    async def hide(self, interaction: discord.Interaction, button: discord.ui.Button):
        check = await interaction.client.db.fetchrow(
            "SELECT * FROM voicemaster WHERE guild_id = $1", interaction.guild.id
        )
        if check is not None:
            channeid = check["channel_id"]
            voicechannel = interaction.guild.get_channel(channeid)
            category = voicechannel.category
            if await check_vc(interaction, category) is False:
                return
            if (
                not await interaction.client.db.fetchrow(
                    "SELECT * FROM authorize WHERE guild_id = $1", interaction.guild.id
                )
                and not await interaction.client.db.fetchrow(
                    "SELECT * FROM donor WHERE user_id = $1", interaction.user.id
                )
                and not interaction.guild.id in interaction.client.main_guilds
            ):
                return await interaction.client.ext.send_warning(
                    interaction,
                    "This server wasn't **upgraded** to **premium**. Join [here](https://discord.gg/clust) to upgrade!",
                    ephemeral=True,
                )
            che = await interaction.client.db.fetchrow(
                "SELECT * FROM vcs WHERE voice = $1 AND user_id = $2",
                interaction.user.voice.channel.id,
                interaction.user.id,
            )
            if che is None:
                return await interaction.client.ext.send_warning(
                    interaction,
                    "you don't own this voice channel".capitalize(),
                    ephemeral=True,
                )
            elif che is not None:
                await interaction.user.voice.channel.set_permissions(
                    interaction.guild.default_role, view_channel=False
                )
                await interaction.client.ext.send_success(
                    interaction,
                    f"hidden <#{interaction.user.voice.channel.id}>",
                    ephemeral=True,
                )

    @discord.ui.button(
        label="",
        emoji=channelemoji,
        style=discord.ButtonStyle.gray,
        custom_id="persistent_view:rename",
    )
    async def rename(self, interaction: discord.Interaction, button: discord.ui.Button):
        check = await interaction.client.db.fetchrow(
            "SELECT * FROM voicemaster WHERE guild_id = $1", interaction.guild.id
        )
        if check is not None:
            channeid = check["channel_id"]
            voicechannel = interaction.guild.get_channel(channeid)
            category = voicechannel.category
            if await check_vc(interaction, category) is False:
                return
            che = await interaction.client.db.fetchrow(
                "SELECT * FROM vcs WHERE voice = $1 AND user_id = $2",
                interaction.user.voice.channel.id,
                interaction.user.id,
            )
            if che is None:
                return await interaction.client.ext.send_warning(
                    interaction,
                    "you don't own this voice channel".capitalize(),
                    ephemeral=True,
                )
            elif che is not None:
                rename = vcModal()
                await interaction.response.send_modal(rename)

    @discord.ui.button(
        label="",
        emoji=plusemoji,
        style=discord.ButtonStyle.gray,
        custom_id="persistent_view:increase",
    )
    async def increase(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        check = await interaction.client.db.fetchrow(
            "SELECT * FROM voicemaster WHERE guild_id = $1", interaction.guild.id
        )
        if check is not None:
            channeid = check["channel_id"]
            voicechannel = interaction.guild.get_channel(channeid)
            category = voicechannel.category
            if await check_vc(interaction, category) is False:
                return
            che = await interaction.client.db.fetchrow(
                "SELECT * FROM vcs WHERE voice = $1 AND user_id = $2",
                interaction.user.voice.channel.id,
                interaction.user.id,
            )
            if che is None:
                return await interaction.client.ext.send_warning(
                    interaction,
                    "you don't own this voice channel".capitalize(),
                    ephemeral=True,
                )
            elif che is not None:
                limit = interaction.user.voice.channel.user_limit
                if limit == 99:
                    return await interaction.client.ext.send_warning(
                        interaction,
                        f"I can't increase the limit for <#{interaction.user.voice.channel.id}>",
                        ephemeral=True,
                    )
                res = limit + 1
                await interaction.user.voice.channel.edit(user_limit=res)
                await interaction.client.ext.send_success(
                    interaction,
                    f"increased <#{interaction.user.voice.channel.id}> limit to **{res}** members",
                    ephemeral=True,
                )

    @discord.ui.button(
        label="",
        emoji=minusemoji,
        style=discord.ButtonStyle.gray,
        custom_id="persistent_view:decrease",
    )
    async def decrease(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        check = await interaction.client.db.fetchrow(
            "SELECT * FROM voicemaster WHERE guild_id = $1", interaction.guild.id
        )
        if check is not None:
            channeid = check["channel_id"]
            voicechannel = interaction.guild.get_channel(channeid)
            category = voicechannel.category
            if await check_vc(interaction, category) is False:
                return
            che = await interaction.client.db.fetchrow(
                "SELECT * FROM vcs WHERE voice = $1 AND user_id = $2",
                interaction.user.voice.channel.id,
                interaction.user.id,
            )
            if che is None:
                return await interaction.client.ext.send_warning(
                    interaction,
                    "you don't own this voice channel".capitalize(),
                    ephemeral=True,
                )
            elif che is not None:
                limit = interaction.user.voice.channel.user_limit
                if limit == 0:
                    return await interaction.client.ext.send_warning(
                        interaction,
                        f"I can't decrease the limit for <#{interaction.user.voice.channel.id}>",
                        ephemeral=True,
                    )
                res = limit - 1
                await interaction.user.voice.channel.edit(user_limit=res)
                await interaction.client.ext.send_success(
                    interaction,
                    f"decreased <#{interaction.user.voice.channel.id}> limit to **{res}** members",
                    ephemeral=True,
                )

    @discord.ui.button(
        label="",
        emoji=claimemoji,
        style=discord.ButtonStyle.gray,
        custom_id="persistent_view:claim",
    )
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        check = await interaction.client.db.fetchrow(
            "SELECT * FROM voicemaster WHERE guild_id = $1", interaction.guild.id
        )
        if check is not None:
            channeid = check["channel_id"]
            voicechannel = interaction.guild.get_channel(channeid)
            category = voicechannel.category
            if await check_vc(interaction, category) is False:
                return
            che = await interaction.client.db.fetchrow(
                "SELECT * FROM vcs WHERE voice = $1", interaction.user.voice.channel.id
            )
            memberid = che["user_id"]
            member = interaction.guild.get_member(memberid)
            if member.id == interaction.user.id:
                return await interaction.client.ext.send_warning(
                    interaction,
                    "You are already the owner of this voice channel",
                    ephemeral=True,
                )
            if member in interaction.user.voice.channel.members:
                return await interaction.client.ext.send_warning(
                    interaction,
                    "The owner is still in the voice channel",
                    ephemeral=True,
                )
            else:
                await interaction.client.db.execute(
                    f"UPDATE vcs SET user_id = $1 WHERE voice = $2",
                    interaction.user.id,
                    interaction.user.voice.channel.id,
                )
                return await interaction.client.ext.send_success(
                    interaction,
                    "You are the new owner of this voice channel",
                    ephemeral=True,
                )

    @discord.ui.button(
        label="",
        emoji=manemoji,
        style=discord.ButtonStyle.gray,
        custom_id="persistent_view:info",
    )
    async def info(self, interaction: discord.Interaction, button: discord.ui.Button):
        check = await interaction.client.db.fetchrow(
            "SELECT * FROM voicemaster WHERE guild_id = $1", interaction.guild.id
        )
        if not interaction.user.voice:
            return await interaction.client.ext.send_warning(
                interaction, "You are not in a voice channel", ephemeral=True
            )
        if check is not None:
            che = await interaction.client.db.fetchrow(
                "SELECT * FROM vcs WHERE voice = $1", interaction.user.voice.channel.id
            )
            if che is not None:
                memberid = che["user_id"]
                member = interaction.guild.get_member(memberid)
                embed = discord.Embed(
                    color=interaction.client.color,
                    title=interaction.user.voice.channel.name,
                    description=f"owner: **{member}** (`{member.id}`)\ncreated: **{discord.utils.format_dt(interaction.user.voice.channel.created_at, style='R')}**\nbitrate: **{interaction.user.voice.channel.bitrate/1000}kbps**\nconnected: **{len(interaction.user.voice.channel.members)} member{'s' if len(interaction.user.voice.channel.members) > 1 else ''}**",
                )
                embed.set_author(
                    name=interaction.user.name, icon_url=interaction.user.display_avatar
                )
                embed.set_thumbnail(url=member.display_avatar)
                await interaction.response.send_message(
                    embed=embed, view=None, ephemeral=True
                )

    @discord.ui.button(
        label="",
        emoji=hammeremoji,
        style=discord.ButtonStyle.gray,
        custom_id="persistent_view:activity",
    )
    async def activity(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        check = await interaction.client.db.fetchrow(
            "SELECT * FROM voicemaster WHERE guild_id = $1", interaction.guild.id
        )
        if check is not None:
            channeid = check["channel_id"]
            voicechannel = interaction.guild.get_channel(channeid)
            category = voicechannel.category
            if await check_vc(interaction, category) is False:
                return
            che = await interaction.client.db.fetchrow(
                "SELECT * FROM vcs WHERE voice = $1 AND user_id = $2",
                interaction.user.voice.channel.id,
                interaction.user.id,
            )
            if che is None:
                return await interaction.client.ext.send_warning(
                    interaction,
                    "you don't own this voice channel".capitalize(),
                    ephemeral=True,
                )
            if (
                not await interaction.client.db.fetchrow(
                    "SELECT * FROM authorize WHERE guild_id = $1", interaction.guild.id
                )
                and not interaction.guild.id in interaction.client.main_guilds
            ):
                return await interaction.client.ext.send_warning(
                    interaction,
                    "This server wasn't **upgraded** to **premium**. Join [here](https://discord.gg/clust) to upgrade!",
                    ephemeral=True,
                )
            if len(interaction.user.voice.channel.members) == 1:
                return await interaction.response.send_message(
                    embed=discord.Embed(
                        color=interaction.client.color,
                        description=f"{interaction.client.warning} {interaction.user.mention}: You are the only person in the voice channel",
                    ),
                    ephemeral=True,
                )
            em = discord.Embed(
                color=interaction.client.color,
                title="VoiceMaster Moderation Menu",
                description="Moderate your voice channel using the menu below",
            )
            options = [
                discord.SelectOption(
                    label="mute",
                    description="mute member in the voice channel",
                    emoji="<:muted:1126831997596205136>",
                ),
                discord.SelectOption(
                    label="unmute",
                    description="unmute members in the voice channel",
                    emoji="<:unmuted:1126831992399482932>",
                ),
                discord.SelectOption(
                    label="deafen",
                    description="deafen members in your voice channel",
                    emoji="<:deafened:1126831978604400640>",
                ),
                discord.SelectOption(
                    label="undeafen",
                    emoji="<:undeafened:1126831987714433106>",
                    description="undeafen members in your voice channel",
                ),
                discord.SelectOption(
                    label="kick",
                    description="kick members from your voice channel",
                    emoji="<:bxnhammer:1126829770928304178>",
                ),
            ]
            select = discord.ui.Select(
                options=options, placeholder="select category..."
            )
            members = []
            for member in interaction.user.voice.channel.members:
                if member.id == interaction.user.id:
                    continue
                members.append(
                    discord.SelectOption(
                        label=member.name + "#" + member.discriminator, value=member.id
                    )
                )

            async def select_callback(interactio: discord.Interaction):
                if select.values[0] == "mute":
                    e = discord.Embed(
                        color=interaction.client.color,
                        title="VoiceMaster Moderation | Mute Members",
                        description="mute members in your voice channel",
                    )
                    sel = Select(
                        options=members,
                        placeholder="select members...",
                        min_values=1,
                        max_values=len(members),
                    )

                    async def sel_callback(interacti: discord.Interaction):
                        for s in sel.values:
                            await interacti.guild.get_member(int(s)).edit(
                                mute=True, reason=f"muted by {interacti.user}"
                            )

                        embede = discord.Embed(
                            color=interaction.client.color,
                            description="{} {}: Muted all members".format(
                                interaction.client.yes, interacti.user.mention
                            ),
                        )
                        await interacti.response.edit_message(embed=embede, view=None)

                    sel.callback = sel_callback

                    vi = View()
                    vi.add_item(sel)
                    await interactio.response.send_message(
                        embed=e, view=vi, ephemeral=True
                    )

                elif select.values[0] == "unmute":
                    e = discord.Embed(
                        color=interaction.client.color,
                        title="VoiceMaster Moderation | Unmute Members",
                        description="unmute members in your voice channel",
                    )
                    sel = Select(
                        options=members,
                        placeholder="select members...",
                        min_values=1,
                        max_values=len(members),
                    )

                    async def sel_callback(interacti: discord.Interaction):
                        for s in sel.values:
                            await interacti.guild.get_member(int(s)).edit(
                                mute=False, reason=f"unmuted by {interacti.user}"
                            )

                        embede = discord.Embed(
                            color=interaction.client.color,
                            description="{} {}: Unuted all members".format(
                                interaction.client.yes, interacti.user.mention
                            ),
                        )
                        await interacti.response.edit_message(embed=embede, view=None)

                    sel.callback = sel_callback

                    vi = View()
                    vi.add_item(sel)
                    await interactio.response.send_message(
                        embed=e, view=vi, ephemeral=True
                    )

                if select.values[0] == "deafen":
                    e = discord.Embed(
                        color=interaction.client.color,
                        title="VoiceMaster Moderation | Deafen Members",
                        description="deafen members in your voice channel",
                    )
                    sel = Select(
                        options=members,
                        placeholder="select members...",
                        min_values=1,
                        max_values=len(members),
                    )

                    async def sel_callback(interacti: discord.Interaction):
                        for s in sel.values:
                            await interacti.guild.get_member(int(s)).edit(
                                deafen=True, reason=f"deafened by {interacti.user}"
                            )

                        embede = discord.Embed(
                            color=interaction.client.color,
                            description="{} {}: Deafened all members".format(
                                interaction.client.yes, interacti.user.mention
                            ),
                        )
                        await interacti.response.edit_message(embed=embede, view=None)

                    sel.callback = sel_callback

                    vi = View()
                    vi.add_item(sel)
                    await interactio.response.send_message(
                        embed=e, view=vi, ephemeral=True
                    )

                elif select.values[0] == "undeafen":
                    e = discord.Embed(
                        color=interaction.client.color,
                        title="VoiceMaster Moderation | Undeafen Members",
                        description="undeafen members in your voice channel",
                    )
                    sel = Select(
                        options=members,
                        placeholder="select members...",
                        min_values=1,
                        max_values=len(members),
                    )

                    async def sel_callback(interacti: discord.Interaction):
                        for s in sel.values:
                            await interacti.guild.get_member(int(s)).edit(
                                deafen=False, reason=f"undeafened by {interacti.user}"
                            )

                        embede = discord.Embed(
                            color=interaction.client.color,
                            description="{} {}: Undeafened all members".format(
                                interaction.client.yes, interacti.user.mention
                            ),
                        )
                        await interacti.response.edit_message(embed=embede, view=None)

                    sel.callback = sel_callback

                    vi = View()
                    vi.add_item(sel)
                    await interactio.response.send_message(
                        embed=e, view=vi, ephemeral=True
                    )

                elif select.values[0] == "kick":
                    e = discord.Embed(
                        color=interaction.client.color,
                        title="VoiceMaster Moderation | Kick Members",
                        description="kick members from your voice channel",
                    )
                    sel = Select(
                        options=members,
                        placeholder="select members...",
                        min_values=1,
                        max_values=len(members),
                    )

                    async def sel_callback(interacti: discord.Interaction):
                        for s in sel.values:
                            await interacti.guild.get_member(int(s)).move_to(
                                channel=None,
                                reason="kicked by {}".format(interacti.user),
                            )

                        embede = discord.Embed(
                            color=interaction.client.color,
                            description="{} {}: Kicked all members".format(
                                interaction.client.yes, interacti.user.mention
                            ),
                        )
                        await interacti.response.edit_message(embed=embede, view=None)

                    sel.callback = sel_callback

                    vi = View()
                    vi.add_item(sel)
                    await interactio.response.send_message(
                        embed=e, view=vi, ephemeral=True
                    )

            select.callback = select_callback

            view = View()
            view.add_item(select)
            await interaction.response.send_message(embed=em, view=view, ephemeral=True)


class Voicemaster(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot

    def create_interface(self, ctx: commands.Context) -> discord.Embed:
        em = discord.Embed(
            color=self.bot.color,
            title="VoiceMaster Interface",
            description="click the buttons below to control the voice channel",
        )
        em.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
        em.add_field(
            name="Manage",
            value=f"{lockemoji} [`lock`](https://discord.gg/clust) the voice channel\n{unlockemoji} [`unlock`](https://discord.gg/clust) the voice channel\n{ghostemoji} [`hide`](https://discord.gg/clust) the voice channel\n{unghostemoji} [`reveal`](https://discord.gg/clust) the voice channel\n{channelemoji} [`rename`](https://discord.gg/clust) the voice channel",
        )
        em.add_field(
            name="Misc",
            value=f"{plusemoji} [`increase`](https://discord.gg/clust) the user limit\n{minusemoji} [`decrease`](https://discord.gg/clust) the user limit\n{claimemoji} [`claim`](https://discord.gg/clust) the voice channel\n{manemoji} [`info`](https://discord.gg/clust) of the channel\n{hammeremoji} [`moderate`](https://discord.gg/clust) the voice channel",
        )
        return em

    async def get_channel_categories(
        self, channel: discord.VoiceChannel, member: discord.Member
    ) -> bool:
        if len(channel.category.channels) == 50:
            await member.move_to(channel=None)
            try:
                view = discord.ui.View()
                view.add_item(
                    discord.ui.Button(
                        label=f"sent from {member.guild.name}", disabled=True
                    )
                )
                await member.send(
                    "I couldn't make a new voice channel (category full of channels)",
                    view=view,
                )
            except:
                pass
        return len(channel.category.channels) == 50

    async def get_channel_overwrites(
        self, channel: discord.VoiceChannel, member: discord.Member
    ) -> bool:
        if member.bot:
            return
        che = await self.bot.db.fetchrow(
            "SELECT * FROM vcs WHERE voice = $1", channel.id
        )
        if che:
            if che["user_id"] == member.id:
                return
            if channel.overwrites_for(channel.guild.default_role).connect == False:
                if (
                    member not in channel.overwrites
                    and member.id != member.guild.owner_id
                ):
                    if not channel.overwrites_for(member).connect == True:
                        try:
                            return await member.move_to(
                                channel=None,
                                reason="not allowed to join this voice channel",
                            )
                        except:
                            pass

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
            return
        check = await self.bot.db.fetchrow(
            "SELECT * FROM voicemaster WHERE guild_id = $1", member.guild.id
        )
        if check:
            jtc = int(check["channel_id"])
            if not before.channel and after.channel:
                if after.channel.id == jtc:
                    if await self.get_channel_categories(after.channel, member) is True:
                        return
                    channel = await member.guild.create_voice_channel(
                        name=f"{member.name}'s lounge",
                        category=after.channel.category,
                        reason="creating temporary voice channel",
                    )
                    await channel.set_permissions(
                        member.guild.default_role, connect=True
                    )
                    await member.move_to(channel=channel)
                    return await self.bot.db.execute(
                        "INSERT INTO vcs VALUES ($1,$2)", member.id, channel.id
                    )
                else:
                    return await self.get_channel_overwrites(after.channel, member)
            elif before.channel and after.channel:
                if before.channel.id == jtc:
                    return
                if before.channel.category == after.channel.category:
                    if after.channel.id == jtc:
                        che = await self.bot.db.fetchrow(
                            "SELECT * FROM vcs WHERE voice = $1", before.channel.id
                        )
                        if che:
                            if len(before.channel.members) == 0:
                                return await member.move_to(channel=before.channel)
                        if (
                            await self.get_channel_categories(after.channel, member)
                            is True
                        ):
                            return
                        cha = await member.guild.create_voice_channel(
                            name=f"{member.name}'s lounge",
                            category=after.channel.category,
                            reason="creating temporary voice channel",
                        )
                        await cha.set_permissions(
                            member.guild.default_role, connect=True
                        )
                        await member.move_to(channel=cha)
                        return await self.bot.db.execute(
                            "INSERT INTO vcs VALUES ($1,$2)", member.id, cha.id
                        )
                    elif before.channel.id != after.channel.id:
                        await self.get_channel_overwrites(after.channel, member)
                        che = await self.bot.db.fetchrow(
                            "SELECT * FROM vcs WHERE voice = $1", before.channel.id
                        )
                        if che:
                            if len(before.channel.members) == 0:
                                await self.bot.db.execute(
                                    "DELETE FROM vcs WHERE voice = $1",
                                    before.channel.id,
                                )
                                await before.channel.delete(
                                    reason="no one in the temporary voice channel"
                                )
                else:
                    if after.channel.id == jtc:
                        if (
                            await self.get_channel_categories(after.channel, member)
                            is True
                        ):
                            return
                        cha = await member.guild.create_voice_channel(
                            name=f"{member.name}'s lounge",
                            category=after.channel.category,
                            reason="creating temporary voice channel",
                        )
                        await cha.set_permissions(
                            member.guild.default_role, connect=True
                        )
                        await member.move_to(channel=cha)
                        return await self.bot.db.execute(
                            "INSERT INTO vcs VALUES ($1,$2)", member.id, cha.id
                        )
                    else:
                        await self.get_channel_overwrites(after.channel, member)
                        result = await self.bot.db.fetchrow(
                            "SELECT * FROM vcs WHERE voice = $1", before.channel.id
                        )
                        if result:
                            if len(before.channel.members) == 0:
                                await self.bot.db.execute(
                                    "DELETE FROM vcs WHERE voice = $1",
                                    before.channel.id,
                                )
                                return await before.channel.delete(
                                    reason="no one in the temporary voice channel"
                                )
            elif before.channel and not after.channel:
                if before.channel.id == jtc:
                    return
                che = await self.bot.db.fetchrow(
                    "SELECT * FROM vcs WHERE voice = $1", before.channel.id
                )
                if che:
                    if len(before.channel.members) == 0:
                        await self.bot.db.execute(
                            "DELETE FROM vcs WHERE voice = $1", before.channel.id
                        )
                        await before.channel.delete(
                            reason="no one in the temporary voice channel"
                        )

    @commands.hybrid_group(aliases=["vc"], invoke_without_command=True)
    async def voice(self, ctx):
        await ctx.create_pages()

    @voice.command(help="lock the voice channel", brief="vc owner")
    @check_vc_owner()
    async def lock(self, ctx: commands.Context):
        await ctx.author.voice.channel.set_permissions(
            ctx.guild.default_role, connect=False
        )
        return await ctx.send_success(f"locked <#{ctx.author.voice.channel.id}>")

    @voice.command(help="unlock the voice channel", brief="vc owner")
    @check_vc_owner()
    async def unlock(self, ctx: commands.Context):
        await ctx.author.voice.channel.set_permissions(
            ctx.guild.default_role, connect=True
        )
        return await ctx.send_success(f"unlocked <#{ctx.author.voice.channel.id}>")

    @voice.command(
        help="rename the voice channel",
        usage="[name]",
        brief="vc owner",
    )
    @check_vc_owner()
    async def rename(self, ctx: commands.Context, *, name: str):
        await ctx.author.voice.channel.edit(name=name)
        return await ctx.send_success(f"renamed voice channel to **{name}**")

    @voice.command(help="hide the voice channel", brief="vc owner")
    @check_vc_owner()
    async def hide(self, ctx: commands.Context):
        await ctx.author.voice.channel.set_permissions(
            ctx.guild.default_role, view_channel=False
        )
        return await ctx.send_success(f"hidden <#{ctx.author.voice.channel.id}>")

    @voice.command(help="reveal the voice channel", brief="vc owner")
    @check_vc_owner()
    async def reveal(self, ctx: commands.Context):
        await ctx.author.voice.channel.set_permissions(
            ctx.guild.default_role, view_channel=True
        )
        return await ctx.send_success(f"revealed <#{ctx.author.voice.channel.id}>")

    @voice.command(
        help="let someone join your locked voice channel",
        usage="[member]",
        brief="vc owner",
    )
    @check_vc_owner()
    async def permit(self, ctx: commands.Context, *, member: discord.Member):
        await ctx.author.voice.channel.set_permissions(member, connect=True)
        return await ctx.send_success(
            f"**{member}** is allowed to join <#{ctx.author.voice.channel.id}>"
        )

    @voice.command(
        help="restrict someone from joining your voice channel",
        usage="[member]",
        brief="vc owner",
    )
    @check_vc_owner()
    async def reject(self, ctx: commands.Context, *, member: discord.Member):
        if member.id == ctx.author.id:
            return await ctx.reply("why would u wanna kick urself >_<")
        if member in ctx.author.voice.channel.members:
            await member.move_to(channel=None)
        await ctx.author.voice.channel.set_permissions(member, connect=False)
        return await ctx.send_success(
            f"**{member}** not is allowed to join <#{ctx.author.voice.channel.id}> anymore"
        )

    @voice.command(
        name="kick",
        help="kick a member from your voice channel",
        usasge="[member]",
        brief="vc owner",
    )
    @check_vc_owner()
    async def vc_kick(self, ctx: commands.Context, *, member: discord.Member):
        if member.id == ctx.author.id:
            return await ctx.reply("why would u wanna kick urself >_<")
        if not member in ctx.author.voice.channel.members:
            return await ctx.send_error(f"**{member}** isn't in **your** voice channel")
        await member.move_to(channel=None)
        return await ctx.send_success(
            f"**{member}** got kicked from <#{ctx.author.voice.channel.id}>"
        )

    @voice.command(help="claim the voice channel ownership")
    async def claim(self, ctx: commands.Context):
        if not ctx.author.voice:
            return await ctx.send_warning("You are **not** in a voice channel")
        check = await self.bot.db.fetchrow(
            "SELECT user_id FROM vcs WHERE voice = $1", ctx.author.voice.channel.id
        )
        if not check:
            return await ctx.send_warning(
                "You are **not** in a voice channel made by the bot"
            )
        if ctx.author.id == check[0]:
            return await ctx.send_warning("You are the **owner** of this voice channel")
        if check[0] in [m.id for m in ctx.author.voice.channel.members]:
            return await ctx.send_warning("The owner is still in the voice channel")
        await self.bot.db.execute(
            "UPDATE vcs SET user_id = $1 WHERE voice = $2",
            ctx.author.voice.channel.id,
            ctx.author.voice.channel.id,
        )
        return await ctx.send_success("**You** are the new owner of this voice channel")

    @voice.command(
        help="transfer the voice channel ownership to another member",
        usage="[member]",
        brief="vc owner",
    )
    @check_vc_owner()
    async def transfer(self, ctx: commands.Context, *, member: discord.Member):
        if not member in ctx.author.voice.channel.members:
            return await ctx.send_warning(f"**{member}** is not in your voice channel")
        if member == ctx.author:
            return await ctx.send_warning(
                "You are already the **owner** of this **voice channel**"
            )
        await self.bot.db.execute(
            "UPDATE vcs SET user_id = $1 WHERE voice = $2",
            member.id,
            ctx.author.voice.channel.id,
        )
        return await ctx.send_success(f"Transfered the voice ownership to **{member}**")

    @commands.command(
        help="sends an updated interface of voicemaster",
        brief="administrator",
    )
    @Perms.get_perms("administrator")
    async def interface(self, ctx: commands.Context):
        check = await self.bot.db.execute(
            "SELECT * FROM voicemaster WHERE guild_id = $1", ctx.guild.id
        )
        if check is None:
            return await ctx.send_warning("VoiceMaster isn't configured")
        await ctx.send(embed=self.create_interface(ctx), view=vmbuttons())
        await ctx.message.delete()

    @commands.hybrid_group(invoke_without_command=True, aliases=["vm", "jtc"])
    async def voicemaster(self, ctx):
        await ctx.create_pages()

    @voicemaster.command(
        help="sets voicemaster module for your server",
        brief="administrator",
    )
    @Perms.get_perms("administrator")
    async def setup(self, ctx: commands.Context):
        check = await self.bot.db.fetchrow(
            "SELECT * FROM voicemaster WHERE guild_id = $1", ctx.guild.id
        )
        if check is not None:
            return await ctx.send_warning("VoiceMaster is configured")
        elif check is None:
            category = await ctx.guild.create_category("voice channels")
            overwrite = {
                ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False)
            }
            text = await ctx.guild.create_text_channel(
                "interface", category=category, overwrites=overwrite
            )
            vc = await ctx.guild.create_voice_channel(
                "Join to create", category=category
            )
            await text.send(embed=self.create_interface(ctx), view=vmbuttons())
            await self.bot.db.execute(
                "INSERT INTO voicemaster VALUES ($1,$2,$3)",
                ctx.guild.id,
                vc.id,
                text.id,
            )
            return await ctx.send_success("Configured the VoiceMaster interface")

    @voicemaster.command(
        help="remove voicemaster module from your server",
        aliases=["unset"],
        brief="administrator",
    )
    @Perms.get_perms("administrator")
    async def remove(self, ctx: commands.Context):
        check = await self.bot.db.fetchrow(
            "SELECT * FROM voicemaster WHERE guild_id = $1", ctx.guild.id
        )
        if check is None:
            return await ctx.send_warning("VoiceMaster is not configured")
        elif check is not None:
            try:
                channelid = check["channel_id"]
                interfaceid = check["interface"]
                channel2 = ctx.guild.get_channel(interfaceid)
                channel = ctx.guild.get_channel(channelid)
                category = channel.category
                channels = category.channels
                for chan in channels:
                    try:
                        await chan.delete()
                    except:
                        continue

                await category.delete()
                await channel2.delete()
                await self.bot.db.execute(
                    "DELETE FROM voicemaster WHERE guild_id = $1", ctx.guild.id
                )
                await ctx.send_success("VoiceMaster module has been disabled")
            except:
                await self.bot.db.execute(
                    "DELETE FROM voicemaster WHERE guild_id = $1", ctx.guild.id
                )
                await ctx.send_success("VoiceMaster module has been disabled")


async def setup(bot) -> None:
    await bot.add_cog(Voicemaster(bot))
