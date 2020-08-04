import praw
import datetime
import configparser
import asyncio
import random
import discord
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from discord.ext import commands
from subprocess import call

# Loads up the configparser to read our login file
config = configparser.ConfigParser()
config.read('config')

#########################################################################################################
# Google Sheets information to remotely store data
#########################################################################################################
googleauth = False

while not googleauth:
    try:
        googlescope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
                       "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("ShturmanBOTcreds.json", googlescope)
        googleclient = gspread.authorize(creds)
        spreadsheet = googleclient.open("ShturmanBOTSheets")  # Open the spreadsheet
        serversheet = spreadsheet.worksheet('Servers')  # Server spreadsheet
        loggingsheet = spreadsheet.worksheet('Logging')  # Logging spreadsheet
        datasheet = spreadsheet.worksheet('Data')  # Comment sticky functionality
        usersheet = spreadsheet.worksheet('Users')  # User spreadsheet
        modposts = spreadsheet.worksheet('ModeratedPosts')  # User spreadsheet
        variablestorage = spreadsheet.worksheet('Variable Storage')  # Long term storage of variables.
        # Get a list of all server records, required for reddit_loop function
        allserverdata = serversheet.get_all_records()
        alluserdata = usersheet.get_all_records()  # Get a list of all user records, required for run_bot function.
        allvariables = variablestorage.get_all_records()  # Get a list of all variable records.
        # allmodposts = modposts.get_all_records()    # Get a list of all post Mod actions have been performed on
        googleauth = True
    except:
        continue

founddata = False


#########################################################################################################
# Google Sheets Logging functions
#########################################################################################################
def adddata(sheetobject, datatoadd, dupecheck):
    global founddata
    if dupecheck:
        alldata = sheetobject.get_all_records()
        iterator = 1
        founddata = False
        for data in alldata:
            iterator += 1  # Iterates through Google Sheet rows so we know which one we are working on.  0 is headers
            if datatoadd[0] in data.values():  # Find a duplicate, delete and update the row.
                sheetobject.delete_rows(iterator, iterator)
                sheetobject.insert_row(datatoadd, iterator)
                founddata = True
                return 'Update'
        if not founddata:  # No duplicates found so append the row.
            sheetobject.append_row(datatoadd)
            return 'Append'
    else:  # Don't check for dupes and just append
        sheetobject.append_row(datatoadd)
        return 'Append'


# Need to update function so it doesn't kill off the entire row and just the specific occurance, if requested.
def removedata(sheetobject, datatoremove):
    alldata = sheetobject.get_all_records()
    iterator = 1
    founddata = False
    for data in alldata:
        iterator += 1
        print(data.values(), "searching for: ", datatoremove)
        if datatoremove in data.values():
            print('found ', datatoremove, 'kill it!')
            sheetobject.delete_rows(iterator, iterator)
            founddata = True
            return founddata
    return founddata


def shturmanlog(errorlevel, datatolog):
    timestamp = str(datetime.datetime.utcnow())
    try:
        loggingsheet.append_row([timestamp, errorlevel, datatolog])
    except:
        print('Failed to connect to Google Sheets for some reason.')
        print(f'I was going to log: {datatolog}')


#########################################################################################################
# Raspberry Pi temp monitoring
#########################################################################################################
async def getCPUtemperature():
    global body, raspi_temp
    try:
        while True:
            res = os.popen('vcgencmd measure_temp').readline()
            raspi_temp = float((res.replace("temp=", "").replace("'C\n", "")))
            if 60 > raspi_temp > 50:
                shturmanlog('Info', f'Temp check: {raspi_temp}C')
            if 80 > raspi_temp > 60:
                shturmanlog('Warning', f'Temp check: {raspi_temp}C')
            if raspi_temp > 80:
                shturmanlog('Critical', f'Temp check: {raspi_temp}C')
                body = 'Raspberry Pi is getting too damn hot!  We\'re shutting this shit down!'
                call("sudo shutdown -h now", shell=True)  # This shuts down the Raspberry Pi automatically
            await asyncio.sleep(60)
    except:
        shturmanlog('Error', 'The raspberry pi temp monitoring has failed due to an unknown reason.')
        raspi_temp = 'Error'


#########################################################################################################
# Reddit Login / Scanner
#########################################################################################################


def bot_login():
    # Sets up the login for Reddit
    print("Logging in...")
    redditlogin = praw.Reddit(username=config['LOGIN']['username'],
                              password=config['LOGIN']['password'],
                              client_id=config['LOGIN']['client_id'],
                              client_secret=config['LOGIN']['client_secret'],
                              user_agent=config['LOGIN']['user_agent'])
    print('Logged on to Reddit as ShturmanBOT!')
    return redditlogin


