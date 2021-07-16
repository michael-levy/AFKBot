
import json
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True
intents.messages = True
bot = commands.Bot(command_prefix=".", intents=intents)

file = open('./config.json')
variables = json.load(file)
file.close()

afkfile = open('./afks.json', 'r+')
afks = json.load(afkfile)

@bot.event
async def on_ready():
    print('Logged in')
    channel = bot.get_channel(743747680651444276)
    if(channel):
        await channel.send("I LIVE")

@bot.command(aliases=["quit"])
@commands.has_role('Command')
async def close(ctx):
    """
    !! Turns off the bot !!
    """
    await ctx.send("You AFK'd the AFK bot")
    await bot.close()

@bot.command()
async def afk(ctx, message):    
    afks[str(ctx.message.author.id)]=message
    afkfile.seek(0)
    json.dump(afks, afkfile, indent=4)
    afkfile.truncate()
    print(afks)
    await ctx.send("AFK for " + ctx.message.author.display_name + "set to " + afks[str(ctx.message.author.id)])

@bot.command()
async def ping(ctx):
    await ctx.send("pong")

@bot.event
async def on_message(ctx):
    if(str(ctx.author.id) in afks):
        await ctx.channel.send(afks[str(ctx.author.id)])
    
    

bot.run(variables["token"])




