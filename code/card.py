import os.path

import pandas as pd
import sys





TEXT_FLAG = 'text'
DATA_FLAG = 'data:{'
TEXT_LABELS = ['Mana Cost', 'Title', 'Type', 'Rules Text', 'Power/Toughness']
BREAK_FLAGS = (',x:', ',y:', ',width:', ',height:')
DIGITS = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}

class ColorId:
    VALID = {'w','u','b','r','g'}
    COLOR_MAP = {
        frozenset({'w'}): 'White',
        frozenset({'u'}): 'Blue',
        frozenset({'b'}): 'Black',
        frozenset({'r'}): 'Red',
        frozenset({'g'}): 'Green',
        frozenset({'w','u'}): 'Azorius',
        frozenset({'w','b'}): 'Orzhov',
        frozenset({'w','r'}): 'Boros',
        frozenset({'w','g'}): 'Selesnya',
        frozenset({'u','b'}): 'Dimir',
        frozenset({'u','r'}): 'Izzet',
        frozenset({'u','g'}): 'Simic',
        frozenset({'b','r'}): 'Rakdos',
        frozenset({'b','g'}): 'Golgari',
        frozenset({'r','g'}): 'Gruul',
        frozenset({'w','u','b'}): 'Esper',
        frozenset({'w','u','r'}): 'Jeskai',
        frozenset({'w','u','g'}): 'Bant',
        frozenset({'w','b','r'}): 'Mardu',
        frozenset({'w','b','g'}): 'Abzan',
        frozenset({'w','r','g'}): 'Naya',
        frozenset({'u','b','r'}): 'Grixis',
        frozenset({'u','b','g'}): 'Sultai',
        frozenset({'u','r','g'}): 'Temur',
        frozenset({'b','r','g'}): 'Jund',
        frozenset({'w','u','b','r'}): 'Nongreen',
        frozenset({'w','u','r','g'}): 'Nonblack',
        frozenset({'w','b','r','g'}): 'Nonblue',
        frozenset({'w','u','b','g'}): 'Nonred',
        frozenset({'u','b','r','g'}): 'Nonwhite',
        frozenset({'w','u','b','r','g'}): 'wubrg'
    }

    def __init__(self):
        self.Color = set()
        self.Id = 'Colorless'

    def __add__(self, other):
        if isinstance(other, ColorId):
            self.Color = self.Color.union(other.Color)
        elif isinstance(other, str) and other.lower() in self.VALID:
            self.Color.add(other.lower())
        else:
            return self

        key = frozenset(self.Color)
        self.Id = self.COLOR_MAP[key]

        return self

    def __iter__(self):
        Iter = ''
        for c in self.Color:
            Iter += c
        return Iter.__iter__()

    def getColors(self):
        it = ''
        for c in self.Color:
            it += c
        return it


Debug = 0