def run_bot(redditlogin):
    # Ensure that we're using global variables so we can interact with this portion of the script on the fly
    global TimeBackChecker, SleepyTime, redditlooper, subreddit_name, devcommentsticky, usersheet, datasheet
    # Gets the script run time so it can compare how long ago something happened
    StartRunTime = datetime.datetime.utcnow()
    delta = datetime.timedelta(seconds=TimeBackChecker)
    TimeBackCheckerUTS = StartRunTime - delta
    print(f'StartRunTime: {StartRunTime} | Delta: {delta} | TimeBackCheckerUTS: {TimeBackCheckerUTS}')
    print(f'Getting new comments from /r/EscapeFromTarkov and tracking users.')
    redditcomment = []  # Creating a list to store comment output in
    redditpost = []  # Creating a list to store post output in
    alluserdata = usersheet.get_all_records()  # Get an updated list of all user records
    for usertrack in alluserdata:  # Creating the list of users to track from Google Sheets
        usercomments = redditlogin.redditor(usertrack['Usernames']).comments.new(limit=10)
        userposts = redditlogin.redditor(usertrack['Usernames']).submissions.new(limit=2)
        # Loop through the found comments to check their age
        for comment in usercomments:
            if TimeBackCheckerUTS < datetime.datetime.utcfromtimestamp(comment.created_utc):
                print('comment within timerange')
                username = usertrack['Usernames']
                thecomment = 'C:', f'{datetime.datetime.utcfromtimestamp(comment.created_utc)}', f'{comment.id}', f'{username}', f'{comment.body}', f'https://old.reddit.com{comment.permalink}'
                redditcomment.append(thecomment)
                if comment.subreddit.display_name == subreddit_name and usertrack['CommentSticky'] == 'TRUE':
                    print('Matched comment in specified subreddit, and matched sticky: ', subreddit_name)
                    header = '##### BSG Comments in this Thread:\n\n***'
                    footer = '***\n\n*I am a bot and this was created automatically.*'
                    author = comment.author.name  # Author of comment
                    permalink = comment.permalink  # Permalink to comment
                    submissionlink = comment.submission  # link to submission
                    bodytext = comment.body  # Body of comment
                    stickybody = f'\n\n{author} - [link](https://www.reddit.com{permalink}?context=3), - *{bodytext}*\n\n'

                    responded = False
                    alldatadata = datasheet.get_all_records()  # refresh our list of data.

                    for data in alldatadata:
                        if data['SubLink'] == submissionlink:
                            commenthistory = data['Comment Link']
                            commenthistorybody = data['Body Text']
                            responded = True
                            # matched in google sheets
                    if responded:  # Edit previous comment that we've made
                        editpost = redditlogin.comment(commenthistory)  # Get the comment to edit
                        newbody = commenthistorybody + stickybody
                        newpost = header + newbody + footer
                        editpost.edit(newpost)
                        gsnewbody = [commenthistory, str(submissionlink), str(newbody)]
                        adddata(datasheet, gsnewbody, True)
                    elif not responded:  # Create new post since we haven't made one
                        newpost = submissionlink.reply(
                            header + body + footer)  # Reply to link with header + line + footer
                        newpost.mod.distinguish(sticky=True)
                        mycommentlink = newpost.id
                        updatesheets = [mycommentlink, str(submissionlink), str(stickybody)]
                        adddata(datasheet, updatesheets, True)

        # Loop through the found posts to check their age
        for post in userposts:
            if comment.subreddit.display_name == subreddit_name:
                if TimeBackCheckerUTS < datetime.datetime.utcfromtimestamp(post.created_utc):
                    username = usertrack['Usernames']
                    thepost = 'P:', f'{datetime.datetime.utcfromtimestamp(post.created_utc)}', f'{post.id}', f'{username}', f'{post.title}', f'{post.selftext}', f'https://old.reddit.com{post.permalink}'
                    redditpost.append(thepost)
    print(f'Scan completed.')
    return redditcomment, redditpost


