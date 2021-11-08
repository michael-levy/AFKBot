
import getngrams
import os
import sys
from enum import Enum
from dataclasses import dataclass
import pickle 
import random
import asyncio
import discord
from discord.ext import commands
import jsonio

intents = discord.Intents.default()
intents.members = True
intents.messages = True
bot = commands.Bot(command_prefix=".", intents=intents)

def callngrams(word: str)->float:
    """
    Call the getngrams module and return the result

    Result is the frequency of the word as percentage from 2009-2019
    """
    fn= 'getngrams_'+word.replace(' ','_')
    try:
        getngrams.ngrams(word+" -startYear=2009", filename=fn,   toPlot=False)
        url, urlquery, df = pickle.load(open(    fn, "rb" ) )
        os.remove(fn)
        os.remove(fn +".csv")
        total: float = 0
        total = (sum(df[word.split(" ")[0]]))/10
        return total
    except:
        os.remove(fn)
        return -1

@bot.event
async def on_ready():
    print('Logged in')
    channel = bot.get_channel(743747680651444276)
    if channel:
        await channel.send("I LIVE")

@bot.command()
async def afk(ctx, *, arg):
    """
    Set an AFK message
    """
    jsonio.write(ctx.message.author.id, arg)
    await textembed(ctx, "AFK for " + ctx.message.author.display_name + " set.")

@bot.command()
async def ping(ctx):
    """
    pong
    """
    await textembed(ctx, "pong")

@bot.command()
@commands.cooldown(1, 30, commands.BucketType.user)
async def freq(ctx, word):
    """
    Return frequency of a word as percentage
    """
    percent = callngrams(word)
    if(percent<0):
        await textembed(ctx, "Not represented in Google Ngram data.")
        return
    rounded = '{:g}'.format(float('{:.{p}g}'.format(percent, p=5)))
    await textembed(ctx, word + " represents " + str(rounded) + "% of all words");

@freq.error
async def freq_error(ctx,error):
    if isinstance(error, commands.CommandOnCooldown):
        await textembed(ctx,f'This command is on cooldown, you can use it in {round(error.retry_after, 2)} seconds')

@bot.command()
@commands.cooldown(1, 30, commands.BucketType.user)
async def freqm(ctx, word):
    """
    Return frequency of a word per million
    """
    wpm = callngrams(word)*1000000
    if(wpm<0):
        await textembed(ctx, "Not represented in Google Ngram data.")
        return
    rounded = '{:g}'.format(float('{:.{p}g}'.format(wpm, p=5)))
    await textembed(ctx, word + " represents " + str(rounded) + " words per million");
    
@freqm.error
async def freqm_error(ctx,error):
    if isinstance(error, commands.CommandOnCooldown):
        await textembed(ctx, f'This command is on cooldown, you can use it in {round(error.retry_after, 2)} seconds')

