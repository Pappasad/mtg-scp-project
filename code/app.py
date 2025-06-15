from pycards import Cards
from database import CardDatabase
import os
import sys
import img_manager as im
from ui import Interface
from datetime import datetime
import deckMaker as dm
import pandas as pd
from printing import createPDF
from ci import IDENTITY_MAP
from tts import createCardSheet
import ccInterface as ccI

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
    global app
    app = QApplication(args)

    interface = Interface(save_logs=True)
    interface.initialize()
    interface.addButton("Fix Img Paths", fixImgs)
    interface.addButton("Find Incongruencies", findWeirdge)
    interface.addButton("Color ID Stats", getColorIDStats)
    interface.addButton("Theme Stats", getThemeStats)
    interface.addButton("Update Themes Manual", addManualThemes)
    # interface.addButton("Update Themes Auto", addAutoThemes)
    interface.addButton("Reload", reload)
    interface.addButton("Type Stats", getTypeStats)
    interface.addButton('Get Card', getCardInfo, interface)
    interface.addButton("Change Cards", changeCards)
    interface.addButton("Create Cards", createNewCards)

    interface.show()

    sys.exit(app.exec())

### Functions For Manager.exe ###
def changeCards():
    print(timeString())
    try:
        ccI.changeCards()
    except Exception as e:
        print(e)
    print("Done.")

def createNewCards():
    print(timeString())
    try:
        ccI.chooseAndExport()
    except Exception as e:
        raise(e)
    print("Done.")

def getCardInfo(interface):
    print(timeString())
    try:
        name = interface.input
        card = Database[name]
        for key, val in card.items():
            if key != 'Rules Text':
                print(f'\t{key}: {val}')
    except Exception as e:
        print(f"Cant get card :'{name}'")
    print('Done.')

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

def launchDeckMaker(args):
    from PySide6.QtWidgets import QApplication
    global app
    app = QApplication(args)
    card_names = list(Database['Title'])

    global Deckmaker
    Deckmaker = dm.DeckManager(card_names, app)
    Deckmaker.addButton('Reload', reload)
    Deckmaker.addButton('clear', Deckmaker.clearLayout)
    Deckmaker.addButton('New Deck', createDeck)
    Deckmaker.addButton('Load Deck', loadDeck)
    Deckmaker.addButton('Save Deck', saveDeck)
    Deckmaker.addButton('Add Card', addCardToDeck)
    Deckmaker.addButton("Remove Card", removeCardFromDeck)
    Deckmaker.addButton("Search Cards", displayCards)
    Deckmaker.addButton("Deck Stats", getDeckStats)
    Deckmaker.addButton("Add Basics", addLands)
    Deckmaker.addButton("Add Ramp", addRamp)
    Deckmaker.addButton("Set Commander", setCommander)
    Deckmaker.addButton("Print", create_PDF)
    Deckmaker.addButton("Create TTS", create_TTS)

    Deckmaker.show()

    sys.exit(app.exec())


### Functions for Deck Maker ###
def createPath(card):
    if 'Dimension' in card['Type']:
        directory = 'dim'
    elif 'Token' in card['Type']:
        directory = 'tokens'
    elif card['Title']+'.png' in os.listdir(os.path.join('cards', 'orgs and commanders')):
        directory = 'orgs and commanders'
    else:
        directory = 'scp'

    return os.path.join('cards', directory, card['Title']+'.png')

def getCardImg():
    card = Database[Deckmaker.input]
    if card is None:
        return
    
    path = createPath(card)
    return path

def createDeck():
    Deckmaker.newDeck()
    print(f"Created new deck: {Deckmaker.deck.name}")

def saveDeck():
    if Deckmaker.deck is None:
        print("<<<ERROR>>> No deck.")
        return
    
    Deckmaker.deck.save()
    print(f"Saved deck: {Deckmaker.deck.name}")

def loadDeck():
    Deckmaker.loadDeck(Deckmaker.input)
    print(f"Loaded deck: {Deckmaker.deck.name}")