async def flair_helper_bot(redditlogin):
    global subreddit_name, fhblooper, fhbinterval, hellomsg
    print('Started the FHB!')

    randhello = random.choice(hellomsg)
    flairdict = {}
    fditerator = 1

    removalreason = "Your post does not have a flair.  You can assign flair to the post and " \
                    "I'll approve it, or you can reply to this comment with the following " \
                    "and I'll flair the post for you and approve it:\n\n"
    footermsg = "***\n\n*I am a bot, and this post was generated automatically. If you believe this was done in error, please contact the " \
                "[mod team](https://www\.reddit\.com/message/compose?to=%2Fr%2FEscapefromTarkov&subject=My removed submission&message=I'm writing to you about the following submission: https://old.reddit.com/r/EscapefromTarkov/comments/hwjcc9/-/. %0D%0DMy issue is...)*"

    flairmsg = ""
    for flair in redditlogin.subreddit(subreddit_name).flair.link_templates:
        flairdict[f'flair{fditerator}'] = flair['text']
        flairdict[f'flair{fditerator}class'] = flair['css_class']
        flairtext = flair['text']
        flairmsg += f'!flair{fditerator} --- {flairtext}\n\n'
        fditerator += 1

    while fhblooper:
        submissions = redditlogin.subreddit(subreddit_name).new(limit=15)
        for submission in submissions:
            if str(submission.link_flair_text).lower() == 'none':
                print('Caught a post!', submission.title, submission.link_flair_text)
                greeting = "{0} {1}!, \n\n".format(randhello, submission.author)
                commentremovalmsg = greeting + removalreason + flairmsg + footermsg  # Construct removal message
                submission.mod.remove(spam=False, mod_note="No flair", reason_id=None)  # Remove the post
                submission.mod.send_removal_message(commentremovalmsg, title='ignored', type='public')  # Send message
                # Check for the message we just sent and then log it to Google Sheets
                sentmsgs = redditlogin.redditor("ShturmanBOT").comments.new(limit=1)
                for message in sentmsgs:
                    sentmsg = message.id
                datatoadd = [submission.title, submission.id, sentmsg, submission.permalink]
                adddata(modposts, datatoadd, True)

        # Now check previous submissions to see if they've been flaired
        allmodposts = modposts.get_all_records()  # Get a list of all post Mod actions have been performed on
        print('Checking previously modded posts for updates.')
        for modaction in allmodposts:
            posthistory = modaction['ID']
            commenthistory = modaction['Comment']
            prevsubission = redditlogin.submission(posthistory)
            try:
                deletecheck = str(prevsubission.author.name)
                print(deletecheck)
                if str(prevsubission.link_flair_text).lower() != 'none':
                    print("Passed the if loop")
                    prevsubission.mod.approve()
                    redditlogin.comment(commenthistory).delete()
                    removedata(modposts, commenthistory)
                    redditlogin.submission(posthistory).report("FHB Approved - Need content check!")
                else:
                    continue
            except:
                # Deleted post, remove from mod action history
                print('User deleted post, doing cleanup...')
                removedata(modposts, commenthistory)

        print("Finished searching for post flairs.  Checking inbox")

        for item in redditlogin.inbox.unread(limit=None):
            if item.subreddit == subreddit_name and item.type == 'comment_reply':  # Check to see if comment reply is in modded subreddit
                commenthistory = str(item.parent_id).split("_")[1]
                for modactions in allmodposts:
                    if commenthistory in modactions['Comment']:  # Check to see if the reply is made in a modded post
                        posthistory = modactions['ID']
                        commenthistory = modactions['Comment']
                        prevsubission = redditlogin.submission(posthistory)
                        whichflair = str(item.body).lower().split("!")[1]  # Splits up the user reply string
                        if whichflair in flairdict:  # Checks to see if the user selected a valid post flair
                            print(flairdict[whichflair],
                                  flairdict[f'{whichflair}class'])  # Assign the post the flair and aprove it.
                            prevsubission.mod.flair(text=flairdict[whichflair],
                                                    css_class=flairdict[f'{whichflair}class'])
                            prevsubission.mod.approve()
                            redditlogin.comment(commenthistory).delete()
                            removedata(modposts, commenthistory)  # Cleanup our logging and remove the entry
                            # Report the post so it shows up in modqueue.
                            redditlogin.submission(posthistory).report("FHB Approved - Need content check!")
                            item.mark_read()  # Marks the comment reply as read so we don't act on it in the future
        print("Finished checking for flairs, going to sleep")
        await asyncio.sleep(fhbinterval)
    if not fhblooper:
        print('FHB has been halted!')


#  Need to ensure that we aren't going back and reporting on prior items.  Maybe short interval + same sleep time?
async def dupe_mod_log():
    global dmlloop, dmlinterval, subreddit_name
    StartRunTime = datetime.datetime.utcnow()
    dmlloop = True  # Determines whether or not the loop will run
    delta = datetime.timedelta(seconds=dmlinterval)
    TimeBackCheckerUTS = StartRunTime - delta
    textchannel = client.get_channel(dmlchannel)
    nickdb = []  # Establishes empty list for storing multiple dicts
    for i in textchannel.members:  # Loop through all members in the text channel and create our list
        nickdb.append({"nick": i.nick, "mention": i.mention})
    while dmlloop is True:
        modlogdict = {'Target Post': None, 'Mod': None, 'Time': None, 'Perma': None}  # Establish dict
        modloghist = []  # Establish list we want to store dict entries in
        for log in redditlogin.subreddit(subreddit_name).mod.log(limit=5):  # Grab latest moderation actions
            logactiontime = datetime.datetime.utcfromtimestamp(log.created_utc)
            if TimeBackCheckerUTS < logactiontime:  # Checks to see if the mod action has occurred in our timeframe.
                moddedpost = str(log.target_fullname).split("_")[1]
                whomod = str(log._mod)
                modlogdict['Target Post'] = moddedpost
                modlogdict['Mod'] = whomod
                modlogdict['Time'] = str(datetime.datetime.utcfromtimestamp(log.created_utc))
                modlogdict['Perma'] = log.target_permalink
                modloghist.append(
                    modlogdict.copy())  # Have to use .copy() otherwise the dictionary doesn't get copied, just a reference is created.

        dupes = {}
        # I don't know how this works, I think it checks for the duplicate 'Target Post' and then appends the Mods who
        # have performed actions on that Target Post
        for dupecheck in modloghist:
            dupes.setdefault(dupecheck['Target Post'], []).append(dupecheck['Mod'])
        duplicates = [{'Target Post': k, 'Mod': v} for k, v in dupes.items()]

        # We loop through our duplicate list
        for duplicate in duplicates:
            modlen = len(set(
                duplicate['Mod']))  # Grabs the unique mods to filter out same mod performing multiple actions on post
            if modlen > 1:  # Makes sure there's multiple unique mods working on a post.
                dupemods = set(duplicate['Mod'])  # Generates a set of unique mods on Posts that have more than 1 mod
                print(dupemods)
                nickdb = []  # Create an empty list to store mod info in
                for i in textchannel.members:
                    if i.nick is None:  # This is to catch people whose discord name matches Reddit name
                        if i.display_name in dupemods:  # Checks to see if we've got a match for duplicate mods
                            nickdb.append({"name": i.display_name, "mention": i.mention})
                    else:
                        if i.nick in dupemods:  # Checks to see if we've got a match for duplicate mods
                            nickdb.append({"name": i.nick, "mention": i.mention})
                nummods = len(nickdb)
                nummoditerate = 0
                while nummoditerate < nummods:
                    await textchannel.send("Hey {0}".format(nickdb[nummoditerate]['mention']))
                    nummoditerate += 1
                else:
                    await textchannel.send(
                        "It looks like you guys are moderating the same post: www.reddit.com{0}".format(
                            modlogdict['Perma']))
        await asyncio.sleep(dmlinterval)
    else:
        print('Dupemodlog has been halted!')


