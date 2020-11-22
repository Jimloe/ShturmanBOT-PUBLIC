import configparser
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Loads up the configparser to read our login file
config = configparser.ConfigParser()
config.read('config')

#########################################################################################################
# Google Sheets information to remotely store data
#########################################################################################################
googlescope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
               "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("ShturmanBOTcreds.json", googlescope)
googleclient = gspread.authorize(creds)
spreadsheet = googleclient.open("ShturmanBOTSheets")  # Open the spreadsheet


def get_data(sheetname):
    individualsheet = spreadsheet.worksheet(sheetname)
    founddata = individualsheet.get_all_records()
    return founddata


def adddata(sheetname, datatoadd, dupecheck):
    sheetobject = spreadsheet.worksheet(sheetname)
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


def removedata(sheetname, datatoremove):  # Need to update function so it doesn't kill off the entire row and just the specific occurance, if requested.
    sheetobject = spreadsheet.worksheet(sheetname)
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

# Old variables for reference
# serversheet = spreadsheet.worksheet('Servers')  # Server spreadsheet
# loggingsheet = spreadsheet.worksheet('Logging')  # Logging spreadsheet
# datasheet = spreadsheet.worksheet('Data')  # Comment sticky functionality
# usersheet = spreadsheet.worksheet('Users')  # User spreadsheet
# modposts = spreadsheet.worksheet('ModeratedPosts')  # User spreadsheet
# variablestorage = spreadsheet.worksheet('Variable Storage')  # Long term storage of variables.
# Get a list of all server records, required for reddit_loop function
# allserverdata = serversheet.get_all_records()
# alluserdata = usersheet.get_all_records()  # Get a list of all user records, required for run_bot function.
# allvariables = variablestorage.get_all_records()  # Get a list of all variable records.
# allmodposts = modposts.get_all_records()    # Get a list of all post Mod actions have been performed on
