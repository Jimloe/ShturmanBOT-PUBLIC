import random
import asyncio
import discord
from discord.ext import commands
from bot import shturclass
from bot import reddit
from bot import flairhelperbot, dupe_mod_log, media_spam


intents = discord.Intents.default()  # This sets up the new intentions in 1.5
intents.members = True
client = commands.Bot(command_prefix='%', intents=intents)  # Set the syntax for recognizing Discord commands

moduleset = {'fhb', 'mediaspam'}
fhbloop = ''
medialoop = ''
dmlloop = ''
quewatchloop = ''
subredditmod = 'EscapefromTarkov'

#########################################################################################################
# Discord bot events
#########################################################################################################


@client.event
async def on_ready():
    activity = discord.Activity(name='Waiting game | %about', type=discord.ActivityType.playing)
    await client.change_presence(activity=activity)
    print('The bot is ready!')


#########################################################################################################
# Discord Commands
#########################################################################################################


@client.command(aliases=['hi', 'yo'])
async def hello(ctx):
    randhello = random.choice(shturclass.Shturclass.hellomsg)
    randmsg = random.choice(shturclass.Shturclass.saymsg)
    await ctx.send(f'{randhello} {ctx.author.mention}! {randmsg}')


@client.command(aliases=['goodbye', 'later', 'cya'])
async def bye(ctx):
    randbye = random.choice(shturclass.Shturclass.byemsg)
    await ctx.send(f'{randbye}, {ctx.author.mention}!')


@client.command()
async def about(ctx):
    person = ctx.author.mention
    randhello = random.choice(shturclass.Shturclass.hellomsg)
    await ctx.send(f'{randhello} {person}!  This bot is a dev tracker and moderation utility for /r/EscapeFromtTarkov\n'
                   f'Use %commands to get a list of all commands available')


@client.command()  # Command to turn on / off flair helper bot
async def fhb(ctx, runprgm, ignoremods='True', interval=30):
    global fhbloop
    randhello = random.choice(shturclass.Shturclass.hellomsg)
    person = ctx.author.mention
    if ctx.author.nick not in flairhelperbot.FlairHelperBot.mods:
        await ctx.send(f'{randhello} {person}!  You\'re not allowed to do that.')
    else:
        if runprgm.lower() == 'stop':
            try:
                fhbloop.cancel()  # Canceles the Asyncio Task that was created
                await ctx.send(f'{randhello} {person}!  I will no longer enforce flairs on the subreddit, {subredditmod}.')
            except:
                await ctx.send(f'{randhello} {person}!  I don\'t think that\'s currently running.')
        else:
            try:
                interval = int(interval)  # Validate if a number was entered
                if (runprgm.lower() == 'start') and (ignoremods.lower() == 'false' or ignoremods.lower() == 'true') and (isinstance(interval, int)):
                    fhbstart = flairhelperbot.FlairHelperBot(subredditmod, running=False, ignoremod=ignoremods.capitalize(), interval=interval)  # Create the FHB object to do stuff with
                    await ctx.send(f'{randhello} {person}!  I will now enforce flairs on submission in the subreddit, {fhbstart.subreddit}.')
                    fhbloop = asyncio.create_task(fhbstart.run(True))  # Have to do the create_task, otherwise we can't cancel it later
                    await fhbloop
                else:
                    await ctx.send(f'{randhello} {person}!  I didn\'t recognize your command.')
            except ValueError:
                await ctx.send(f'{randhello} {person}!  I didn\t recognize your command.')


@client.command()  # Command to turn on / off the media spam checker
async def mediaspam(ctx, runprgm, ignoremods='', interval=30, action=''):
    global medialoop
    randhello = random.choice(shturclass.Shturclass.hellomsg)
    person = ctx.author.mention
    if ctx.author.nick not in media_spam.MediaSpam.mods:
        await ctx.send(f'{randhello} {person}!  You\'re not allowed to do that.')
    else:
        if runprgm.lower() == 'stop':
            try:
                medialoop.cancel()  # Canceles the Asyncio Task that was created
                await ctx.send(f'{randhello} {person}!  I will no longer watch for media spam, {subredditmod}.')
            except:
                await ctx.send(f'{randhello} {person}!  I don\'t think that\'s currently running.')
        else:
            try:
                interval = int(interval)  # Validate if a number was entered
                if (runprgm.lower() == 'start') and (ignoremods.lower() == 'true' or ignoremods.lower() == 'false') and (isinstance(interval, int) and (action.lower() == 'report' or action.lower() == 'remove')):
                    msstart = media_spam.MediaSpam(subredditmod, running=False, ignoremod=ignoremods.capitalize(), interval=interval, action=action.capitalize())  # Create the mediaspam object to do stuff with
                    await ctx.send(f'{randhello} {person}!  I will now watch for media being spammed to the sub, {msstart.subreddit} and will {action} them.')
                    medialoop = asyncio.create_task(msstart.run(True))  # Have to do the create_task, otherwise we can't cancel it later
                    await medialoop
                else:
                    await ctx.send(f'{randhello} {person}!  I didn\'t recognize your command.')
            except ValueError:
                await ctx.send(f'{randhello} {person}!  I didn\'t recognize your command.')


