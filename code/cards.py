import json
import re
import sys
import pandas as pd
import os

# Map of color identities to their descriptive names
IDENTITY_MAP = {
    '': 'Colorless',
    'w': 'White',
    'u': 'Blue',
    'b': 'Black',
    'r': 'Red',
    'g': 'Green',
    'bg': 'Golgari',
    'br': 'Rakdos',
    'bu': 'Dimir',
    'bw': 'Orzhov',
    'gr': 'Gruul',
    'gu': 'Simic',
    'gw': 'Selesnya',
    'ru': 'Izzet',
    'rw': 'Boros',
    'uw': 'Azorius',
    'bgr': 'Jund',
    'bgu': 'Sultai',
    'bgw': 'Abzan',
    'bru': 'Grixis',
    'brw': 'Mardu',
    'buw': 'Esper',
    'gru': 'Temur',
    'grw': 'Naya',
    'guw': 'Bant',
    'ruw': 'Jeskai',
    'bgru': 'Non-White',
    'bgrw': 'Non-Blue',
    'bruw': 'Non-Green',
    'bguw': 'Non-Red',
    'gruw': 'Non-Black',
    'bgruw': 'Wubrg'
}

# Reverse mapping of color descriptions to color identities
REVERSE_MAP = {value: key for key, value in IDENTITY_MAP.items()}

# Utility functions to check substrings in strings
def anyIn(string: str, *substrings):
    """
    Checks if any of the substrings are present in the given string.

    :param string: The string to search.
    :param substrings: Substrings to check for.
    :return: True if any substring is found, False otherwise.
    """
    return any(sub in string for sub in substrings)

def allIn(string: str, *substrings):
    """
    Checks if all of the substrings are present in the given string.

    :param string: The string to search.
    :param substrings: Substrings to check for.
    :return: True if all substrings are found, False otherwise.
    """
    return all(sub in string for sub in substrings)

def noneIn(string: str, *substrings):
    """
    Checks if none of the substrings are present in the given string.

    :param string: The string to search.
    :param substrings: Substrings to check for.
    :return: True if no substrings are found, False otherwise.
    """
    return not anyIn(string, *substrings)

