import discord, asyncio, typing, difflib
from discord.ext import commands


class DataBatchEntry(typing.TypedDict):
    guild: typing.Optional[int]
    channel: int
    author: int
    used: str
    prefix: str
    command: str
    failed: bool


class commandevents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._batch_lock = asyncio.Lock()
        self._data_batch: list[DataBatchEntry] = []

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            x = [cmd.name.lower() for cmd in self.bot.commands]
            cmd = ctx.message.content.split()[0].strip("#")
            used = ctx.message.content.split()[0]

            z = difflib.get_close_matches(cmd, x)
            if z:
                p = ctx.prefix + z[0]
                embed = discord.Embed(color=self.bot.color)
                embed.description = f"{self.bot.fail} {ctx.author.mention}**:** {used} isnt a **valid** command, did you mean `{p}` instead?"

                await ctx.reply(embed=embed)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        channel_count = len(guild.text_channels) + len(guild.voice_channels)
        invite = "N/A"
        if guild.vanity_url is not None:
            invite = f"[{guild.vanity_url_code}]({guild.vanity_url})"
        e = discord.Embed(
            color=0x2B2D31,
            title=f"{guild.name} ({guild.id})",
            description=f'Created {discord.utils.format_dt(guild.created_at, style="F")}',
        )
        e.add_field(
            name="Members",
            value=f"**Total:** {guild.member_count}\n"
            f"**Humans:** {len(list(filter(lambda m: not m.bot, guild.members)))}\n"
            f"**Bots:** {len(list(filter(lambda m: m.bot, guild.members)))}",
        )
        e.add_field(
            name="Channels",
            value=f"**Total:** {channel_count}\n"
            f"**Text:** {len(guild.text_channels)}\n"
            f"**Voice:** {len(guild.voice_channels)}",
        )
        e.add_field(
            name="Other",
            value=f"**Categories:** {len(guild.categories)}\n"
            f"**Roles:** {len(guild.roles)}\n"
            f"**Emotes:** {len(guild.emojis)}",
        )
        e.add_field(
            name="Boost",
            value=f"**Level:** {guild.premium_tier}/3\n"
            f"**Boosts:** {guild.premium_subscription_count}",
        )
        e.add_field(
            name="Information",
            value=f"**Verification:** {guild.verification_level}\n"
            f"**Vanity:** {invite}",
        )
        e.set_footer(text=f"{guild.owner} ({guild.owner_id})")
        e.set_author(
            name=f"{self.bot.user.name}", icon_url=self.bot.user.display_avatar
        )
        channel = self.bot.get_channel(1139603853583581245)
        await channel.send("**Joined:**")
        await channel.send(embed=e)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        channel_count = len(guild.text_channels) + len(guild.voice_channels)
        invite = "N/A"
        if guild.vanity_url is not None:
            invite = f"[{guild.vanity_url_code}]({guild.vanity_url})"
        e = discord.Embed(
            color=0x2B2D31,
            title=f"{guild.name} ({guild.id})",
            description=f'Created {discord.utils.format_dt(guild.created_at, style="F")}',
        )
        e.add_field(
            name="Members",
            value=f"**Total:** {guild.member_count}\n"
            f"**Humans:** {len(list(filter(lambda m: not m.bot, guild.members)))}\n"
            f"**Bots:** {len(list(filter(lambda m: m.bot, guild.members)))}",
        )
        e.add_field(
            name="Channels",
            value=f"**Total:** {channel_count}\n"
            f"**Text:** {len(guild.text_channels)}\n"
            f"**Voice:** {len(guild.voice_channels)}",
        )
        e.add_field(
            name="Other",
            value=f"**Categories:** {len(guild.categories)}\n"
            f"**Roles:** {len(guild.roles)}\n"
            f"**Emotes:** {len(guild.emojis)}",
        )
        e.add_field(
            name="Boost",
            value=f"**Level:** {guild.premium_tier}/3\n"
            f"**Boosts:** {guild.premium_subscription_count}",
        )
        e.add_field(
            name="Information",
            value=f"**Verification:** {guild.verification_level}\n"
            f"**Vanity:** {invite}",
        )
        e.set_footer(text=f"{guild.owner} ({guild.owner_id})")
        e.set_author(
            name=f"{self.bot.user.name}", icon_url=self.bot.user.display_avatar
        )
        channel = self.bot.get_channel(1139603853583581245)
        await channel.send("**Left:**")
        await channel.send(embed=e)


async def setup(bot):
    await bot.add_cog(commandevents(bot))
