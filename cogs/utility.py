from discord.ext.commands import (
    Cog,
    command,
    Context,
    AutoShardedBot as Bot,
    hybrid_command,
    hybrid_group,
    group,
    check,
)
import datetime, discord, humanize, os, arrow, uwuipy, humanfriendly, asyncio, platform
from discord import Embed, File, TextChannel, Member, User, Role
from deep_translator import GoogleTranslator
from discord.ext import commands, tasks
from extensions.lastfmhandling import Handler
from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim
from discord.ui import Button, View
from extensions.control import Perms
from aiogtts import aiogTTS
from typing import Union
from io import BytesIO
from PIL import Image

my_system = platform.uname()
DISCORD_API_LINK = "https://discord.com/api/invite/"
downloadCount = 0
clientid = "f567fb50e0b94b4e8224d2960a00e3ce"
clientsecret = "f4294b7b837940f996b3a4dcf5230628"


def is_there_a_reminder():
    async def predicate(ctx: Context):
        check = await ctx.bot.db.fetchrow(
            "SELECT * FROM reminder WHERE guild_id = $1 AND user_id = $2",
            ctx.guild.id,
            ctx.author.id,
        )
        if not check:
            await ctx.send_warning("You don't have a reminder set in this server")
        return check is not None

    return check(predicate)


@tasks.loop(seconds=5)
async def reminder_task(bot: Bot):
    results = await bot.db.fetch("SELECT * FROM reminder")
    for result in results:
        if datetime.datetime.now().timestamp() > result["date"].timestamp():
            channel = bot.get_channel(int(result["channel_id"]))
            if channel:
                await channel.send(f"🕰️ <@{result['user_id']}> {result['task']}")
                await bot.db.execute(
                    "DELETE FROM reminder WHERE guild_id = $1 AND user_id = $2 AND channel_id = $3",
                    channel.guild.id,
                    result["user_id"],
                    channel.id,
                )


@tasks.loop(seconds=10)
async def bday_task(bot: Bot):
    results = await bot.db.fetch("SELECT * FROM birthday")
    for result in results:
        if (
            arrow.get(result["bday"]).day == arrow.utcnow().day
            and arrow.get(result["bday"]).month == arrow.utcnow().month
        ):
            if result["said"] == "false":
                member = await bot.fetch_user(result["user_id"])
                if member:
                    try:
                        await member.send("🎂 Happy birthday!!")
                        await bot.db.execute(
                            "UPDATE birthday SET said = $1 WHERE user_id = $2",
                            "true",
                            result["user_id"],
                        )
                    except:
                        continue
        else:
            if result["said"] == "true":
                await bot.db.execute(
                    "UPDATE birthday SET said = $1 WHERE user_id = $2",
                    "false",
                    result["user_id"],
                )


class Timezone(object):
    def __init__(self, bot: Bot):
        """
        Get timezones of people
        """
        self.bot = bot
        self.clock = "🕑"
        self.months = {
            "01": "January",
            "02": "February",
            "03": "March",
            "04": "April",
            "05": "May",
            "06": "June",
            "07": "July",
            "08": "August",
            "09": "September",
            "10": "October",
            "11": "November",
            "12": "December",
        }

    async def timezone_send(self, ctx: Context, message: str):
        return await ctx.reply(
            embed=discord.Embed(
                color=self.bot.color,
                description=f"{self.clock} {ctx.author.mention}: {message}",
            )
        )

    async def timezone_request(self, member: discord.Member):
        coord = await self.get_user_lat_long(member)
        if coord is None:
            return None
        utc = arrow.utcnow()
        local = utc.to(coord)
        timestring = local.format("YYYY-MM-DD HH:mm").split(" ")
        date = timestring[0][5:].split("-")
        try:
            hours, minutes = [int(x) for x in timestring[1].split(":")[:2]]
        except IndexError:
            return "N/A"

        if hours >= 12:
            suffix = "PM"
            hours -= 12
        else:
            suffix = "AM"
        if hours == 0:
            hours = 12
        return f"{self.months.get(date[0])} {self.bot.ordinal(date[1])} {hours}:{minutes:02d} {suffix}"

    async def get_user_lat_long(self, member: discord.Member):
        check = await self.bot.db.fetchrow(
            "SELECT * FROM timezone WHERE user_id = $1", member.id
        )
        if check is None:
            return None
        return check["zone"]

    async def tz_set_cmd(self, ctx: Context, location: str):
        await ctx.typing()
        geolocator = Nominatim(
            user_agent="Mozilla/5.0 (Linux; Android 8.0.0; SM-G955U Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Mobile Safari/537.36"
        )
        lad = location
        location = geolocator.geocode(lad)
        if location is None:
            return await ctx.send_warning(
                "Couldn't find a **timezone** for that location"
            )
        check = await self.bot.db.fetchrow(
            "SELECT * FROM timezone WHERE user_id = $1", ctx.author.id
        )
        obj = TimezoneFinder()
        result = obj.timezone_at(lng=location.longitude, lat=location.latitude)
        if not check:
            await self.bot.db.execute(
                "INSERT INTO timezone VALUES ($1,$2)", ctx.author.id, result
            )
        else:
            await self.bot.db.execute(
                "DELETE FROM timezone WHERE user_id = $1", ctx.author.id
            )
            await self.bot.db.execute(
                "INSERT INTO timezone VALUES ($1,$2)", ctx.author.id, result
            )
        embed = Embed(
            color=self.bot.color,
            description=f"Saved your timezone as **{result}**\n{self.clock} Current time: **{await self.timezone_request(ctx.author)}**",
        )
        await ctx.reply(embed=embed)

    async def get_user_timezone(self, ctx: Context, member: discord.Member):
        if await self.timezone_request(member) is None:
            if member.id == ctx.author.id:
                return await ctx.send_warning(
                    f"You don't have a **timezone** set. Use `{ctx.clean_prefix}tz set` command instead"
                )
            else:
                return await ctx.send_warning(
                    f"**{member.name}** doesn't have their **timezone** set"
                )
        if member.id == ctx.author.id:
            return await self.timezone_send(
                ctx, f"Your current time: **{await self.timezone_request(member)}**"
            )
        else:
            return await self.timezone_send(
                ctx,
                f"**{member.name}'s** current time: **{await self.timezone_request(member)}**",
            )