class Card:
    DATABASE = 'database.csv'

    def __init__(self, cc: dict):
        self.cc = cc
        text = self.cc['text']
        self.Name = text['Title']
        if '{-}' in text['Type']:
            type, subtype = text['Type'].split('{-}', 1)
            self.Types = type.split(' ')
            self.Subtypes = subtype.split(' ')
        else:
            self.Types = text['Type'].split(' ')

        if 'Creature' in self.Types:
            if text['Power/Toughness'] == '':
                pass
            else:
                self.PT = text['Power/Toughness']
                i = 0
                while self.PT[i] not in DIGITS and self.PT[i] != '*':
                    i += 1
                self.PT = self.PT[i:]

        self.Commander = False

        self.Cost = ''
        self.Mana_Value = 0

        if 'Mana Cost' in text.keys():
            mana_text = text['Mana Cost'].replace('{', '').split('}')
            color = ColorId()
            for pip in mana_text:
                if pip == '':
                    continue
                if len(pip) > 1 and not all(c in DIGITS for c in pip):
                    if '2' in pip:
                        self.Mana_Value += 2
                    else:
                        self.Mana_Value += 1

                    new_pip = '('
                    for p in pip:
                        new_pip += p
                        if p != pip[-1]:
                            new_pip += '/'
                        color += p
                    new_pip += ')'

                    self.Cost += new_pip
                elif all(c in DIGITS for c in pip):
                    self.Mana_Value += int(pip)
                    self.Cost += pip
                else:
                    self.Mana_Value += 1
                    color += pip
                    self.Cost += pip
            self.__setattr__('Color Identity', color.Id)
            self.Color = color.getColors()
            self.Cost = self.Cost.upper()
        self.__setattr__('Mana Value', self.Mana_Value)

        if 'Rules Text' in text.keys():
            self.rules = text['Rules Text']
            self.getThemes()

    def asEntry(self):
        columns = list(pd.read_csv(self.DATABASE).columns)
        entry = pd.Series(index=columns, dtype=object)
        for column in (col for col in columns if col in dir(self)):
            value = self.__getattribute__(column)
            if isinstance(value, list):
                value = list(filter(None, value))
            entry[column] = value
            
        return entry

    def getThemes(self):
        self.Themes = []

        r = self.rules.lower()

        iors = any(k in r for k in ('Instant', 'Sorcery'))

        if 'discard' in r:
            self.Themes.append('Discard')
            self.Themes.append('Graveyard')

        if iors:
            self.Themes.append('Spellslinger')
        elif 'Instant' in self.Types or 'Sorcery' in self.Types:
            if 'draw' in r and 'card' in r:
                self.Themes.append('Spellslinger')
            elif self.Mana_Value <= 3:
                self.Themes.append('Spellslinger')

        if all(w in r for w in ('return', 'creature', 'graveyard')):
            self.Themes.append('Graveyard')
            self.Themes.append('Reanimator')

        if all(w in r for w in ('sacrifice', 'creature')):
            if 'opponent sacrifices' not in r:
                self.Themes.append('Graveyard')
                self.Themes.append('Aristocrats')
        elif 'Creature' in self.Types and all(w in r for w in ('when', 'dies')):
            self.Themes.append('Graveyard')
            self.Themes.append('Aristocrats')

        if any(w in r for w in ('destroy', 'exile')):
            self.Themes.append('Control')
            if 'all' in r or 'each' in r:
                self.Themes.append('Control')
                self.Themes.append('Board_Wipe')

        if self.Mana_Value <= 4:
            if 'haste' in r:
                self.Themes.append('Aggro')
                self.Themes.append('Aggro')

        cmd_dmg = all(w in r for w in ('when', 'deals', 'combat', 'damage'))
        att = all(w in r for w in ('when', 'attack'))

        if cmd_dmg or att:
            self.Themes.append('Combat')
            if self.Mana_Value <= 4:
                self.Themes.append('Aggro')

        if 'mill' in r and 'opponent' in r:
            self.Themes.append('Mill')
            self.Themes.append('Graveyard')

        if 'draw' in r and 'discard' in r:
            self.Themes.append('Wheels')

        if 'draw' in r and self.Mana_Value <= 4:
            self.Themes.append('Card-Draw')

        if any(w in r for w in ('indestructible', 'hexproof')) and iors:
            self.Themes.append('Protection')

        if 'wondertain' in r or 'wondertain' in self.Name.lower():
            self.Themes.append('Wondertain')

        if 'fifthist' in r:
            self.Themes.append('Fifthist')

        if all(w in r for w in ('exile', 'battlefield', 'control', 'return')):
            self.Themes.append('Blink')
        elif all(w in r for w in ('when', 'enters', 'battlefield')) and 'landfall' not in r:
            self.Themes.append('Blink')

        if 'landfall' in r:
            self.Themes.append('Landfall')

        if 'dimension' in r:
            self.Themes.append('Dimensions')

        if 'treasure' in r:
            self.Themes.append('Treasures')

        if 'artifact' in r:
            self.Themes.append('Artifacts')

        self.Themes = list(set(self.Themes))

        return self.Themes



    def __repr__(self):
        return str(self.asEntry())


