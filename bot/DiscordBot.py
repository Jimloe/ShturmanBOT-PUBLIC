import random
import asyncio
import discord
from discord.ext import commands
from bot import reddit
from bot import flairhelperbot

client = commands.Bot(command_prefix='%')

hellomsg = ['Привет', 'Hello', 'Hey', 'Приветик', 'What\'s up', 'Что нового', 'Yo']
saymsg = ['How are you today?', 'Pretty shit raids today, eh?', 'Have you seen my Red Rebel anywhere?',
          'Some PMC just stole my key!', 'Jaeger just put a bounty on my head, I\'ll pay you double',
          'Want to go to labs?  I got a keycard.', 'Desync seems bad today, be careful out there.',
          'Have you seen the Svetloozerskiy brothers?  They were supposed to be protecting my loot...',
          'Got any Slickers?', 'Got any Tushonka?', 'Got any Alyonka?', 'Got any TarCola?',
          'Got some mooonshine? Reshala drank all mine ... Vot khuy!', 'Stay off Woods, I\'m hunting PMCs',
          'Have you seen Jaeger\'s camp?', 'Where\'s ZB-014?  Dimon said there was some 60 round mags there.',
          'Armor is for pussies, a jacket is all you need.']
nestedloop = ''

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


@client.command()
async def hello(ctx):
    global hellomsg, saymsg
    randhello = random.choice(hellomsg)
    randmsg = random.choice(saymsg)
    await ctx.send('{1} {0.author.mention}! {2}'.format(ctx, randhello, randmsg))


@client.command()
async def about(ctx):
    randhello = random.choice(hellomsg)
    await ctx.send(
        "{1} {0.author.mention}!  This bot is a dev tracker and moderation utility for /r/EscapeFromtTarkov\n"
        "Use %listcommands to get a list of all commands available".format(ctx, randhello))


@client.command()
async def commands(ctx):
    global hellomsg
    randhello = random.choice(hellomsg)
    await ctx.send(
        "{1} {0.author.mention}!  Here's a list of all commands:\n"
        "I have no commands because I'm completely redoing this".format(ctx, randhello))


@client.command(pass_context=True)  # Command to turn on / off flair helper bot
async def fhb(ctx, arg1, arg2='', arg3=''):
    global nestedloop  # This is to store our Asyncio task so we can later stop it gracefully
    randhello = random.choice(hellomsg)
    if ctx.author.nick not in flairhelperbot.FlairHelperBot.mods:
        await ctx.send("{1} {0.author.mention}!  You're not allowed to do that.".format(ctx, randhello))
    else:
        if arg1.lower() == 'stop':
            try:
                nestedloop.cancel()  # Canceles the Asyncio Task that was created
                await ctx.send("{1} {0.author.mention}!  I will no longer enforce flairs on the subreddit, PLACEHOLDER.".format(ctx, randhello))
            except:
                await ctx.send("{1} {0.author.mention}!  I don't think that's currently running.".format(ctx, randhello))
        else:
            try:
                arg3 = int(arg3)
                if (arg1.lower() == 'start') and (arg2.lower() == 'false' or arg2.lower() == 'true') and (isinstance(arg3, int)):
                    fhbstart = flairhelperbot.FlairHelperBot('EFTDesign', running=False, ignoremod=arg2.capitalize(), interval=arg3)  # Create the FHB object to do stuff with
                    await ctx.send("{1} {0.author.mention}!  I will now enforce flairs on submission in the subreddit, {2}.".format(ctx, randhello, fhbstart.subreddit))
                    # nestedloop = asyncio.create_task(fhbstart.run(True))
                    nestedloop = fhbstart.run(True)
                    await nestedloop
                else:
                    await ctx.send("{1} {0.author.mention}!  I didn't recognize your command.".format(ctx, randhello))
            except ValueError:
                await ctx.send("{1} {0.author.mention}!  I didn't recognize your command.".format(ctx, randhello))


@client.command()  # Command to add moderators to allow them to mess with this function
async def fhbmod(ctx, arg1, arg2):
    randhello = random.choice(hellomsg)
    if arg2.lower() == 'remove':  # Check to see if we want to remove first.
        try:
            flairhelperbot.FlairHelperBot.remove_mod(arg1)  # Attempt to remove the mod from our set
            await ctx.send("{1} {0.author.mention}!  I've removed that mod from the approved list.".format(ctx, randhello))
        except:
            await ctx.send("{1} {0.author.mention}!  I think you mispelled that mod name.".format(ctx, randhello))
    elif arg2.lower() == 'add':  # We want to add the mod
        validmod = reddit.verify_mod(arg1)
        if validmod:
            flairhelperbot.FlairHelperBot.add_mod(arg1)
            await ctx.send("{1} {0.author.mention}!  I added them to the approved mod list for this function.".format(ctx, randhello))
        else:
            await ctx.send("{1} {0.author.mention}!  I didn't recognize that moderator.".format(ctx, randhello))
    else:  # We didn't recongize the command, tell the user
        await ctx.send("{1} {0.author.mention}!  I didn't recognize your command.".format(ctx, randhello))


@client.command()
async def listcommands(ctx):
    global hellomsg
    randhello = random.choice(hellomsg)
    await ctx.send(
        "{1} {0.author.mention}!  Here's a list of all commands:\n"
        "`%fhb Start/Stop IgnoreMods Interval` - Enables/disables the enforcement of flairs on subreddit posts. Default IgnoreMods is True. Default Interval is 60s.  \n"
        "`%fhbmod ModName Add/Remove` - Modify who is able to use this module.  \n".format(ctx, randhello))

# activity = discord.Activity(name='for Flairs | %about', type=discord.ActivityType.watching)
# await client.change_presence(activity=activity)
# "`%getusers` - Shows a list of tracked users\n"
# "`%adduser Xusername TRUE/FALSE` - Adds/Updates a user to the tracked user list.  TRUE/FALSE notates whether or not a sticky will be created in the thread they've posted in.\n"
# "`%removeuser Xusername` - Removes a user from tracked user list\n\n"
# "`%devtracker True/False` - Enables or disables dev tracking and Discord notifications\n"
# "`%devchannel add/remove` - Adds or removes a channel for Dev post notifications.\n"
# "`%updatetime` - Updates the time interval for the Reddit scans\n\n"
# "`%commentsticky True/False` - Enables or disables the Reddit sticky comment functionality.  References the tracked users list.\n"
# "`%nextscan` - Displays next run time\n\n"
# "`%dml True/False` - Enables/disables checking the mod log for duplicate actions.\n"
# "`%dmlchannel add/remove` - Adds or removes a channel for Duplicate Mod Log notifications.\n"
# "`%dmltype DM/Channel` - Specifies whether you want reports to go to a channel or to DM the users.\n\n"
# "`%r5 True/False` - Enables/disables checking new submissions for potential R5 violations.\n"
# "`%r5remove True/False` - Enables/disables automatic removal of posts.\n\n"
# "`%whatsrunning` - Shows which modules are running.\n\n"
# "`%monitor` - See how hot my server is running at\n\n"
# "`%updatemodlist` - Scan the mod Discord and see if there's been any changes in the Moderator roles.\n\n"
# "`%updatesubreddit Xsubname` - Change the subreddit that the bot performs MODERATION actions on.  This does not affect dev tracking."
