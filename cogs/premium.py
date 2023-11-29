import discord, uwuipy, aiohttp
from discord.ext import commands
from extensions.control import Perms, Mod
from extensions.utilities import NoStaff
from typing import Union


async def uwuthing(bot, text: str) -> str:
    uwu = uwuipy.uwuipy()
    return uwu.uwuify(text)

def premium():
    async def predicate(ctx: commands.Context):
        if ctx.command.name in ["hardban", "uwulock", "unhardban"]:
            if ctx.author.id == ctx.guild.owner_id:
                return True
        check = await ctx.bot.db.fetchrow(
            "SELECT * FROM donor WHERE user_id = {}".format(ctx.author.id)
        )
        res = await ctx.bot.db.fetchrow
        if check is None and res is None:
            await ctx.send_warning("Donator only")
            return False
        return True

    return commands.check(predicate)


class Premium(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.pool = None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild:
            return
        if isinstance(message.author, discord.User):
            return
        check = await self.bot.db.fetchrow(
            "SELECT * FROM uwulock WHERE guild_id = {} AND user_id = {}".format(
                message.guild.id, message.author.id
            )
        )
        if check:
            try:
                await message.delete()
                uwumsg = await uwuthing(self.bot, message.clean_content)
                webhooks = await message.channel.webhooks()
                if len(webhooks) == 0:
                    webhook = await message.channel.create_webhook(
                        name="clust - uwulock", reason="for uwulock"
                    )
                else:
                    webhook = webhooks[0]
                await webhook.send(
                    content=uwumsg,
                    username=message.author.name,
                    avatar_url=message.author.display_avatar.url,
                )
            except:
                pass

    @commands.command(
        help="revoke the hardban from an user",
        usage="[user]",
        brief="ban_members",
    )
    @Perms.get_perms("ban_members")
    @premium()
    async def hardunban(self, ctx: commands.Context, *, member: discord.User):
        che = await self.bot.db.fetchrow(
            "SELECT * FROM hardban WHERE guild_id = {} AND banned = {}".format(
                ctx.guild.id, member.id
            )
        )
        if che is None:
            return await ctx.send_warning(f"{member} is **not** hardbanned")
        await self.bot.db.execute(
            "DELETE FROM hardban WHERE guild_id = {} AND banned = {}".format(
                ctx.guild.id, member.id
            )
        )
        await ctx.guild.unban(
            member, reason="unhardbanned by {}".format(ctx.author.mention)
        )
        await ctx.message.add_reaction("<:blue_guy_thumbs_up:1126833290867908660>")

    @commands.command(
        help="hardban someone from a guild with clust in it",
        usage="[user]",
        brief="ban_members",
    )
    @Perms.get_perms("ban_members")
    @premium()
    async def hardban(
        self, ctx: commands.Context, *, member: Union[discord.Member, discord.User]
    ):
        if isinstance(member, discord.Member):
            if member == ctx.message.author:
                return await ctx.send_warning("You cannot hardban **yourself**")
            if member.id == self.bot.user.id:
                return await ctx.reply(
                    "leave me alone <a:6keroppiangry:1126827028348420116>"
                )
            if await Mod.check_hieracy(ctx, member):
                che = await self.bot.db.fetchrow(
                    "SELECT * FROM hardban WHERE guild_id = {} AND banned = {}".format(
                        ctx.guild.id, member.id
                    )
                )
                if che is not None:
                    return await ctx.send_warning(
                        f"**{member}** has been hardbanned by **{await self.bot.fetch_user(che['author'])}**"
                    )
                await ctx.guild.ban(
                    member, reason="hardbanned by {}".format(ctx.author)
                )
                await self.bot.db.execute(
                    "INSERT INTO hardban VALUES ($1,$2,$3)",
                    ctx.guild.id,
                    member.id,
                    ctx.author.id,
                )
                await ctx.message.add_reaction(
                    "<:blue_guy_thumbs_up:1126833290867908660>"
                )

    @commands.command(
        help="uwuify a person's messages",
        usage="[member]",
        brief="administrator",
    )
    @Perms.get_perms("administrator")
    @premium()
    async def uwulock(self, ctx: commands.Context, *, member: NoStaff):
        if member.bot:
            return await ctx.send_warning("You can't **uwulock** a bot")
        check = await self.bot.db.fetchrow(
            "SELECT user_id FROM uwulock WHERE user_id = {} AND guild_id = {}".format(
                member.id, ctx.guild.id
            )
        )
        if check is None:
            await self.bot.db.execute(
                "INSERT INTO uwulock VALUES ($1,$2)", ctx.guild.id, member.id
            )
        else:
            await self.bot.db.execute(
                "DELETE FROM uwulock WHERE user_id = {} AND guild_id = {}".format(
                    member.id, ctx.guild.id
                )
            )
        return await ctx.message.add_reaction(
            "<:blue_guy_thumbs_up:1126833290867908660>"
        )

    @commands.command(
        help="force nicknames an user",
        usage="[member] [nickname]\nif none is passed as nickname, the force nickname gets removed",
        aliases=["locknick"],
        brief="manage nicknames",
    )
    @Perms.get_perms("manage_nicknames")
    @premium()
    async def forcenick(self, ctx: commands.Context, member: NoStaff, *, nick: str):
        if nick.lower() == "none":
            check = await self.bot.db.fetchrow(
                "SELECT * FROM forcenick WHERE user_id = {} AND guild_id = {}".format(
                    member.id, ctx.guild.id
                )
            )
            if check is None:
                return await ctx.send_warning(f"**No** forcenick found for {member}")
            await self.bot.db.execute(
                "DELETE FROM forcenick WHERE user_id = {} AND guild_id = {}".format(
                    member.id, ctx.guild.id
                )
            )
            await member.edit(nick=None)
            await ctx.message.add_reaction("<:blue_guy_thumbs_up:1126833290867908660>")
        else:
            check = await self.bot.db.fetchrow(
                "SELECT * FROM forcenick WHERE user_id = {} AND guild_id = {}".format(
                    member.id, ctx.guild.id
                )
            )
            if check is None:
                await self.bot.db.execute(
                    "INSERT INTO forcenick VALUES ($1,$2,$3)",
                    ctx.guild.id,
                    member.id,
                    nick,
                )
            else:
                await self.bot.db.execute(
                    "UPDATE forcenick SET nickname = '{}' WHERE user_id = {} AND guild_id = {}".format(
                        nick, member.id, ctx.guild.id
                    )
                )
            await member.edit(nick=nick)
            await ctx.message.add_reaction("<:blue_guy_thumbs_up:1126833290867908660>")

    @commands.command(
        help="purges an amount of messages sent by you",
        usage="[amount]",
    )
    @premium()
    async def selfpurge(self, ctx: commands.Context, amount: int):
        mes = []
        async for message in ctx.channel.history():
            if len(mes) == amount + 1:
                break
            if message.author == ctx.author:
                mes.append(message)

        await ctx.channel.delete_messages(mes)

    @commands.command(help="check the premium perks")
    async def perks(self, ctx: commands.Context):
        embed = discord.Embed(
            color=self.bot.color,
            title="donator perks",
            help="Perks for the donators. Boost **2** time's or donate **3$** to have access to these perks",
        )
        embed.add_field(
            name="commands",
            value="**embed steal** - steal member's lastfm custom embeds\n"
            + "\n".join(
                [
                    f"**{command.name}** - {command.description}"
                    for command in set(ctx.cog.walk_commands())
                    if not command.name in [ctx.command.name, "premium"]
                    and not "discrim" in command.name
                ]
            ),
            inline=False,
        )
        return await ctx.reply(embed=embed)

    @commands.command(
        help="See donation info",
        aliases=["payment"],
        usage="donate",
    )
    async def donate(self, ctx: commands.Context):
        embed = discord.Embed(
            color=self.bot.color,
            title="Make sure to include your guild id and user id in the payment note!",
            description=f"<:paypal1:1136335209369976923> - [`claqzwyd`](https://paypal.me/claqzwyd)\n<:boost:1121826890886422611> - [`/clust`](https://discord.gg/clust)\n<:cashapp:1115322711997173790> - [`$bwruise`](https://cash.app/$bwruise)\n<:bitcoin:1115322723858665654> - `bc1qy2dx64xq6mxyvup098z3hk82teqy6cy6q7zqs9`\n<:ethe:1115322733585240135> - `0x1bbed1a48dEf83EC7D78a4662831E017d47E7c8b`\n <:icons8litecoin50:1136334299956777132> - `Lg1aL3haSfEBSUf5dSd6eiT8Qb4FuTdYVP`\n**Boosting gets u perks till u unboost, for help dm stardle**",
        )
        footer_text = "Most of the payments go for the bot hosting and API and other investments for clust."
        footer_image = "https://media.discordapp.net/attachments/1099716882052960259/1123196245524103300/Money.gif"
        embed.set_footer(text=footer_text, icon_url=footer_image)
        paypal = discord.ui.Button(emoji="<:paypal1:1136335209369976923>")
        boost = discord.ui.Button(emoji="<:boost:1121826890886422611>")
        cashapp = discord.ui.Button(emoji="<:cashapp:1115322711997173790>")
        btc = discord.ui.Button(emoji="<:bitcoin:1115322723858665654>")
        eth = discord.ui.Button(emoji="<:ethe:1115322733585240135>")
        ltc = discord.ui.Button(emoji="<:icons8litecoin50:1136334299956777132>")
        view = discord.ui.View(timeout=None)

        async def paypal_callback(interaction: discord.Interaction):
            await interaction.response.send_message(
                "https://paypal.me/claqzwyd", ephemeral=True
            )

        async def boost_callback(interaction: discord.Interaction):
            await interaction.response.send_message(
                "boost https://discord.gg/clust for perks", ephemeral=True
            )

        async def cashapp_callback(interaction: discord.Interaction):
            await interaction.response.send_message(
                "https://cash.app/$bwruise", ephemeral=True
            )

        async def btc_callback(interaction: discord.Interaction):
            await interaction.response.send_message(
                "`bc1qy2dx64xq6mxyvup098z3hk82teqy6cy6q7zqs9`", ephemeral=True
            )

        async def eth_callback(interaction: discord.Interaction):
            await interaction.response.send_message(
                "`0x1bbed1a48dEf83EC7D78a4662831E017d47E7c8b`", ephemeral=True
            )

        async def ltc_callback(interaction: discord.Interaction):
            await interaction.response.send_message(
                "`Lg1aL3haSfEBSUf5dSd6eiT8Qb4FuTdYVP`", ephemeral=True
            )

        paypal.callback = paypal_callback
        boost.callback = boost_callback
        cashapp.callback = cashapp_callback
        btc.callback = btc_callback
        eth.callback = eth_callback
        ltc.callback = ltc_callback
        view.add_item(paypal)
        view.add_item(boost)
        view.add_item(cashapp)
        view.add_item(btc)
        view.add_item(eth)
        await ctx.reply(embed=embed, view=view, mention_author=False)


async def setup(bot) -> None:
    await bot.add_cog(Premium(bot))
