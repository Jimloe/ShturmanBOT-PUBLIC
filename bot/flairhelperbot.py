import random
import asyncio
import datetime
from bot import reddit
from bot import shturclass
from bot import Google_Logger

# Authenticate to Reddit
redditauth = reddit.reddit_auth()

hellomsg = ['Привет', 'Hello', 'Hey', 'Приветик', 'What\'s up', 'Что нового', 'Yo']
saymsg = ['How are you today?', 'Pretty shit raids today, eh?', 'Have you seen my Red Rebel anywhere?',
          'Some PMC just stole my key!', 'Jaeger just put a bounty on my head, I\'ll pay you double',
          'Want to go to labs?  I got a keycard.', 'Desync seems bad today, be careful out there.',
          'Have you seen the Svetloozerskiy brothers?  They were supposed to be protecting my loot...',
          'Got any Slickers?', 'Got any Tushonka?', 'Got any Alyonka?', 'Got any TarCola?',
          'Got some mooonshine? Reshala drank all mine ... Vot khuy!', 'Stay off Woods, I\'m hunting PMCs',
          'Have you seen Jaeger\'s camp?', 'Where\'s ZB-014?  Dimon said there was some 60 round mags there.',
          'Armor is for pussies, a jacket is all you need.']


class FlairHelperBot(shturclass.Shturclass):
    mods = {'Fwopp', 'bxxxxxxxs'}

    def __init__(self, subreddit, running=False, ignoremod=False, interval=60):
        super().__init__(subreddit, running, ignoremod, interval)

    async def run(self, running):
        self.running = running
        if self.running:
            print(f'Running FHB:{self.running} on {self.subreddit} with an interval of {self.interval}. Ignoring mod posts is set to:{self.ignoremod}')
            print('Started the FHB!')

            randhello = random.choice(hellomsg)
            flairdict = {}
            fditerator = 1

            removalreason = "Your post does not have a flair.  You can assign flair to your post and " \
                            "I'll approve it, or you can reply to this comment with the following " \
                            "and I'll flair the post for you and approve it.\n\n" \
                            "Reply with this | Flair/Category\n" \
                            ":-------:|----------\n"
            flairmsg = ""

            for flair in redditauth.subreddit(self.subreddit).flair.link_templates:
                flairdict[f'flair{fditerator}'] = flair['text']
                flairdict[f'flair{fditerator}class'] = flair['css_class']
                flairtext = flair['text']
                flairmsg += f'!flair{fditerator}|```{flairtext}```\n'
                fditerator += 1

            while True:  # Always loop this
                print("Starting Loop!")
                nettest = False
                while not nettest:
                    try:
                        submissions = redditauth.subreddit(self.subreddit).new(limit=15)  # Grab the newest 15 submissions
                        nettest = True
                    except Exception as e:
                        print(f'{e} ||| Trying again in 5s')
                        await asyncio.sleep(5)
                for submission in submissions:  # Loop through each one
                    if str(submission.link_flair_text).lower() == 'none':
                        if self.ignoremod and submission.author in self.mods:
                            continue
                        else:
                            print('Caught a post!', submission.title, submission.link_flair_text)
                            fhbtime = str(datetime.datetime.utcnow().timestamp()).split(".")[0]
                            greeting = "{0} {1}!, \n\n".format(randhello, submission.author)
                            footermsg = "***\n\n*I am a bot, and this post was generated automatically. If you believe this was done in error, please contact the " \
                                        "[mod team](https://www\.reddit\.com/message/compose?to=%2Fr%2FEscapefromTarkov&subject=ShturmanBOT " \
                                        "error&message=I'm writing to you about the following submission: https://old.reddit.com{0}. " \
                                        "%0D%0D ShturmanBOT has removed my post by mistake)*".format(submission.permalink)
                            commentremovalmsg = greeting + removalreason + flairmsg + footermsg  # Construct removal message
                            submission.mod.remove(spam=False, mod_note="No flair", reason_id=None)  # Remove the post
                            submission.mod.send_removal_message(commentremovalmsg, title='ignored', type='public')  # Send message
                            # Check for the message we just sent and then log it to Google Sheets
                            sentmsgs = redditauth.redditor("ShturmanBOT").comments.new(limit=1)
                            for message in sentmsgs:
                                sentmsg = message.id
                            datatoadd = [submission.title, submission.id, sentmsg, submission.permalink, fhbtime]
                            await Google_Logger.adddata('ModeratedPosts', datatoadd, True)
                # Now check previous submissions to see if they've been flaired
                allmodposts = await Google_Logger.get_data('ModeratedPosts')  # Get a list of all post Mod actions have been performed on
                deletedthings = False
                print('Checking previously modded posts for updates.')
                for modaction in allmodposts:
                    print("Checking: ", modaction)
                    posthistory = modaction['ID']
                    commenthistory = modaction['Comment']
                    subpermalink = modaction['Permalink']
                    modtime = datetime.datetime.fromtimestamp(int(modaction['Time']))  # Grab the time the post was modded
                    prevsubission = redditauth.submission(posthistory)
                    deletedthings = False
                    try:  # Check to see if user has deleted the post.
                        print(f'Trying to see if {modaction} has been deleted')
                        deletecheck = str(prevsubission.author.name)
                        print(f'It has not been deleted: {deletecheck}')
                    except:  # User deleted post, remove from mod action history
                        print('User deleted post, doing cleanup...')
                        await Google_Logger.removedata('ModeratedPosts', commenthistory)
                        deletedthings = True
                    finally:
                        if deletedthings is False:
                            rightnow = datetime.datetime.utcnow()
                            delta = datetime.timedelta(seconds=1200)  # Delta time is 20 minutes
                            cutofftime = modtime + delta  # Take the post modded time and add 20 minutes to it
                            if str(prevsubission.link_flair_text).lower() != 'none':  # Checks to see if there's any flair.
                                prevsubission.mod.approve()
                                redditauth.comment(commenthistory).delete()
                                await Google_Logger.removedata('ModeratedPosts', commenthistory)
                                redditauth.submission(posthistory).report("FHB Approved - Need content check!")
                            elif rightnow > cutofftime:  # Checking to see if the post is older than 20m.  If so delete!
                                print("Time exceeded on the post, removing and leaving comment")
                                editpost = redditauth.comment(commenthistory)  # Get the comment to edit
                                newbody = "Sorry, your recent post still does not have any flair and was " \
                                          "permanently removed. Feel free to resubmit your post and remember " \
                                          "to flair it once it is posted."
                                footermsg = "***\n\n*I am a bot, and this post was generated automatically. If you believe this was done in error, please contact the " \
                                            "[mod team](https://www\.reddit\.com/message/compose?to=%2Fr%2FEscapefromTarkov&subject=ShturmanBOT " \
                                            "error&message=I'm writing to you about the following submission: https://old.reddit.com{0}. " \
                                            "%0D%0D ShturmanBOT has removed my post by mistake)*".format(subpermalink)
                                newpost = newbody + footermsg
                                editpost.edit(newpost)
                                await Google_Logger.removedata('ModeratedPosts', commenthistory)
                                deletedthings = True
                            else:
                                continue
                print("Finished checking old posts.")
                if deletedthings:
                    allmodposts = await Google_Logger.get_data('ModeratedPosts')  # Update our list because we've deleted things.
                    print("Checking inbox")
                    for item in redditauth.inbox.unread(limit=None):  # Loop through each item in our inbox
                        if item.subreddit == self.subreddit and item.type == 'comment_reply':  # Check to see if comment reply is in modded subreddit
                            commenthistory = str(item.parent_id).split("_")[1]
                            for modactions in allmodposts:
                                if commenthistory in modactions['Comment']:  # Check to see if the reply is made in a modded post
                                    posthistory = modactions['ID']
                                    commenthistory = modactions['Comment']
                                    prevsubission = redditauth.submission(posthistory)
                                    whichflair = str(item.body).lower().split("!")[1]  # Splits up the user reply string
                                    if whichflair in flairdict:  # Checks to see if the user selected a valid post flair
                                        # Assign the post the flair and aprove it.
                                        prevsubission.mod.flair(text=flairdict[whichflair], css_class=flairdict[f'{whichflair}class'])
                                        prevsubission.mod.approve()
                                        redditauth.comment(commenthistory).delete()  # Delete Shturmans comment
                                        await Google_Logger.removedata('ModeratedPosts', commenthistory)  # Cleanup our logging and remove the entry
                                        # Report the post so it shows up in modqueue.
                                        redditauth.submission(posthistory).report("FHB Approved - Need content check!")
                                        item.mark_read()  # Marks the comment reply as read so we don't act on it in the future
                                else:  # Ignore the message as we don't care about it.
                                    item.mark_read()
                del submissions, submission, allmodposts, deletedthings
                print(f'Finished scanning for posts, sleeping for {self.interval}')
                await asyncio.sleep(self.interval)

        elif not self.running:
            print(f'Running FHB:{self.running} on {self.subreddit} with an interval of {self.interval}. Ignoring mod posts is set to:{self.ignoremod}')
