import discord, json, datetime, requests, os, psutil, json, random, aiohttp, asyncio, animec
from discord.ext import commands
from discord.utils import format_dt
from discord.ui import View, Button
from io import BytesIO
from extensions import paginator as pg
from bs4 import BeautifulSoup
from discord import Embed, Message
from colorthief import ColorThief
from PIL import Image
from googleapiclient.discovery import build
from urllib.parse import quote
from typing import Union

now = datetime.datetime.now()


class TikTokLinkBUtton(discord.ui.Button):
    def __init__(self, username: str, custom_emoji: Union[discord.Emoji, str] = None):
        self.username = username
        super().__init__(
            style=discord.ButtonStyle.link,
            label=None,
            url=f"https://www.tiktok.com/@{self.username}?lang=en",
            emoji=custom_emoji,
        )


class YoutubeButton(discord.ui.Button):
    def __init__(
        self, channel_name: str, custom_emoji: Union[discord.Emoji, str] = None
    ):
        self.channel_name = channel_name
        super().__init__(
            style=discord.ButtonStyle.link,
            label=None,
            url=f"https://www.youtube.com/channel/{quote(self.channel_name)}",
            emoji=custom_emoji,
        )


class Info(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self.youtube = build(
            "youtube", "v3", developerKey="AIzaSyCSSiHIlwCYEE17VCV5Ig4SdvVsvngafdA"
        )

    @commands.hybrid_command(help="check how long the bot has been online for")
    async def uptime(self, ctx: commands.Context):
        e = discord.Embed(
            color=self.bot.color,
            description=f"⏰ **{self.bot.user.name}'s** uptime: **{self.bot.ext.uptime}**",
        )
        await ctx.reply(embed=e)

    @commands.command(name="ping", aliases=["latency"])
    async def ping(self, ctx):
        embed = discord.Embed(
            description=f":satellite: Gateway: `{self.bot.latency * 1000:.2f}ms`",
            color=self.bot.color,
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(help="show credits to contributors of the bot")
    async def credits(self, ctx: commands.Context):
        embed = discord.Embed(
            color=self.bot.color,
            description=f">>> **{self.bot.get_user(self.bot.owner_ids[0])}** - Main developer of the bot\n**xotic** - Sponsor/Admin\n**caden** - Api/Sponsor",
        )
        await ctx.reply(embed=embed)

    @commands.hybrid_command(help="invite the bot", aliases=["support", "inv"])
    async def invite(self, ctx):
        avatar_url = self.bot.user.avatar.url
        embed = discord.Embed(
            color=self.bot.color, description="Add the bot in your server!"
        )
        embed.set_author(name=self.bot.user.name, icon_url=f"{avatar_url}")
        button1 = Button(
            label="invite",
            url=f"https://discord.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&scope=bot%20applications.commands",
        )
        button2 = Button(label="support", url="https://discord.gg/clust")
        view = View()
        view.add_item(button1)
        view.add_item(button2)
        await ctx.reply(embed=embed, view=view)

    @commands.command(
        help="Shows information on an anime",
        usage=" <name>",
        aliases=["ani"],
    )
    @commands.cooldown(1, 4, commands.BucketType.guild)
    async def anime(self, ctx, *, query):
        try:
            embed = discord.Embed(
                description=f"Fetching anime information", colour=0x2B2D31
            )
            message = await ctx.reply(embed=embed)
            anime = animec.Anime(query)
        except:
            embed = discord.Embed(description="No results found")
            await ctx.reply(embed=embed)

        try:
            title = (
                str(anime.title_english)
                if str(anime.title_english)
                else str(anime.title_japanese)
            )
            embed = discord.Embed(
                title="Anime search results",
                url=anime.url,
                description=f"""**{str(anime.title_english)}**
**Description:** {anime.description[:500]}...""",
                colour=0x2B2D31,
            )
            embed.add_field(
                name="General",
                value=f"""**Genres:** {str(anime.genres)}
**Aired:** {str(anime.aired)}
**Broadcast:** {str(anime.broadcast)}
**Popularity:** {str(anime.popularity)}""",
            )
            embed.add_field(
                name="Overview",
                value=f"""**Episodes:** {str(anime.episodes)}
**NSFW:** {str(anime.is_nsfw())}
**Status:** {str(anime.status)}""",
            )
            embed.add_field(
                name="Scores",
                value=f"""**Favorites:** {str(anime.favorites)}
**Rating:** {str(anime.rating)}
**Rank:** {str(anime.ranked)}""",
            )
            embed.set_thumbnail(url=anime.poster)
            embed.set_author(
                name=ctx.message.author.name, icon_url=ctx.message.author.avatar
            )
            await message.delete()
            await ctx.reply(embed=embed)
        except Exception as e:
            print(e)

    @commands.command(
        help="Shows the latest anime news",
        usage="",
        aliases=["animenews"],
    )
    async def aninews(self, ctx, amount: int = 4):
        try:
            embed = discord.Embed(description=f"Fetching anime news", colour=0x2B2D31)
            message = await ctx.reply(embed=embed)
            await asyncio.sleep(1)
            news = animec.Aninews(amount)
            links = news.links
            titles = news.titles
            descriptions = news.description

            embed = discord.Embed(
                title="Latest Anime News",
                timestamp=datetime.datetime.utcnow(),
                colour=0x2B2D31,
            )
            embed.set_thumbnail(url=news.images[0])

            for i in range(amount):
                embed.add_field(
                    name=f"{i+1}) {titles[i]}",
                    value=f"{descriptions[i][:200]}...\n[Read more]({links[i]})",
                    inline=False,
                )
            await message.delete()
            await ctx.reply(embed=embed)
        except Exception as e:
            print(e)

    @commands.command(
        name="xbox",
        help="show a xbox account",
        usage="[username]",
        aliases=["xb"],
    )
    @commands.cooldown(1, 4, commands.BucketType.guild)
    async def xbox(self, ctx, *, username):
        try:
            try:
                username = username.replace(" ", "%20")
            except:
                pass
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=False)
            ) as client:
                async with client.get(
                    f"https://playerdb.co/api/player/xbox/{username}"
                ) as r:
                    data = await r.json()
                    try:
                        embed = (
                            discord.Embed(
                                title=data["data"]["player"]["username"],
                                color=int("0f7c0f", 16),
                                url=f"https://xboxgamertag.com/search/{username}",
                            )
                            .add_field(
                                name="Gamerscore",
                                value=data["data"]["player"]["meta"]["gamerscore"],
                                inline=True,
                            )
                            .add_field(
                                name="Tenure",
                                value=data["data"]["player"]["meta"]["tenureLevel"],
                                inline=True,
                            )
                            .add_field(
                                name="Tier",
                                value=data["data"]["player"]["meta"]["accountTier"],
                                inline=True,
                            )
                            .add_field(
                                name="Rep",
                                value=data["data"]["player"]["meta"][
                                    "xboxOneRep"
                                ].strip("Player"),
                                inline=True,
                            )
                            .set_author(
                                name=ctx.author, icon_url=ctx.author.display_avatar
                            )
                            .set_footer(
                                text="Xbox",
                                icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/f/f9/Xbox_one_logo.svg/1024px-Xbox_one_logo.svg.png",
                            )
                        )
                        embed.set_thumbnail(
                            url=data["data"]["player"]["avatar"]
                        ).add_field(
                            name="ID", value=data["data"]["player"]["id"], inline=True
                        )
                        if data["data"]["player"]["meta"]["bio"]:
                            embed.description = data["data"]["player"]["meta"]["bio"]
                        await ctx.reply(embed=embed)
                    except:
                        embed = (
                            discord.Embed(
                                title=data["data"]["player"]["username"],
                                color=int("0f7c0f", 16),
                                url=f"https://xboxgamertag.com/search/{username}",
                            )
                            .add_field(
                                name="Gamerscore",
                                value=data["data"]["player"]["meta"]["gamerscore"],
                                inline=True,
                            )
                            .add_field(
                                name="Tenure",
                                value=data["data"]["player"]["meta"]["tenureLevel"],
                                inline=True,
                            )
                            .add_field(
                                name="Tier",
                                value=data["data"]["player"]["meta"]["accountTier"],
                                inline=True,
                            )
                            .add_field(
                                name="Rep",
                                value=data["data"]["player"]["meta"][
                                    "xboxOneRep"
                                ].strip("Player"),
                                inline=True,
                            )
                            .set_author(
                                name=ctx.author, icon_url=ctx.author.display_avatar
                            )
                            .set_footer(
                                text="Xbox",
                                icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/f/f9/Xbox_one_logo.svg/1024px-Xbox_one_logo.svg.png",
                            )
                            .add_field(
                                name="ID",
                                value=data["data"]["player"]["id"],
                                inline=True,
                            )
                        )
                        if data["data"]["player"]["meta"]["bio"]:
                            embed.description = data["data"]["player"]["meta"]["bio"]
                        await ctx.reply(embed=embed)
        except:
            return await ctx.reply(
                embed=discord.Embed(
                    description=f"<:watttt:1139317517408546816> Gamertag **`{username}`** not found",
                    color=int("f7f9f8", 16),
                )
            )

    @commands.command(
        name="wolfram",
        help="Search a query on Wolfram Alpha",
        usage="(query)\nExample: ;wolfram integral of x^2",
        aliases=["wolframalpha", "wa", "w"],
    )
    async def wolfram(self, ctx, *, query: str):
        response = requests.get(
            "https://notsobot.com/api/search/wolfram-alpha",
            params=dict(query=query),
        )
        data = response.json()

        if not data.get("fields"):
            return await ctx.warn("Couldn't **understand** your input")

        embed = discord.Embed(
            url=data.get("url"),
            title=query,
        )

        for index, field in enumerate(data.get("fields")[:4]):
            if index == 2:
                continue

            embed.add_field(
                name=field.get("name"),
                value=(">>> " if index == 3 else "")
                + field.get("value")
                .replace("( ", "(")
                .replace(" )", ")")
                .replace("(", "(`")
                .replace(")", "`)"),
                inline=(False if index == 3 else True),
            )
        embed.set_footer(
            text="Wolfram Alpha",
            icon_url="https://cdn.discordapp.com/attachments/1107734070659653652/1121513483385708554/Cherry_Blossoms.png",
        )
        await ctx.send(embed=embed)

    @commands.command(
        name="channelinfo",
        help="See info about channel",
        usage="<channel>",
        aliases=[
            "cinfo",
            "ci",
        ],
    )
    async def channelinfo(
        self,
        ctx,
        *,
        channel: discord.TextChannel
        | discord.VoiceChannel
        | discord.CategoryChannel = None,
    ) -> Message:
        channel = channel or ctx.channel
        if not isinstance(
            channel,
            (discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel),
        ):
            return await ctx.send_help()

        embed = Embed(title=channel.name)

        embed.add_field(
            name="Channel ID",
            value=f"`{channel.id}`",
            inline=True,
        )
        embed.add_field(
            name="Type",
            value=f"`{channel.type}`",
            inline=True,
        )
        embed.add_field(
            name="Guild",
            value=f"{ctx.guild} (`{ctx.guild.id}`)",
            inline=True,
        )

        if category := channel.category:
            embed.add_field(
                name="Category",
                value=f"{category} (`{category.id}`)",
                inline=False,
            )

        if isinstance(channel, discord.TextChannel) and channel.topic:
            embed.add_field(
                name="Topic",
                value=channel.topic,
                inline=False,
            )

        elif isinstance(channel, discord.VoiceChannel):
            embed.add_field(
                name="Bitrate",
                value=f"{int(channel.bitrate / 1000)} kbps",
                inline=False,
            )
            embed.add_field(
                name="User Limit",
                value=(channel.user_limit or "Unlimited"),
                inline=False,
            )

        elif isinstance(channel, discord.CategoryChannel) and channel.channels:
            embed.add_field(
                name=f"{len(channel.channels)} Children",
                value=", ".join([child.name for child in channel.channels]),
                inline=False,
            )

        embed.add_field(
            name="Creation Date",
            value=(
                format_dt(channel.created_at, style="f")
                + " **("
                + format_dt(channel.created_at, style="R")
                + ")**"
            ),
            inline=False,
        )

        return await ctx.send(embed=embed)

    @commands.command(
        name="color",
        help="View hex color",
        aliases=["hex"],
        usage="[hex code]",
    )
    async def color(self, ctx, hex_code: str):
        try:
            hex_code = hex_code.strip("#")
            color_int = int(hex_code, 16)
            color = discord.Color(color_int)
            embed = discord.Embed(
                title="Color", description=f"Hex Code: {hex_code}", color=color
            )
            embed.set_thumbnail(
                url=f"https://dummyimage.com/200x200/{hex_code}/{hex_code}.png"
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                description=f"<:deny:1121826907739144412> An error occurred: {e}",
                color=0x2B2D31,
            )
            await ctx.send(embed=embed)

    @commands.command(
        name="extract",
        help="show dominant color from image",
        aliases=["et"],
        usage="[attachment]",
    )
    async def extract(self, ctx, attachment: discord.Attachment):
        try:
            image_data = await attachment.read()
            image = Image.open(BytesIO(image_data))
            image = image.resize((200, 200))

            dominant_color = self.extract_dominant_color(image)
            color_image_url = self.upload_color_image(dominant_color)

            embed = discord.Embed(
                description="Here is the dominant color extracted from the image:",
                color=int(dominant_color[1:], 16),
            )
            embed.add_field(name="Hex Color", value=dominant_color, inline=True)
            embed.set_thumbnail(url=color_image_url)
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                description=f"<:deny:1121826907739144412> An error occurred: {e}",
                color=0x2B2D31,
            )
            await ctx.send(embed=embed)

    def extract_dominant_color(self, image):
        temp_file = "temp_image.png"
        image.save(temp_file)
        color_thief = ColorThief(temp_file)
        dominant_color = color_thief.get_color(quality=1)
        hex_color = "#{:02x}{:02x}{:02x}".format(
            dominant_color[0], dominant_color[1], dominant_color[2]
        )
        return hex_color

    def upload_color_image(self, hex_color):
        url = f"https://dummyimage.com/100x100/{hex_color[1:]}/{hex_color[1:]}.png"
        response = requests.get(url)
        if response.status_code == 200:
            return url
        return None

    @commands.command(
        name="btcaddy",
        usage="(address)",
        help="Show info about btc",
        aliases=["bitcoinaddy", "btcinfo", "btctransactions"],
        invoke_without_command=True,
    )
    async def btcaddy(self, ctx, address: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://blockchain.info/rawaddr/" + str(address)
            ) as response:
                data = await response.json()

        if data.get("error"):
            return await ctx.warn(f"Couldn't find an **address** for `{address}`")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://min-api.cryptocompare.com/data/price",
                params=dict(fsym="BTC", tsyms="USD"),
            ) as response:
                price = await response.json()
                price = price["USD"]

        embed = discord.Embed(
            url=f"https://mempool.space/address/{address}",
            title="Bitcoin Address",
        )
        embed.add_field(
            name="Balance",
            value=f"{(data['final_balance'] / 100000000 * price):,.2f} USD",
        )
        embed.add_field(
            name="Received",
            value=f"{(data['total_received'] / 100000000 * price):,.2f} USD",
        )
        embed.add_field(
            name="Sent", value=f"{(data['total_sent'] / 100000000 * price):,.2f} USD"
        )
        if data["txs"]:
            embed.add_field(
                name="Transactions",
                value="\n".join(
                    f"> [`{tx['hash'][:19]}..`](https://mempool.space/tx/{tx['hash']}) {(tx['result'] / 100000000 * price):,.2f} USD"
                    for tx in data["txs"][:5]
                ),
            )

        await ctx.send(embed=embed)

    @commands.command(
        name="google",
        usage="[query]",
        aliases=["g", "search", "ggl"],
        help="Search for results on the web",
    )
    async def google(self, ctx, *, query: str):
        async with ctx.typing():
            async with aiohttp.ClientSession() as session:
                params = {
                    "query": query.replace(" ", ""),
                    "safe": "true" if not ctx.channel.is_nsfw() else "false",
                }
                async with session.get(
                    "https://notsobot.com/api/search/google", params=params
                ) as response:
                    data = await response.json()

        if not data.get("total_result_count"):
            return await ctx.reply(f"Couldn't find any images for **{query}**")

        embed = discord.Embed(title=f"Google Search: {query}", description="")

        for card in data.get("cards", []):
            embed.description += f"**Rich Card Information:** `{card.get('title')}`\n"
            if card.get("description"):
                embed.description += f"{card.get('description')}\n"
            for field in card.get("fields"):
                embed.description += (
                    f"> **{field.get('name')}:** `{field.get('value')}`\n"
                )
            for section in card.get("sections"):
                embed.description += f"> **{section.get('title')}:** `{section['fields'][0].get('name')}`\n"
            if card.get("image"):
                embed.set_image(url=card.get("image"))

        for entry in (
            data.get("results")[:2]
            if data.get("cards", [])
            else data.get("results")[:3]
        ):
            embed.add_field(
                name=entry.get("title"),
                value=f"{entry.get('url')}\n{entry.get('description')}",
                inline=False,
            )
        await ctx.send(embed=embed)

    @commands.command(
        name="image",
        usage="(query)\nexample: clairo",
        aliases=["img", "im", "i"],
        help="Search the web for images",
    )
    async def image(self, ctx, *, query: str):
        async with aiohttp.ClientSession() as session:
            response = await session.get(
                "https://notsobot.com/api/search/google/images",
                params=dict(
                    query=query.replace(" ", ""),
                    safe="true" if not ctx.channel.is_nsfw() else "false",
                ),
            )
            data = await response.json()

        if not data:
            return await ctx.warn(f"Couldn't find any images for **{query}**")

        embeds = [
            discord.Embed(
                url=entry.get("url"),
                title=entry.get("header"),
                description=entry.get("description"),
            ).set_image(url=entry["image"]["url"])
            for entry in data
            if not entry.get("header") in ("TikTok", "Facebook")
        ]

        paginator = pg.Paginator(self.bot, embeds, ctx, invoker=ctx.author.id)
        paginator.add_button("prev", emoji="<:left:1107307769582850079>")
        paginator.add_button("goto", emoji="<:filter:1113850464832868433>")
        paginator.add_button("next", emoji="<:right:1107307767041105920>")
        paginator.add_button("delete", emoji="<:page_cancel:1121826948520362045>")
        await paginator.start()

    @commands.command(
        name="wikihow",
        usage="(query)\nexample: how to get a girlfriend",
        help="info",
        aliases=[
            "wiki",
            "whow",
            "how",
        ],
    )
    async def wikihow(self, ctx, *, query: str) -> Message:
        async with ctx.typing():
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://notsobot.com/api/search/wikihow",
                    params={"query": query},
                ) as response:
                    data = await response.json()
                    if not data:
                        return await ctx.send_warning(
                            f"No results were found for **{query}**"
                        )

                    item = data[0]

                    async with session.get(item["url"]) as soup_response:
                        soup_text = await soup_response.text()
                        soup = BeautifulSoup(
                            soup_text, "html.parser"
                        )  # Parse the soup object

        return await ctx.send(
            embed=Embed(
                url=item["url"],
                title=item["title"],
                description=(
                    f"{item['title']}\n"
                    + "\n".join(
                        [
                            f"{index + 1} - {step.text}"
                            for index, step in enumerate(
                                soup.findAll("b", class_="whb")[:15]
                            )
                        ]
                    )
                    + (
                        f"\n... Too much to show, more available information @ {item['url']}"
                        if len(soup.findAll("b", class_="whb")) > 15
                        else ""
                    )
                ),
            ).set_footer(
                text="Information from WikiHow",
                icon_url="https://lh3.googleusercontent.com/PRyVT9EUZs5elFJfMugM-cRUQM9rzegZiLdheMh-4Oc_ehFmG5lQN6vuFxOx_AN7r50",
            )
        )

    @commands.command(
        name="joinposition",
        aliases=["joinpos"],
        help="view your join position",
        usage=" [member]",
    )
    async def joinpos(self, ctx, member: discord.Member = None):
        joinedList = []
        if member == None:
            member = ctx.author
        for mem in ctx.message.guild.members:
            joinedList.append({"ID": mem.id, "Joined": mem.joined_at})
        joinedList = sorted(
            joinedList,
            key=lambda x: x["Joined"].timestamp() if x["Joined"] != None else -1,
        )

        check_item = {"ID": member.id, "Joined": member.joined_at}
        total = len(joinedList)
        position = joinedList.index(check_item) + 1
        before = ""
        after = ""
        msg = "*{}'s* join position is **{:,}**.".format((member), position, total)
        if position - 1 == 1:
            before = "**1** user"
        elif position - 1 > 1:
            before = "**{:,}** users".format(position - 1)
        if total - position == 1:
            after = "**1** user"
        elif total - position > 1:
            after = "**{:,}** users".format(total - position)
        if len(before) and len(after):
            msg += "\n\n{} joined before, and {} after.".format(before, after)
        elif len(before):
            msg += "\n\n{} joined before.".format(before)
        elif len(after):
            msg += "\n\n{} joined after.".format(after)
        await ctx.send(msg)

    @commands.command(
        help="Remove background from an image",
        usage="[attachment]",
        aliases=["removebg", "rbg", "removebackground", "transparentimg", "transimg"],
    )
    @commands.max_concurrency(1, commands.BucketType.default, wait=True)
    async def transparent(self, ctx, url: str = None):
        import requests, logging

        if not url:
            if not ctx.message.attachments:
                return
            url = ctx.message.attachments[0].url

        API_ENDPOINT = "https://api.remove.bg/v1.0/removebg"

        class RemoveBg(object):
            def __init__(self, api_key):
                self.__api_key = api_key

            def _output_file(self, response, new_file_name):
                if response.status_code == requests.codes.ok:
                    with open(new_file_name, "wb") as removed_bg_file:
                        removed_bg_file.write(response.content)
                else:
                    error_reason = response.json()["errors"][0]["title"].lower()
                    logging.error(
                        "Unable to save %s due to %s", new_file_name, error_reason
                    )

            def _check_arguments(self, size, type, type_level, format, channels):
                """Check if arguments are valid."""
                if size not in [
                    "auto",
                    "preview",
                    "small",
                    "regular",
                    "medium",
                    "hd",
                    "full",
                    "4k",
                ]:
                    raise ValueError("size argument wrong")

                if type not in [
                    "auto",
                    "person",
                    "product",
                    "animal",
                    "car",
                    "car_interior",
                    "car_part",
                    "transportation",
                    "graphics",
                    "other",
                ]:
                    raise ValueError("type argument wrong")

                if type_level not in ["none", "latest", "1", "2"]:
                    raise ValueError("type_level argument wrong")

                if format not in ["jpg", "zip", "png", "auto"]:
                    raise ValueError("format argument wrong")

                if channels not in ["rgba", "alpha"]:
                    raise ValueError("channels argument wrong")

            def remove_background_from_img_url(
                self,
                img_url,
                size="regular",
                type="auto",
                type_level="none",
                format="auto",
                roi="0 0 100% 100%",
                crop=None,
                scale="original",
                position="original",
                channels="rgba",
                shadow=False,
                semitransparency=True,
                bg=None,
                bg_type=None,
                new_file_name="transparent.png",
            ):
                self._check_arguments(size, type, type_level, format, channels)

                files = {}

                data = {
                    "image_url": img_url,
                    "size": size,
                    "type": type,
                    "type_level": type_level,
                    "format": format,
                    "roi": roi,
                    "crop": "true" if crop else "false",
                    "crop_margin": crop,
                    "scale": scale,
                    "position": position,
                    "channels": channels,
                    "add_shadow": "true" if shadow else "false",
                    "semitransparency": "true" if semitransparency else "false",
                }

                if bg_type == "path":
                    files["bg_image_file"] = open(bg, "rb")
                elif bg_type == "color":
                    data["bg_color"] = bg
                elif bg_type == "url":
                    data["bg_image_url"] = bg

                response = requests.post(
                    API_ENDPOINT, data=data, headers={"X-Api-Key": self.__api_key}
                )
                response.raise_for_status()

                self._output_file(response, new_file_name)

        x = RemoveBg(api_key=random.choice(self.bot.removebg_api))
        x.remove_background_from_img_url(url)
        await ctx.reply(file=discord.File("transparent.png"))
        os.remove("transparent.png")

    @commands.command(
        aliases=["about", "bi", "info"],
        help="check bot's statistics",
    )
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def botinfo(self, ctx: commands.Context):
        channels = []
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                channels.append(channel)

        embed = discord.Embed(
            color=0x2B2D31, description=f"**bot information**"
        ).set_thumbnail(url=self.bot.user.display_avatar)
        embed.add_field(
            name="about",
            value=f"> <:miroreply:1107719722394456065> created by [Claqz](https://discord.com/users/236931919063941121)",
            inline=False,
        )
        embed.add_field(
            name="stats",
            value=f"> <:miroreply:1107719722394456065> servers: ``{len(self.bot.guilds)}`` \n> <:miroreply:1107719722394456065> users: ``{len(self.bot.users):,}`` \n> <:miroreply:1107719722394456065> channels: ``{len(channels):,}`` \n> <:miroreply:1107719722394456065> commands: ``520``",
            inline=False,
        )
        embed.add_field(
            name="versions",
            value=f"> <:miroreply:1107719722394456065> py: ``3.10.2`` \n> <:miroreply:1107719722394456065> discord.py ``2.3.1``",
            inline=False,
        )
        embed.add_field(
            name="usage",
            value=f"> <:miroreply:1107719722394456065> ping: ``{round(self.bot.latency * 1000)}ms`` \n> <:miroreply:1107719722394456065> ram: ``{psutil.virtual_memory().percent}%`` \n> <:miroreply:1107719722394456065> cpu: ``{psutil.cpu_percent()}%``",
            inline=False,
        )
        embed.set_footer(text="clust/v4.0.0")
        mes = await ctx.send(embed=embed)

    async def sport_scores(self, sport: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"http://site.api.espn.com/apis/site/v2/sports/{sport}/scoreboard"
            ) as response:
                data = await response.json()

        if not data.get("events"):
            raise commands.CommandError(
                f"There aren't any **{sport.split('/')[0].title()}** events!"
            )

        embeds = []
        for event in data.get("events"):
            embed = discord.Embed(
                url=f"https://www.espn.com/{sport.split('/')[1]}/game?gameId={event['id']}",
                title=event.get("name"),
            )
            embed.set_author(
                name=event["competitions"][0]["competitors"][0]["team"]["displayName"],
                icon_url=event["competitions"][0]["competitors"][0]["team"]["logo"],
            )
            embed.set_thumbnail(
                url=event["competitions"][0]["competitors"][1]["team"]["logo"],
            )
            embed.add_field(
                name="Status",
                value=event["status"]["type"].get("detail"),
                inline=True,
            )
            embed.add_field(
                name="Teams",
                value=(
                    f"{event['competitions'][0]['competitors'][1]['team']['abbreviation']} -"
                    f" {event['competitions'][0]['competitors'][0]['team']['abbreviation']}"
                ),
                inline=True,
            )
            embed.add_field(
                name="Score",
                value=f"{event['competitions'][0]['competitors'][1]['score']} - {event['competitions'][0]['competitors'][0]['score']}",
                inline=True,
            )
            embed.timestamp
            embeds.append(embed)

        return embeds

    @commands.command(
        name="nba",
        description="Returns nba stats",
        aliases=["basketball"],
        usage="",
        help="info",
    )
    async def nba(self, ctx):
        """National Basketball Association Scores"""

        scores = await self.sport_scores("basketball/nba")
        await ctx.paginator(scores)

    @commands.command(
        name="nfl",
        description="Returns nfl stats",
        aliases=["football"],
        usage="",
        help="info",
    )
    async def nfl(self, ctx):
        """National Football League Scores"""

        scores = await self.sport_scores("football/nfl")
        await ctx.paginator(scores)

    @commands.command(
        name="mlb", description="Returns mlb stats", usage="", help="info"
    )
    async def mlb(self, ctx):
        """Major League Baseball Scores"""

        scores = await self.sport_scores("baseball/mlb")
        await ctx.paginator(scores)

    @commands.command(
        name="nhl",
        description="Returns nhl stats",
        aliases=["hockey"],
        usage="",
        help="info",
    )
    async def nhl(self, ctx):
        scores = await self.sport_scores("hockey/nhl")
        await ctx.paginator(scores)

    @commands.command(
        name="ocr",
        aliases=["opticalcharacterrecognition"],
        usage="[attachment]",
        help="Return text off image",
    )
    @commands.cooldown(1, 8, commands.BucketType.guild)
    async def ocr(self, ctx, image: discord.Attachment):
        await ctx.typing()
        if isinstance(image, discord.Attachment):
            payload = {
                "url": image.url,
                "isOverlayRequired": False,
                "apikey": "K88991768788957",
                "language": "eng",
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.ocr.space/parse/image", data=payload
                ) as response:
                    x = await response.read()
                    await ctx.reply(
                        embed=discord.Embed(
                            color=0x2B2D31,
                            description=json.loads(x.decode())["ParsedResults"][0][
                                "ParsedText"
                            ],
                        )
                    )

        elif isinstance(image, str):
            payload = {
                "url": __import__("yarl").URL(image),
                "isOverlayRequired": False,
                "apikey": "K88991768788957",
                "language": "eng",
            }
            x = await self.bot.session.post(
                "https://api.ocr.space/parse/image", data=payload
            )

            x = await x.read()
            await ctx.reply(
                embed=discord.Embed(
                    color=0x2B2D31,
                    description=json.loads(x.decode())["ParsedResults"][0][
                        "ParsedText"
                    ],
                )
            )

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.rival.rocks/media/ocr",
                    headers={"api-key": self.bot.rival_api},
                    params={"url": image},
                ) as resp:
                    return await ctx.reply(
                        embed=discord.Embed(
                            color=0x2B2D31, description=eval(await resp.text())
                        )
                    )

    @commands.command(
        name="youtube",
        aliases=["yt", "tube", "you"],
        usage="[user]",
        help="Show info about youtube profile",
    )
    @commands.cooldown(1, 4, commands.BucketType.guild)
    async def youtube(self, ctx, *, username):
        search_request = self.youtube.search().list(
            part="id", q=username, type="channel"
        )
        search_response = search_request.execute()
        if not search_response["items"]:
            embed = discord.Embed(
                title="<:deny:1121826907739144412> Error",
                description=f"> *`Could not find a youtube channel with the uername {username}`*",
                color=0x2B2D31,
            )
            await ctx.send(embed=embed)
            return
        channel_id = search_response["items"][0]["id"]["channelId"]
        channel_request = self.youtube.channels().list(
            part="snippet,contentDetails,statistics", id=channel_id
        )
        channel_response = channel_request.execute()
        channel = channel_response["items"][0]
        title = channel["snippet"]["title"]
        description = channel["snippet"]["description"]
        subs = int(channel["statistics"]["subscriberCount"])
        videos = int(channel["statistics"]["videoCount"])
        views = int(channel["statistics"]["viewCount"])
        thumbnail_url = channel["snippet"]["thumbnails"]["high"]["url"]
        country = channel["snippet"].get("country", "Unknown")
        created_at = channel["snippet"]["publishedAt"]
        embed = discord.Embed(
            title=f"<:youtube:1136340636694478949> {title}", color=0x2B2D31
        )
        user = ctx.author
        embed.set_author(name=str(user.name), icon_url=user.display_avatar.url)
        embed.add_field(name="Description", value=f">>> *{description}*")
        embed.add_field(name="Subscribers", value=f"> `{subs:,}`", inline=False)
        embed.add_field(name="Videos", value=f">>> `{videos:,}`", inline=False)
        embed.add_field(name="Views", value=f">>> `{views:,}`", inline=False)
        embed.add_field(name="Country", value=f">>> `{country}`", inline=False)
        embed.add_field(
            name="Channel Created At", value=f">>> `{created_at}`", inline=False
        )
        embed.set_thumbnail(url=thumbnail_url)

        button = YoutubeButton(
            channel_id, custom_emoji="<:youtube:1136340636694478949>"
        )
        view = discord.ui.View()
        view.add_item(button)

        await ctx.send(embed=embed, view=view)

    @commands.command(
        name="tiktok",
        aliases=["tic", "tik", "tok", "toc"],
        usage=" [user]\nExample: ;tiktok claqzfangirl",
        help="Show info about tiktok profile",
    )
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def fetch_tiktok_profile(self, ctx, username):
        url = f"https://www.tiktok.com/@{username}?lang=en"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            embed = discord.Embed(
                title="<:deny:1121826907739144412> Error",
                description=f">>> ***{e}***",
                color=0x2B2D31,
            )
            await ctx.send(embed=embed)
            return

        html = response.text
        try:
            nickname = html.split('nickname":"')[1].split('"')[0]
            followers = html.split('followerCount":')[1].split(",")[0]
            following = html.split('followingCount":')[1].split(",")[0]
            likes = html.split('heartCount":')[1].split(",")[0]
            videos = html.split('videoCount":')[1].split(",")[0]
            bio = html.split('desc":"')[1].split('"')[0]
            profile_pic_url = html.split('og:image" content="')[1].split('"')[0]
        except IndexError as e:
            embed = discord.Embed(
                title="<:deny:1121826907739144412> Error",
                description=f">>> ***{e}***",
                color=0x2B2D31,
            )
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title=f"<:tiktok:1114291908659908719> {nickname}'s TikTok Stats",
            color=0x2B2D31,
        )

        embed.set_thumbnail(url=profile_pic_url)

        embed.add_field(
            name="<:user:1113553595422494792> Username",
            value=f"> *@{username}*",
            inline=False,
        )
        embed.add_field(
            name="<:Recording:1115337793808380015> Posts",
            value=f"> `{videos}`",
            inline=False,
        )
        embed.add_field(
            name="<:likes:1114659127025729562> Likes",
            value=f"> `{likes}`",
            inline=False,
        )
        embed.add_field(
            name="<:___follow:1115322721459523746> Followers",
            value=f"> `{followers}`",
            inline=False,
        )
        embed.add_field(
            name="<:___follow:1115322721459523746> Following",
            value=f"> `{following}`",
            inline=False,
        )
        embed.add_field(
            name="<:description:1115337795880353834> Bio",
            value=f"> *{bio}*",
            inline=False,
        )

        button = TikTokLinkBUtton(
            username, custom_emoji="<:tiktok:1114291908659908719>"
        )
        view = discord.ui.View()
        view.add_item(button)

        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(
        help="see someone's banner",
        usage="(user)",
        aliases=["userbanner", "ubanner"],
    )
    async def banner(
        self, ctx: commands.Context, *, member: discord.User = commands.Author
    ):
        user = await self.bot.fetch_user(member.id)
        if not user.banner:
            return await ctx.send_warning(f"**{user}** Doesn't have a banner")
        embed = discord.Embed(
            color=self.bot.color, title=f"{user.name}'s banner", url=user.banner.url
        )
        embed.set_image(url=user.banner.url)
        return await ctx.reply(embed=embed)

    @commands.command(
        name="youngest",
        help="Show the youngest member in the guild by account creation date.",
        aliases=["young", "newaccount"],
    )
    async def youngest(self, ctx):
        youngest_member = None
        for member in ctx.guild.members:
            if (
                youngest_member is None
                or member.created_at > youngest_member.created_at
            ):
                youngest_member = member

        if youngest_member:
            embed = discord.Embed(title="Youngest User", color=self.bot.color)
            embed.add_field(name="Username", value=youngest_member.name, inline=False)
            embed.add_field(
                name="Account Creation",
                value=youngest_member.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                inline=False,
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("No members found in the server.")

    @commands.command(
        name="boomer",
        help="Show the oldest member in the guild by account creation date.",
        aliases=["boomers", "oldest"],
    )
    async def boomer(self, ctx):
        oldest_member = min(ctx.guild.members, key=lambda m: m.created_at)

        embed = discord.Embed(title="Oldest Member", color=self.bot.color)

        embed.add_field(name="Username", value=oldest_member.name, inline=False)
        embed.add_field(
            name="Account Creation Date",
            value=oldest_member.created_at.strftime("%Y-%m-%d"),
            inline=False,
        )

        await ctx.send(embed=embed)

    @commands.command(
        name="setbanner",
        usage="(attachment)",
        aliases=["setb"],
    )
    @commands.has_permissions(administrator=True)
    async def setbanner(self, ctx, image_url):
        embed = discord.Embed(
            title="Server Banner Set",
            description=f"Server banner has been updated.",
            color=self.bot.color,
        )
        embed.set_image(url=image_url)
        await ctx.send(embed=embed)

    @commands.command(
        name="seticon",
        usage="(attachment)",
        aliases=["seti"],
    )
    @commands.has_permissions(administrator=True)
    async def seticon(self, ctx, image_url):
        embed = discord.Embed(
            title="Server Icon Set",
            description=f"Server icon has been updated.",
            color=self.bot.color,
        )
        embed.set_image(url=image_url)
        await ctx.send(embed=embed)

    @commands.command(
        name="setchannel",
        usage="(channel)",
        aliases=["setchan"],
    )
    @commands.has_permissions(administrator=True)
    async def setchannel(self, ctx, channel: discord.TextChannel, *, new_name_or_topic):
        old_name = channel.name
        old_topic = channel.topic

        await channel.edit(name=new_name_or_topic, topic=new_name_or_topic)

        embed = discord.Embed(
            title="Channel Updated",
            description=f"Channel {old_name} has been updated.\nNew name/topic: {new_name_or_topic}",
            color=self.bot.color,
        )
        await ctx.send(embed=embed)

    @commands.command(
        usage="(name)\nExample: ;instagram iceee",
        aliases=["instagram", "ig"],
        help="Shows information on given instagram name",
    )
    async def instaprofile(self, ctx, username):
        api_key = (
            "claqz_Qt5c73ExW5pEtjjCknvL4djlPUK6RA1D4Ll4vx8SJcp1HPfFchYiWCarMHtuNCbm"
        )

        headers = {"Authorization": api_key}

        async with aiohttp.ClientSession() as session:
            response = await session.get(
                f"https://dev.lains.life/instagram/profile?username={username}",
                headers=headers,
            )
            data = await response.json()

        if response.status != 200:
            return await ctx.send("An error occurred while fetching the profile.")

        profile = data

        embed = discord.Embed(
            title=f"Instagram Profile - {profile['username']}", color=self.bot.color
        )
        embed.set_thumbnail(url=profile["avatar_url"])
        embed.add_field(name="Full Name", value=profile["display_name"], inline=False)
        embed.add_field(
            name="Followers", value=profile["statistics"]["followers"], inline=True
        )
        embed.add_field(
            name="Following", value=profile["statistics"]["following"], inline=True
        )
        embed.add_field(name="Posts", value=profile["statistics"]["posts"], inline=True)
        embed.add_field(name="Bio", value=profile["description"], inline=False)
        embed.set_footer(text="Api by lain")

        await ctx.send(embed=embed)

    @commands.command(
        usage="(name)\nExample: ;cashapp bwruise",
        aliases=["cashtag"],
        help="Shows information on a cashapp account",
    )
    async def cashapp(self, ctx, cashtag):
        api_key = (
            "claqz_Qt5c73ExW5pEtjjCknvL4djlPUK6RA1D4Ll4vx8SJcp1HPfFchYiWCarMHtuNCbm"
        )

        headers = {"Authorization": api_key}

        async with aiohttp.ClientSession() as session:
            response = await session.get(
                f"https://dev.lains.life/cashapp/profile?username={cashtag}",
                headers=headers,
            )
            data = await response.json()

        if response.status != 200:
            return await ctx.send("An error occurred while fetching the profile.")

        embed = discord.Embed(
            title=f"CashApp Profile - {data['display_name']}", color=self.bot.color
        )
        embed.set_thumbnail(url=data["avatar_url"]["image_url"])
        embed.add_field(name="Cashtag", value=data["cashtag"], inline=False)
        embed.add_field(name="Country Code", value=data["country_code"], inline=True)
        embed.add_field(name="QR Code", value=data["qr"], inline=False)
        embed.add_field(name="URL", value=data["url"], inline=False)
        embed.set_footer(text="Api by lain")

        await ctx.send(embed=embed)

    @commands.command(
        usage="(name)\nExample: ;snapchat ice",
        aliases=["snap"],
        help="Shows information on a snapchat account",
    )
    async def snapchat(self, ctx, username):
        api_key = (
            "claqz_Qt5c73ExW5pEtjjCknvL4djlPUK6RA1D4Ll4vx8SJcp1HPfFchYiWCarMHtuNCbm"
        )

        headers = {"Authorization": api_key}

        async with aiohttp.ClientSession() as session:
            response = await session.get(
                f"https://dev.lains.life/snapchat/profile?username={username}",
                headers=headers,
            )
            data = await response.json()
        embed = discord.Embed(
            title=f"Snapchat Profile - {data['display_name']}", color=self.bot.color
        )
        embed.set_thumbnail(url=data["snapcode"])
        embed.add_field(name="Username", value=data["username"], inline=False)
        embed.add_field(name="Subscribers", value=data["subscribers"], inline=True)
        embed.add_field(name="URL", value=data["url"], inline=False)
        embed.set_footer(text="Api by lain")

        await ctx.send(embed=embed)

    @commands.command(
        usage="(name)\nExample: ;roblox santaclaqz",
        aliases=["rblx"],
        help="Shows information on a roblox account",
    )
    async def roblox(self, ctx, username):
        api_key = (
            "claqz_Qt5c73ExW5pEtjjCknvL4djlPUK6RA1D4Ll4vx8SJcp1HPfFchYiWCarMHtuNCbm"
        )

        headers = {"Authorization": api_key}

        async with aiohttp.ClientSession() as session:
            response = await session.get(
                f"https://dev.lains.life/roblox/profile?username={username}",
                headers=headers,
            )
            data = await response.json()

        if response.status != 200:
            return await ctx.send("An error occurred while fetching the profile.")

        embed = discord.Embed(
            title=f"Roblox Profile - {data['display_name']}", color=self.bot.color
        )
        embed.set_thumbnail(url=data["avatar_url"])
        embed.add_field(name="Username", value=data["username"], inline=False)
        embed.add_field(name="Description", value=data["description"], inline=False)
        embed.add_field(name="Created At", value=data["created_at"], inline=True)
        embed.add_field(name="URL", value=data["url"], inline=False)
        embed.add_field(name="Badges", value=", ".join(data["badges"]), inline=False)
        embed.add_field(
            name="Followers", value=data["statistics"]["followers"], inline=True
        )
        embed.add_field(
            name="Following", value=data["statistics"]["following"], inline=True
        )
        embed.add_field(
            name="Friends", value=data["statistics"]["friends"], inline=True
        )
        embed.set_footer(text="Api by lain")

        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if "clust" in message.content.lower():
            tiktok_links = self.get_tiktok_links(message.content)
            for link in tiktok_links:
                await self.send_tiktok_embed(message.channel, link)

    def get_tiktok_links(self, content):
        return [
            link.strip()
            for link in content.split()
            if link.startswith("https://www.tiktok.com")
        ]

    async def send_tiktok_embed(self, channel, tiktok_link):
        api_key = (
            "claqz_Qt5c73ExW5pEtjjCknvL4djlPUK6RA1D4Ll4vx8SJcp1HPfFchYiWCarMHtuNCbm"
        )

        headers = {"Authorization": api_key}

        async with aiohttp.ClientSession() as session:
            response = await session.get(
                f"https://dev.lains.life/tiktok/post?url={tiktok_link}", headers=headers
            )
            data = await response.json()

        if response.status != 200:
            return await channel.send(
                "An error occurred while fetching the TikTok post."
            )

        embed = discord.Embed(
            title="TikTok Post", description=data["caption"], color=self.bot.color
        )
        embed.set_image(url=data["assets"]["cover"])
        embed.add_field(name="Likes", value=data["statistics"]["likes"], inline=True)
        embed.add_field(
            name="Comments", value=data["statistics"]["comments"], inline=True
        )
        embed.add_field(name="Plays", value=data["statistics"]["plays"], inline=True)
        embed.add_field(name="Shares", value=data["statistics"]["shares"], inline=True)
        embed.add_field(name="User", value=data["user"]["nickname"], inline=True)
        embed.set_footer(text="Api by lain")

        await channel.send(embed=embed)

    @commands.command(usage="(attachment or URL)", help="Identify a song using Shazam")
    async def shazam(self, ctx, url_or_attachment):
        api_key = (
            "claqz_Qt5c73ExW5pEtjjCknvL4djlPUK6RA1D4Ll4vx8SJcp1HPfFchYiWCarMHtuNCbm"
        )

        headers = {"Authorization": api_key}
        if url_or_attachment.startswith("http"):
            url = url_or_attachment
        else:
            url = ctx.message.attachments[0].url

        async with aiohttp.ClientSession() as session:
            response = await session.get(
                f"https://dev.lains.life/shazam/song?url={url}", headers=headers
            )
            data = await response.json()

        if response.status != 200:
            return await ctx.send("An error occurred while identifying the song.")

        embed = discord.Embed(title=f"Shazam Result", color=self.bot.color)
        embed.add_field(name="Artist", value=data["artist"], inline=False)
        embed.add_field(name="Title", value=data["title"], inline=False)
        embed.add_field(name="URL", value=data["url"], inline=False)
        embed.set_footer(text="Api by lain")

        await ctx.send(embed=embed)

    @commands.command(usage="(medal link)", help="Share a Medal/Clip video link")
    async def medal(self, ctx, medal_link):
        api_key = (
            "claqz_Qt5c73ExW5pEtjjCknvL4djlPUK6RA1D4Ll4vx8SJcp1HPfFchYiWCarMHtuNCbm"
        )

        headers = {"Authorization": api_key}

        async with aiohttp.ClientSession() as session:
            response = await session.get(
                f"https://dev.lains.life/medal/clip?url={medal_link}", headers=headers
            )
            data = await response.json()

        if response.status != 200:
            return await ctx.send(
                "An error occurred while fetching the Medal clip information."
            )

        embed = discord.Embed(title=data["title"], color=self.bot.color)
        embed.set_thumbnail(url=data["author"]["avatar"])
        embed.add_field(
            name="Author",
            value=f"[{data['author']['display_name']}]({data['author']['url']})",
            inline=False,
        )
        embed.add_field(name="Views", value=data["statistics"]["views"], inline=True)
        embed.add_field(name="Likes", value=data["statistics"]["likes"], inline=True)
        embed.add_field(
            name="Comments", value=data["statistics"]["comments"], inline=True
        )
        embed.add_field(
            name="Description",
            value=data["description"] or "No description provided.",
            inline=False,
        )
        embed.add_field(
            name="Video URL", value=data["asset"]["video_url"], inline=False
        )
        embed.set_footer(text="Api by lain")

        await ctx.send(embed=embed)

    @commands.command(
        usage="", help="Show all default avs in guild", aliases=["defaultavs"]
    )
    async def defaultavatars(self, ctx):
        default_avatar_count = sum(
            1 for member in ctx.guild.members if member.avatar is None
        )
        embed = discord.Embed(
            description=f"{default_avatar_count} users in this server with default Discord avatars.",
            color=self.bot.color,
        )
        await ctx.send(embed=embed)

    @commands.command(
        name="help",
        usage="<command or module>",
        example="userinfo",
        aliases=["h"],
    )
    async def _help(self, ctx, *, command: str = None):
        embeds = []
        if not command:
            embed = discord.Embed(
                description=f"```yml\n[ {len(set(self.bot.walk_commands()))} commands ]\n```\n",
                color=0x2B2D31,
            )
            for category in sorted(self.bot.cogs, key=lambda c: len(c)):
                if category.lower() in (
                    "jishaku",
                    "developer",
                    "commandevents",
                    "reactions",
                    "messages",
                    "economy",
                    "cog",
                    "users",
                    "tasks",
                    "confirm",
                ):
                    continue
                embed.description += f"> [`{category}`](https://discord.gg/clust)\n"
            embed.set_thumbnail(url=self.bot.user.display_avatar)
            embeds.append(embed)
            for name, category in sorted(
                self.bot.cogs.items(), key=lambda c: len(c[0])
            ):
                if name.lower() in (
                    "jishaku",
                    "developer",
                    "commandevents",
                    "reactions",
                    "messages",
                    "economy",
                    "cog",
                    "users",
                    "tasks",
                    "confirm",
                ):
                    continue
                category_embed = discord.Embed(
                    description=f"```yml\n[ {category.qualified_name} ]\n[ {len(set(category.walk_commands()))} commands ]\n```\n",
                    color=0x2B2D31,
                )
                for cmd in category.walk_commands():
                    if cmd.hidden:
                        continue
                    category_embed.description += (
                        f"> [`{cmd.qualified_name}`](https://discord.gg/clust)\n"
                    )
                category_embed.set_thumbnail(url=self.bot.user.display_avatar)
                embeds.append(category_embed)
            return await ctx.paginator(embeds)

        _command = command
        command = self.bot.get_command(command)
        if not command:
            return await ctx.send(f"Command `{_command}` doesn't exist")

        embed = discord.Embed(
            description=command.help or "No description provided",
            color=0x2B2D31,
        )
        usage = f"{ctx.prefix}{command.qualified_name} {command.usage or ''}"
        example = (
            f"{ctx.prefix}{command.qualified_name} {command.example}"
            if hasattr(command, "example") and command.example
            else ""
        )
        syntax = (
            f"```yml\nSyntax: {usage}\nExample: {example}```"
            if example
            else f"```yml\nSyntax: {usage}```"
        )
        embed.description += syntax

        embed.set_author(
            name=command.cog_name or "No category",
            icon_url=self.bot.user.display_avatar,
            url=f"https://discord.gg/clust",
        )

        aliases = ", ".join([f"`{alias}`" for alias in command.aliases]) or "`N/A`"
        embed.add_field(
            name="Aliases",
            value=aliases,
            inline=(False if len(command.aliases) >= 4 else True),
        )

        params = ", ".join([f"`{param}`" for param in command.clean_params]) or "`N/A`"
        embed.add_field(
            name="Parameters",
            value=params,
            inline=True,
        )

        if isinstance(command, commands.Group):
            subcommands = "\n".join(
                [
                    f"> `{cmd.qualified_name}` - {cmd.help or 'No description provided'}"
                    for cmd in sorted(
                        command.walk_commands(), key=lambda c: c.qualified_name.lower()
                    )
                    if not cmd.hidden
                ]
            )
            embed.add_field(
                name="Subcommands",
                value=subcommands,
                inline=False,
            )

        await ctx.send(embed=embed)


async def setup(bot) -> None:
    await bot.add_cog(Info(bot))
