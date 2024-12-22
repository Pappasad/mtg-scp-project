from cards import Cards, IDENTITY_MAP
from database import CardDatabase
import os
import pandas as pd
import img_manager as im

SHEET = "mtgscp"
CC_DIR = 'cc'

Database = CardDatabase(SHEET)

def main():
    global Database
    Database = CardDatabase(SHEET)
    for cc in os.listdir(CC_DIR):
        path = os.path.join(CC_DIR, cc)
        cards = Cards(path)

        for card in cards:
            Database[card['Title']] = card

    Database.update()

def fixImgs():
    im.correctImgPaths()

def findWeirdge():
    im.correctImgPaths()
    titles = list(Database['Title'])
    im.findIncongruencies(titles)

def cardRoutine1():
    cards = getCards(('Color Identity', '==', 'Colorless'))
    cards.printCards()

def getColorIDStats():
    for cid in IDENTITY_MAP.values():
        num = len(getCards(('Color Identity', '==', cid)))
        print(f"{num} {cid}")

def getCards(key):
    return Cards.from_data(Database[key])


if __name__ == '__main__':
    main()
    getColorIDStats()