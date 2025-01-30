import os
from ui import Interface
from cards import Cards, IDENTITY_MAP, REVERSE_MAP
import shutil
import PySide6.QtWidgets as Widgets
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QStringListModel
from difflib import SequenceMatcher
import numpy as np
import pandas as pd
import json


GEOMETRY = (100, 100, 800, 600)
os.makedirs('decks', exist_ok=True)

CARD_WIDTH = 200
MAX_COL = 4

RAMP_OPTIONS = ['Sol Ring', 'Arcane Signet', 'Fellwar Stone', 'Thought Vessel', 'Mind Stone']
GREEN_RAMP = ["Nature's Lore", "Three Visits", 'Rampant Growth']
BASIC_OPTIONS = {'w':'Plains', 'u':'Island', 'b':'Swamp', 'r':'Mountain', 'g':'Forest'}

class Deck:

    def __init__(self, name: str):
        self.cards = Cards.empty()
        self.cards_to_add = []
        self.cards_to_remove = []
        self.name = name
        self.dir = os.path.join('decks', name)
        self.decklist = os.path.join('decks', '.'+name+'_decklist.json')
        self.commander = None
        self.color_id = None
        self.ramp = None
        self.basic_lands = None
        self.length = 0

    def addCard(self, card: dict, card_path):
        if not os.path.exists(card_path):
            print(f"<<<ERROR>>> Card {card_path} does not exist.")
            return
        
        card['path'] = card_path
        self.cards_to_add.append(card)

    def setCommander(self, card: dict):
        self.commander = card['Title']
        self.color_id = card['Color Identity']
        print(f"{self.name} Commander Set: {card['Title']}")

    def remCard(self, card_name):
        if not card_name in self.cards or card_name in self.cards_to_remove:
            print(f"<<<ERROR>>> Card {card_name} not in deck {self.name}.")
            return
        
        card = self.cards[card_name]
        self.cards_to_remove.append(card)
        return os.path.join(self.dir, card_name+'.png')
    
    def save(self):
        os.makedirs(self.dir, exist_ok=True)
        for card in self.cards_to_add:
            self.cards.addCard(card)
            path = card['path']
            copy_path = os.path.join(self.dir, card['Title']+'.png')
            if self.commander is not None:
                if card['Title'] == self.commander:
                    copy_path = os.path.join(self.dir, f'{card["Title"]}--COMMANDER.png')
            shutil.copy(path, copy_path)

        self.length += len(self.cards_to_add)

        for card in self.cards_to_remove:
            self.cards.removeCard(card)
            path = os.path.join(self.dir, card['path'])
            if self.commander is not None:
                if card['Title'] == self.commander:
                    path = os.path.join(self.dir, f'{card["Title"]}--COMMANDER.png')
                    self.commander = None
                    self.color_id = None
            os.remove(path)

        self.length -= len(self.cards_to_remove)

        self.cards_to_add = []
        self.cards_to_remove = []

        real_cards = ''
        real_card_file = os.path.join('decks', '_REAL_CARDS_'+self.name+'.txt')
        if self.basic_lands is not None:
            real_cards += self.basic_lands
        if self.ramp is not None:
            real_cards += self.ramp
        if real_cards:
            self.length = 0
            with open(real_card_file, 'w') as f:
                f.write(real_cards)
            for line in real_cards.split('\n'):
                if line:
                    self.length += int(line[:line.find('x')])
            self.length += len(self.cards)

        with open(self.decklist, 'w') as decklist:
            json.dump(self.cards.cards, decklist)

    def addBasics(self):
        if self.color_id is None:
            print("<<<ERROR>>> No commander.")
            return
        
        num_lands_to_add = 100 - len(self)

        if num_lands_to_add < 1:
            print("No room for lands")
            return
        
        colors = REVERSE_MAP[self.color_id]
        lands_per_color = [num_lands_to_add//len(colors)]*len(colors)
        i = 0
        while sum(lands_per_color) < num_lands_to_add:
            lands_per_color[i] += 1
            i+=1

        self.basic_lands = {BASIC_OPTIONS[colors[i]]: lands_per_color[i] for i in range(len(colors))}
        self.basic_lands = '\n'.join([f'{number}x {land}' for land, number in self.basic_lands.items()])
        
    def addRamp(self):
        if self.color_id is None:
            print("<<<ERROR>>> No commander.")
            return
        
        num_ramp = sum(1 if 'Ramp' in card['Themes'] else 0 for card in self.cards)
        num_ramp_needed = 2*self.cards[self.commander]['Mana Value'] - num_ramp

        self.ramp = '\n'
        for i in range(num_ramp_needed):
            if i < len(RAMP_OPTIONS):
                self.ramp += '1x ' + RAMP_OPTIONS[i] + '\n'
            elif 'g' in self.cards[self.commander]['Color'].lower():
                self.ramp += '1x ' + GREEN_RAMP[i - len(GREEN_RAMP)] + '\n'
    
    @classmethod
    def load(cls, name):
        deckpath = os.path.join('decks', name)
        if not os.path.exists(deckpath):
            print(f"<<<ERROR>>> Deck {deckpath} does not exist.")
            return

        instance = cls.__new__(cls)
        instance.name = name
        instance.dir = deckpath
        instance.cards_to_add = []
        instance.cards_to_remove = []
        instance.decklist = os.path.join('decks', '.'+name+'_decklist.json')
        instance.cards = Cards.empty()
        instance.commander = None
        instance.basic_lands = None
        instance.ramp = None
        instance.color_id = None
        with open(instance.decklist, 'r') as decklist:
            instance.cards.cards = json.load(decklist)

        instance.length = len(instance.cards)

        #for card in instance.cards: print(f'{card["Title"]}\n')
        real_card_file = os.path.join('decks', '_REAL_CARDS_'+instance.name+'.txt')
        if os.path.exists(real_card_file):
            with open(real_card_file, 'r') as f:
                lines = f.readlines()
            for line in lines:
                if line:
                    instance.length += int(line[:line.find('x')])

        for card in os.listdir(instance.dir):
            if 'COMMANDER' in card:
                instance.commander = card[:card.find('--')]
                instance.color_id = instance.cards[instance.commander]['Color Identity']

        return instance
    
    def __len__(self):
        return self.length

    def __contains__(self, item):
        return item in self.cards

class DeckManager(Interface):

    def __init__(self, card_names: list[str], geometry=GEOMETRY):
        super().__init__(save_logs=False, geometry=geometry)
        self.setWindowTitle("DeckCreator")

        self.text_output = Widgets.QTextEdit()
        self.text_output.setReadOnly(True)
        self.text_output.setFixedHeight(100)  # Limit the height for smaller output
        self.layout.addWidget(self.text_output)

        self.output_box = Widgets.QWidget()
        self.output_box.setStyleSheet("background-color: white")
        self.output_box.setSizePolicy(Widgets.QSizePolicy.Policy.Expanding, Widgets.QSizePolicy.Policy.Expanding)

        self.display_frame = Widgets.QGridLayout()
        self.display_frame.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)  # Align widgets to the top-left
        self.display_frame.setHorizontalSpacing(10)  # Spacing between images
        self.display_frame.setVerticalSpacing(10)  # Spacing between rows
        self.output_box.setLayout(self.display_frame)

        self.scroll_area = Widgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)  # Allow the scroll area to adjust to the widget size
        self.scroll_area.setWidget(self.output_box)  # Set the image display area as the scroll area's content

        self.layout.addWidget(self.scroll_area)

        self.completer = Widgets.QCompleter(self)
        self.model = QStringListModel()
        self.completer.setModel(self.model)
        self.input_box.setCompleter(self.completer)
        self.input_box.textChanged.connect(self.suggest)

        self.row = 0
        self.col = 0
        self.deck = None
        self.card_names = np.array(card_names, dtype=str)
        self.images = {}

    def suggest(self, text):
        if not text.strip():
            self.model.setStringList([])
            return
        
        similarity = lambda name: SequenceMatcher(None, text, name).ratio()

        sim = np.vectorize(similarity)(self.card_names)
        top10 = np.argsort(sim)[-10:][::-1]
        suggestions = self.card_names[top10]

        self.model.setStringList(list(suggestions))
        self.completer.complete()
        
    def print(self, msg: str):
        """
        Appends a message to the main output box.

        :param msg: The message to display.
        """
        self.text_output.append(msg)

    def displayCard(self, path):
        if not os.path.exists(path):
            print(f"Card not found: {path}")
            return
        elif path in self.images:
            print(f"Already showing card")
            return
        
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            pixmap.setDevicePixelRatio(self.devicePixelRatioF())
            label = Widgets.QLabel(self.output_box)
            pixmap = pixmap.scaledToWidth(CARD_WIDTH, Qt.TransformationMode.SmoothTransformation)
            label.setPixmap(pixmap)
            self.display_frame.addWidget(label, self.row, self.col)

            self.images[path] = label
            
            self.col += 1
            if self.col >= MAX_COL:
                self.col = 0
                self.row += 1

    def clearLayout(self):
        while self.display_frame.count() > 0:
            child = self.display_frame.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.images = {}
        self.row = 0
        self.col = 0

    def loadDeck(self, name):
        self.deck = Deck.load(name)
        if self.deck is None:
            return
        
        self.clearLayout()

        for img_file in os.listdir(self.deck.dir):
            path = os.path.join(self.deck.dir, img_file)
            self.displayCard(path)

    def newDeck(self):
        name = self.input
        self.deck = Deck(name)
        self.clearLayout()

    def printDeck(self):
        if self.deck is None:
            print("<<<ERROR>>> No deck.")
            return
        
        for card in self.deck.cards:
            print(card)

    def removeCard(self, card_name):
        if self.deck is None:
            print("<<<ERROR>>> No deck.")
            return
        
        path = self.deck.remCard(card_name)
        if not path:
            return
        
        image = self.images.pop(path)
        idx = self.display_frame.indexOf(image)
        self.display_frame.takeAt(idx)
        image.deleteLater()
        return True
        
    def displayMultiple(self, card_paths: list[str]):
        self.clearLayout()
        for path in card_paths:
            self.displayCard(path)
        




        

    