class Cards:
    """
    Represents a collection of cards and provides utilities for managing them.

    The Cards class acts as a container for all the card data used in the application.
    It loads card information from JSON files or DataFrames, processes their attributes,
    and supports querying and theme assignment. This class is central to the application,
    enabling interaction with the card database and performing operations such as
    retrieving, iterating, and filtering cards based on specific criteria.
    """
    class Card(dict):
        """
        Represents a single card and its attributes.

        Each card is a dictionary-like object with additional methods to calculate
        derived properties such as mana value, color, and themes. The Card class
        encapsulates the logic for handling individual card data.
        """

        def __init__(self, info: dict, themes=None):
            """
            Initializes a card instance with given information and optionally assigns themes.

            :param info: Dictionary containing card information.
            :param themes: Method for assigning themes ('Manual' or 'Auto').
            """
            super().__init__()
            for key, value in info.items():
                if isinstance(value, dict):
                    if 'name' in value:
                        if value['name'] in {'Title', 'Type', 'Power/Toughness'}:
                            to_rem = re.findall(r'\{(.*?)\}', value['text'])
                            to_rem += ['?', ':']
                            for to in to_rem: 
                                value['text'] = value['text'].replace(to, '')
                            value['text'] = value['text'].replace('{', '')
                            value['text'] = value['text'].replace('}', '')

                        self[value['name']] = value['text']

                elif isinstance(value, str):
                    self[key] = value

            self['Mana Value'] = self.getManaValue()
            self['Color'] = self.getColor()
            self['Color Identity'] = self.getColorIdentity()
            if themes is not None:
                if themes.lower() == 'manual':
                    self['Themes'] = self.getThemesMan()
                elif themes.lower() == 'auto':
                    self['Themes'] = self.getThemesAuto()

        def getManaValue(self):
            """
            Calculates the mana value (converted mana cost) of the card.

            :return: Total mana value as an integer.

            Example:
                If the mana cost is "{3}{U}{U}", the mana value is 5.
                If the mana cost is "{2/W}{2/U}{R}", the mana value is 5 ("{2/W}" adds 2).
                If the mana cost is "{X}{G}", "X" contributes 0 unless specified elsewhere.
            """
            mv = 0
            if 'Mana Cost' in self:
                cost = self['Mana Cost']
                pips = re.findall(r'\{(.*?)\}', cost)
                for pip in pips:
                    if str.isdigit(pip):
                        mv += int(pip)  # Add numerical values directly
                    elif '2' in pip:
                        mv += 2  # Hybrid mana with "2"
                    else:
                        mv += 1  # Other single-mana symbols add 1
            return mv

        def getColor(self):
            """
            Determines the primary color of the card based on its mana cost.

            :return: Color of the card as a string.
            """
            color = 'Colorless'
            if 'Mana Cost' in self:
                cost = self['Mana Cost']
                pip_set = set(re.findall(r'\{(.*?)\}', cost))
                for pip in pip_set:
                    if pip.lower() in {'w', 'u', 'b', 'r', 'g'}:
                        color = color.replace('Colorless', '')
                        color += pip.upper()
            return color

        def getColorIdentity(self):
            """
            Determines the color identity of the card based on its mana cost and rules text.

            :return: Color identity as a string.
            """
            ci = set()
            if 'Mana Cost' in self:
                cost = self['Mana Cost']
                pip_set = set(re.findall(r'\{(.*?)\}', cost))
                for pip in pip_set:
                    if pip.lower() in {'w', 'u', 'b', 'r', 'g'}:
                        ci.add(pip.lower())
            if 'Rules Text' in self:
                rules = self['Rules Text']
                pip_set = set(re.findall(r'\{(.*?)\}', rules))
                for pip in pip_set:
                    if pip.lower() in {'w', 'u', 'b', 'r', 'g'}:
                        ci.add(pip.lower())

            key = ''.join(sorted(c for c in ci))
            ci = IDENTITY_MAP[key]
            return ci
        
        def remFlavor(self):
            """
            Removes flavor text from the rules text of the card.

            :return: Rules text without flavor text.
            """
            try:
                rules = self['Rules Text']
                if '{flavor}' in rules:
                    flav_st = rules.find('{flavor}')
                    rules = rules[:flav_st]
                return rules
            except Exception as e:
                print(f"Can't remove flavor from {self['Title']} due to {e}")
                sys.exit()

        def getThemesMan(self):
            """
            Assigns themes to the card manually based on predefined rules.

            :return: Themes as a space-separated string or 'None' if no themes are assigned.

            Examples of theme assignment rules:
                - Cards with "wonder" in their rules text and a color identity subset of Jeskai are assigned the "Wondertainment" theme.
                - Sarkic themes are assigned to cards with mechanics like "sacrifice a creature" or references to "+1/+1 counters" if their color identity fits Jund.
                - Cards containing keywords like "treasure" or "haste" with Mardu color identity are assigned the "MC&D" theme.
                - Cards mentioning "return" and "graveyard" with Sultai color identity are labeled with the "Serpents" theme.

            These rules are designed to group cards into thematic categories based on their mechanics and color identity.
            """
            if 'Type' not in self:
                return 'N/A'
            if anyIn(self['Type'], 'Token', 'Dimension'):
                return 'N/A'
            
            themes = set()
            if 'Rules Text' in self:
                rules = self.remFlavor().lower()

                #Wondertainment
                if set(REVERSE_MAP[self['Color Identity']]).issubset(REVERSE_MAP['Jeskai']):
                    if anyIn(rules, 'wonder', "you own but don't control"):
                        themes.add('Wondertainment')

                #Sarkites
                if set(REVERSE_MAP[self['Color Identity']]).issubset(REVERSE_MAP['Jund']):
                    if anyIn(rules, 'sarkic', 'sacrifice a creature', '+1/+1 counter', 'proliferate'):
                        themes.add('Sarkic')
                    elif 'Contagion' in self['Type']:
                        themes.add('Sarkic')
                    elif allIn(self['Type'], 'Creature', 'Anomalous'):
                        if not str.isdigit(self['Power/Toughness'][0]):
                            themes.add('Sarkic')
                        elif int(self['Power/Toughness'][0]) >= 4:
                            themes.add('Sarkic')

                #Church of the Broken God
                if set(REVERSE_MAP[self['Color Identity']]).issubset(REVERSE_MAP['Esper']):
                    if anyIn(rules, 'improvise', 'artifact'):
                        themes.add('Broken-God')
                    elif 'Artifact' in self['Type']:
                        themes.add('Broken-God')

                #SCP Foundation
                if set(REVERSE_MAP[self['Color Identity']]).issubset(REVERSE_MAP['Bant']):
                    if anyIn(rules, 'allied anomaly', 'scientist', 'soldier'):
                        themes.add('Foundation')
                    elif 'Anomalous' in self['Type'] and noneIn(self['Type'], 'Instant', 'Sorcery'):
                        themes.add('Foundation')
                    elif anyIn(self['Type'], 'Scientist', 'Soldier'):
                        themes.add('Foundation')

                #Chaos Insurgency
                if set(REVERSE_MAP[self['Color Identity']]).issubset(REVERSE_MAP['Grixis']):
                    if anyIn(rules, 'instant', 'sorcery', 'flashback', 'sorceries'):
                        themes.add('Insurgency')
                    elif anyIn(self['Type'], 'Instant', 'Sorcery'):
                        themes.add('Insurgency')

                #Are We Cool Yet?
                if set(REVERSE_MAP[self['Color Identity']]).issubset(REVERSE_MAP['Temur']):
                    if anyIn(rules, 'anart', 'noncreature'):
                        themes.add('AWCY?')
                    elif 'Anomalous' in self['Type'] and 'Creature' not in self['Type']:
                        themes.add('AWCY?')

                #Wilson's Wildlife Solutions
                if set(REVERSE_MAP[self['Color Identity']]).issubset(REVERSE_MAP['Naya']):
                    if anyIn(rules, 'convoke', 'tap a creature for mana', 'mana from a creature', 'nonhuman', 'non-human'):
                        themes.add("Wilsons")
                    elif 'Creature' in self['Type'] and 'Human' not in self['Type']:
                        themes.add('Wilsons')

                #Marshall, Carter, and Dark
                if set(REVERSE_MAP[self['Color Identity']]).issubset(REVERSE_MAP['Mardu']):
                    if anyIn(rules, 'treasure', 'haste'):
                        themes.add('MC&D')
                    elif 'Anomalous' in self['Type'] and (allIn(rules, 'deals damage', 'opponent') or 'any target' in rules):
                        themes.add('MC&D')
                    elif allIn(self['Type'], 'Anomalous', 'Creature') and int(self['Mana Value']) <= 5:
                        themes.add('MC&D')

                #The Serpent's Hand
                if set(REVERSE_MAP[self['Color Identity']]).issubset(REVERSE_MAP['Sultai']):
                    if anyIn(rules, 'escape', 'mill'):
                        themes.add('Serpents')
                    elif allIn(rules, 'return', 'creature card', 'graveyard'):
                        themes.add('Serpents')
                    elif 'Rogue' in self['Type']:
                        themes.add('Serpents')
                    elif 'Creature' in self['Type'] and 'graveyard' in rules:
                        themes.add('Serpents')

                #The Global Occult Coalition
                if set(REVERSE_MAP[self['Color Identity']]).issubset(REVERSE_MAP['Abzan']):
                    if anyIn(rules, 'non-anomalous', 'nonanomalous', 'destroy', 'exile', 'graveyard'):
                        themes.add('Goc')
                    elif noneIn(self['Type'], 'Anomalous', 'Instant', 'Sorcery'):
                        themes.add('Goc')

                #The Fifth Church
                rules_full = self['Rules Text'].lower()
                if anyIn(rules_full, 'fifthist', 'five', '5'):
                    themes.add('Fifthist')
                elif 'Power/Toughness' in self:
                    if '5' in self['Power/Toughness']:
                        themes.add('Fifthist')
                elif int(self['Mana Value']) == 5:
                    themes.add('Fifthist')

                #Removal
                if anyIn(rules, 'destroy', 'exile') and anyIn(rules, 'target', 'all', 'each'):
                    themes.add('Removal')
                elif allIn(rules, 'return', "owner's hand"):
                    themes.add('Removal')
                elif allIn(rules, 'opponent', 'sacrifice'):
                    themes.add('Removal')

                #Ramp
                if 'Land' not in self['Type']:
                    if anyIn(rules, 'add') or allIn(rules, 'search', 'land'):
                        themes.add('Ramp')
                    elif allIn(rules, 'land', 'battlefield'):
                        themes.add('Ramp')

                #Card Draw
                if 'draw' in rules:
                    themes.add('Card-Draw')

            if len(themes) == 0:
                return 'None'
            else:
                return ' '.join(sorted(theme for theme in themes))

        def getThemesAuto(self):
            """
            Automatically assigns themes to the card (not yet implemented).
            """
            return "Not Yet Implemented"
        
        def __repr__(self):
            s = self['Title']
            if 'Mana Cost' in self:
                s += '      ' + self['Mana Cost']
            if 'Type' in self:
                s += f"\n{self['Type']}\n"
            if 'Rules Text' in self:
                s += self['Rules Text'] + '\n'
            if 'Power/Toughness' in self:
                s += f"[{self['Power/Toughness']}]\n"
            return s

    def __init__(self, path, themes='Auto'):
        """
        Initializes the Cards object by loading card data from a file.

        :param path: Path to the card data file.
        :param themes: Method for assigning themes ('Manual' or 'Auto').
        """
        self.path = path
        with open(path, 'r', encoding='utf-8') as f:
            self.raw = json.load(f)

        self.cards = {}
        self.tokens = {}

        for raw in self.raw:
            name = raw['key']
            info = raw['data']['text']
            card = self.Card(info, themes)
            card['CC'] = os.path.basename(self.path)
            if 'Type' in card:
                if 'Token' in card['Type']:
                    self.tokens[name] = card
                else:
                    self.cards[name] = card

    @classmethod
    def empty(cls):
        instance = cls.__new__(cls)
        instance.path = 'N/A'
        instance.raw = None
        instance.cards = {}
        return instance

    @classmethod
    def from_data(cls, df):
        """
        Creates a Cards object from a pandas DataFrame.

        :param df: DataFrame containing card data.
        :return: Cards object.
        """
        if isinstance(df, pd.Series):
            return cls.Card(df.to_dict())
        
        if not isinstance(df, pd.DataFrame):
            df = df._df
        instance = cls.__new__(cls)
        instance.path = 'N/A'
        instance.raw = None
        instance.cards = {}

        for idx, row in df.iterrows():
            instance.cards[row['Title']] = cls.Card(row.to_dict())

        return instance
    
    def addCard(self, card):
        self.cards[card['Title']] = card

    def removeCard(self, card):
        del self.cards[card['Title']]

    def printCards(self):
        """
        Prints the details of all cards in the collection.
        """
        for card in self.cards.values():
            print(card, '\n')

    def __getitem__(self, idx):
        """
        Retrieves a card by index or name.

        :param idx: Index or name of the card.
        :return: The corresponding Card object.
        """
        try:
            if isinstance(idx, int):
                return list(self.cards.values())[idx]
            else:
                return self.cards[idx]
        except:
            print(f"<<<ERROR>>> cards.py: Cards has no card named {idx}\n")
            raise

    def __iter__(self):
        """
        Returns an iterator for the card collection.
        """
        return self.cards.values().__iter__()

    def __repr__(self):
        """
        Returns a string representation of the Cards object.
        """
        s = '----------------------------------\n'
        s += '\n'.join(list(self.cards.keys()))
        s += '\n---------------------------------'
        return s
    
    def __len__(self):
        """
        Returns the number of cards in the collection.
        """
        return len(self.cards)
    
    def __contains__(self, item):
        return item in self.cards

if __name__ == '__main__':
    # Example usage of the Cards class
    c = Cards('code/Leaders.cardconjurer')
    print(c['The O5 Council'])
