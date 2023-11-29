import discord, aiohttp, random, json, asyncio, requests, datetime, os
from discord.ext import commands
from random import randrange
from typing import List
from discord import ButtonStyle
from discord.ui import Button, View
from discord import Interaction, Message, HTTPException
from contextlib import suppress

session = requests.Session()


class RockPaperScissors(discord.ui.View):
    def __init__(self, ctx: commands.Context):
        self.ctx = ctx
        self.get_emoji = {"rock": "🪨", "paper": "📰", "scissors": "✂️"}
        self.status = False
        super().__init__(timeout=10)

    async def disable_buttons(self):
        for item in self.children:
            item.disabled = True

        await self.message.edit(view=self)

    async def action(self, interaction: discord.Interaction, selection: str):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.client.ext.send_warning(
                interaction, "This is not your game", ephemeral=True
            )
        botselection = random.choice(["rock", "paper, scissors"])

        def getwinner():
            if botselection == "rock" and selection == "scissors":
                return interaction.client.user.id
            elif botselection == "rock" and selection == "paper":
                return interaction.user.id
            elif botselection == "paper" and selection == "rock":
                return interaction.client.user.id
            elif botselection == "paper" and selection == "scissors":
                return interaction.user.id
            elif botselection == "scissors" and selection == "rock":
                return interaction.user.id
            elif botselection == "scissors" and selection == "paper":
                return interaction.client.user.id
            else:
                return "tie"

        if getwinner() == "tie":
            await interaction.response.edit_message(
                embed=discord.Embed(
                    color=interaction.client.color,
                    title="Tie!",
                    description=f"You both picked {self.get_emoji.get(selection)}",
                )
            )
        elif getwinner() == interaction.user.id:
            await interaction.response.edit_message(
                embed=discord.Embed(
                    color=interaction.client.color,
                    title="You won!",
                    description=f"You picked {self.get_emoji.get(selection)} and the bot picked {self.get_emoji.get(botselection)}",
                )
            )
        else:
            await interaction.response.edit_message(
                embed=discord.Embed(
                    color=interaction.client.color,
                    title="Bot won!",
                    description=f"You picked {self.get_emoji.get(selection)} and the bot picked {self.get_emoji.get(botselection)}",
                )
            )
        await self.disable_buttons()
        self.status = True

    @discord.ui.button(emoji="🪨")
    async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):
        return await self.action(interaction, "rock")

    @discord.ui.button(emoji="📰")
    async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):
        return await self.action(interaction, "paper")

    @discord.ui.button(emoji="✂️")
    async def scissors(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        return await self.action(interaction, "scissors")

    async def on_timeout(self):
        if self.status == False:
            await self.disable_buttons()


class TicTacToeButton(discord.ui.Button["TicTacToe"]):
    def __init__(
        self, x: int, y: int, player1: discord.Member, player2: discord.Member
    ):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=y)
        self.x = x
        self.y = y
        self.player1 = player1
        self.player2 = player2

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: TicTacToe = self.view
        state = view.board[self.y][self.x]
        if state in (view.X, view.O):
            return

        if view.current_player == view.X:
            if interaction.user != self.player1:
                return await interaction.response.send_message(
                    "you can't interact with this button", ephemeral=True
                )
            self.style = discord.ButtonStyle.danger
            self.label = "X"
            self.disabled = True
            view.board[self.y][self.x] = view.X
            view.current_player = view.O
            content = f"It is now **{self.player2.name}**'s turn"
        else:
            if interaction.user != self.player2:
                return await interaction.response.send_message(
                    "you can't interact with this button", ephemeral=True
                )
            self.style = discord.ButtonStyle.success
            self.label = "O"
            self.disabled = True
            view.board[self.y][self.x] = view.O
            view.current_player = view.X
            content = f"It is now **{self.player1.name}'s** turn"

        winner = view.check_board_winner()
        if winner is not None:
            if winner == view.X:
                content = f"**{self.player1.name}** won!"
            elif winner == view.O:
                content = "**{}** won!".format(self.player2.name)
            else:
                content = "It's a tie!"

            for child in view.children:
                child.disabled = True

            view.stop()

        await interaction.response.edit_message(content=content, view=view)


