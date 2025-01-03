from cards import Cards, IDENTITY_MAP
from database import CardDatabase
import os
import sys
import img_manager as im
from ui import Interface
from datetime import datetime

# Name of the Google Sheet to use as the database
SHEET = "mtgscp"

# Directory for custom card data
CC_DIR = 'cc'

# Themes used in the application
THEMES = ['Sarkic', 'Wondertainment', 'Foundation', 'Goc', 'AWCY?', 'Fifthist', 'MC&D', 'Insurgency', 'Broken-God', 'Serpents', 'Removal', 'Ramp', 'Card-Draw']

def init():
    """
    Initializes the global database object by connecting to the specified Google Sheet.
    """
    global Database
    Database = CardDatabase(SHEET)

def getCards(key):
    """
    Retrieves cards from the database based on a specific key or filter condition.

    :param key: Key or filter condition to query the database.
    :return: Cards object containing the filtered data.
    """
    return Cards.from_data(Database[key])

def timeString():
    """
    Generates a timestamp string for logging purposes.

    :return: Current timestamp as a formatted string.
    """
    return datetime.now().strftime("<%a %m-%d-%Y %I:%M %p> ")

def launchManager(args):
    """
    Launches the graphical user interface (GUI) for managing card data.

    :param args: Command-line arguments.
    """
    from PySide6.QtWidgets import QApplication
    app = QApplication(args)

    interface = Interface(save_logs=True)
    interface.addButton("Fix Img Paths", fixImgs)
    interface.addButton("Find Incongruencies", findWeirdge)
    interface.addButton("Color ID Stats", getColorIDStats)
    interface.addButton("Theme Stats", getThemeStats)
    interface.addButton("Update Themes Manual", addManualThemes)
    # interface.addButton("Update Themes Auto", addAutoThemes)
    interface.addButton("Reload", reload)
    interface.addButton("Type Stats", getTypeStats)

    interface.show()

    sys.exit(app.exec())

### Functions For Manager.exe ###
def reload():
    """
    Reloads the database and updates the application state.
    """
    print(timeString() + "Reloading...")
    init()
    print("Done.")

def fixImgs():
    """
    Corrects the file paths of images by renaming them to a consistent format.
    """
    print(timeString() + "Correcting Img Paths...")
    im.correctImgPaths()
    print("Done.")

def findWeirdge():
    """
    Identifies and logs discrepancies between the database and image files.
    """
    print(timeString() + "Finding Incongruencies...")
    titles = list(Database['Title'])
    im.findIncongruencies(titles)
    print("Done.")

def getColorIDStats():
    """
    Logs the count of cards for each color identity.
    """
    print(timeString() + "Getting Color ID Stats...")
    for cid in IDENTITY_MAP.values():
        num = len(getCards(('Color Identity', '==', cid)))
        print(f"\t{num} {cid}")
    print("Done.")

def getThemeStats():
    """
    Logs the count of cards for each theme.
    """
    print(timeString() + "Getting Theme Stats...")
    for theme in THEMES:
        num = len(getCards(('Themes', '==', theme)))
        print(f"{num} {theme}")
    print("Done.")

def getTypeStats():
    """
    Logs the count of cards for each type, including a count of non-legendary cards.
    """
    print(timeString() + "Getting Type Stats...")
    types = {}
    for type_str in Database['Type']:
        type_list = type_str.strip().split()
        for t in type_list:
            if t in types:
                types[t] += 1
            else:
                types[t] = 1
    types['Non-Legendary'] = len(getCards(('Type', '!=', 'Legendary')))

    types = dict(sorted(types.items()))

    for k, v in types.items():
        print(f"\t{v} {k}")
    print("Done.")

def addManualThemes():
    """
    Updates the database with manually assigned themes for cards.
    """
    print(timeString() + "Adding Manual Themes...")
    global Database
    Database = CardDatabase(SHEET)
    for cc in os.listdir(CC_DIR):
        path = os.path.join(CC_DIR, cc)
        cards = Cards(path, themes='Manual')

        for card in cards:
            Database[card['Title']] = card

    Database.update()
    print("Done.")

def addAutoThemes():
    """
    Updates the database with automatically assigned themes for cards (not implemented).
    """
    print(timeString() + "Adding Auto Themes...")
    global Database
    Database = CardDatabase(SHEET)
    for cc in os.listdir(CC_DIR):
        path = os.path.join(CC_DIR, cc)
        cards = Cards(path, themes='Auto')

        for card in cards:
            Database[card['Title']] = card

    Database.update()
    print("Done.")
### End of Functions For Manager.exe ###


def test():
    cards = Cards.from_data(Database)
    misters = [card for card in cards if 'Mr.' in card['Title']]
    print(misters[0]['Rules Text'].lower(), '\n\n')
    print(misters[0].getThemesMan())


if __name__ == '__main__':
    # Entry point for standalone execution
    init()
    if len(sys.argv) <= 1:
        test()
    elif sys.argv[1] == 'manager':
        launchManager(sys.argv)
   