#########################################################################################################
# Discord task & functions
#########################################################################################################

# Revamp this so it can be called as it's own deal and respond directly back to the user.
# Also add the functionality when it's called to specify how far back to look and who to track.

async def reddit_loop():
    global redditlooper, nextscan, allserverdata
    while redditlooper:
        await client.wait_until_ready()
        activity = discord.Activity(name='Reddit | %about', type=discord.ActivityType.watching)
        await client.change_presence(activity=activity)
        # Call the reddit function and return info in the RedditResults variable
        redditresults = (run_bot(redditlogin))
        # First check to see if we've found any comments/posts.  Then we're going to iterate though each list, and then
        # for each iteration we have to check to see if it's a comment or post
        # Once comment/post is checked, output that.
        for op in redditresults[0]:
            if op[0] == 'C:':
                for data in allserverdata:  # Loops through each entry in our server list google doc
                    # Formatting for comment
                    # [0] is C or P, [1] is Time, [2] is post ID, [3] is Author, [4] is comment text, [5] is permalink
                    channel = client.get_channel(data["Dev Channel"])
                    await channel.send(f'{op[1]} - Found comment made by {op[3]}: "{op[4]}".  Link: {op[5]}')
        for op in redditresults[1]:
            if op[0] == 'P:':
                for data in allserverdata:  # Loops through each entry in our server list google doc
                    channel = client.get_channel(data["Dev Channel"])
                    # Formatting for post
                    # [0] is C or P, [1] is Time, [2] is post ID, [3] is Author,
                    # [4] is title text, [5] is post body, [6] is permalink
                    await channel.send(f'{op[1]} - Found "{op[4]}" post made by {op[3]}.  Link: {op[6]}')
        activity = discord.Activity(name='Waiting game | %about', type=discord.ActivityType.playing)
        await client.change_presence(activity=activity)
        print(f'Going to sleep for {SleepyTime} seconds...')
        # Global nextscan will tell us the schedule time the loop will run next
        nextscan = datetime.datetime.now() + datetime.timedelta(seconds=SleepyTime)
        await asyncio.sleep(SleepyTime)
    if not redditlooper:
        print(f'Scanning Reddit has been halted!')
        shturmanlog('Info', 'Reddit Scanner has been halted.')


#########################################################################################################
# Discord Commands
#########################################################################################################

client = commands.Bot(command_prefix='%')


@client.event
async def on_ready():
    activity = discord.Activity(name='Waiting game | %about', type=discord.ActivityType.playing)
    await client.change_presence(activity=activity)
    print('The bot is ready!')


@client.command()
async def hello(ctx):
    global hellomsg, saymsg
    randhello = random.choice(hellomsg)
    randmsg = random.choice(saymsg)
    await ctx.send('{1} {0.author.mention}! {2}'.format(ctx, randhello, randmsg))


@client.command()
async def about(ctx):
    global SleepyTime, hellomsg
    randhello = random.choice(hellomsg)
    await ctx.send(
        "{2} {0.author.mention}!  This bot is a dev tracker and moderation utility for /r/EscapeFromtTarkov\n"
        "Use %commands to get a list of all commands available".format(ctx, SleepyTime, randhello))