class TicTacToe(discord.ui.View):
    children: List[TicTacToeButton]
    X = -1
    O = 1
    Tie = 2

    def __init__(self, player1: discord.Member, player2: discord.Member):
        super().__init__()
        self.current_player = self.X
        self.board = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]

        for x in range(3):
            for y in range(3):
                self.add_item(TicTacToeButton(x, y, player1, player2))

    def check_board_winner(self):
        for across in self.board:
            value = sum(across)
            if value == 3:
                return self.O
            elif value == -3:
                return self.X

        for line in range(3):
            value = self.board[0][line] + self.board[1][line] + self.board[2][line]
            if value == 3:
                return self.O
            elif value == -3:
                return self.X

        diag = self.board[0][2] + self.board[1][1] + self.board[2][0]
        if diag == 3:
            return self.O
        elif diag == -3:
            return self.X

        diag = self.board[0][0] + self.board[1][1] + self.board[2][2]
        if diag == 3:
            return self.O
        elif diag == -3:
            return self.X

        if all(i != 0 for row in self.board for i in row):
            return self.Tie

        return None

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self.view)


class BlackTea:
    MatchStart = {}
    lifes = {}

    async def get_string():
        lis = await BlackTea.get_words()
        word = random.choice([l for l in lis if len(l) > 3])
        return word[:3]

    async def get_words():
        async with aiohttp.ClientSession() as cs:
            async with cs.get("https://www.mit.edu/~ecprice/wordlist.100000") as r:
                byte = await r.read()
                data = str(byte, "utf-8")
                return data.splitlines()


