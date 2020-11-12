from bot import DiscordBot
import configparser

# Loads up the configparser to read our login file
config = configparser.ConfigParser()
config.read('config')

# fhb = flairhelperbot.FlairHelperBot('EFTDesign')  # Create the FHB object to do stuff with
# asyncio.run(fhb.run(True))  # Create an Asyncio task to run the FHB object

# Run our Discord Bot from the python script we've created
DiscordBot.client.run(config['DISCORD']['token'])

