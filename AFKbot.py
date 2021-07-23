
import os
import discord
from discord.ext import commands
import jsonio

intents = discord.Intents.default()
intents.members = True
intents.messages = True
bot = commands.Bot(command_prefix=".", intents=intents)

@bot.event
async def on_ready():
    print('Logged in')
    channel = bot.get_channel(743747680651444276)
    if channel:
        await channel.send("I LIVE")

@bot.command()
async def afk(ctx, *, arg):
    jsonio.write(ctx.message.author.id, arg)
    await ctx.send("AFK for " + ctx.message.author.display_name + " set.")

@bot.command()
async def ping(ctx):
    await ctx.send("pong")

@bot.event
async def on_message(ctx):
    for member in ctx.mentions:
        if jsonio.contains(member.id):
            await ctx.channel.send(member.display_name + " is AFK: " + jsonio.read(member.id))

    if jsonio.contains(ctx.author.id):
        jsonio.remove(ctx.author.id)

    await bot.process_commands(ctx)

token = os.getenv("DISCORD_BOT_TOKEN")
bot.run(token)
