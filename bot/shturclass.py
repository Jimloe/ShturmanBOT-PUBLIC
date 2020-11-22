class Shturclass(object):
    mods = {'Fwopp', 'bxxxxxxxs'}
    hellomsg = ['Привет', 'Hello', 'Hey', 'Приветик', 'What\'s up', 'Что нового', 'Yo']
    saymsg = ['How are you today?', 'Pretty shit raids today, eh?', 'Have you seen my Red Rebel anywhere?',
              'Some PMC just stole my key!', 'Jaeger just put a bounty on my head, I\'ll pay you double',
              'Want to go to labs?  I got a keycard.', 'Desync seems bad today, be careful out there.',
              'Have you seen the Svetloozerskiy brothers?  They were supposed to be protecting my loot...',
              'Got any Slickers?', 'Got any Tushonka?', 'Got any Alyonka?', 'Got any TarCola?',
              'Got some mooonshine? Reshala drank all mine ... Vot khuy!', 'Stay off Woods, I\'m hunting PMCs',
              'Have you seen Jaeger\'s camp?', 'Where\'s ZB-014?  Dimon said there was some 60 round mags there.',
              'Armor is for pussies, a jacket is all you need.']

    def __init__(self, subreddit, running=False, ignoremod=False, interval=60):
        self.subreddit = subreddit
        self.ignoremod = ignoremod
        self.interval = interval
        self.running = running

    def ignoremod(self, ignoremod):
        self.ignoremod = ignoremod

    def interval(self, interval):
        self.interval = interval

    @classmethod
    def add_mod(cls, moderator):
        return cls.mods.add(moderator)

    @classmethod
    def remove_mod(cls, moderator):
        return cls.mods.remove(moderator)
