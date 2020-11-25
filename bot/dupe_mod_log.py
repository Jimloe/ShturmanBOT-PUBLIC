import asyncio
import datetime
from bot import reddit
from bot import shturclass

# Authenticate to Reddit
redditauth = reddit.reddit_auth()


class DupeModLog(shturclass.Shturclass):
    mods = {'Fwopp', 'bxxxxxxxs'}

    def __init__(self, subreddit, userobj, running=False, interval=30):
        super().__init__(subreddit, running)
        self.userobj = userobj
        self.interval = interval

    async def run(self, running):
        self.running = running
        print(f'Running DML:{self.running} on {self.subreddit} with an interval of {self.interval}.')
        print('Started the DML!')

        while True:
            startruntime = datetime.datetime.utcnow()  # Establish a starting time
            delta = datetime.timedelta(seconds=self.interval)  # Create our delta time with the interval
            timebackcheckeruts = startruntime - delta  # Establish a history window
            modlogdict = {'Target Post': None, 'Mod': None, 'Time': None, 'Perma': None}  # Establish dict
            modloghist = []  # Establish list we want to store dict entries in
            print("Getting latest mod actions.")
            for loginst in redditauth.subreddit(self.subreddit).mod.log(limit=20):  # Grab latest moderation actions
                logactiontime = datetime.datetime.utcfromtimestamp(loginst.created_utc)
                modaction = False
                if timebackcheckeruts < logactiontime:  # Checks to see if the mod action has occurred in our timeframe.
                    modaction = True
                    # Setup a try block to ensure we have a valid moderator action.
                    # Need to catch mod actions that aren't related to posts/comments.
                    # Aka wiki updates, mods accepting invites, etc
                    try:
                        moddedpost = str(loginst.target_fullname).split("_")[1]
                        whomod = str(loginst._mod)
                        modlogdict['Target Post'] = moddedpost
                        modlogdict['Mod'] = whomod
                        modlogdict['Time'] = str(datetime.datetime.utcfromtimestamp(loginst.created_utc))
                        modlogdict['Perma'] = loginst.target_permalink
                        # Have to use .copy() otherwise the dictionary doesn't get copied, just a reference is created.
                        modloghist.append(modlogdict.copy())
                    except:  # Need to do better error handling for network connectivity.
                        continue
            dupes = {}
            # I don't know how this works, I think it checks for the duplicate 'Target Post' and then appends
            # the Mods who have performed actions on that Target Post
            for dupecheck in modloghist:
                dupes.setdefault(dupecheck['Target Post'], []).append(dupecheck['Mod'])
            duplicates = [{'Target Post': k, 'Mod': v} for k, v in dupes.items()]
            #  Sample duplicates output
            # [{'Target Post': 'jycpbx', 'Mod': ['ShturmanBOT', 'Fwopp']}]

            # We loop through our duplicate list
            for duplicate in duplicates:
                print("Looping through duplicates...")
                # Grabs the unique mods to filter out same mod performing multiple actions on post
                modlen = len(set(duplicate['Mod']))
                if modlen > 1:  # Makes sure there's multiple unique mods working on a post.
                    # Generates a set of unique mods on Posts that have more than 1 mod
                    dupemods = set(duplicate['Mod'])
                    print(dupemods)

                    # Check to see if mods other than ShturmanBOT have taken action on posts
                    if 'ShturmanBOT' in dupemods and len(dupemods) < 3:
                        pass
                    else:
                        # Then we need to loop through our Discord mod list and match them up
                        for usermod in self.userobj:
                            if usermod['nick'] in dupemods:  # If we found a match do things.
                                targetpost = duplicate['Target Post']  # Set target post so we can tell the mods.
                                await usermod['dmobj'].send(f'Hey!  You\'re doing double work on this post: https://www.reddit.com/r/EFTDesign/comments/{targetpost}')
                    # Example userobj output
                    # {'nick': 'Fwopp', 'mention': '<@!126756564550942721>', 'id': 126756564550942721, 'dmobj': <User id=126756564550942721 name='Jimlo' discriminator='4389' bot=False>}

            print(f'DML sleeping for {self.interval}')
            await asyncio.sleep(self.interval)