@client.command()
async def commands(ctx):
    global hellomsg
    randhello = random.choice(hellomsg)
    await ctx.send("{1} {0.author.mention}!  Here's a list of all commands:\n"
                   "`%getuser` - Shows a list of tracked users\n"
                   "`%adduser Xusername TRUE/FALSE` - Adds/Updates a user to the tracked user list.  TRUE/FALSE notates whether or not a sticky will be created in the thread they've posted in.\n"
                   "`%removeuser Xusername` - Removes a user from tracked user list\n\n"
                   "`%devtracker True/False` - Enables or disables dev tracking and Discord notifications\n"
                   "`%devtrackerstatus` - Shows whether or not the dev tracking and Discord notifications are running.\n"
                   "`%updatetime` - Updates the time interval for the Reddit scans\n"
                   "`%commentsticky True/False` - Enables or disables the Reddit sticky comment functionality.  References the tracked users.\n"
                   "`%commentstickystatus` - Shows whether or not the Reddit sticky comment functionality is running.\n\n"
                   "`%nextscan` - Displays next run time\n"
                   "`%devchannel add/remove` - Adds or removes a channel for Dev post notifications.\n\n"
                   "`%fhb True/False` - Enables/disables the enforcement of flairs on subreddit posts.\n"
                   "`%fhbint number` - Changes the interval of Flair Helper.\n\n"
                   "`%dml True/False` - Enables/disables checking the mod log for duplicate actions.\n\n"
                   "`%monitor` - See how hot I'm running\n"
                   "`%updatesubreddit Xsubname` - Change the subreddit that the bot performs MODERATION actions on.  This does not affect dev tracking.".format(ctx, randhello))


@client.command()
async def getuser(ctx):  # Gets a list of all users being tracked
    global usertracker, hellomsg
    randhello = random.choice(hellomsg)
    await ctx.send(
        "{1} {0.author.mention}!  I am currently tracking the following users and if 'True' "
        "I'll post a comment in threads with links to their comment.".format(ctx, randhello))
    alluserdata = usersheet.get_all_records()
    for user in alluserdata:
        await ctx.send("{0}: {1}".format(user['Usernames'], user['CommentSticky']))


@client.command()
async def adduser(ctx, arg1, arg2):  # arg1 = username, arg2 = whether or not to sticky comments in threads
    global redditlooper, usersheet, hellomsg
    randhello = random.choice(hellomsg)
    userupdate = [arg1, arg2]
    resultsadddata = adddata(usersheet, userupdate, True)
    if resultsadddata == 'Update':
        shturmanlog('Info', f'{ctx.author} Has updated {arg1} on the Reddit tracking list')
        await ctx.send(
            "{2} {0.author.mention}!  {1} has been updated on the "
            "list of users that I'll track.".format(ctx, arg1, randhello))
    if resultsadddata == 'Append':
        shturmanlog('Info', f'{ctx.author} Has added {arg1} on the Reddit tracking list')
        await ctx.send(
            "{2} {0.author.mention}!  {1} has been added to the list "
            "of users that I'll track.".format(ctx, arg1,randhello))


@client.command()
async def removeuser(ctx, arg1):  # Removes a user from the dev tracking list
    global redditlooper, usersheet, hellomsg
    randhello = random.choice(hellomsg)
    if removedata(usersheet, str(arg1)):
        shturmanlog('Info', f'{ctx.author} Has removed {arg1} from the Reddit tracking list')
        await ctx.send("{2} {0.author.mention}!  I will no longer track {1}.".format(ctx, arg1, randhello))
    else:
        await ctx.send(
            "{2} {0.author.mention}!  Double check the spelling of {1}, "
            "I couldn't find it in my list of users I'm tracking.".format(ctx, arg1, randhello))


@client.command()
async def nextscan(ctx):  # Gets the next run time for the dev tracker
    global nextscan, hellomsg
    randhello = random.choice(hellomsg)
    if nextscan == '':
        await ctx.send("{1} {0.author.mention}!  Dev tracking is not enabled.".format(ctx, randhello))
    else:
        howmuchtime = nextscan - datetime.datetime.now()
        await ctx.send(
            "{2} {0.author.mention}!  I'm going to scan Reddit again in {1}.".format(ctx, howmuchtime, randhello))


@client.command()
async def monitor(ctx):  # Raspberry Pi temperature monitoring
    global hellomsg, raspi_temp
    randhello = random.choice(hellomsg)
    if raspi_temp != 'Error':
        if raspi_temp < 50:
            await ctx.send("{2} {0.author.mention}!  I'm staying frosty ... {1}C.".format(ctx, raspi_temp, randhello))
        elif 50 < raspi_temp < 60:
            await ctx.send("{2} {0.author.mention}!  I'm warming up ... {1}C .".format(ctx, raspi_temp, randhello))
        elif 60 < raspi_temp < 70:
            await ctx.send("{2} {0.author.mention}!  I'm getting hot ... {1}C .".format(ctx, raspi_temp, randhello))
        elif 60 < raspi_temp < 70:
            await ctx.send(
                "{2} {0.author.mention}!  I'm in the danger zone ... {1}C .".format(ctx, raspi_temp, randhello))
    else:
        await ctx.send(
            "{2} {0.author.mention}!  I currently don't know how hot the "
            "Raspberry Pi is running due to an error.".format(ctx, raspi_temp, randhello))


