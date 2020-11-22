import random
import asyncio
import datetime
from bot import reddit
from praw.models.util import BoundedSet
from bot import shturclass


class MediaSpam(shturclass.Shturclass):
    mods = {'Fwopp', 'bxxxxxxxs'}
    redditauth = reddit.reddit_auth()

    def __init__(self, subreddit, running=False, ignoremod=False, interval=30, removepost=False):
        super().__init__(subreddit, running, ignoremod, interval)
        self.removepost = removepost
        self.interval = interval

    async def run(self, running):
        self.running = running
        if self.running:
            newids = BoundedSet(100)  # PRAW set functionality.  Creates a set and boots out old data as needed.
            urlmatch = ["youtube.com", "twitch.tv"]
            while True:  # Create a loop so we can exit out of this via Discord command
                print("Checking subreddit for R5 submissions")
                submissions = self.redditauth.subreddit(self.subreddit).new(limit=15)  # Grab the newest 15 submissions
                startruntime = datetime.datetime.utcnow()  # Establish current run time to compare 2 day cutoff date to
                delta = datetime.timedelta(days=2)
                timecutoff = startruntime - delta
                for submission in submissions:  # Loop through each subreddit submission
                    if submission.id in newids:  # Checks to see if our item is in the set we've built
                        continue  # It has found a match, so continue to the next submission in the for loop
                    newids.add(submission.id)  # We haven't found a match above, so add it to the BoundedSet for next time
                    for url in urlmatch:  # Loop through youtube & twitch to see if we've got youtube/twitch submissions
                        if url in submission.url:  # Finds a match
                            subauthor = submission.author  # Grabs the author.  We want to check their history
                            # Create a user object and check their post history
                            for userhistory in self.redditauth.redditor(str(subauthor)).submissions.new(limit=10):
                                # Checks to see if a submission has been removed, if so we want to ignore it
                                try:
                                    if userhistory.removed is True:
                                        continue  # The post has been removed, continue on to next submission
                                except:
                                    pass  # The post has not been removed, so we want to move on to the rest of the script
                                # Checks to see if submissions are in our subreddit
                                # If they are, make sure the domain matches twitch or youtube
                                if userhistory.subreddit_name_prefixed == f'r/{self.subreddit}' and userhistory.domain == 'twitch.tv' or userhistory.domain == 'youtube.com':
                                    # Make sure that our 2 day cutoff is observed.
                                    # We also want to make sure we're not matching against the original submission.
                                    # Compare history with our original permalink
                                    if timecutoff < datetime.datetime.fromtimestamp(
                                            userhistory.created_utc) and userhistory.permalink != submission.permalink:
                                        print("match found!", userhistory.subreddit_name_prefixed, userhistory.domain,
                                              userhistory.permalink,
                                              datetime.datetime.fromtimestamp(userhistory.created_utc))
                                        #  Do things like report the post
                                        if self.removepost:  # Checks to see if we want to remove the post
                                            randhello = random.choice(self.hellomsg)
                                            bodymsg = f'{randhello},\n\nLimit posting of your own linked content to one (1) video ' \
                                                      f'every two (2) days.  Those excessively posting their own content must ' \
                                                      f'contribute to the subreddit in other ways outside of ' \
                                                      f'their own video posts.  [Your recent post](https://reddit.com{submission.permalink}) has ' \
                                                      f'been removed for violating this rule.'
                                            footermsg = f'***\n\n*I am a bot, and this post was generated automatically. ' \
                                                        f'If you believe this was done in error, please contact the ' \
                                                        f'[mod team](https://www\.reddit\.com/message/compose?to=%2Fr%2FEscapefromTarkov&subject=ShturmanBOT ' \
                                                        f'error&message=I\'m writing to you about the following submission: https://reddit.com{submission.permalink} ' \
                                                        f'%0D%0D ShturmanBOT has removed my post by mistake)*'
                                            commentremovalmsg = bodymsg + footermsg
                                            submission.mod.remove(spam=False, mod_note="No flair", reason_id=None)
                                            submission.mod.send_removal_message(commentremovalmsg, title='ignored',type='public')
                                        else:  # If we don't have post removal set, then we want to report the post.
                                            submission.report("R5 violation check!")
                print(f'Finished R5 checking, sleeping for {self.interval}')
                await asyncio.sleep(self.interval)
        elif not self.running:
            print(f'Running Media Spam Checker:{self.running} on {self.subreddit} with an interval of {self.interval}. Ignoring mod posts is set to:{self.ignoremod}')