def addCardToDeck():
    card_path = getCardImg()
    if card_path is None:
        return
    elif Deckmaker.deck is None:
        print("<<<ERROR>>> No deck.")
        return
    elif Deckmaker.input in Deckmaker.deck:
        print("<<<ERROR>>> Already in deck.")
        return
    card = Cards.from_data(Database[Deckmaker.input])
    Deckmaker.deck.addCard(card, card_path)
    Deckmaker.displayCard(card_path)
    print(f"Added {Deckmaker.input} to deck {Deckmaker.deck.name}")

def removeCardFromDeck():
    name = Deckmaker.input
    if Deckmaker.removeCard(name):
        print(f"Removed {Deckmaker.input} from deck {Deckmaker.deck.name}")

def displayCards():
    args = tuple(arg.strip().replace('_', ' ') for arg in Deckmaker.input.split())
    if len(args) != 3:
        print("<<<ERROR>>> Search Cards Requires 3 Arguments")
        return
    
    cards = Database[args]
    card_paths = cards.apply(createPath, axis=1)
    Deckmaker.displayMultiple(list(card_paths))

def getDeckStats():
    if Deckmaker.deck is None:
        print("<<<ERROR>>> No deck.")
        return
    
    cards = Deckmaker.deck.cards

    # Filter for removal cards (assuming you want rows where a specific condition is True)
    removal = [card for card in cards if 'Removal' in card['Themes']]

    # Filter for cards with the "Card-Draw" theme
    card_draw = [card for card in cards if 'Card-Draw' in card['Themes']]

    # Filter for cards with the "Ramp" theme
    ramp = [card for card in cards if 'Ramp' in card['Themes']]

    # Filter for cards of type "Land"
    lands = [card for card in cards if 'Land' in card['Type']]


    print(Deckmaker.deck.name)
    if Deckmaker.input.lower() == 'removal':
        for card in removal: print(card)
    elif Deckmaker.input.lower() == 'card-draw':
        for card in card_draw: print(card)
    elif Deckmaker.input.lower() == 'ramp':
        for card in ramp: print(card)
    elif Deckmaker.input.lower() == 'land':
        for card in lands: print (card)
    else:
        print(f'Removal: {len(removal)}')
        print(f'Card-Draw: {len(card_draw)}')
        print(f'Ramp: {len(ramp)}')
        print(f'Lands: {len(lands)}')
        print(f'Total: {len(Deckmaker.deck)}')

def addRamp():
    Deckmaker.deck.addRamp()
    print(f"Added ramp to {Deckmaker.deck.name}")

def addLands():
    Deckmaker.deck.addBasics()
    print(f"Added basics to {Deckmaker.deck.name}")

def setCommander():
    commander = Cards.from_data(Database[Deckmaker.input])
    Deckmaker.deck.setCommander(commander)

def create_PDF():
    if Deckmaker.deck is None:
        print("<<<ERROR>>> No deck.")
        return
    
    createPDF(Deckmaker.deck.name)
    print(f"Created PDF for deck {Deckmaker.deck.name}")

def create_TTS():
    if Deckmaker.deck is None:
        print("<<<ERROR>>> No deck.")
        return

    name = Deckmaker.deck.name
    paths = Deckmaker.deck.img_paths
    createCardSheet(paths, name)


def test():
    # from PySide6.QtWidgets import QApplication
    # app = QApplication(sys.argv)
    # card_names = list(Database['Title'])
    # deckmanager = dm.DeckManager(card_names)
    # deckmanager.loadDeck('Spiders')
    # deckmanager.deck.addRamp()
    # deckmanager.deck.addBasics()
    # deckmanager.deck.save()
    launchManager(sys.argv)


if __name__ == '__main__':
    # Entry point for standalone execution
    init()
    if len(sys.argv) <= 1:
        test()
    elif sys.argv[1] == 'manager':
        launchManager(sys.argv)
    elif sys.argv[1] == 'deck-creator':
        launchDeckMaker(sys.argv)
   

