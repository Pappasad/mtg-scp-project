import json
import re
import sys
import pandas as pd

IDENTITY_MAP = {
    '': 'Colorless',
    'w': 'Red',
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

class Cards:

    class Card(dict):

        def __init__(self, info: dict):
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

                        if value['name'] == 'Type':
                            if 'token' in value['text'].lower():
                                continue
            
                        self[value['name']] = value['text']

                elif isinstance(value, str):
                    self[key] = value

            self['Mana Value'] = self.getManaValue()
            self['Color'] = self.getColor()
            self['Color Identity'] = self.getColorIdentity()

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


        def __repr__(self):
            s = f'{self['Title']}  {self['Mana Cost']}\n'
            s += f'{self['Type']}\n'
            s += f'{self['Rules Text']}'
            if 'Power/Toughness' in self:
                if self['Power/Toughness'] != '':
                    s += f'\n[{self['Power/Toughness']}]'
            return s

    def __init__(self, path):
        self.path = path
        with open(path, 'r', encoding='utf-8') as f:
            self.raw = json.load(f)

        self.cards = {}

        for raw in self.raw:
            name = raw['key']
            info = raw['data']['text']
            self.cards[name] = self.Card(info)

    @classmethod
    def from_data(cls, df: pd.DataFrame):
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