@client.command()
async def devchannel(ctx, arg1):  # Command to change the channel of the dev tracker alert
    global hellomsg
    randhello = random.choice(hellomsg)
    friendlyserver = str(ctx.message.guild.name)
    servernameID = str(ctx.message.guild.id)
    channelnameID = str(ctx.message.channel.id)

    # Check to see if there's existing and if so, save the DML channel so we can re-add it.
    allserverdata = serversheet.get_all_records()
    iterator = 0
    dmlchannel = ''
    for data in allserverdata:
        iterator += 1
        if servernameID in data.values():
            dmlchannel = data['DML Channel'][servernameID]
            return dmlchannel
    else:
        print("No pre-existing DML channel found")

    channelupdate = [friendlyserver, servernameID, channelnameID, dmlchannel]

    if arg1.lower() == 'add':
        resultsadddata = adddata(serversheet, channelupdate, True)
        if resultsadddata == 'Update':
            shturmanlog('Info', f'{ctx.author} Has updated the channel for {friendlyserver}')
            await ctx.send(
                "{1} {0.author.mention}!  It seems a channel was already set for this server.  "
                "I've updated my records and will post notifications here now.".format(ctx, randhello))
        if resultsadddata == 'Append':
            shturmanlog('Info', f'{ctx.author} Has updated the channel for {friendlyserver}')
            await ctx.send(
                "{1} {0.author.mention}!  I've updated my records and will post "
                "notifications here now.".format(ctx, randhello))
    if arg1.lower() == 'remove':
        removechannel = removedata(serversheet, int(channelnameID))
        if removechannel:
            await ctx.send(
                "{1} {0.author.mention}!  I will no longer post notifications to this channel.".format(ctx, randhello))
        elif not removechannel:
            await ctx.send(
                "{1} {0.author.mention}!  I don't think I was posting notifications to this "
                "channel to begin with.".format(ctx, randhello))


@client.command()  # Command to turn on / off the dev comment sticky functionality
async def commentsticky(ctx, arg1):
    global devcommentsticky, hellomsg
    randhello = random.choice(hellomsg)
    if arg1.lower() == 'true':
        devcommentsticky = True
        shturmanlog('Info', f'{ctx.author} Has enabled dev comment stickies for reddit threads.')
        datatoadd = ['devcommentsticky', devcommentsticky]
        adddata(variablestorage, datatoadd, True)
        await ctx.send("{1} {0.author.mention}!  I will now create a sticky comment and update dev "
                       "replies in reddit threads.  Requires devtracking to be enabled".format(ctx, randhello))
    elif arg1.lower() == 'false':
        devcommentsticky = False
        shturmanlog('Info', f'{ctx.author} Has disabled dev comment stickies for reddit threads.')
        datatoadd = ['devcommentsticky', devcommentsticky]
        adddata(variablestorage, datatoadd, True)
        await ctx.send(
            "{1} {0.author.mention}!  I will no longer create a sticky comment and update dev replies in reddit "
            "threads.".format(ctx, randhello))
    else:
        await ctx.send("{1} {0.author.mention}!  I didn't recognize your command.".format(ctx, randhello))


@client.command()  # Gets the running status of the dev comment sticky
async def commentstickystatus(ctx):
    global devcommentsticky, hellomsg
    randhello = random.choice(hellomsg)
    if devcommentsticky:
        await ctx.send(
            "{1} {0.author.mention}!  I am currently stickying comments in Reddit threads.  FYI: This requires the "
            "devtracker to be turned on!".format(ctx, randhello))
    if not devcommentsticky:
        await ctx.send(
            "{1} {0.author.mention}!  I am currently NOT stickying comments in Reddit threads.".format(ctx, randhello))


@client.command()  # Command to turn on / off the dev tracker
async def devtracker(ctx, arg1):
    global redditlooper, hellomsg
    randhello = random.choice(hellomsg)
    if arg1.lower() == 'true':
        redditlooper = True
        shturmanlog('Info', f'{ctx.author} has enabled dev comment tracking & Discord notifications.')
        await ctx.send(
            "{1} {0.author.mention}!  I will now track dev comments and post notifications in Discord.".format(ctx,
                                                                                                               randhello))
        client.loop.create_task(reddit_loop())
    elif arg1.lower() == 'false':
        redditlooper = False
        shturmanlog('Info', f'{ctx.author} has disabled dev comment tracking & Discord notifications.')
        await ctx.send(
            "{1} {0.author.mention}!  I will no longet track dev comments and post notifications in Discord.".format(
                ctx, randhello))
    else:
        await ctx.send("{1} {0.author.mention}!  I didn't understand your command.".format(ctx, randhello))


@client.command()  # Gets the running status of the dev tracker
async def devtrackerstatus(ctx):
    global redditlooper, hellomsg
    randhello = random.choice(hellomsg)
    if redditlooper:
        await ctx.send(
            "{1} {0.author.mention}!  I am currently tracking dev comments and posting Discord notifications.".format(
                ctx, randhello))
    if not redditlooper:
        await ctx.send(
            "{1} {0.author.mention}!  I am currently NOT tracking dev comments and posting Discord notifications.".format(
                ctx, randhello))


