import json
import re
import sys
import pandas as pd

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
REVERSE_MAP = {value: key for key, value in IDENTITY_MAP.items()}

def anyIn(string: str, *substrings):
    return any(sub in string for sub in substrings)

def allIn(string: str, *substrings):
    return all(sub in string for sub in substrings)

def noneIn(string: str, *substrings):
    return not anyIn(string, *substrings)

class Cards:

    class Card(dict):

        def __init__(self, info: dict, themes=None):
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
            mv = 0
            if 'Mana Cost' in self:
                cost = self['Mana Cost']
                pips = re.findall(r'\{(.*?)\}', cost)
                for pip in pips:
                    if str.isdigit(pip):
                        mv += int(pip)
                    elif '2' in pip:
                        mv += 2
                    else:
                        mv += 1
            return mv

        def getColor(self):
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
            themes = set()
            if 'Rules Text' in self:
                rules = self.remFlavor().lower()
                #Wondertainment
                if set(self['Color Identity']).issubset(REVERSE_MAP['Jeskai']):
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
                    if anyIn(rules, 'add:') or allIn(rules, 'search', 'land'):
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
                                
        #TODO
        def getThemesAuto(self):
            return "Not Yet Implemented"





        def __repr__(self):
            s = f'{self['Title']}  {self['Mana Cost']}\n'
            s += f'{self['Type']}\n'
            s += f'{self['Rules Text']}'
            if 'Power/Toughness' in self:
                if self['Power/Toughness'] != '':
                    s += f'\n[{self['Power/Toughness']}]'
            return s

    def __init__(self, path, themes='Auto'):
        self.path = path
        with open(path, 'r', encoding='utf-8') as f:
            self.raw = json.load(f)

        self.cards = {}

        for raw in self.raw:
            name = raw['key']
            info = raw['data']['text']
            self.cards[name] = self.Card(info, themes)

    @classmethod
    def from_data(cls, df):
        if not isinstance(df, pd.DataFrame):
            df = df._df
        instance = cls.__new__(cls)
        instance.path = 'N/A'
        instance.raw = None
        instance.cards = {}

        for idx, row in df.iterrows():
            instance.cards[row['Title']] = cls.Card(row.to_dict())

        return instance


    def printCards(self):
        for card in self.cards.values():
            print(card, '\n')

    def __getitem__(self, idx):
        try:
            if isinstance(idx, int):
                return self.cards.values()[idx]
            else:
                return self.cards[idx]
        except:
            print(f"<<<ERROR>>> cards.py: Cards has no card named {idx}\n")
            raise

    def __iter__(self):
        return self.cards.values().__iter__()

    def __repr__(self):
        s = '----------------------------------\n'
        s += '\n'.join(list(self.cards.keys()))
        s += '\n---------------------------------'
        return s
    
    def __len__(self):
        return len(self.cards)





if __name__ == '__main__':
    c = Cards('code/Leaders.cardconjurer')
    print(c['The O5 Council'])