@client.command()  # Command to turn on / off the dupe_mod_log
async def dml(ctx, runprgm, subreddit=subredditmod, memberchannel=734804241994219605, interval=30):
    global dmlloop
    randhello = random.choice(shturclass.Shturclass.hellomsg)
    person = ctx.author.mention
    if ctx.author.nick not in media_spam.MediaSpam.mods:
        await ctx.send(f'{randhello} {person}!  You\'re not allowed to do that.')
    else:
        if runprgm.lower() == 'stop':
            await ctx.send(f'{randhello} {person}!  I will no longer watch for duplicate mod actions.')
            dmlloop.cancel()
        elif runprgm.lower() == 'start':
            memberchannelobj = client.get_channel(memberchannel)  # Convert our ID to a channel object
            # We want to generate a list of moderators on Discord from the provided memberchannel, and match them up to our Reddit admins.
            nickdb = []  # Establishes empty list for storing multiple dicts+
            for member in memberchannelobj.members:  # Loop through all members in the text channel and create our list
                userobj = client.get_user(member.id)  # Get the user object so we can send them a DM later.
                nickdb.append({"nick": member.nick, "mention": member.mention, "id": member.id, "dmobj": userobj})
            # Create the dmlstart object to run the task.
            dmlloop = dupe_mod_log.DupeModLog(subreddit, userobj=nickdb, running=False, interval=interval)
            await ctx.send(f'{randhello} {person}!  I will now watch for duplicate moderator actions.')
            dmlloop = asyncio.create_task(dmlloop.run(True))  # Have to do the create_task, otherwise we can't cancel it later
            await dmlloop
        else:
            await ctx.send(f'{randhello} {person}!  I didn\'t understand your command.')


@client.command()  # Command to add mods from modules
async def addmod(ctx, module, moderator):
    randhello = random.choice(shturclass.Shturclass.hellomsg)
    person = ctx.author.mention
    personnick = ctx.author.nick
    if personnick not in shturclass.Shturclass.mods:
        await ctx.send(f'{randhello} {person}!  You\'re not allowed to do that.')
    elif (module not in moduleset) and (not reddit.verify_mod(moderator)):
        await ctx.send(f'{randhello} {person}!  I didn\'t recognize your command.')
    else:
        if module.lower() == 'fhb':
            flairhelperbot.FlairHelperBot.add_mod(moderator)
            await ctx.send(f'{randhello} {person}!  I\'ve granted {moderator} permissions to {module}.')
        if module.lower() == 'mediaspam':
            media_spam.MediaSpam.add_mod(moderator)
            await ctx.send(f'{randhello} {person}!  I\'ve granted {moderator} permissions to {module}.')


@client.command()  # Command to remove mods from modules
async def removemod(ctx, module, moderator):
    randhello = random.choice(shturclass.Shturclass.hellomsg)
    person = ctx.author.mention
    personnick = ctx.author.nick
    if personnick not in shturclass.Shturclass.mods:
        await ctx.send(f'{randhello} {person}!  You\'re not allowed to do that.')
    elif (module not in moduleset) and (not reddit.verify_mod(moderator)):
        await ctx.send(f'{randhello} {person}!  I didn\'t recognize your command.')
    else:
        if module.lower() == 'fhb':
            flairhelperbot.FlairHelperBot.remove_mod(moderator)
            await ctx.send(f'{randhello} {person}!  I\'ve removed {moderator}s permissions to {module}.')
        if module.lower() == 'mediaspam':
            media_spam.MediaSpam.remove_mod(moderator)
            await ctx.send(f'{randhello} {person}!  I\'ve removed {moderator}s permissions to {module}.')


@client.command()
async def watchque(ctx, runprgm, interval=30):
    guild = client.get_guild(340973813238071298)  # Reddit Mod server guild
    mqchannel = client.get_channel(820867845163450399)  # Probo mod channel
    modmention = guild.get_role(386999610117324800)  # Moderator Role ID
    probomention = guild.get_role(386999654694256651)  # Probo Mod Role ID

    while True:
        print("Starting loop")
        modqueue = reddit.reddit_auth().subreddit('EscapefromTarkov').mod.modqueue(limit=None)
        unmodded = reddit.reddit_auth().subreddit('EscapefromTarkov').mod.unmoderated(limit=None)
        mqcounter = 0
        umcounter = 0
        for item in modqueue:
            mqcounter += 1
        for item in unmodded:
            umcounter += 1

        print("modqueue is: ", mqcounter)
        print("unmodded is: ", umcounter)
        discordactivity = f"MQ:{mqcounter} UM:{umcounter}"
        activity = discord.Activity(name=discordactivity, type=discord.ActivityType.watching)
        if mqcounter >= 25:
            await mqchannel.send(f"\n{modmention.mention}\n{probomention.mention}, the MQ is over 25!")
        if umcounter >= 25:
            await mqchannel.send(f"\n{modmention.mention}\n{probomention.mention}, the UM is over 25!")
        await client.change_presence(activity=activity)
        await asyncio.sleep(interval)


@client.command()
async def commands(ctx):
    randhello = random.choice(shturclass.Shturclass.hellomsg)
    person = ctx.author.mention
    await ctx.send(
        f'{randhello} {person}!  Here\'s a list of all commands:\n'
        f'`%fhb Start/Stop IgnoreMods Interval` - Enables/disables the enforcement of flairs on subreddit posts.\n'
        f'> Default IgnoreMods is False. Default Interval is 30s.\n'
        f'`%mediaspam Start/Stop IgnoreMods Interval Report/Remove` - Enables/disables the enforcement of flairs on subreddit posts.\n'
        f'> Default IgnoreMods is False. Default Interval is 30s. Default removal is report.\n\n'
        f'`%dml Start/Stop` - Enables/disables the watching for duplicate moderator actions on a post.\n\n'
        f'`%addmod ModuleName ModeratorName` - Grant a mod permissions to a module - NOT FUNCTIONAL ON REBOOT\n'
        f'`%removemod ModuleName ModeratorName` - Remove a mods permissions to a module - NOT FUNCTIONAL ON REBOOT\n')
