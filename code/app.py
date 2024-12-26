from cards import Cards, IDENTITY_MAP
from database import CardDatabase
import os
import sys
import img_manager as im
from ui import Interface
from datetime import datetime

SHEET = "mtgscp"
CC_DIR = 'cc'
THEMES = ['Sarkic', 'Wondertainment', 'Foundation', 'Goc', 'AWCY?', 'Fifthist', 'MC&D', 'Insurgency', 'Broken-God', 'Serpents', 'Removal', 'Ramp', 'Card-Draw']

def init():
    global Database
    Database = CardDatabase(SHEET)

def getCards(key):
    return Cards.from_data(Database[key])

def timeString():
    return datetime.now().strftime("<%a %m-%d-%Y %I:%M %p> ")

def launchManager(args):
    from PySide6.QtWidgets import QApplication
    app = QApplication(args)

    interface = Interface(save_logs=True)
    interface.addButton("Fix Img Paths", fixImgs)
    interface.addButton("Find Incongruencies", findWeirdge)
    interface.addButton("Color ID Stats", getColorIDStats)
    interface.addButton("Theme Stats", getThemeStats)
    interface.addButton("Update Themes Manual", addManualThemes)
    #interface.addButton("Update Themes Auto", addAutoThemes)
    interface.addButton("Reload", reload)
    interface.addButton("Type Stats", getTypeStats)

    interface.show()

    sys.exit(app.exec())

### Functions For Manager.exe ###
def reload():
    print(timeString() + "Reloading...")
    init()
    print("Done.")

def fixImgs():
    print(timeString() + "Correcting Img Paths...")
    im.correctImgPaths()
    print("Done.")

def findWeirdge():
    print(timeString() + "Finding Incongruencies...")
    titles = list(Database['Title'])
    im.findIncongruencies(titles)
    print("Done.")

def getColorIDStats():
    print(timeString() + "Getting Color ID Stats...")
    for cid in IDENTITY_MAP.values():
        num = len(getCards(('Color Identity', '==', cid)))
        print(f"{num} {cid}")
    print("Done.")

def getThemeStats():
    print(timeString() + "Getting Theme Stats...")
    for theme in THEMES:
        num = len(getCards(('Themes', '==', theme)))
        print(f"{num} {theme}")
    print("Done.")

def getTypeStats():
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
        print(f"{v} {k}")
    print("Done.")

def addManualThemes():
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


if __name__ == '__main__':
    init()
    launchManager(sys.argv)
elif __name__.lower() == 'manager':
    init()
    launchManager(sys.argv)