@client.command()  # Changes the time interval for the dev tracker
async def updatetime(ctx, arg1):
    global hellomsg, TimeBackChecker, SleepyTime, redditlooper, nextscan
    randhello = random.choice(hellomsg)
    try:
        convint = int(arg1)
        TimeBackChecker = convint
        SleepyTime = TimeBackChecker
        await ctx.send(
            "{1} {0.author.mention}!  I'll now sleep for {2} between scans.".format(ctx, randhello, TimeBackChecker))
        shturmanlog('Info',
                    f'{ctx.author} updated the scan time to be {TimeBackChecker}. Stoping scans and '
                    f'sleeping for that time before starting another scan.')
        print('Attempting to stop task')
        redditlooper = False  # Sets the variable to break the loop
        updatetimeTS = nextscan - datetime.datetime.now()  # Grabs the timestamp for the next scan
        updatetimeTS = str(updatetimeTS).split(".")[0]  # Converts our timestamp to a useable format
        timestampconv = datetime.datetime.strptime(str(updatetimeTS), "%H:%M:%S")
        a_timedelta = timestampconv - datetime.datetime(1900, 1, 1)
        secondstowait = a_timedelta.total_seconds() + 1
        print('Sleeping until current task finishes:', secondstowait)
        await asyncio.sleep(secondstowait)  # Sleeps until the current loop finishes.
        redditlooper = True  # Restarts the loop again with the new time interval.
        client.loop.create_task(reddit_loop())
    except:
        await ctx.send("{1} {0.author.mention}!  Something went wrong!".format(ctx, randhello))


@client.command()  # Changes the subreddit to moderate
async def updatesubreddit(ctx, arg1):
    global hellomsg, subreddit_name
    randhello = random.choice(hellomsg)
    try:  # Catches if the subreddit doesn't exist
        exists = True
        redditlogin.subreddits.search_by_name(arg1, exact=True)
    except:
        exists = False
    if exists:
        try:  # Catches if the subreddit is privte or the bot is not a Mod.
            modlist = []
            for mod in redditlogin.subreddit(arg1).moderator():
                modlist.append(mod)
            if "ShturmanBOT" in modlist:
                shturmanlog('Info', f'{ctx.author} has changed ShturmanBOT to moderate {arg1}.')
                await ctx.send(
                    "{1} {0.author.mention}!  I will now perform actions on {2}".format(ctx, randhello, arg1))
            elif "ShturmanBOT" not in modlist:
                await ctx.send("{1} {0.author.mention}!  I'm not a mod on that subreddit.".format(ctx, randhello))
        except:
            await ctx.send("{1} {0.author.mention}!  I can't access that subreddit.".format(ctx, randhello))
    if not exists:
        await ctx.send("{1} {0.author.mention}!  Double check the spelling, "
                       "I couldn't find that subreddit.".format(ctx, randhello))


@client.command()  # Command to turn on / off flair helper bot
async def fhb(ctx, arg1):
    global hellomsg, subreddit_name, redditlogin, fhblooper
    randhello = random.choice(hellomsg)
    if arg1.lower() == 'true':
        shturmanlog('Info', f'{ctx.author} enabled flair enforcement on the subbreddit, {subreddit_name}.')
        fhblooper = True
        client.loop.create_task(flair_helper_bot(redditlogin))
        await ctx.send(
            "{1} {0.author.mention}!  I will now enforce flairs on "
            "submission in the subreddit, {2}.".format(ctx, randhello, subreddit_name))
    elif arg1.lower() == 'false':
        fhblooper = False
        shturmanlog('Info', f'{ctx.author} disabled flair enforcement on the subbreddit, {subreddit_name}.')
        await ctx.send(
            "{1} {0.author.mention}!  I will no longer enforce "
            "flairs on the subreddit, {2}.".format(ctx, randhello,subreddit_name))
    else:
        await ctx.send(
            "{1} {0.author.mention}!  I didn't recognize your command.".format(ctx, randhello, TimeBackChecker))


@client.command()  # Command to change the flairhelperbot interval
async def fhbint(ctx, arg1):
    global hellomsg, subreddit_name, redditlogin, fhblooper
    randhello = random.choice(hellomsg)
    if int(arg1):
        shturmanlog('Info', f'{ctx.author} has changed the FHB internval to , {arg1}.')
        await ctx.send(
            "{1} {0.author.mention}!  I will now check posts for flair every {2} seconds.".format(ctx, randhello, arg1))
    else:
        await ctx.send(
            "{1} {0.author.mention}!  I didn't recognize your command.".format(ctx, randhello, TimeBackChecker))


