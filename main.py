import os, time, discord, asyncpg, random, string, datetime, typing, json
from discord.ext import commands
from discord.gateway import DiscordWebSocket
from cogs.voicemaster import vmbuttons
from cogs.ticket import CreateTicket, DeleteTicket
from extensions.utilities import StartUp, create_db
from extensions.extension import Client, HTTP
from humanfriendly import format_timespan
from typing import List
from extensions.utilities import PaginatorView
from io import BytesIO

with open("config.json", "r") as config_file:
    config = json.load(config_file)
token = config["token"]


def generate_key():
    return "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(6)
    )


async def checkthekey(key: str):
    check = await bot.db.fetchrow("SELECT * FROM cmderror WHERE code = $1", key)
    if check:
        newkey = await generate_key(key)
        return await checkthekey(newkey)
    return key


DiscordWebSocket.identify = StartUp.identify
intents = discord.Intents.all()


async def getprefix(bot, message):
    if not message.guild:
        return ";"
    check = await bot.db.fetchrow(
        "SELECT * FROM selfprefix WHERE user_id = $1", message.author.id
    )
    if check:
        selfprefix = check["prefix"]
    res = await bot.db.fetchrow(
        "SELECT * FROM prefixes WHERE guild_id = $1", message.guild.id
    )
    if res:
        guildprefix = res["prefix"]
    else:
        guildprefix = ";"
    if not check and res:
        selfprefix = res["prefix"]
    elif not check and not res:
        selfprefix = ";"
    return guildprefix, selfprefix