class WordGame(commands.Cog):
    class GameState(Enum):
        INACTIVE = 0,
        SETUP = 1,
        TURN = 2,
        END = 3,

    class TurnState(Enum):
        INACTIVE = 0,
        GUESS = 1,
        HANDLE = 2,

    @dataclass
    class Player():
        id: int
        name: str
        points: int = 0

    @dataclass
    class Turn():
        syl: str = ""
        correct: bool = False

    def __init__(self, ctx):
        self.gameState: self.GameState = self.GameState.INACTIVE
        self.turnState: self.TurnState = self.TurnState.INACTIVE
        self.players = []
        self.rounds = 0
        self.currentTurn = None
        self.currentPlayer = 0

    @commands.command()
    async def stop(self, ctx):
        """
        End a game
        """
        self.gameState = self.GameState.INACTIVE
        self.turnState = self.TurnState.INACTIVE
        self.players = []
        self.rounds = 0
        self.currentTurn = None
        self.currentPlayer = 0

    @commands.command()
    async def setup(self, ctx):
        """
        Setup a game
        """
        if(self.gameState is not self.GameState.INACTIVE):
            await self.error(ctx) 
            return

        await textembed(ctx,"How many rounds would you like to play?")

        def check(m)->bool:
            return m.content.isnumeric() and int(m.content) > 0

        try:
            msg = await bot.wait_for('message',check=check,timeout=20)
        except asyncio.TimeoutError:
            await textembed(ctx,"Timeout reached. Setup aborted.")
            self.gameState=self.GameState.INACTIVE
            return
        
        self.rounds = int(msg.content)
        await textembed(ctx,f"You have begun a {self.rounds} round game! Send .join to join and .start to begin.")
        self.gameState = self.GameState.SETUP

    @commands.command()
    async def join(self, ctx):
        """
        Add yourself to a game during setup
        """
        if(self.gameState is not self.GameState.SETUP):
            await self.error(ctx)
            return
        id = ctx.message.author.id
        playerName = ctx.message.author.display_name
        self.players.append(self.Player(id,playerName))
        await textembed(ctx,"You have joined the game.")

    @commands.command()
    async def start(self, ctx):
        """
        After setup, begin a game
        """
        if(self.gameState is not self.GameState.SETUP):
            await self.error(ctx)
            return
        if(len(self.players)==0):
            await textembed(ctx,"I cannot play by myself.")
            return
        self.gameState = self.GameState.TURN
        await self.turn(ctx)

    async def turn(self, ctx):
        """
        Handle each player's turn
        """
        if(not await self.isTurn() or self.turnState is not self.TurnState.INACTIVE):
            await self.error(ctx)

        # Send embed with current player and leaderboard
        embed = discord.Embed(title=f"{self.players[self.currentPlayer].name}'s turn.",color=0xFF00FF)
        table = self.playerTable()
        embed.add_field(name="Leaderboard", value=table, inline=False)
        await ctx.channel.send(embed=embed)

        # get a random syllable
        with open("syllables.txt", "r") as fp:
            lines = fp.readlines()
        syl = random.choice(lines)[:-1]
        self.currentTurn = self.Turn(syl)

        # send embed with syllable
        time = 10
        embed = discord.Embed(title=time,description=f"What's a word containing {syl}?",color=0xFF00FF)
        message = await ctx.channel.send(embed=embed)

        self.turnState = self.TurnState.GUESS 

        # count down until 0 or user makes correct attempt (handled asynchronously in guess())
        while time > 0:
            await asyncio.sleep(1)
            time = time - 1
            if(time!=1):
                await message.edit(embed=discord.Embed(title=time,description=f"What's a word containing {syl}?"),color=0xFF00FF)
            else:
                await message.edit(embed=discord.Embed(title=time,description=f"What's a word containing {syl}?"),color=0xFF00FF)
            if(self.currentTurn.correct): break
        
        self.turnState = self.TurnState.HANDLE 

        await asyncio.sleep(2)

        if(time==0 and not self.currentTurn.correct):
            await textembed(ctx,"You have failed.")

        # move to next player
        if(self.currentPlayer<len(self.players)-1):
            self.currentPlayer = self.currentPlayer+1
        else:
            self.currentPlayer = 0
            self.rounds = self.rounds-1

        self.turnState = self.TurnState.INACTIVE

        # either end game or move to next turn
        if(self.rounds == 0):
            self.gameState = self.GameState.END
            await self.end(ctx)
        else:
            await self.turn(ctx)

    def playerTable(self)->str:
        """
        Return a string representation of players sorted by score
        """
        sortedList = sorted(self.players, key=lambda p: p.points, reverse=True)
        table: str = ""
        for player in sortedList:
            table= table + (f"{player.name}: {player.points}\n")
        return table
    
    async def end(self, ctx):
        """
        Conclude the game, send leaderboard embed
        """
        embed = discord.Embed(title=f"Game Over!",color=0xFF00FF)
        table = self.playerTable()
        embed.add_field(name="Leaderboard", value=table, inline=False)
        await ctx.channel.send(embed=embed)
        await self.stop(ctx)
        
    async def isTurn(self)->bool:
        """
        Is the game in the turn state
        """
        return self.gameState is self.GameState.TURN

    async def guess(self, ctx, guess):
        """
        Handle a guess
        """
        if(not await self.isTurn() or self.turnState is not self.TurnState.GUESS):
            return

        points = 0
        wpm = callngrams(guess)*10000000

        if(wpm <= 0):
            await textembed(ctx,"Not represented in Google Ngram data.")
        elif(self.currentTurn.syl in guess and wpm > 0.001):
            self.turnState = self.TurnState.HANDLE 
            points = await self.wordBand(wpm)
            self.currentTurn.correct = True
            await textembed(ctx,f"Correct! You have been awarded {points}" +  (" point"  if points==1 else " points"))
            self.players[self.currentPlayer].points = self.players[self.currentPlayer].points+points
        elif(self.currentTurn.syl in guess and wpm < 0.001):
            await textembed(ctx,f"Hmm. No, I don't think so.")
        else:
            await textembed(ctx,f"{self.currentTurn.syl} is not in that word.")
        
    async def isCurrentPlayer(self, id: int)->bool:
        """
        Decide if given id is the current player
        """
        try:
            return self.players[self.currentPlayer].id==id
        except:
            return False

    async def wordBand(self, wpm):
        """
        Convert words per million to their oxford word band
        """
        if(wpm>1000):
            return 1
        elif(wpm>100):
            return 2
        elif(wpm>10):
            return 3
        elif(wpm>1):
            return 4
        elif(wpm>0.1):
            return 5
        elif(wpm>0.01):
            return 6
        elif(wpm>0.001):
            return 7
        return 0

    async def error(self, ctx):
        """
        Send error embed if FSM attempts an invalid state
        """
        embed = discord.Embed(description="That is an invalid command right now.", color=0xEEDD00)
        embed.set_author(name="Error", icon_url="https://www.pngall.com/wp-content/uploads/2017/05/Alert-Download-PNG.png")
        await ctx.channel.send(embed=embed)

async def textembed(ctx, text: str):
    """
    Send a basic embed with text as the description
    """
    embed = discord.Embed(description=text, color=0xFF00FF)
    return await ctx.channel.send(embed=embed)

bot.add_cog(WordGame(bot))
cog = bot.get_cog('WordGame')

@bot.event
async def on_message(ctx):
    # respond to pings with set AFK message
    for member in ctx.mentions:
        if jsonio.contains(member.id):
            await textembed(ctx, member.display_name + " is AFK: " + jsonio.read(member.id))

    # remove AFK if member sends a message
    if jsonio.contains(ctx.author.id):
        jsonio.remove(ctx.author.id)

    # respond angrily to dad jokes
    if "i'm dad" in ctx.content.lower() or "im dad" in ctx.content.lower():
        await ctx.channel.send("NO")

    # assume everything is a guess for the word game
    if(await cog.isCurrentPlayer(ctx.author.id)):
        await cog.guess(ctx, ctx.content.lower())

    await bot.process_commands(ctx)

token = os.getenv("DISCORD_BOT_TOKEN")
bot.run(token)
