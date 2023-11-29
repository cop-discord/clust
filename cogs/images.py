import discord, asyncio, os, requests, aiohttp
from discord.ext import commands
from io import BytesIO

session = requests.Session()


class Images(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot

    @commands.command(name="goose", help="return random goose image")
    async def goose(self, ctx):
        url = "https://nekos.life/api/v2/img/goose"
        resp = session.get(url)
        js = resp.json()
        embed = discord.Embed(color=0x2B2D31)
        embed.set_image(url=js["url"])
        await ctx.reply(embed=embed)

    @commands.command(name="lizard", help="return random lizard image")
    async def lizard(self, ctx):
        url = "https://nekos.life/api/v2/img/lizard"
        resp = session.get(url)
        js = resp.json()
        embed = discord.Embed(color=0x2B2D31)
        embed.set_image(url=js["url"])
        await ctx.reply(embed=embed)

    @commands.command(name="fox", help="return random fox image", aliases=["foxie"])
    async def fox(self, ctx):
        url = "https://randomfox.ca/floof/"
        response = requests.get(url)
        fox = response.json()
        embed = discord.Embed(color=0x2B2D31)
        embed.set_image(url=fox["image"])
        await ctx.send(embed=embed)

    @commands.command(help="send a random bird image")
    async def bird(self, ctx):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.alexflipnote.dev/birb") as response:
                data = await response.json()
                bird_url = data["file"]
                async with session.get(bird_url) as image_response:
                    bird_image_data = await image_response.read()
        await ctx.reply(
            file=discord.File(fp=BytesIO(bird_image_data), filename="bird.png")
        )

    @commands.command(help="send a random cat image")
    async def cat(self, ctx):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.thecatapi.com/v1/images/search"
            ) as response:
                data = await response.json()
                cat_url = data[0]["url"]
                async with session.get(cat_url) as image_response:
                    cat_image_data = await image_response.read()
        await ctx.reply(
            file=discord.File(fp=BytesIO(cat_image_data), filename="cat.png")
        )

    @commands.command(help="send a random capybara image")
    async def capybara(self, ctx):
        async with self.bot.session.get(
            "https://api.capy.lol/v1/capybara?json=true"
        ) as response:
            data = await response.json()
            url = data["data"]["url"]
            async with self.bot.session.get(url) as image_response:
                image_data = await image_response.read()
        await ctx.reply(
            file=discord.File(fp=BytesIO(image_data), filename="capybara.png")
        )

    @commands.command(
        name="keef", help="return random chief keef image", aliases=["chiefkeef"]
    )
    async def keef(self, ctx):
        api_key = (
            "claqz_Qt5c73ExW5pEtjjCknvL4djlPUK6RA1D4Ll4vx8SJcp1HPfFchYiWCarMHtuNCbm"
        )
        headers = {"Authorization": api_key}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://dev.lains.life/images/keef", headers=headers
            ) as response:
                if response.status == 200:
                    image_data = await response.read()
                    file = discord.File(fp=BytesIO(image_data), filename="keef.png")
                    embed = discord.Embed(color=self.bot.color)
                    embed.set_image(url="attachment://keef.png")
                    await ctx.send(embed=embed, file=file)
                    await self.bot.wait_for(
                        "message_delete",
                        check=lambda m: m.author == ctx.author
                        and m.attachments
                        and m.attachments[0].filename == "keef.png",
                    )
                    await asyncio.sleep(1)
                    os.remove("keef.png")
                else:
                    await ctx.send("Failed to fetch the image.")

    @commands.command(name="obama", help="return random obama image")
    async def obama(self, ctx):
        api_key = (
            "claqz_Qt5c73ExW5pEtjjCknvL4djlPUK6RA1D4Ll4vx8SJcp1HPfFchYiWCarMHtuNCbm"
        )
        headers = {"Authorization": api_key}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://dev.lains.life/images/obama", headers=headers
            ) as response:
                if response.status == 200:
                    image_data = await response.read()
                    file = discord.File(fp=BytesIO(image_data), filename="obama.png")
                    embed = discord.Embed(color=self.bot.color)
                    embed.set_image(url="attachment://obama.png")
                    await ctx.send(embed=embed, file=file)
                    await self.bot.wait_for(
                        "message_delete",
                        check=lambda m: m.author == ctx.author
                        and m.attachments
                        and m.attachments[0].filename == "obama.png",
                    )
                    await asyncio.sleep(1)
                    os.remove("obama.png")
                else:
                    await ctx.send("Failed to fetch the image.")

    @commands.command(name="trump", help="return random trump image")
    async def trump(self, ctx):
        api_key = (
            "claqz_Qt5c73ExW5pEtjjCknvL4djlPUK6RA1D4Ll4vx8SJcp1HPfFchYiWCarMHtuNCbm"
        )
        headers = {"Authorization": api_key}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://dev.lains.life/images/trump", headers=headers
            ) as response:
                if response.status == 200:
                    image_data = await response.read()
                    file = discord.File(fp=BytesIO(image_data), filename="trump.png")
                    embed = discord.Embed(color=self.bot.color)
                    embed.set_image(url="attachment://trump.png")
                    await ctx.send(embed=embed, file=file)
                    await self.bot.wait_for(
                        "message_delete",
                        check=lambda m: m.author == ctx.author
                        and m.attachments
                        and m.attachments[0].filename == "trump.png",
                    )
                    await asyncio.sleep(1)
                    os.remove("trump.png")
                else:
                    await ctx.send("Failed to fetch the image.")

    @commands.command(name="yeat", help="return random yeat image")
    async def yeat(self, ctx):
        api_key = (
            "claqz_Qt5c73ExW5pEtjjCknvL4djlPUK6RA1D4Ll4vx8SJcp1HPfFchYiWCarMHtuNCbm"
        )
        headers = {"Authorization": api_key}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://dev.lains.life/images/yeat", headers=headers
            ) as response:
                if response.status == 200:
                    image_data = await response.read()
                    file = discord.File(fp=BytesIO(image_data), filename="yeat.png")
                    embed = discord.Embed(color=self.bot.color)
                    embed.set_image(url="attachment://yeat.png")
                    await ctx.send(embed=embed, file=file)
                    await self.bot.wait_for(
                        "message_delete",
                        check=lambda m: m.author == ctx.author
                        and m.attachments
                        and m.attachments[0].filename == "yeat.png",
                    )
                    await asyncio.sleep(1)
                    os.remove("yeat.png")
                else:
                    await ctx.send("Failed to fetch the image.")

    @commands.command(
        name="carti", help="return random carti image", aliases=["playboicarti"]
    )
    async def carti(self, ctx):
        api_key = (
            "claqz_Qt5c73ExW5pEtjjCknvL4djlPUK6RA1D4Ll4vx8SJcp1HPfFchYiWCarMHtuNCbm"
        )
        headers = {"Authorization": api_key}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://dev.lains.life/images/carti", headers=headers
            ) as response:
                if response.status == 200:
                    image_data = await response.read()
                    file = discord.File(fp=BytesIO(image_data), filename="carti.png")
                    embed = discord.Embed(color=self.bot.color)
                    embed.set_image(url="attachment://carti.png")
                    await ctx.send(embed=embed, file=file)
                    await self.bot.wait_for(
                        "message_delete",
                        check=lambda m: m.author == ctx.author
                        and m.attachments
                        and m.attachments[0].filename == "carti.png",
                    )
                    await asyncio.sleep(1)
                    os.remove("carti.png")
                else:
                    await ctx.send("Failed to fetch the image.")

    @commands.command(
        name="peep", help="return random lil peep image", aliases=["lilpeep"]
    )
    async def peep(self, ctx):
        api_key = (
            "claqz_Qt5c73ExW5pEtjjCknvL4djlPUK6RA1D4Ll4vx8SJcp1HPfFchYiWCarMHtuNCbm"
        )
        headers = {"Authorization": api_key}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://dev.lains.life/images/peep", headers=headers
            ) as response:
                if response.status == 200:
                    image_data = await response.read()
                    file = discord.File(fp=BytesIO(image_data), filename="peep.png")
                    embed = discord.Embed(color=self.bot.color)
                    embed.set_image(url="attachment://peep.png")
                    await ctx.send(embed=embed, file=file)
                    await self.bot.wait_for(
                        "message_delete",
                        check=lambda m: m.author == ctx.author
                        and m.attachments
                        and m.attachments[0].filename == "peep.png",
                    )
                    await asyncio.sleep(1)
                    os.remove("peep.png")
                else:
                    await ctx.send("Failed to fetch the image.")

    @commands.command(
        name="yb", help="return random youngboy image", aliases=["youngboy", "nbayb"]
    )
    async def yb(self, ctx):
        api_key = (
            "claqz_Qt5c73ExW5pEtjjCknvL4djlPUK6RA1D4Ll4vx8SJcp1HPfFchYiWCarMHtuNCbm"
        )
        headers = {"Authorization": api_key}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://dev.lains.life/images/yb", headers=headers
            ) as response:
                if response.status == 200:
                    image_data = await response.read()
                    file = discord.File(fp=BytesIO(image_data), filename="yb.png")
                    embed = discord.Embed(color=self.bot.color)
                    embed.set_image(url="attachment://yb.png")
                    await ctx.send(embed=embed, file=file)
                    await self.bot.wait_for(
                        "message_delete",
                        check=lambda m: m.author == ctx.author
                        and m.attachments
                        and m.attachments[0].filename == "yb.png",
                    )
                    await asyncio.sleep(1)
                    os.remove("yb.png")
                else:
                    await ctx.send("Failed to fetch the image.")

    @commands.command(
        name="choppa", help="return random youngboy image", aliases=["nlechoppa", "nle"]
    )
    async def choppa(self, ctx):
        api_key = (
            "claqz_Qt5c73ExW5pEtjjCknvL4djlPUK6RA1D4Ll4vx8SJcp1HPfFchYiWCarMHtuNCbm"
        )
        headers = {"Authorization": api_key}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://dev.lains.life/images/choppa", headers=headers
            ) as response:
                if response.status == 200:
                    image_data = await response.read()
                    file = discord.File(fp=BytesIO(image_data), filename="choppa.png")
                    embed = discord.Embed(color=self.bot.color)
                    embed.set_image(url="attachment://choppa.png")
                    await ctx.send(embed=embed, file=file)
                    await self.bot.wait_for(
                        "message_delete",
                        check=lambda m: m.author == ctx.author
                        and m.attachments
                        and m.attachments[0].filename == "choppa.png",
                    )
                    await asyncio.sleep(1)
                    os.remove("choppa.png")
                else:
                    await ctx.send("Failed to fetch the image.")

    @commands.command(
        name="kai", help="return random kai cenat image", aliases=["kaicenat"]
    )
    async def kai(self, ctx):
        api_key = (
            "claqz_Qt5c73ExW5pEtjjCknvL4djlPUK6RA1D4Ll4vx8SJcp1HPfFchYiWCarMHtuNCbm"
        )
        headers = {"Authorization": api_key}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://dev.lains.life/images/kai", headers=headers
            ) as response:
                if response.status == 200:
                    image_data = await response.read()
                    file = discord.File(fp=BytesIO(image_data), filename="kai.png")
                    embed = discord.Embed(color=self.bot.color)
                    embed.set_image(url="attachment://kai.png")
                    await ctx.send(embed=embed, file=file)
                    await self.bot.wait_for(
                        "message_delete",
                        check=lambda m: m.author == ctx.author
                        and m.attachments
                        and m.attachments[0].filename == "kai.png",
                    )
                    await asyncio.sleep(1)
                    os.remove("kai.png")
                else:
                    await ctx.send("Failed to fetch the image.")

    @commands.command(
        name="destroylonely", help="return random kai cenat image", aliases=["lonely"]
    )
    async def destroylonely(self, ctx):
        api_key = (
            "claqz_Qt5c73ExW5pEtjjCknvL4djlPUK6RA1D4Ll4vx8SJcp1HPfFchYiWCarMHtuNCbm"
        )
        headers = {"Authorization": api_key}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://dev.lains.life/images/destroylonely", headers=headers
            ) as response:
                if response.status == 200:
                    image_data = await response.read()
                    file = discord.File(
                        fp=BytesIO(image_data), filename="destroylonely.png"
                    )
                    embed = discord.Embed(color=self.bot.color)
                    embed.set_image(url="attachment://destroylonely.png")
                    await ctx.send(embed=embed, file=file)
                    await self.bot.wait_for(
                        "message_delete",
                        check=lambda m: m.author == ctx.author
                        and m.attachments
                        and m.attachments[0].filename == "destroylonely.png",
                    )
                    await asyncio.sleep(1)
                    os.remove("destroylonely.png")
                else:
                    await ctx.send("Failed to fetch the image.")

    @commands.command(
        name="juice", help="return random juicewrld image", aliases=["juicewrld", "999"]
    )
    async def juice(self, ctx):
        api_key = (
            "claqz_Qt5c73ExW5pEtjjCknvL4djlPUK6RA1D4Ll4vx8SJcp1HPfFchYiWCarMHtuNCbm"
        )
        headers = {"Authorization": api_key}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://dev.lains.life/images/juice", headers=headers
            ) as response:
                if response.status == 200:
                    image_data = await response.read()
                    file = discord.File(fp=BytesIO(image_data), filename="juice.png")
                    embed = discord.Embed(color=self.bot.color)
                    embed.set_image(url="attachment://juice.png")
                    await ctx.send(embed=embed, file=file)
                    await self.bot.wait_for(
                        "message_delete",
                        check=lambda m: m.author == ctx.author
                        and m.attachments
                        and m.attachments[0].filename == "juice.png",
                    )
                    await asyncio.sleep(1)
                    os.remove("juice.png")
                else:
                    await ctx.send("Failed to fetch the image.")

    @commands.command(
        name="juice", help="return random juicewrld image", aliases=["juicewrld", "999"]
    )
    async def juice(self, ctx):
        api_key = (
            "claqz_Qt5c73ExW5pEtjjCknvL4djlPUK6RA1D4Ll4vx8SJcp1HPfFchYiWCarMHtuNCbm"
        )
        headers = {"Authorization": api_key}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://dev.lains.life/images/juice", headers=headers
            ) as response:
                if response.status == 200:
                    image_data = await response.read()
                    file = discord.File(fp=BytesIO(image_data), filename="juice.png")
                    embed = discord.Embed(color=self.bot.color)
                    embed.set_image(url="attachment://juice.png")
                    await ctx.send(embed=embed, file=file)
                    await self.bot.wait_for(
                        "message_delete",
                        check=lambda m: m.author == ctx.author
                        and m.attachments
                        and m.attachments[0].filename == "juice.png",
                    )
                    await asyncio.sleep(1)
                    os.remove("juice.png")
                else:
                    await ctx.send("Failed to fetch the image.")

    @commands.command(
        name="ken", help="return random ken carson image", aliases=["kenc", "kencarson"]
    )
    async def ken(self, ctx):
        api_key = (
            "claqz_Qt5c73ExW5pEtjjCknvL4djlPUK6RA1D4Ll4vx8SJcp1HPfFchYiWCarMHtuNCbm"
        )
        headers = {"Authorization": api_key}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://dev.lains.life/images/ken", headers=headers
            ) as response:
                if response.status == 200:
                    image_data = await response.read()
                    file = discord.File(fp=BytesIO(image_data), filename="ken.png")
                    embed = discord.Embed(color=self.bot.color)
                    embed.set_image(url="attachment://ken.png")
                    await ctx.send(embed=embed, file=file)
                    await self.bot.wait_for(
                        "message_delete",
                        check=lambda m: m.author == ctx.author
                        and m.attachments
                        and m.attachments[0].filename == "ken.png",
                    )
                    await asyncio.sleep(1)
                    os.remove("ken.png")
                else:
                    await ctx.send("Failed to fetch the image.")

    @commands.command(
        name="speed",
        help="return random ishowspeed image",
        aliases=["ishowspeed", "ishowmeat"],
    )
    async def speed(self, ctx):
        api_key = (
            "claqz_Qt5c73ExW5pEtjjCknvL4djlPUK6RA1D4Ll4vx8SJcp1HPfFchYiWCarMHtuNCbm"
        )
        headers = {"Authorization": api_key}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://dev.lains.life/images/speed", headers=headers
            ) as response:
                if response.status == 200:
                    image_data = await response.read()
                    file = discord.File(fp=BytesIO(image_data), filename="speed.png")
                    embed = discord.Embed(color=self.bot.color)
                    embed.set_image(url="attachment://speed.png")
                    await ctx.send(embed=embed, file=file)
                    await self.bot.wait_for(
                        "message_delete",
                        check=lambda m: m.author == ctx.author
                        and m.attachments
                        and m.attachments[0].filename == "speed.png",
                    )
                    await asyncio.sleep(1)
                    os.remove("speed.png")
                else:
                    await ctx.send("Failed to fetch the image.")

    @commands.command(
        name="xxx",
        help="return random xxxtentacion image",
        aliases=["xxxtentacion", "xxxt"],
    )
    async def xxx(self, ctx):
        api_key = (
            "claqz_Qt5c73ExW5pEtjjCknvL4djlPUK6RA1D4Ll4vx8SJcp1HPfFchYiWCarMHtuNCbm"
        )
        headers = {"Authorization": api_key}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://dev.lains.life/images/xxx", headers=headers
            ) as response:
                if response.status == 200:
                    image_data = await response.read()
                    file = discord.File(fp=BytesIO(image_data), filename="xxx.png")
                    embed = discord.Embed(color=self.bot.color)
                    embed.set_image(url="attachment://xxx.png")
                    await ctx.send(embed=embed, file=file)
                    await self.bot.wait_for(
                        "message_delete",
                        check=lambda m: m.author == ctx.author
                        and m.attachments
                        and m.attachments[0].filename == "xxx.png",
                    )
                    await asyncio.sleep(1)
                    os.remove("xxx.png")
                else:
                    await ctx.send("Failed to fetch the image.")


async def setup(bot):
    await bot.add_cog(Images(bot))