def convert(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    return "%d:%02d:%02d" % (hour, minutes, seconds)


def human_format(number):
    if number > 999:
        return humanize.naturalsize(number, False, True)
    return number


class Utils(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.tz = Timezone(self.bot)
        self.lastfmhandler = Handler("43693facbb24d1ac893a7d33846b15cc")
        self.cake = "🎂"
        self.weather_key = ("64581e6f1d7d49ae834142709230804",)

    async def bday_send(self, ctx: Context, message: str) -> discord.Message:
        return await ctx.reply(
            embed=discord.Embed(
                color=self.bot.color,
                description=f"{self.cake} {ctx.author.mention}: {message}",
            )
        )

    async def do_again(self, url: str):
        re = await self.make_request(url)
        if re["status"] == "converting":
            return await self.do_again(url)
        elif re["status"] == "failed":
            return None
        else:
            return tuple([re["url"], re["filename"]])

    async def make_request(self, url: str, action: str = "get", params: dict = None):
        r = await self.bot.session.get(url, params=params)
        if action == "get":
            return await r.json()
        if action == "read":
            return await r.read()

    @Cog.listener()
    async def on_ready(self):
        await self.bot.wait_until_ready()
        bday_task.start(self.bot)
        reminder_task.start(self.bot)

    @command(
        help="clear your usernames",
        aliases=["clearusernames", "clearusers"],
    )
    async def clearnames(self, ctx):
        embed = discord.Embed(
            color=self.bot.color,
            description=f"{ctx.author.mention} are you sure you want to clear your usernames. This decision is **irreversible**",
        )
        button1 = discord.ui.Button(emoji=self.bot.yes)
        button2 = discord.ui.Button(emoji=self.bot.no)

        async def button1_callback(interaction: discord.Interaction):
            if interaction.user.id != ctx.author.id:
                return await self.bot.ext.send_warning(
                    interaction, "You are not the author of this embed", ephemeral=True
                )
            await self.bot.db.execute(
                "DELETE FROM oldusernames WHERE user_id = $1", ctx.author.id
            )
            return await interaction.response.edit_message(
                view=None,
                embed=discord.Embed(
                    color=self.bot.color,
                    description=f"> {self.bot.yes} {interaction.user.mention}: Name history cleared",
                ),
            )

        async def button2_callback(interaction: discord.Interaction):
            if interaction.user.id != ctx.author.id:
                return await self.bot.ext.send_warning(
                    interaction, "You are not the author of this embed", ephemeral=True
                )
            return await interaction.response.edit_message(
                view=None,
                embed=discord.Embed(
                    color=self.bot.color, description=f"Aborting action..."
                ),
            )

        button1.callback = button1_callback
        button2.callback = button2_callback
        view = discord.ui.View()
        view.add_item(button1)
        view.add_item(button2)
        return await ctx.reply(embed=embed, view=view)

    @hybrid_command(
        help="clear all snipe data",
        brief="manage messages",
        aliases=["cs"],
    )
    @Perms.get_perms("manage_messages")
    async def clearsnipes(self, ctx: Context):
        lis = ["snipe", "reactionsnipe", "editsnipe"]
        for l in lis:
            await self.bot.db.execute(
                f"DELETE FROM {l} WHERE guild_id = $1", ctx.guild.id
            )
        return await ctx.send_success("Cleared all snipes from this server")

    @command(
        aliases=["names", "usernames"],
        usage="<user>",
        help="check an user's past usernames",
    )
    async def pastusernames(self, ctx, member: User = None):
        if not member:
            member = ctx.author
        data = await self.bot.db.fetch(
            "SELECT * FROM oldusernames WHERE user_id = $1", member.id
        )
        i = 0
        k = 1
        l = 0
        number = []
        messages = []
        num = 0
        auto = ""
        if data:
            for table in data[::-1]:
                username = table["username"]
                discrim = table["discriminator"]
                num += 1
                auto += f"\n`{num}` {username}: <t:{int(table['time'])}:R> "
                k += 1
                l += 1
                if l == 10:
                    messages.append(auto)
                    number.append(
                        Embed(color=self.bot.color, description=auto).set_author(
                            name=f"{member}'s past usernames",
                            icon_url=member.display_avatar,
                        )
                    )
                    i += 1
                    auto = ""
                    l = 0
            messages.append(auto)
            embed = Embed(description=auto, color=self.bot.color)
            embed.set_author(
                name=f"{member}'s past usernames", icon_url=member.display_avatar
            )
            number.append(embed)
            return await ctx.paginator(number)
        else:
            return await ctx.send_warning(
                f"no logged usernames for **{member}**".capitalize()
            )

    @command(
        usage="[message]",
        help="uwify a message",
        aliases=["uwu"],
    )
    async def uwuify(self, ctx: Context, *, text: str):
        uwu = uwuipy.uwuipy()
        uwu_message = uwu.uwuify(text)
        await ctx.send(uwu_message)

    @hybrid_command(
        help="give someone permission to post pictures in a channel",
        usage="[member] <channel>",
        brief="manage roles",
    )
    @Perms.get_perms("manage_roles")
    async def picperms(
        self, ctx: Context, member: Member, *, channel: TextChannel = None
    ):
        if channel is None:
            channel = ctx.channel
        if (
            channel.permissions_for(member).attach_files
            and channel.permissions_for(member).embed_links
        ):
            await channel.set_permissions(member, attach_files=False, embed_links=False)
            return await ctx.send_success(
                f"Removed pic perms from {member.mention} in {channel.mention}"
            )
        await channel.set_permissions(member, attach_files=True, embed_links=True)
        return await ctx.send_success(
            f"Added pic perms to {member.mention} in {channel.mention}"
        )

    @hybrid_command(
        help="see when a user was last seen",
        usage="[member]",
        aliases=["lastseen"],
    )
    async def seen(self, ctx, *, member: Member):
        check = await self.bot.db.fetchrow(
            "SELECT * FROM seen WHERE guild_id = {} AND user_id = {}".format(
                ctx.guild.id, member.id
            )
        )
        if check is None:
            return await ctx.send_warning(f"I didn't see **{member}**")
        ts = check["time"]
        await ctx.reply(
            embed=Embed(
                color=self.bot.color,
                description="{}: **{}** was last seen <t:{}:R>".format(
                    ctx.author.mention, member, ts
                ),
            )
        )

    @hybrid_command(help="let everyone know you are away", usage="<reason>")
    async def afk(self, ctx: Context, *, reason="AFK"):
        ts = int(datetime.datetime.now().timestamp())
        result = await self.bot.db.fetchrow(
            "SELECT * FROM afk WHERE guild_id = {} AND user_id = {}".format(
                ctx.guild.id, ctx.author.id
            )
        )
        if result is None:
            await self.bot.db.execute(
                "INSERT INTO afk VALUES ($1,$2,$3,$4)",
                ctx.guild.id,
                ctx.author.id,
                reason,
                ts,
            )
            await ctx.send_success(f"You're now AFK with the status: **{reason}**")

    @hybrid_command(
        aliases=["es"],
        help="get the most recent edited messages from the channel",
        usage="<number>",
    )
    async def editsnipe(self, ctx: Context, number: int = 1):
        results = await self.bot.db.fetch(
            "SELECT * FROM editsnipe WHERE guild_id = $1 AND channel_id = $2",
            ctx.guild.id,
            ctx.channel.id,
        )
        if len(results) == 0:
            return await ctx.send_warning(
                "There are no edited messages in this channel"
            )
        if number > len(results):
            return await ctx.send_warning(
                f"The maximum amount of snipes is **{len(results)}**"
            )
        sniped = results[::-1][number - 1]
        embed = Embed(color=self.bot.color)
        embed.set_author(name=sniped["author_name"], icon_url=sniped["author_avatar"])
        embed.add_field(name="before", value=sniped["before_content"])
        embed.add_field(name="after", value=sniped["after_content"])
        embed.set_footer(text=f"{number}/{len(results)}")
        await ctx.reply(embed=embed)

    @hybrid_command(
        aliases=["rs"],
        help="get the most recent messages that got one of their reactions removed",
        usage="number",
    )
    async def reactionsnipe(self, ctx: Context, number: int = 1):
        results = await self.bot.db.fetch(
            "SELECT * FROM reactionsnipe WHERE guild_id = $1 AND channel_id = $2",
            ctx.guild.id,
            ctx.channel.id,
        )
        if len(results) == 0:
            return await ctx.send_warning(
                "There are no reaction removed in this channel"
            )
        if number > len(results):
            return await ctx.send_warning(
                f"The maximum amount of snipes is **{len(results)}**"
            )
        sniped = results[::-1][number - 1]
        message = await ctx.channel.fetch_message(sniped["message_id"])
        embed = Embed(
            color=self.bot.color,
            description=f"[{sniped['emoji_name']}]({sniped['emoji_url']})\n[message link]({message.jump_url if message else 'https://none.none'})",
        )
        embed.set_author(name=sniped["author_name"], icon_url=sniped["author_avatar"])
        embed.set_image(url=sniped["emoji_url"])
        embed.set_footer(text=f"{number}/{len(results)}")
        await ctx.reply(embed=embed)

    @hybrid_command(
        aliases=["s"],
        help="check the latest deleted message from a channel",
        usage="<number>",
    )
    async def snipe(self, ctx: Context, *, number: int = 1):
        check = await self.bot.db.fetch(
            "SELECT * FROM snipe WHERE guild_id = {} AND channel_id = {}".format(
                ctx.guild.id, ctx.channel.id
            )
        )
        if len(check) == 0:
            return await ctx.send_warning(
                "There are no deleted messages in this channel"
            )
        if number > len(check):
            return await ctx.send_warning(
                f"current snipe limit is **{len(check)}**".capitalize()
            )
        sniped = check[::-1][number - 1]
        em = Embed(
            color=self.bot.color,
            description=sniped["content"],
            timestamp=sniped["time"],
        )
        em.set_author(name=sniped["author"], icon_url=sniped["avatar"])
        em.set_footer(text="{}/{}".format(number, len(check)))
        if sniped["attachment"] != "none":
            if ".mp4" in sniped["attachment"] or ".mov" in sniped["attachment"]:
                url = sniped["attachment"]
                r = await self.bot.session.read(url)
                bytes_io = BytesIO(r)
                file = File(fp=bytes_io, filename="video.mp4")
                return await ctx.reply(embed=em, file=file)
            else:
                try:
                    em.set_image(url=sniped["attachment"])
                except:
                    pass
        return await ctx.reply(embed=em)

    @hybrid_command(
        aliases=["mc"],
        help="check how many members does your server have",
    )
    async def membercount(self, ctx: Context):
        b = len(set(b for b in ctx.guild.members if b.bot))
        h = len(set(b for b in ctx.guild.members if not b.bot))
        embed = Embed(color=self.bot.color)
        embed.set_author(
            name=f"{ctx.guild.name}'s member count", icon_url=ctx.guild.icon
        )
        embed.add_field(
            name=f"members (  {len([m for m in ctx.guild.members if (datetime.datetime.now() - m.joined_at.replace(tzinfo=None)).total_seconds() < 3600*24 and not m.bot])})",
            value=h,
        )
        embed.add_field(name="total", value=ctx.guild.member_count)
        embed.add_field(name="bots", value=b)
        await ctx.reply(embed=embed)

    @hybrid_command(help="see user's avatar", usage="<user>", aliases=["av"])
    async def avatar(self, ctx: Context, *, member: Union[Member, User] = None):
        if member is None:
            member = ctx.author

        if isinstance(member, Member):
            button1 = Button(
                label="default avatar",
                url=member.avatar.url
                if member.avatar is not None
                else "https://none.none",
            )
            button2 = Button(label="server avatar", url=member.display_avatar.url)
            embed = Embed(
                color=self.bot.color,
                title=f"{member.name}'s avatar",
                url=member.display_avatar.url,
            )
            embed.set_author(
                name=ctx.author.name, icon_url=ctx.author.display_avatar.url
            )
            embed.set_image(url=member.display_avatar.url)
            view = View()
            view.add_item(button1)
            view.add_item(button2)
            await ctx.reply(embed=embed, view=view)
        elif isinstance(member, User):
            button3 = Button(label="default avatar", url=member.display_avatar.url)
            embed = Embed(
                color=self.bot.color,
                title=f"{member.name}'s avatar",
                url=member.display_avatar.url,
            )
            embed.set_author(
                name=ctx.author.name, icon_url=ctx.author.display_avatar.url
            )
            embed.set_image(url=member.display_avatar.url)
            view = View()
            view.add_item(button3)
            await ctx.reply(embed=embed, view=view)

    @command(
        help="get role information",
        usage="[role]",
        aliases=["ri"],
    )
    async def roleinfo(self, ctx: Context, *, role: Union[Role, str]):
        if isinstance(role, str):
            role = ctx.find_role(role)
            if role is None:
                return await ctx.send_warning("This is not a valid role")

        perms = (
            ", ".join([str(p[0]) for p in role.permissions if bool(p[1]) is True])
            if role.permissions
            else "none"
        )
        embed = Embed(
            color=role.color,
            title=f"@{role.name}",
            description="`{}`".format(role.id),
            timestamp=role.created_at,
        )
        embed.set_thumbnail(
            url=role.display_icon if not isinstance(role.display_icon, str) else None
        )
        embed.add_field(name="members", value=str(len(role.members)))
        embed.add_field(name="mentionable", value=str(role.mentionable).lower())
        embed.add_field(name="hoist", value=str(role.hoist).lower())
        embed.add_field(name="permissions", value=f"```{perms}```", inline=False)
        await ctx.reply(embed=embed)

    @command(help="see all members in a role", usage="[role]")
    async def inrole(self, ctx: Context, *, role: Union[Role, str]):
        if isinstance(role, str):
            role = ctx.find_role(role)
            if role is None:
                return await ctx.send_warning("This isn't a valid role")

        if len(role.members) == 0:
            return await ctx.send_error("Nobody (even u) has this role")
        i = 0
        k = 1
        l = 0
        mes = ""
        number = []
        messages = []
        for member in role.members:
            mes = f"{mes}`{k}` {member} - ({member.id})\n"
            k += 1
            l += 1
            if l == 10:
                messages.append(mes)
                number.append(
                    Embed(
                        color=self.bot.color,
                        title=f"members in {role.name} [{len(role.members)}]",
                        description=messages[i],
                    )
                )
                i += 1
                mes = ""
                l = 0

        messages.append(mes)
        embed = Embed(
            color=self.bot.color,
            title=f"members in {role.name} [{len(role.members)}]",
            description=messages[i],
        )
        number.append(embed)
        await ctx.paginator(number)

    @command(
        help="see all members joined within 24 hours",
        aliases=["recentmembers", "recents", "recentjoin", "newusers"],
    )
    async def joins(self, ctx: Context):
        members = [
            m
            for m in ctx.guild.members
            if (
                datetime.datetime.now() - m.joined_at.replace(tzinfo=None)
            ).total_seconds()
            < 3600 * 24
        ]
        if len(members) == 0:
            return await ctx.send_error("No members joined in the last **24** hours")
        members = sorted(members, key=lambda m: m.joined_at)
        i = 0
        k = 1
        l = 0
        mes = ""
        number = []
        messages = []
        for member in members[::-1]:
            mes = f"{mes}`{k}` {member} - {discord.utils.format_dt(member.joined_at, style='R')}\n"
            k += 1
            l += 1
            if l == 10:
                messages.append(mes)
                number.append(
                    Embed(
                        color=self.bot.color,
                        title=f"joined today [{len(members)}]",
                        description=messages[i],
                    )
                )
                i += 1
                mes = ""
                l = 0

        messages.append(mes)
        embed = Embed(
            color=self.bot.color,
            title=f"joined today [{len(members)}]",
            description=messages[i],
        )
        number.append(embed)
        await ctx.paginator(number)

    @group(
        invoke_without_command=True,
        help="see all server boosters",
        aliases=["boosts"],
    )
    async def boosters(self, ctx: Context):
        if (
            not ctx.guild.premium_subscriber_role
            or len(ctx.guild.premium_subscriber_role.members) == 0
        ):
            return await ctx.send_warning(
                "this server doesn't have any boosters".capitalize()
            )
        i = 0
        k = 1
        l = 0
        mes = ""
        number = []
        messages = []
        for member in ctx.guild.premium_subscriber_role.members:
            mes = f"{mes}`{k}` {member} - <t:{int(member.premium_since.timestamp())}:R> \n"
            k += 1
            l += 1
            if l == 10:
                messages.append(mes)
                number.append(
                    Embed(
                        color=self.bot.color,
                        title=f"boosters [{len(ctx.guild.premium_subscriber_role.members)}]",
                        description=messages[i],
                    )
                )
                i += 1
                mes = ""
                l = 0

        messages.append(mes)
        embed = Embed(
            color=self.bot.color,
            title=f"boosters [{len(ctx.guild.premium_subscriber_role.members)}]",
            description=messages[i],
        )
        number.append(embed)
        await ctx.paginator(number)

    @boosters.command(name="lost", help="display lost boosters")
    async def boosters_lost(self, ctx: Context):
        results = await self.bot.db.fetch(
            "SELECT * FROM boosterslost WHERE guild_id = $1", ctx.guild.id
        )
        if len(results) == 0:
            return await ctx.send_warning("There are no lost boosters")
        i = 0
        k = 1
        l = 0
        mes = ""
        number = []
        messages = []
        for result in results[::-1]:
            mes = f"{mes}`{k}` <@!{int(result['user_id'])}> - <t:{result['time']}:R> \n"
            k += 1
            l += 1
            if l == 10:
                messages.append(mes)
                number.append(
                    Embed(
                        color=self.bot.color,
                        title=f"lost boosters [{len(results)}]",
                        description=messages[i],
                    )
                )
                i += 1
                mes = ""
                l = 0

        messages.append(mes)
        embed = Embed(
            color=self.bot.color,
            title=f"lost boosters [{len(results)}]",
            description=messages[i],
        )
        number.append(embed)
        await ctx.paginator(number)

    @command(
        help="see all server roles",
    )
    async def roles(self, ctx: Context):
        i = 0
        k = 1
        l = 0
        mes = ""
        number = []
        messages = []
        for role in ctx.guild.roles:
            mes = f"{mes}`{k}` {role.mention} - <t:{int(role.created_at.timestamp())}:R> ({len(role.members)} members)\n"
            k += 1
            l += 1
            if l == 10:
                messages.append(mes)
                number.append(
                    Embed(
                        color=self.bot.color,
                        title=f"roles [{len(ctx.guild.roles)}]",
                        description=messages[i],
                    )
                )
                i += 1
                mes = ""
                l = 0

        messages.append(mes)
        embed = Embed(
            color=self.bot.color,
            title=f"roles [{len(ctx.guild.roles)}]",
            description=messages[i],
        )
        number.append(embed)
        await ctx.paginator(number)

    @command(
        help="see all server's bots",
    )
    async def bots(self, ctx: Context):
        i = 0
        k = 1
        l = 0
        b = len(set(b for b in ctx.guild.members if b.bot))
        mes = ""
        number = []
        messages = []
        for member in ctx.guild.members:
            if member.bot:
                mes = f"{mes}`{k}` {member} - ({member.id})\n"
                k += 1
                l += 1
                if l == 10:
                    messages.append(mes)
                    number.append(
                        Embed(
                            color=self.bot.color,
                            title=f"bots [{b}]",
                            description=messages[i],
                        )
                    )
                    i += 1
                    mes = ""
                    l = 0

        messages.append(mes)
        embed = Embed(
            color=self.bot.color,
            title=f"{ctx.guild.name} bots [{b}]",
            description=messages[i],
        )
        number.append(embed)
        await ctx.paginator(number)

    @hybrid_command(
        help="show user information",
        usage="<user>",
        aliases=["whois", "ui", "user"],
    )
    async def userinfo(self, ctx: Context, *, member: Union[Member, User] = None):
        await ctx.typing()
        if member is None:
            member = ctx.author
        user = await self.bot.fetch_user(member.id)
        discrim = ["0001", "1337", "0002", "9999", "0666", "0888", "6969", "0069"]
        badges = []
        if user.id in self.bot.owner_ids:
            badges.append("<a:8ACOSP_skulllul:1126830798713127033>")
        if user.public_flags.active_developer:
            badges.append("<:5847activedeveloperbadge:1118847964018913330>")
        if user.public_flags.early_supporter:
            badges.append("<:early:1121826930556153908>")
        if user.public_flags.verified_bot_developer:
            badges.append("<:developer:1107720972112502794>")
        if user.public_flags.staff:
            badges.append("<:0_BadgeStaff:1110494810185412669>")
        if user.public_flags.bug_hunter:
            badges.append("<:bug1:1121826895198158930>")
        if user.public_flags.bug_hunter_level_2:
            badges.append("<:goldbughunter:1107721498715770900>")
        if user.public_flags.partner:
            badges.append("<:partner:1118849087807176714>")
        if user.public_flags.discord_certified_moderator:
            badges.append("<:moderator:1121826912201871400>")
        if user.public_flags.hypesquad_bravery:
            badges.append("<:bravery:1118848963760635935>")
        if user.public_flags.hypesquad_balance:
            badges.append("<:1033balancedhypesquad:1118848176368136202>")
        if user.public_flags.hypesquad_brilliance:
            badges.append("<:6318iconhypesquadbrilliance:1136342340089421824>")
        if (
            user.discriminator in discrim
            or user.display_avatar.is_animated()
            or user.banner is not None
        ):
            badges.append("<:nitro:1121826940484079697>")

        for guild in self.bot.guilds:
            mem = guild.get_member(user.id)
            if mem is not None:
                if mem.premium_since is not None:
                    badges.append("<:3659boosticon:1118847629099540520>")
                    break

        async def tz_find(mem: discord.Member):
            if await self.tz.timezone_request(mem):
                return f"{self.tz.clock} Current time: {await self.tz.timezone_request(mem)}"
            return ""

        async def lf(mem: Union[Member, User]):
            check = await self.bot.db.fetchrow(
                "SELECT username FROM lastfm WHERE user_id = {}".format(mem.id)
            )
            if check is not None:
                u = str(check["username"])
                if u != "error":
                    a = await self.lastfmhandler.get_tracks_recent(u, 1)
                    return f"<:lastfm:1121826921223819386> Listening to [{a['recenttracks']['track'][0]['name']}]({a['recenttracks']['track'][0]['url']}) by **{a['recenttracks']['track'][0]['artist']['#text']}** on lastfm.."

            return ""

        def vc(mem: Member):
            if mem.voice:
                channelname = mem.voice.channel.name
                deaf = (
                    "<:deafened:1126831978604400640>"
                    if mem.voice.self_deaf or mem.voice.deaf
                    else "<:undeafened:1126831987714433106>"
                )
                mute = (
                    "<:muted:1126831997596205136>"
                    if mem.voice.self_mute or mem.voice.mute
                    else "<:unmuted:1126831992399482932>"
                )
                stream = (
                    "<:stream:1126831983360737320>" if mem.voice.self_stream else ""
                )
                video = "<:video:1126832001819873371>" if mem.voice.self_video else ""
                channelmembers = (
                    f"with {len(mem.voice.channel.members)-1} other member{'s' if len(mem.voice.channel.members) > 2 else ''}"
                    if len(mem.voice.channel.members) > 1
                    else ""
                )
                return f"{deaf} {mute} {stream} {video} **in voice channel** {channelname} {channelmembers}"
            return ""

        e = Embed(
            color=self.bot.color, title=str(user) + " " + "".join(map(str, badges))
        )
        if isinstance(member, Member):
            e.description = f"{vc(member)}\n{await tz_find(member)}\n{await lf(member)}"
            members = sorted(ctx.guild.members, key=lambda m: m.joined_at)
            ordinal = self.bot.ordinal(int(members.index(member) + 1))
            e.set_author(
                name=f"{member} • {ordinal} member", icon_url=member.display_avatar.url
            )
            e.add_field(
                name="dates",
                value=f"**joined:** {self.bot.convert_datetime(member.joined_at)}\n**created:** {self.bot.convert_datetime(member.created_at)}\n{f'**boosted:** {self.bot.convert_datetime(member.premium_since)}' if self.bot.convert_datetime(member.premium_since) else ''}",
                inline=False,
            )
            roles = member.roles[1:][::-1]
            if len(roles) > 0:
                e.add_field(
                    name=f"roles ({len(roles)})",
                    value=" ".join([r.mention for r in roles])
                    if len(roles) < 5
                    else " ".join([r.mention for r in roles[:4]])
                    + f" ... and {len(roles)-4} more",
                )
        elif isinstance(member, User):
            e.add_field(
                name="dates",
                value=f"**created:** {self.bot.convert_datetime(member.created_at)}",
                inline=False,
            )
        e.set_thumbnail(url=member.display_avatar.url)
        try:
            e.set_footer(
                text="ID: "
                + str(member.id)
                + f" | {len(member.mutual_guilds)} mutual server(s)"
            )
        except:
            e.set_footer(text="ID: " + str(member.id))
        await ctx.reply(embed=e)

    @command(help="get the server's banner", aliases=["guildbanner"])
    async def serverbanner(self, ctx: Context):
        return await ctx.invoke(self.bot.get_command("server banner"))

    @command(
        help="get a server's icon",
        aliases=["guildicon", "guildavatar", "serveravatar"],
    )
    async def servericon(self, ctx: Context):
        return await ctx.invoke(self.bot.get_command("server icon"))

    @command(
        help="get the server's invite background image",
        aliases=["guildsplash"],
    )
    async def serversplash(self, ctx: Context):
        return await ctx.invoke(self.bot.get_command("server splash"))

    @hybrid_command(
        aliases=["si"],
        help="show information about the server",
    )
    async def serverinfo(self, ctx: Context):
        guild = ctx.guild
        icon = f"[icon]({guild.icon.url})" if guild.icon is not None else "N/A"
        splash = f"[splash]({guild.splash.url})" if guild.splash is not None else "N/A"
        banner = f"[banner]({guild.banner.url})" if guild.banner is not None else "N/A"
        desc = guild.description if guild.description is not None else ""
        embed = Embed(
            color=self.bot.color,
            title=f"{guild.name} ・ shard {guild.shard_id}/{self.bot.shard_count-1}",
            description=f"Created on {self.bot.convert_datetime(guild.created_at.replace(tzinfo=None))}\n{desc}",
        )
        embed.set_thumbnail(url=guild.icon)
        embed.add_field(name="owner", value=f"{guild.owner.mention}\n{guild.owner}")
        embed.add_field(
            name=f"channels ({len(guild.channels)})",
            value=f"**text:** {len(guild.text_channels)}\n**voice:** {len(guild.voice_channels)}\n**categories** {len(guild.categories)}",
        )
        embed.add_field(
            name="members",
            value=f"**users:** {len(set(i for i in guild.members if not i.bot))} ({((len(set(i for i in guild.members if not i.bot)))/guild.member_count) * 100:.2f}%)\n**bots:** {len(set(i for i in guild.members if i.bot))} ({(len(set(i for i in guild.members if i.bot))/guild.member_count) * 100:.2f}%)\n**total:** {guild.member_count}",
        )
        embed.add_field(name="icons", value=f"{icon}\n{splash}\n{banner}")
        embed.add_field(
            name="info",
            value=f"**verification:** {guild.verification_level}\n**boosts:** {guild.premium_subscription_count} (level {guild.premium_tier})\n**large:** {'yes' if guild.large else 'no'}",
        )
        embed.add_field(
            name="counts",
            value=f"**roles:** {len(guild.roles)}/250\n**emojis:** {len(guild.emojis)}/{guild.emoji_limit*2}\n**stickers:** {len(guild.stickers)}/{guild.sticker_limit}",
        )
        if len([g for g in guild.features]) > 0:
            embed.add_field(
                name="features",
                value=f"```{', '.join([g for g in guild.features])}```",
                inline=False,
            )
        embed.set_footer(text=f"ID: {guild.id}")
        await ctx.reply(embed=embed)

    @hybrid_group(aliases=["guild"], invoke_without_command=True)
    async def server(self, ctx: Context):
        return await ctx.invoke(self.bot.get_command("serverinfo"))

    @server.command(
        help="show information about the server",
    )
    async def info(self, ctx: Context):
        return await ctx.invoke(self.bot.get_command("serverinfo"))

    @server.command(
        help="get a server's banner",
    )
    async def banner(self, ctx: Context):
        guild = ctx.guild
        if not guild.banner:
            return await ctx.send_warning("this server has no banner".capitalize())
        embed = Embed(
            color=self.bot.color, title=f"{guild.name}'s banner", url=guild.banner.url
        )
        embed.set_image(url=guild.banner.url)
        await ctx.reply(embed=embed)

    @server.command(
        help="get a server's icon",
    )
    async def icon(self, ctx: Context, *, id: int = None):
        guild = ctx.guild
        if not guild.icon:
            return await ctx.send_warning("this server has no icon".capitalize())
        embed = Embed(
            color=self.bot.color, title=f"{guild.name}'s icon", url=guild.icon.url
        )
        embed.set_image(url=guild.icon.url)
        await ctx.reply(embed=embed)

    @server.command(
        help="get a server's invite background image",
    )
    async def splash(self, ctx: Context):
        guild = ctx.guild
        if not guild.splash:
            return await ctx.send_warning("this server has no splash".capitalize())
        embed = Embed(
            color=self.bot.color,
            title=f"{guild.name}'s invite background",
            url=guild.splash.url,
        )
        embed.set_image(url=guild.splash.url)
        await ctx.reply(embed=embed)

    @hybrid_command(
        help="shows the number of invites an user has",
        usage="<user>",
    )
    async def invites(self, ctx: Context, *, member: Member = None):
        if member is None:
            member = ctx.author
        invites = await ctx.guild.invites()
        await ctx.reply(
            f"{member} has **{sum(invite.uses for invite in invites if invite.inviter.id == member.id)}** invites"
        )

    @command(help="see the list of donators", aliases=["donors"])
    async def donators(self, ctx):
        i = 0
        k = 1
        l = 0
        mes = ""
        number = []
        messages = []
        results = await self.bot.db.fetch("SELECT * FROM donor")
        if len(results) == 0:
            return await ctx.send_error("There are no donators")
        for result in results:
            mes = f"{mes}`{k}` <@!{result['user_id']}> ({result['user_id']}) - (<t:{int(result['time'])}:R>)\n"
            k += 1
            l += 1
            if l == 10:
                messages.append(mes)
                number.append(
                    Embed(
                        color=self.bot.color,
                        title=f"donators ({len(results)})",
                        description=messages[i],
                    )
                )
                i += 1
                mes = ""
                l = 0

        messages.append(mes)
        number.append(
            Embed(
                color=self.bot.color,
                title=f"donators ({len(results)})",
                description=messages[i],
            )
        )
        await ctx.paginator(number)

    @command(
        aliases=["tts", "speech"],
        help="convert your message to mp3",
        usage="[message]",
    )
    async def texttospeech(self, ctx: Context, *, txt: str):
        i = BytesIO()
        aiogtts = aiogTTS()
        await aiogtts.save(txt, "tts.mp3", lang="en")
        await aiogtts.write_to_fp(txt, i, slow=False, lang="en")
        await ctx.reply(file=discord.File(fp="tts.mp3", filename="tts.mp3"))
        return os.remove("tts.mp3")

    @hybrid_command(
        help="gets the invite link with administrator permission of a bot",
        usage="[bot id]",
    )
    async def getbotinvite(self, ctx, id: User):
        if not id.bot:
            return await ctx.send_error("This isn't a bot")
        embed = Embed(
            color=self.bot.color,
            description=f"**[invite the bot](https://discord.com/api/oauth2/authorize?client_id={id.id}&permissions=8&scope=bot%20applications.commands)**",
        )
        await ctx.reply(embed=embed)

    @command(
        aliases=["tr"],
        help="translate a message",
        usage="[language] [message]",
    )
    async def translate(self, ctx: Context, lang: str, *, mes: str):
        translated = GoogleTranslator(source="auto", target=lang).translate(mes)
        embed = Embed(
            color=self.bot.color,
            description="```{}```".format(translated),
            title="translated to {}".format(lang),
        )
        await ctx.reply(embed=embed)

    @hybrid_command(
        aliases=["firstmsg"],
        help="get the first message",
        usage="<channel>",
    )
    async def firstmessage(self, ctx: Context, *, channel: TextChannel = None):
        channel = channel or ctx.channel
        messages = [mes async for mes in channel.history(oldest_first=True, limit=1)]
        message = messages[0]
        embed = Embed(
            color=self.bot.color,
            title="first message in #{}".format(channel.name),
            description=message.content,
            timestamp=message.created_at,
        )
        embed.set_author(name=message.author, icon_url=message.author.display_avatar)
        view = View()
        view.add_item(Button(label="jump to message", url=message.jump_url))
        await ctx.reply(embed=embed, view=view)

    @group(
        invoke_without_command=True,
        help="check member's birthday",
        aliases=["bday"],
    )
    async def birthday(self, ctx: Context, *, member: Member = None):
        if member is None:
            member = ctx.author
        lol = "'s"
        date = await self.bot.db.fetchrow(
            "SELECT bday FROM birthday WHERE user_id = $1", member.id
        )
        if not date:
            return await ctx.send_warning(
                f"**{'Your' if member == ctx.author else str(member) + lol}** birthday is not set"
            )
        date = date["bday"]
        if "ago" in arrow.get(date).humanize(granularity="day"):
            date = date.replace(year=date.year + 1)
        else:
            date = date
        if arrow.get(date).humanize(granularity="day") == "in 0 days":
            date = "tomorrow"
        elif (
            arrow.get(date).day == arrow.utcnow().day
            and arrow.get(date).month == arrow.utcnow().month
        ):
            date = "today"
        else:
            date = arrow.get(date + datetime.timedelta(days=1)).humanize(
                granularity="day"
            )
        await self.bday_send(
            ctx,
            f"{'Your' if member == ctx.author else '**' + member.name + lol + '**'} birthday is **{date}**",
        )

    @birthday.command(
        name="set",
        help="set your birthday",
        usage="[month] [day]\nexample: birthday set January 19",
    )
    async def bday_set(self, ctx: Context, month: str, day: str):
        try:
            if len(month) == 1:
                mn = "M"
            elif len(month) == 2:
                mn = "MM"
            elif len(month) == 3:
                mn = "MMM"
            else:
                mn = "MMMM"
            if "th" in day:
                day = day.replace("th", "")
            if "st" in day:
                day = day.replace("st", "")
            if len(day) == 1:
                dday = "D"
            else:
                dday = "DD"
            ts = f"{month} {day} {datetime.date.today().year}"
            if "ago" in arrow.get(ts, f"{mn} {dday} YYYY").humanize(granularity="day"):
                year = datetime.date.today().year + 1
            else:
                year = datetime.date.today().year
            string = f"{month} {day} {year}"
            date = arrow.get(string, f"{mn} {dday} YYYY")
            check = await self.bot.db.fetchrow(
                "SELECT * FROM birthday WHERE user_id = $1", ctx.author.id
            )
            if not check:
                await self.bot.db.execute(
                    "INSERT INTO birthday VALUES ($1,$2,$3)",
                    ctx.author.id,
                    date.datetime,
                    "false",
                )
            else:
                await self.bot.db.execute(
                    "UPDATE birthday SET bday = $1 WHERE user_id = $2",
                    date.datetime,
                    ctx.author.id,
                )
            await self.bday_send(ctx, f"Configured your birthday as **{month} {day}**")
        except:
            return await ctx.send_error(
                f"usage: `{ctx.clean_prefix}birthday set [month] [day]`"
            )

    @birthday.command(name="unset", help="unset your birthday")
    async def bday_unset(self, ctx: Context):
        check = await self.bot.db.fetchrow(
            "SELECT bday FROM birthday WHERE user_id = $1", ctx.author.id
        )
        if not check:
            return await ctx.send_warning("Your birthday is not set")
        await self.bot.db.execute(
            "DELETE FROM birthday WHERE user_id = $1", ctx.author.id
        )
        await ctx.send_warning("Unset your birthday")

    @group(
        invoke_without_command=True,
        help="check member's timezones",
        aliases=["tz"],
    )
    async def timezone(self, ctx: Context, *, member: discord.Member = None):
        if member is None:
            member = ctx.author
        return await self.tz.get_user_timezone(ctx, member)

    @timezone.command(
        name="set",
        help="set the timezone",
        usage="[location]\nexample: ;tz set russia",
    )
    async def tz_set(self, ctx: Context, *, location: str):
        return await self.tz.tz_set_cmd(ctx, location)

    @timezone.command(
        name="list",
        help="return a list of server member's timezones",
    )
    async def tz_list(self, ctx: Context):
        ids = [str(m.id) for m in ctx.guild.members]
        results = await self.bot.db.fetch(
            f"SELECT * FROM timezone WHERE user_id IN ({','.join(ids)})"
        )
        if len(results) == 0:
            await self.tz.timezone_send(ctx, "Nobody (even you) has their timezone set")
        await ctx.typing()
        i = 0
        k = 1
        l = 0
        mes = ""
        number = []
        messages = []
        for result in results:
            mes = f"{mes}`{k}` <@{int(result['user_id'])}> - {await self.tz.timezone_request(ctx.guild.get_member(int(result['user_id'])))}\n"
            k += 1
            l += 1
            if l == 10:
                messages.append(mes)
                number.append(
                    Embed(
                        color=self.bot.color,
                        title=f"timezone list",
                        description=messages[i],
                    )
                )
                i += 1
                mes = ""
                l = 0

        messages.append(mes)
        embed = Embed(
            color=self.bot.color, title=f"timezone list", description=messages[i]
        )
        number.append(embed)
        await ctx.paginator(number)

    @timezone.command(name="unset", help="unset the timezone")
    async def tz_unset(self, ctx: Context):
        check = await self.bot.db.fetchrow(
            "SELECT * FROM timezone WHERE user_id = $1", ctx.author.id
        )
        if not check:
            return await ctx.send_warning("You don't have a **timezone** set")
        await self.bot.db.execute(
            "DELETE * FROM timezone WHERE user_id = $1", ctx.author.id
        )
        return await ctx.send_success("Removed the timezone")

    @group(invoke_without_command=True)
    async def reminder(self, ctx: Context):
        return await ctx.create_pages()

    @reminder.command(
        name="add",
        help="make the bot remind you about a task",
        usage="[time] [reminder]",
    )
    async def reminder_add(self, ctx: Context, time: str, *, task: str):
        return await ctx.invoke(self.bot.get_command("remind"), time=time, task=task)

    @reminder.command(
        name="stop",
        aliases=["cancel"],
        help="cancel a reminder from this server",
    )
    @is_there_a_reminder()
    async def reminder_stop(self, ctx: Context):
        await self.bot.db.execute(
            "DELETE FROM reminder WHERE guild_id = $1 AND user_id = $2",
            ctx.guild.id,
            ctx.author.id,
        )
        return await ctx.send_success("Deleted a reminder")

    @command(
        aliases=["remindme"],
        help="make the bot remind you about a task",
        usage="[time] [reminder]",
    )
    async def remind(self, ctx: Context, time: str, *, task: str):
        try:
            seconds = humanfriendly.parse_timespan(time)
        except humanfriendly.InvalidTimespan:
            return await ctx.send_warning(f"**{time}** is not a correct time format")
        await ctx.reply(
            f"🕰️ {ctx.author.mention}: I'm going to remind you in {humanfriendly.format_timespan(seconds)} about **{task}**"
        )
        if seconds < 5:
            await asyncio.sleep(seconds)
            return await ctx.channel.send(f"🕰️ {ctx.author.mention}: {task}")
        else:
            try:
                await self.bot.db.execute(
                    "INSERT INTO reminder VALUES ($1,$2,$3,$4,$5)",
                    ctx.author.id,
                    ctx.channel.id,
                    ctx.guild.id,
                    (datetime.datetime.now() + datetime.timedelta(seconds=seconds)),
                    task,
                )
            except:
                return await ctx.send_warning(
                    "You already have a reminder set in this channel. Use `{ctx.clean_prefix}reminder stop` to cancel the reminder"
                )

    @command(
        name="rotate",
        usage="<attachment> <degree>",
        aliases=["rotation"],
        help="rotate a picture to a degree",
    )
    async def rotate(self, ctx, degree: int):
        if len(ctx.message.attachments) == 0:
            embed = discord.Embed(
                title="Rotate",
                help="Please attach an image file to rotate.",
                color=self.bot.color,
            )
            await ctx.send(embed=embed)
            return

        attachment = ctx.message.attachments[0]
        if not attachment.filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
            embed = discord.Embed(
                title="Rotate",
                help="Invalid image format. Please provide a valid image file (PNG, JPG, JPEG, GIF).",
                color=self.bot.color,
            )
            await ctx.send(embed=embed)
            return

        try:
            image_bytes = await attachment.read()
            img = Image.open(BytesIO(image_bytes))
            rotated_img = img.rotate(degree)
            rotated_bytes = BytesIO()
            rotated_img.save(rotated_bytes, format="PNG")
            rotated_bytes.seek(0)

            file = discord.File(rotated_bytes, filename="rotated_image.png")
            await ctx.send(file=file)
        except Exception as e:
            embed = discord.Embed(
                title="Rotate",
                description=f"An error occurred while rotating the image: {str(e)}",
                color=self.bot.color,
            )
            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Utils(bot))