def parseText(val: str):
    new = {}
    for label in (s for s in TEXT_LABELS if s in val):
        sp = val.find(label) + len(label)
        i = val.find('text:', sp) + 5

        num_brack = 0
        new_text = ''

        while i < len(val):
            cur = val[i]
            if cur == '}' and num_brack == 0:
                break
            else:
                new_text += cur

            if cur == '{':
                num_brack += 1
            elif cur == '}' and num_brack > 0:
                num_brack -= 1

            i+=1

        if new_text[0] == '{' and label != 'Mana Cost' and label != 'Rules Text':
            cur = new_text[0]
            i = 0
            while cur != '}':
                i += 1
                cur = new_text[i]
            new_text = new_text[i+1:]

        new_text = new_text.replace('"','')
        new[label] = new_text

    for i in range(len(new)):
        curkey = list(new.keys())[i]
        curval = new[curkey]
        for flag in BREAK_FLAGS:
            if flag in curval:
                ep = curval.find(flag)
                new[curkey] = curval[:ep].replace('"','')
                break

    return new

def parseHelper(content: str):
    parsed = []
    Num_Brackets = 0
    Num_Blocks = 0
    cur = ''
    for i in range(len(content)-1):
        char = content[i]
        if char == '}' and Num_Brackets == 0:
            continue
        if Num_Brackets > 0 or char != ',' or Num_Blocks > 0:
            cur += char
            #print(char, end='')
        else:
            parsed.append(cur)
            cur = ''
            #print()
            continue

        if char == '{':
            Num_Brackets += 1
        elif char == '}' and Num_Brackets > 0:
            Num_Brackets -= 1
        elif char == '[':
            Num_Blocks += 1
        elif char == ']' and Num_Blocks > 0:
            Num_Blocks -= 1
    #print("\n---------------")
    return parsed

def parseCC(file_path: str):
    if not file_path.endswith('.cardconjurer'):
        print(f"ERROR: card.py -> parseCC: {file_path} is not a .cardconjurer file.")
        sys.exit()

    with open(file_path, 'r', encoding='utf-8') as cc:
        content = cc.read()

    all_content = content.replace('"', '').split(DATA_FLAG)

    parsed = []
    for content in all_content:

        content = parseHelper(content)

        content_map = {}
        for c in content:

            if ':' not in c or len(c) > 5000:
                continue

            key, value = c.split(':', 1)
            if 'key' in key:
                continue

            #print(key, value)

            if key == TEXT_FLAG:
                value = parseText(value)
            else:
                value = value.replace('"', '')


            key = key.replace('"', '')

            if value == 'true' or value == 'false':
                value = bool(value)
            if key not in content_map.keys():
                content_map[key] = value
        parsed.append(content_map)

    if Debug:
        for content_map in parsed:
            for k, v in content_map.items():
                print(f"{k} - {v}")
            print("--------------\n")

    return parsed[1:]

def createDatabase(path: str) -> pd.DataFrame:
    cards = pd.DataFrame()

    ccs = parseCC(path)
    for cc in ccs:
        if 'Type' in cc['text'].keys():
            if 'Token' not in cc['text']['Type'] and 'Dimension' not in cc['text']['Type'] and 'Emblem' not in cc['text']['Type']:
                if 'Name' in cards.columns:
                    if cc['text']['Title'] in cards['Name']:
                        print(f"{cc['text']['Title']} already exists")
                        continue
                    if 'Creature' in cc['text']['Type']:
                        if cc['text']['Power/Toughness'] == '':
                            print(f"{cc['text']['Title']} is an invalid creature")

                card = Card(cc)
                cards = pd.concat([cards, card.asEntry().to_frame().T], ignore_index=True)

    return cards

def cardsFromDir(folder=None, ex=True, export_path='new_db.csv', replace=True):
    import os
    from tkinter import filedialog, Tk

    if folder is None:
        root = Tk()
        root.withdraw()
        folder = filedialog.askdirectory(title="Select Folder Containing .cardconjurer Files")
        root.destroy()

    if not replace and os.path.exists(export_path):
        db = pd.read_csv(export_path)
    else:
        db = pd.DataFrame()

    for file in os.listdir(folder):
        if file.endswith('.cardconjurer'):
            print("Processing", file, "...")
            cards = createDatabase(os.path.join(folder, file))
            db = pd.concat([db, cards], axis=0, ignore_index=True)

    duple = db['Name'].duplicated(keep=False)
    db = db[~duple]

    db.fillna(value='')

    db.sort_values(by='Name', inplace=True)

    if ex:
        db.to_csv(export_path, index=False)
    return db

if __name__ == '__main__':
    print(cardsFromDir())