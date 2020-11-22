import praw
import configparser

# Loads up the configparser to read our login file
config = configparser.ConfigParser()
config.read('config')


def reddit_auth():
    # Sets up the login for Reddit
    redditlogin = praw.Reddit(username=config['LOGIN']['username'],
                              password=config['LOGIN']['password'],
                              client_id=config['LOGIN']['client_id'],
                              client_secret=config['LOGIN']['client_secret'],
                              user_agent=config['LOGIN']['user_agent'])
    return redditlogin


def verify_mod(whotoverify):
    modset = set()
    redditauth = reddit_auth()  # Create the authenticator object to access reddit
    for moderator in redditauth.subreddit('EscapefromTarkov').moderator():  # Generates a set of all moderators on the sub.
        modset.add(moderator.name)
    print(modset)
    if whotoverify in modset:
        return True
    else:
        return False


def get_all_mods():
    moderatorset = set()
    redditauth = reddit_auth()  # Create the authenticator object to access reddit
    for moderator in redditauth.subreddit('EscapefromTarkov').moderator():  # Generates a set of all moderators on the sub.
        moderatorset.add(moderator)