class NeoContext(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def find_role(self, name: str):
        for role in self.guild.roles:
            if role.name == "@everyone":
                continue
            if name.lower() in role.name.lower():
                return role
        return None

    async def send_success(self, message: str) -> discord.Message:
        return await self.reply(
            embed=discord.Embed(
                color=self.bot.color,
                description=f"{self.bot.yes} {self.author.mention}: {message}",
            )
        )

    async def send_error(self, message: str) -> discord.Message:
        return await self.reply(
            embed=discord.Embed(
                color=self.bot.color,
                description=f"{self.bot.no} {self.author.mention}: {message}",
            )
        )

    async def send_warning(self, message: str) -> discord.Message:
        return await self.reply(
            embed=discord.Embed(
                color=self.bot.color,
                description=f"{self.bot.warning} {self.author.mention}: {message}",
            )
        )

    async def paginator(self, embeds: List[discord.Embed]):
        if len(embeds) == 1:
            return await self.send(embed=embeds[0])
        view = PaginatorView(self, embeds)
        view.message = await self.reply(embed=embeds[0], view=view)

    async def cmdhelp(self):
        command = self.command
        commandname = (
            f"{str(command.parent)} {command.name}"
            if str(command.parent) != "None"
            else command.name
        )
        if command.cog_name == "owner":
            return
        embed = discord.Embed(
            color=bot.color, title=commandname, description=command.description
        )
        embed.set_author(name=bot.user.name, icon_url=bot.user.avatar.url)
        embed.add_field(name="category", value=command.help)
        embed.add_field(
            name="aliases", value=", ".join(map(str, command.aliases)) or "none"
        )
        embed.add_field(name="permissions", value=command.brief or "any")
        embed.add_field(
            name="usage",
            value=f"```{commandname} {command.usage if command.usage else ''}```",
            inline=False,
        )
        await self.reply(embed=embed)

    async def create_pages(self):
        embeds = []
        i = 0
        for command in self.command.commands:
            commandname = (
                f"{str(command.parent)} {command.name}"
                if str(command.parent) != "None"
                else command.name
            )
            i += 1
            embeds.append(
                discord.Embed(
                    color=bot.color,
                    title=f"{commandname}",
                    description=command.description,
                )
                .set_author(name=bot.user.name, icon_url=bot.user.display_avatar.url)
                .add_field(
                    name="usage",
                    value=f"```{commandname} {command.usage if command.usage else ''}```",
                    inline=False,
                )
                .set_footer(
                    text=f"aliases: {', '.join(a for a in command.aliases) if len(command.aliases) > 0 else 'none'} ・ {i}/{len(self.command.commands)}"
                )
            )
        return await self.paginator(embeds)


class CommandClient(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(
            shard_count=2,
            command_prefix=getprefix,
            allowed_mentions=discord.AllowedMentions(
                roles=False, everyone=False, users=True, replied_user=False
            ),
            intents=intents,
            help_command=None,
            strip_after_prefix=True,
            activity=discord.Activity(
                name=";help ", type=discord.ActivityType.competing
            ),
            owner_ids=[236931919063941121, 825704399523282954],
        )
        self.uptime = time.time()
        self.persistent_views_added = False
        self.cogs_loaded = False
        self.color = 0x2B2D31
        self.removebg_api = [
            "52tiT5sgHQxoVBoQhvXPPaEy",
            "stFyKj4GTUY3CUPFYKWmt57V",
            "nFXg4MpkATXYVHcJM5J9hq1L",
        ]
        self.fail = "<:deny:1121826907739144412>"
        self.yes = "<:approve:1121826853678747710>"
        self.no = "<:deny:1121826907739144412>"
        self.warning = "<:watttt:1139317517408546816>"
        self.invite = "https://discord.com/api/oauth2/authorize?client_id=1107283467655458866&permissions=8&scope=bot"
        self.left = "<:page_previous:1121826961455583336>"
        self.reply = "<:miroreply:1107719722394456065>"
        self.right = "<:page_next:1121826957575852042>"
        self.goto = "<:filter:1113850464832868433>"
        self.m_cd = commands.CooldownMapping.from_cooldown(
            1, 5, commands.BucketType.member
        )
        self.c_cd = commands.CooldownMapping.from_cooldown(
            1, 5, commands.BucketType.channel
        )
        self.m_cd2 = commands.CooldownMapping.from_cooldown(
            1, 10, commands.BucketType.member
        )
        self.main_guilds = [1131605253108813914]
        self.global_cd = commands.CooldownMapping.from_cooldown(
            2, 5, commands.BucketType.member
        )
        self.ext = Client(self)
        self.session_id = "59071245027%3AD0cDcLaxyzVyVQ%3A16%3AAYdIOvL5SM85A62N-zDxn04CaabIDHneyhA6I0r6VQ"

    async def create_db_pool(self):
        self.db = await asyncpg.create_pool(
            port="5432",
            database="postgres",
            user="postgres",
            host="db.uialfmzzwlzpapiqacgg.supabase.co",
            password="yT0Sjuhv53frF64I",
        )

    async def get_context(self, message, *, cls=NeoContext):
        return await super().get_context(message, cls=cls)

    async def setup_hook(self) -> None:
        print("Trying to start my master!")
        self.session = HTTP()
        await self.create_db_pool()
        await self.load_extension("jishaku")
        self.add_view(vmbuttons())
        self.add_view(CreateTicket())
        self.add_view(DeleteTicket())
        bot.loop.create_task(StartUp.startup(bot))
        os.system("cls")

    def convert_datetime(self, date: datetime.datetime = None):
        if date is None:
            return None
        month = f"0{date.month}" if date.month < 10 else date.month
        day = f"0{date.day}" if date.day < 10 else date.day
        year = date.year
        minute = f"0{date.minute}" if date.minute < 10 else date.minute
        if date.hour < 10:
            hour = f"0{date.hour}"
            meridian = "AM"
        elif date.hour > 12:
            hour = f"0{date.hour - 12}" if date.hour - 12 < 10 else f"{date.hour - 12}"
            meridian = "PM"
        else:
            hour = date.hour
            meridian = "PM"
        return f"{month}/{day}/{year} at {hour}:{minute} {meridian} ({discord.utils.format_dt(date, style='R')})"

    def ordinal(self, num: int) -> str:
        numb = str(num)
        if numb.startswith("0"):
            numb = numb.strip("0")
        if numb in ["11", "12", "13"]:
            return numb + "th"
        if numb.endswith("1"):
            return numb + "st"
        elif numb.endswith("2"):
            return numb + "nd"
        elif numb.endswith("3"):
            return numb + "rd"
        else:
            return numb + "th"

    def is_dangerous(self, role: discord.Role) -> bool:
        permissions = role.permissions
        return any(
            [
                permissions.kick_members,
                permissions.ban_members,
                permissions.administrator,
                permissions.manage_channels,
                permissions.manage_guild,
                permissions.manage_messages,
                permissions.manage_roles,
                permissions.manage_webhooks,
                permissions.manage_emojis_and_stickers,
                permissions.manage_threads,
                permissions.mention_everyone,
                permissions.moderate_members,
            ]
        )

    async def prefixes(self, message: discord.Message) -> List[str]:
        prefixes = []
        for l in set(p for p in await self.command_prefix(self, message)):
            prefixes.append(l)
        return prefixes

    async def channel_ratelimit(self, message: discord.Message) -> typing.Optional[int]:
        cd = self.c_cd
        bucket = cd.get_bucket(message)
        return bucket.update_rate_limit()

    async def member_ratelimit(self, message: discord.Message) -> typing.Optional[int]:
        cd = self.m_cd
        bucket = cd.get_bucket(message)
        return bucket.update_rate_limit()

    async def on_ready(self):
        await create_db(self)
        if self.cogs_loaded == False:
            await StartUp.loadcogs(self)
        print(f"Connected to discord as {self.user} {self.user.id}")

    async def on_message_edit(self, before, after):
        if before.content != after.content:
            await self.process_commands(after)

    async def on_message(self, message: discord.Message):
        channel_rl = await self.channel_ratelimit(message)
        member_rl = await self.member_ratelimit(message)
        if channel_rl == True:
            return
        if member_rl == True:
            return
        if message.content == "<@{}>".format(self.user.id):
            return await message.reply(
                content="prefixes: "
                + " ".join(f"`{g}`" for g in await self.prefixes(message))
            )
        await bot.process_commands(message)

    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.NotOwner):
            pass
        elif isinstance(error, commands.CheckFailure):
            if isinstance(error, commands.MissingPermissions):
                return await ctx.send_warning(
                    f"This command requires **{error.missing_permissions[0]}** permission"
                )
        elif isinstance(error, commands.CommandOnCooldown):
            if ctx.command.name != "hit":
                return await ctx.reply(
                    embed=discord.Embed(
                        color=0x2B2D31,
                        description=f"⌛ {ctx.author.mention}: You are on cooldown. Try again in {format_timespan(error.retry_after)}",
                    ),
                    mention_author=False,
                )
        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.cmdhelp()
        elif isinstance(error, commands.EmojiNotFound):
            return await ctx.send_warning(
                f"Unable to convert {error.argument} into an **emoji**"
            )
        elif isinstance(error, commands.MemberNotFound):
            return await ctx.send_warning(f"Unable to find member **{error.argument}**")
        elif isinstance(error, commands.UserNotFound):
            return await ctx.send_warning(f"Unable to find user **{error.argument}**")
        elif isinstance(error, commands.RoleNotFound):
            return await ctx.send_warning(f"Couldn't find role **{error.argument}**")
        elif isinstance(error, commands.ChannelNotFound):
            return await ctx.send_warning(f"Couldn't find channel **{error.argument}**")
        elif isinstance(error, commands.UserConverter):
            return await ctx.send_warning(f"Couldn't convert that into an **user** ")
        elif isinstance(error, commands.MemberConverter):
            return await ctx.send_warning("Couldn't convert that into a **member**")
        elif isinstance(error, commands.BadArgument):
            return await ctx.send_warning(error.args[0])
        elif isinstance(error, commands.BotMissingPermissions):
            return await ctx.send_warning(
                f"I do not have enough **permissions** to execute this command"
            )
        elif isinstance(error, discord.HTTPException):
            return await ctx.send_warning("Unable to execute this command")
        else:
            key = await checkthekey(generate_key())
            trace = str(error)
            rl = await self.member_ratelimit(ctx.message)
            if rl == True:
                return
            await self.db.execute("INSERT INTO cmderror VALUES ($1, $2)", key, trace)
            await self.ext.send_error(
                ctx,
                f"An unexpected error was found. Please report the code `{key}` in our [**support server**](https://discord.gg/clust)",
            )
bot = CommandClient()

@bot.check
async def cooldown_check(ctx: commands.Context):
    bucket = bot.global_cd.get_bucket(ctx.message)
    retry_after = bucket.update_rate_limit()
    if retry_after:
        raise commands.CommandOnCooldown(
            bucket, retry_after, commands.BucketType.member
        )
    return True


async def check_ratelimit(ctx):
    cd = bot.m_cd2.get_bucket(ctx.message)
    return cd.update_rate_limit()


@bot.check
async def disabled_command(ctx: commands.Context):
    cmd = bot.get_command(ctx.invoked_with)
    if not cmd:
        return True
    check = await ctx.bot.db.fetchrow(
        "SELECT * FROM disablecommand WHERE command = $1 AND guild_id = $2",
        cmd.name,
        ctx.guild.id,
    )
    if check:
        await bot.ext.send_warning(ctx, f"The command **{cmd.name}** is **disabled**")
    return check is None


@bot.check
async def blacklist_check(ctx: commands.Context):
    user_id = ctx.author.id
    blacklisted_user = await ctx.bot.db.fetchrow(
        "SELECT * FROM blacklist WHERE user_id = $1", user_id
    )

    if blacklisted_user:
        return False

    return True


if __name__ == "__main__":
    bot.run(token)
