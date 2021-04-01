import random
import asyncio
import datetime
from bot import reddit
from praw.models.util import BoundedSet
from bot import shturclass

# Authenticate to Reddit
redditauth = reddit.reddit_auth()


class MediaSpam(shturclass.Shturclass):
    mods = {'Fwopp', 'bxxxxxxxs'}

    def __init__(self, subreddit, running=False, ignoremod=False, interval=30, action='report'):
        super().__init__(subreddit, running, ignoremod, interval)
        self.action = action
        self.interval = interval

    async def run(self, running):
        self.running = running
        removalreason = "Limit posting of linked content to once every 48 hours. Rule 5 applies  " \
                        "to whether or not you made the content you’re submitting. \n\n"
        subredditstring = f'r/{self.subreddit}'

        if self.running:
            randhello = random.choice(self.hellomsg)
            newids = BoundedSet(100)  # PRAW set functionality.  Creates a set and boots out old data as needed.
            urlmatch = ["youtube.com", "twitch.tv", "youtu.be"]
            while True:  # Create a loop so we can exit out of this via Discord command
                nettest = False
                while not nettest:
                    try:
                        print(f"Checking new submissions.")
                        for post in redditauth.subreddit(self.subreddit).new(limit=10):
                            if post.permalink in newids:  # Checks to see if our item is in the set we've built
                                continue  # It has found a match, so continue to the next submission in the for loop
                            print(f'Submission:{post.title} isn\'t in new IDs, so lets add it and then check it.')
                            newids.add(
                                post.permalink)  # We haven't found a match above, so add it to the BoundedSet for next time
                            for url in urlmatch:  # Loop through youtube & twitch to see if we've got youtube/twitch submissions
                                if url in post.url:  # Finds a match
                                    caughtpost = post.permalink  # Store post in a variable so we can make sure we're not catching it later.
                                    print(f'Found a youtube/twitch link: {post.title}')
                                    subauthor = post.author  # Grabs the author.  We want to check their history.
                                    # Grabs the time of the post.
                                    oppostime = datetime.datetime.fromtimestamp(post.created_utc)
                                    delta = datetime.timedelta(days=2)
                                    timecutoff = oppostime - delta
                                    # Create a user object and check their post history
                                    print(f'Checking the history of {subauthor}')
                                    for userhistory in redditauth.redditor(str(subauthor)).submissions.new(limit=10):
                                        # Checks to see if a submission has been removed, if so we want to ignore it
                                        try:
                                            if userhistory.removed is True:
                                                continue  # The post has been removed, continue on to next submission
                                        except:
                                            pass  # The post has not been removed, so we want to move on to the rest of the script
                                        # Checks post time to make sure we're not going too far back and doing excess checking.
                                        historyposttime = datetime.datetime.fromtimestamp(userhistory.created_utc)
                                        print(f'Checking post:"{userhistory.title}"')
                                        print(f'Is post time: {historyposttime} between the cutoff: {timecutoff} and now?')
                                        if datetime.datetime.fromtimestamp(userhistory.created_utc) < timecutoff:
                                            print(f'Outside our time window, stopping.')
                                            break
                                        # Checks to see if submissions are in our subreddit
                                        # If they are, make sure the domain matches twitch or youtube
                                        if str(userhistory.subreddit_name_prefixed) == str(subredditstring) and userhistory.domain in urlmatch:
                                            print(f'Found a potential match in the {self.subreddit}, checking if it is the OP')
                                            # We want to make sure we're not matching against the original submission.
                                            if userhistory.permalink != caughtpost:
                                                print(f'We found a match: "{userhistory.title}"')
                                                #  Do things like report the post
                                                if self.action == 'remove':  # Checks to see if we want to remove the post
                                                    print('Found one, going to remove the post and leave a message.')
                                                    greeting = "{0} {1}! \n\n".format(randhello, post.author)
                                                    footermsg = "***\n\n*I am a bot, and this post was generated automatically. If you believe this was done in error, please contact the " \
                                                                "[mod team](https://www\.reddit\.com/message/compose?to=%2Fr%2FEscapefromTarkov&subject=ShturmanBOT " \
                                                                "error&message=I'm writing to you about the following submission: https://reddit.com{0}. " \
                                                                "%0D%0D ShturmanBOT has removed my post by mistake)*".format(post.permalink)
                                                    commentremovalmsg = greeting + removalreason + footermsg  # Construct removal message
                                                    post.mod.remove(spam=False, mod_note="No flair", reason_id=None)  # Remove the post
                                                    post.mod.send_removal_message(commentremovalmsg, title='ignored', type='public')  # Send message

                                                else:  # If we don't have post removal set, then we want to report the post.
                                                    print(f'Reporting the post: "{post.title}"')
                                                    post.report(f'R5 violation check!: {userhistory.id}')
                                                    break
                                            else:
                                                print(f'"{userhistory.title}" is the OP, skipping it')
                                        else:
                                            print(f'"{userhistory.title}" is not a media link or within the sub.')
                            print("\n")
                        print("Finished searching, sleeping for 30 seconds")
                        nettest = True
                        await asyncio.sleep(self.interval)
                    except:
                        print(f'FHB couldn\'t connect || Trying again in 5s')
                        await asyncio.sleep(5)
        elif not self.running:
            print(f'Running Media Spam Checker:{self.running} on {self.subreddit} with an interval of {self.interval}. Ignoring mod posts is set to:{self.ignoremod}')