class Fun(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self.session = requests.Session()
        self.bot.session = aiohttp.ClientSession()

    @commands.command(
        name="choose",
        help="choose between options",
        usage="[choices separated by a comma]\nexample ;choose apple, pear, carrot",
    )
    async def choose_cmd(self, ctx: commands.Context, *, choice: str):
        choices = choice.split(", ")
        if len(choices) == 1:
            return await ctx.reply("please put a `,` between your choices")
        final = random.choice(choices)
        await ctx.reply(final)

    @commands.command(
        name="quickpoll",
        help="start a quick poll",
    )
    async def quickpoll_cmd(self, ctx: commands.Context, *, question: str):
        message = await ctx.reply(
            embed=discord.Embed(color=self.bot.color, description=question).set_author(
                name=f"{ctx.author} asked"
            )
        )
        await message.add_reaction("👍")
        await message.add_reaction("👎")

    @commands.hybrid_command(
        aliases=["rps"],
        help="play rock paper scissors with the bot",
    )
    async def rockpaperscisssors(self, ctx: commands.Context):
        view = RockPaperScissors(ctx)
        embed = discord.Embed(
            color=self.bot.color,
            title="Rock Paper Scissors!",
            help="Click a button to play!",
        )
        view.message = await ctx.reply(embed=embed, view=view)

    @commands.hybrid_command(help="retard rate an user", usage="<member>")
    async def howretarded(self, ctx, member: discord.Member = commands.Author):
        await ctx.reply(
            embed=discord.Embed(
                color=self.bot.color,
                title="how retarded",
                description=f"{member.mention} is {randrange(101)}% retarded <:jade_retarded:1114576204431888506>",
            )
        )

    @commands.hybrid_command(help="gay rate an user", usage="<member>")
    async def howgay(self, ctx, member: discord.Member = commands.Author):
        await ctx.reply(
            embed=discord.Embed(
                color=self.bot.color,
                title="gay r8",
                description=f"{member.mention} is {randrange(101)}% gay 🏳️‍🌈",
            )
        )

    @commands.hybrid_command(help="cool rate an user", usage="<member>")
    async def howcool(self, ctx, member: discord.Member = commands.Author):
        await ctx.reply(
            embed=discord.Embed(
                color=self.bot.color,
                title="cool r8",
                description=f"{member.mention} is {randrange(101)}% cool 😎",
            )
        )

    @commands.hybrid_command(help="check an user's iq", usage="<member>")
    async def iq(self, ctx, member: discord.Member = commands.Author):
        await ctx.reply(
            embed=discord.Embed(
                color=self.bot.color,
                title="iq test",
                description=f"{member.mention} has `{randrange(200)}` iq 🧠",
            )
        )

    @commands.hybrid_command(help="hot rate an user", usage="<member>")
    async def hot(self, ctx, member: discord.Member = commands.Author):
        await ctx.reply(
            embed=discord.Embed(
                color=self.bot.color,
                title="hot r8",
                description=f"{member.mention} is `{randrange(100)}%` hot 🥵",
            )
        )

    @commands.command(help="check how many bitches an user has", usage="<member>")
    async def bitches(
        self, ctx: commands.Context, *, user: discord.Member = commands.Author
    ):
        choices = ["regular", "still regular", "lol", "xd", "id", "zero", "infinite"]
        if random.choice(choices) == "infinite":
            result = "∞"
        elif random.choice(choices) == "zero":
            result = "0"
        else:
            result = random.randint(0, 100)
        embed = discord.Embed(
            color=self.bot.color, description=f"{user.mention} has `{result}` bitches"
        )
        await ctx.reply(embed=embed)

    @commands.hybrid_command(help="return an useless fact", aliases=["fact", "uf"])
    async def uselessfact(self, ctx):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://uselessfacts.jsph.pl/random.json?language=en"
            ) as response:
                data = await response.json()
                fact = data["text"]

        await ctx.reply(fact)

    @commands.hybrid_command(help="ship rate an user", usage="[member]")
    async def ship(self, ctx, member: discord.Member):
        return await ctx.reply(
            f"**{ctx.author.name}** 💞 **{member.name}** = **{randrange(101)}%**"
        )

    @commands.hybrid_command(
        aliases=["ttt"],
        help="play tictactoe with your friends",
        usage="[member]",
    )
    async def tictactoe(self, ctx: commands.Context, *, member: discord.Member):
        if member is ctx.author:
            return await ctx.reply(
                embed=discord.Embed(
                    color=self.bot.color,
                    description=f"{self.bot.warning} {ctx.author.mention}: You can't play with yourself. It's ridiculous",
                )
            )
        if member.bot:
            return await ctx.reply("bots can't play")
        embed = discord.Embed(
            color=self.bot.color,
            description=f"**{ctx.author.name}** wants to play **tictactoe** with you. Do you accept?",
        )
        style = discord.ButtonStyle.gray
        yes = discord.ui.Button(emoji=self.bot.yes, style=style)
        no = discord.ui.Button(emoji=self.bot.no, style=style)

        async def yes_callback(interaction: discord.Interaction):
            if interaction.user != member:
                em = discord.Embed(
                    color=self.bot.color,
                    description=f"{self.bot.warning}: {interaction.user.mention} you are not the author of this embed",
                )
                return await interaction.response.send_message(embed=em, ephemeral=True)
            vi = TicTacToe(ctx.author, member)
            await interaction.message.delete()
            vi.message = await ctx.send(
                content=f"Tic Tac Toe: **{ctx.author.name}** goes first",
                embed=None,
                view=vi,
            )

        async def no_callback(interaction: discord.Interaction):
            if interaction.user != member:
                em = discord.Embed(
                    color=self.bot.color,
                    description=f"{self.bot.warning}: {interaction.user.mention} you are not the author of this embed",
                )
                return await interaction.response.send_message(embed=em, ephemeral=True)
            await interaction.response.edit_message(
                embed=discord.Embed(
                    color=self.bot.color,
                    description=f"I'm sorry but **{interaction.user.name}** doesn't want to play with you right now",
                ),
                view=None,
                content=ctx.author.mention,
            )

        yes.callback = yes_callback
        no.callback = no_callback
        view = discord.ui.View()
        view.add_item(yes)
        view.add_item(no)
        await ctx.send(embed=embed, view=view, content=member.mention)

    @commands.hybrid_command(
        help="play blacktea with your friends",
    )
    async def blacktea(self, ctx: commands.Context):
        try:
            if BlackTea.MatchStart[ctx.guild.id] is True:
                return await ctx.reply(
                    "somebody in this server is already playing blacktea"
                )
        except KeyError:
            pass

        BlackTea.MatchStart[ctx.guild.id] = True
        embed = discord.Embed(
            color=self.bot.color,
            title="BlackTea Matchmaking",
            description=f"⏰ Waiting for players to join. To join react with 🍵.\nThe game will begin in **20 seconds**",
        )
        embed.add_field(
            name="goal",
            value="You have **10 seconds** to say a word containing the given group of **3 letters.**\nIf failed to do so, you will lose a life. Each player has **2 lifes**",
        )
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        mes = await ctx.send(embed=embed)
        await mes.add_reaction("🍵")
        await asyncio.sleep(20)
        me = await ctx.channel.fetch_message(mes.id)
        players = [user.id async for user in me.reactions[0].users()]
        leaderboard = []
        players.remove(self.bot.user.id)

        if len(players) < 2:
            BlackTea.MatchStart[ctx.guild.id] = False
            return await ctx.send(
                "😦 {}, not enough players joined to start blacktea".format(
                    ctx.author.mention
                ),
                allowed_mentions=discord.AllowedMentions(users=True),
            )

        while len(players) > 1:
            for player in players:
                strin = await BlackTea.get_string()
                await ctx.send(
                    f"⏰ <@{player}>, type a word containing **{strin.upper()}** in **10 seconds**",
                    allowed_mentions=discord.AllowedMentions(users=True),
                )

                def is_correct(msg):
                    return msg.author.id == player

                try:
                    message = await self.bot.wait_for(
                        "message", timeout=10, check=is_correct
                    )
                except asyncio.TimeoutError:
                    try:
                        BlackTea.lifes[player] = BlackTea.lifes[player] + 1
                        if BlackTea.lifes[player] == 3:
                            await ctx.send(
                                f" <@{player}>, you're eliminated ☠️",
                                allowed_mentions=discord.AllowedMentions(users=True),
                            )
                            BlackTea.lifes[player] = 0
                            players.remove(player)
                            leaderboard.append(player)
                            continue
                    except KeyError:
                        BlackTea.lifes[player] = 0
                    await ctx.send(
                        f"💥 <@{player}>, you didn't reply on time! **{2-BlackTea.lifes[player]}** lifes remaining",
                        allowed_mentions=discord.AllowedMentions(users=True),
                    )
                    continue
                i = 0
                for word in await BlackTea.get_words():
                    if (
                        strin.lower() in message.content.lower()
                        and message.content.lower() == word.lower()
                    ):
                        i += 1
                        pass
                if i == 0:
                    try:
                        BlackTea.lifes[player] = BlackTea.lifes[player] + 1
                        if BlackTea.lifes[player] == 3:
                            await ctx.send(
                                f" <@{player}>, you're eliminated ☠️",
                                allowed_mentions=discord.AllowedMentions(users=True),
                            )
                            BlackTea.lifes[player] = 0
                            players.remove(player)
                            leaderboard.append(player)
                            continue
                    except KeyError:
                        BlackTea.lifes[player] = 0
                    await ctx.send(
                        f"💥 <@{player}>, incorrect word! **{2-BlackTea.lifes[player]}** lifes remaining",
                        allowed_mentions=discord.AllowedMentions(users=True),
                    )
                else:
                    await message.add_reaction("✅")
                    i = 0

        leaderboard.append(players[0])
        le = 1
        auto = ""
        for leader in leaderboard[::-1]:
            auto += f"{'<a:crown:1021829752782323762>' if le == 1 else f'`{le}`'} **{ctx.guild.get_member(leader) or leader}**\n"
            if le == 10:
                break
            le += 1
        e = discord.Embed(
            color=self.bot.color, title=f"leaderboard for blacktea", description=auto
        ).set_footer(
            text=f"top {'10' if len(leaderboard) > 9 else len(leaderboard)} players"
        )
        await ctx.send(embed=e)
        BlackTea.lifes[players[0]] = 0
        BlackTea.MatchStart[ctx.guild.id] = False

    @commands.hybrid_command(
        help="returns a random bible verse",
    )
    async def bible(self, ctx: commands.Context):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://labs.bible.org/api/?passage=random&type=json"
            ) as response:
                data_text = await response.text()

        try:
            data = json.loads(data_text)
            verse = data[0]  # Access the first element of the list

            embed = discord.Embed(
                color=self.bot.color, description=verse["text"]
            ).set_author(
                name="{} {}:{}".format(
                    verse["bookname"], verse["chapter"], verse["verse"]
                ),
                icon_url="https://imgs.search.brave.com/gQ1kfK0nmHlQe2XrFIoLH9vtFloO3HRTDaCwY5oc0Ow/rs:fit:1200:960:1/g:ce/aHR0cDovL3d3dy5w/dWJsaWNkb21haW5w/aWN0dXJlcy5uZXQv/cGljdHVyZXMvMTAw/MDAvdmVsa2EvNzU3/LTEyMzI5MDY0MTlC/MkdwLmpwZw",
            )

            await ctx.reply(embed=embed)

        except json.JSONDecodeError:
            await ctx.send("Failed to parse the response. Please try again later.")

    @commands.hybrid_command(
        name="8ball",
        help="answers to your question",
        usage="[question]",
    )
    async def mtball(self, ctx: commands.Context, *, arg):
        rand = [
            "**Yes**",
            "**No**",
            "**definitely yes**",
            "**Of course not**",
            "**Maybe**",
            "**Never**",
            "**Yes, dummy**",
            "**No wtf**",
        ]
        e = discord.Embed(
            color=self.bot.color,
            description=f"You asked: {arg}\nAnswer: {random.choice(rand)}",
        )
        await ctx.reply(embed=e)

    @commands.command(
        name="eject",
        help="eject specified user",
        aliases=["imposter"],
    )
    async def eject(self, ctx, user: discord.Member = None):
        user = ctx.author if not user else user

        impostor = ["true", "false"]

        crewmate = [
            "black",
            "blue",
            "brown",
            "cyan",
            "darkgreen",
            "lime",
            "orange",
            "pink",
            "purple",
            "red",
            "white",
            "yellow",
        ]

        await ctx.reply(
            f"https://vacefron.nl/api/ejected?name={user.name}&impostor={random.choice(impostor)}&crewmate={random.choice(crewmate)}"
        )

    @commands.command(
        name="emojify",
        help="Make text to emojis",
        aliases=["emojitext"],
        usage="[text]",
    )
    async def emojify(self, ctx, *, text=None):
        if not text:
            return await ctx.reply("?")
        emojis = []
        for char in text.lower().replace(" ", "  "):
            if char.isdigit():
                number2emoji = {
                    "1": "one",
                    "2": "two",
                    "3": "three",
                    "4": "four",
                    "5": "five",
                    "6": "six",
                    "7": "seven",
                    "8": "eight",
                    "9": "nine",
                    "0": "zero",
                }

                emojis.append(f":{number2emoji[char]}:")

            elif char.isalpha():
                emojis.append(f":regional_indicator_{char}:")
            else:
                emojis.append(char)

        await ctx.reply(" ".join(emojis))

    @commands.command(
        name="morse",
        help="Make text to morse code",
        aliases=["morsing"],
        usage="[text]",
    )
    async def morse(self, ctx, *, text: str):
        to_morse = {
            "a": ".-",
            "b": "-...",
            "c": "-.-.",
            "d": "-..",
            "e": ".",
            "f": "..-.",
            "g": "--.",
            "h": "....",
            "i": "..",
            "j": ".---",
            "k": "-.-",
            "l": ".-..",
            "m": "--",
            "n": "-.",
            "o": "---",
            "p": ".--.",
            "q": "--.-",
            "r": ".-.",
            "s": "...",
            "t": "-",
            "u": "..-",
            "v": "...-",
            "w": ".--",
            "x": "-..-",
            "y": "-.--",
            "z": "--..",
            "1": ".----",
            "2": "..---",
            "3": "...--",
            "4": "....-",
            "5": ".....",
            "6": "-....",
            "7": "--...",
            "8": "---..",
            "9": "----.",
            "0": "-----",
        }

        cipher = ""
        for letter in text:
            if letter.isalpha() or letter.isdigit():
                cipher += to_morse[letter.lower()] + " "
            else:
                cipher += letter
        await ctx.reply(cipher)

    @commands.command(
        name="roll",
        usage="(sides)",
        help="Rolls a dice using clust",
    )
    @commands.cooldown(1, 4, commands.BucketType.guild)
    async def roll(self, ctx, sides: int = 6):
        await ctx.reply(f"Rolling a **{sides}-sided** dice..")
        await asyncio.sleep(1)

        await ctx.reply(f"The dice landed on **🎲 {random.randint(1, sides)}**")

    @commands.command(
        help="see how many days till halloween",
        usage="",
        aliases=["spooky"],
    )
    async def halloween(self, ctx):
        today = datetime.date.today()
        halloween_date = datetime.date(today.year, 10, 31)
        if halloween_date < today:
            halloween_date = datetime.date(today.year + 1, 10, 31)

        days_until_halloween = (halloween_date - today).days

        embed = discord.Embed(
            title="Days Until Halloween",
            description=f"🎃 {days_until_halloween} days",
            color=self.bot.color,
        )
        await ctx.send(embed=embed)

    @commands.command(
        help="see how many days till christmas",
        usage="",
        aliases=["xmas"],
    )
    async def christmas(self, ctx):
        today = datetime.date.today()
        christmas_date = datetime.date(today.year, 12, 25)
        if christmas_date < today:
            christmas_date = datetime.date(today.year + 1, 12, 25)

        days_until_christmas = (christmas_date - today).days

        embed = discord.Embed(
            title="Days Until Christmas",
            description=f"🎄 {days_until_christmas} days",
            color=self.bot.color,
        )
        await ctx.send(embed=embed)

    @commands.command(
        help="see how many days till easter",
        usage="",
        aliases=["rabbit"],
    )
    async def easter(self, ctx):
        today = datetime.date.today()

        # Function to calculate the date of Easter for the current year
        def calculate_easter_date(year):
            a = year % 19
            b = year // 100
            c = year % 100
            d = b // 4
            e = b % 4
            f = (b + 8) // 25
            g = (b - f + 1) // 3
            h = (19 * a + b - d - g + 15) % 30
            i = c // 4
            k = c % 4
            l = (32 + 2 * e + 2 * i - h - k) % 7
            m = (a + 11 * h + 22 * l) // 451
            month = (h + l - 7 * m + 114) // 31
            day = ((h + l - 7 * m + 114) % 31) + 1
            return datetime.date(year, month, day)

        easter_date = calculate_easter_date(today.year)
        if easter_date < today:
            easter_date = calculate_easter_date(today.year + 1)

        days_until_easter = (easter_date - today).days

        embed = discord.Embed(
            title="Days Until Easter",
            description=f"🥕 {days_until_easter} days",
            color=self.bot.color,
        )
        await ctx.send(embed=embed)

    @commands.command(
        help="see how many days till thanksgiving",
        usage="",
        aliases=["turkey"],
    )
    async def thanksgiving(self, ctx):
        today = datetime.date.today()

        def calculate_thanksgiving_date(year):
            november_1st = datetime.date(year, 11, 1)
            days_until_thursday = (3 - november_1st.weekday()) % 7
            thanksgiving_date = november_1st + datetime.timedelta(
                days=days_until_thursday + 21
            )
            return thanksgiving_date

        thanksgiving_date = calculate_thanksgiving_date(today.year)
        if thanksgiving_date < today:
            thanksgiving_date = calculate_thanksgiving_date(today.year + 1)

        days_until_thanksgiving = (thanksgiving_date - today).days

        embed = discord.Embed(
            title="Days Until Thanksgiving",
            description=f"🦃 {days_until_thanksgiving} days",
            color=self.bot.color,
        )
        await ctx.send(embed=embed)

    @commands.command(
        help="see how many days till valetinesday",
        usage="",
        aliases=["valetines", "valetine"],
    )
    async def valentinesday(self, ctx):
        today = datetime.date.today()
        valentines_day = datetime.date(today.year, 2, 14)
        if valentines_day < today:
            valentines_day = datetime.date(today.year + 1, 2, 14)

        days_until_valentines_day = (valentines_day - today).days

        embed = discord.Embed(
            title="Days Until Valentine's Day",
            description=f"💖 {days_until_valentines_day} days",
            color=self.bot.color,
        )
        await ctx.send(embed=embed)

    @commands.command(
        name="randomhex",
        help="return random hex color code",
        aliases=["randomcolor"],
        usage="",
    )
    async def randomhex(self, ctx):
        color = random.randint(0, 0x2B2D31)

        hex_color = f"#{color:06x}"

        embed = discord.Embed(title="Random Hex Color", color=color)
        embed.add_field(name="Hex Color", value=hex_color)

        await ctx.send(embed=embed)

    @commands.command(
        name="draw",
    )
    async def draw(self, ctx):
        class Board(Button):
            def __init__(
                self, label: str, style: ButtonStyle, row: int, custom_id: str
            ):
                super().__init__(label=label, style=style, row=row, custom_id=custom_id)

            async def callback(self, interaction: Interaction):
                await self.view.callback(interaction, self)

        class Draw(View):
            def __init__(self, ctx):
                super().__init__(timeout=420.0)
                self.ctx = ctx
                self.message: Message = None

                for i in range(25):
                    self.add_item(
                        Board(
                            label="\u200b",
                            style=ButtonStyle.gray,
                            row=i // 5,
                            custom_id=f"board:{i}",
                        )
                    )

            async def interaction_check(self, interaction: Interaction):
                if interaction.user.id == self.ctx.author.id:
                    return True

                return False

            async def on_timeout(self):
                for child in self.children:
                    child.disabled = True

                with suppress(HTTPException):
                    await self.message.edit(
                        content=f"**{self.ctx.author.name}**'s drawing",
                        view=self,
                    )

                self.stop()

            async def on_error(
                self, error: Exception, item: Button, interaction: Interaction
            ):
                pass

            async def callback(self, interaction: Interaction, item: Board):
                if item.style == ButtonStyle.gray:
                    item.style = ButtonStyle.red
                else:
                    item.style = ButtonStyle.gray

                await interaction.response.edit_message(view=self)

        await ctx.send(
            "Draw something!",
            view=Draw(ctx),
        )


async def setup(bot) -> None:
    await bot.add_cog(Fun(bot))