@client.command()  # Command to turn on / off the duplicate moderator log checker
async def dml(ctx, arg1):
    global hellomsg, subreddit_name, redditlogin, dmlloop
    randhello = random.choice(hellomsg)
    # Check to see if a channel is set for the server before turning on the log checker.
    allserverdata = serversheet.get_all_records()
    iterator = 0
    finder = False
    for data in allserverdata:
        iterator += 1
        if ctx.message.guild.id in data.values():
            finder = True
            return finder

    if finder is True:  # Checks to see if we've found a DML Channel
        if arg1.lower() == 'true':
            shturmanlog('Info', f'{ctx.author} enabled duplicate mod checking on the subbreddit, {subreddit_name}.')
            dmlloop = True
            client.loop.create_task(dupe_mod_log())
            await ctx.send(
                "{1} {0.author.mention}!  I will now check for duplicate moderator "
                "actions on the subreddit, {2}.".format(ctx, randhello, subreddit_name))
        elif arg1.lower() == 'false':
            dmlloop = False
            shturmanlog('Info', f'{ctx.author} disabled duplicate mod checking on the subbreddit, {subreddit_name}.')
            await ctx.send(
                "{1} {0.author.mention}!  I will no longer check for duplicate "
                "moderator actions on the subreddit, {2}.".format(ctx, randhello, subreddit_name))
        else:
            await ctx.send(
                "{1} {0.author.mention}!  I didn't recognize your command.".format(ctx, randhello, TimeBackChecker))
    elif finder is False:  # Sends a message if we don't have a DML channel for the server first
        await ctx.send("{1} {0.author.mention}!  Please set a channel using `%dmlchannel add` first, "
                       "otherwise I won't be able to report things!.".format(ctx, randhello))
    else:  # Sends a message saying we don't recognize the command.
        await ctx.send(
            "{1} {0.author.mention}!  I didn't recognize your command.".format(ctx, randhello, TimeBackChecker))


@client.command()  # Command to update the channel for the duplicate moderator log checker
async def dmlchannel(ctx, arg1):
    global hellomsg
    randhello = random.choice(hellomsg)
    friendlyserver = str(ctx.message.guild.name)
    servernameID = str(ctx.message.guild.id)
    dmlchannel = str(ctx.message.channel.id)

    # Check to see if there's existing and if so, save the dev channel so we can re-add it during the update.
    allserverdata = serversheet.get_all_records()
    iterator = 0
    devchannel = ''
    for data in allserverdata:
        iterator += 1
        if servernameID in data.values():
            devchannel = data['Dev Channel'][iterator]
            return devchannel
    else:
        print("No pre-existing dev channel found")

    channelupdate = [friendlyserver, servernameID, devchannel, dmlchannel]

    if arg1.lower() == 'add':
        resultsadddata = adddata(serversheet, channelupdate, True)
        if resultsadddata == 'Update':
            shturmanlog('Info', f'{ctx.author} Has updated the channel for {friendlyserver}')
            await ctx.send("{1} {0.author.mention}!  It seems a channel was already set for this server.  I've updated my records and will post notifications here now.".format(ctx, randhello))
        if resultsadddata == 'Append':
            shturmanlog('Info', f'{ctx.author} Has updated the channel for {friendlyserver}')
            await ctx.send("{1} {0.author.mention}!  I've updated my records and will post notifications here now.".format(ctx, randhello))
    if arg1.lower() == 'remove':
        removechannel = removedata(serversheet, int(dmlchannel))
        if removechannel == True:
            await ctx.send("{1} {0.author.mention}!  I will no longer post notifications to this channel.".format(ctx, randhello))
        elif removechannel == False:
            await ctx.send("{1} {0.author.mention}!  I don't think I was posting notifications to this channel to begin with.".format(ctx, randhello))


#########################################################################################################
# Global Configuration variables
#########################################################################################################
TimeBackChecker = 60  # Dictates how many seconds ago to check for comments
SleepyTime = TimeBackChecker  # Dictates how many seconds the script should sleep for
redditlooper = False  # True/False will stop the looper from running
nextscan = ''  # Establishing global varible to track the next run time for the Reddit Scanner
fhbinterval = 60  # Time interval for the Flair Helper Bot looper
fhblooper = True  # Determines whether or not Flair Helper Bot will run
dmlinterval = 60  # Sets the time window to see if duplicate mod actions have been taken
dmlloop = True
# dmlchannel = 734805584968417321  # The text channel that the bot will alert moderators in # Test server ATM
raspi_temp = float('40')  # Establishing a global temp float variable
subreddit_name = 'EFTDesign'
devcommentsticky = False
redditlogin = bot_login()  # Logs into reddit and provides PRAW access
#########################################################################################################
# Random messages for Discord greetings
#########################################################################################################
hellomsg = ['Привет', 'Hello', 'Hey', 'Приветик', 'What\'s up', 'Что нового', 'Yo']
saymsg = ['How are you today?', 'Pretty shit raids today, eh?', 'Have you seen my Red Rebel anywhere?',
          'Some PMC just stole my key!', 'Jaeger just put a bounty on my head, I\'ll pay you double',
          'Want to go to labs?  I got a keycard.', 'Desync seems bad today, be careful out there.',
          'Have you seen the Svetloozerskiy brothers?  They were supposed to be protecting my loot...',
          'Got any Slickers?', 'Got any Tushonka?', 'Got any Alyonka?', 'Got any TarCola?',
          'Got some mooonshine? Reshala drank all mine ... Vot khuy!', 'Stay off Woods, I\'m hunting PMCs',
          'Have you seen Jaeger\'s camp?', 'Where\'s ZB-014?  Dimon said there was some 60 round mags there.',
          'Armor is for pussies, a jacket is all you need.'
          ]

#########################################################################################################
# Fire off events
#########################################################################################################
client.loop.create_task(getCPUtemperature())
client.run(config['DISCORD']['token'])
