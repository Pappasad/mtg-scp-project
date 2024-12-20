import pandas as pd
import ast


pd.set_option('display.max_columns', None)  # Show all columns
pd.set_option('display.max_rows', None)     # Show all rows (use with caution for large DataFrames)
pd.set_option('display.width', None)        # Auto-detect width of the display


TRIBES = {'Nightmare', 'Horror', 'Zombie', 'Human', 'Spider', 'Artist', 'Soldier', 'Humanoid', 'Scientist'}
TO_GRAVEYARD = {'Discard', 'Reanimator', 'Mill', 'Aristocrats'}
TYPEMAP = {
    'A': 'Anomalous',
    'N': 'Land',
    'L': 'Legendary',
    'I': 'Instant',
    'S': 'Sorcery',
    'C': 'Creature',
    'P': 'Planeswalker',
    'E': 'Enchantment',
    'R': 'Artifact'
}
IDENTITYMAP = {
    'Jund': {'Jund', 'Rakdos', 'Golgari', 'Gruul', 'Green', 'Black', 'Red'},
    'Jeskai': {'Jeskai', 'Azorius', 'Izzet'},
    'Abzan': {'Abzan', 'Golgari', 'Selesnya', 'White', 'Black', 'Green'},
    'Esper': {'Esper', 'Orzhov', 'Azorius', 'Dimir', 'White', 'Blue', 'Black'},
    'Grixis': {'Grixis', 'Izzet', 'Dimir', 'Rakdos', 'Red', 'Blue', 'Black'},
    'Naya': {'Naya', 'Selesnya', 'Gruul', 'Boros', 'White', 'Green', 'Red'},
    'Temur': {'Temur', 'Izzet', 'Gruul', 'Simic', 'Blue', 'Green', 'Red'},
    'Sultai': {'Sultai', 'Golgari', 'Dimir', 'Simic', 'Blue', 'Green', 'Black'},
    'Bant': {'Bant', 'Selesnya', 'Simic', 'Azorius', 'White', 'Blue', 'Green'},
    'Mardu': {'Mardu', 'Orzhov', 'Rakdos', 'Boros', 'White', 'Red', 'Black'}
}

def getSets(entry: pd.Series):
    themes, types, subtypes = entry['Themes'], entry['Types'], entry['Subtypes']

    if isinstance(themes, str) and themes:
        themes = ast.literal_eval(themes)
    if isinstance(types, str) and types:
        types = ast.literal_eval(types)
    if isinstance(subtypes, str) and subtypes:
        subtypes = ast.literal_eval(subtypes)

    themes = set(themes) if themes != '' else set()
    types = set(types) if types != '' else set()
    subtypes = set(subtypes) if subtypes != '' else set()

    return themes, types, subtypes

def isSarkic(entry: pd.Series):
    if entry['Color Identity'] not in IDENTITYMAP['Jund'] and entry['Color Identity'] != 'Colorless':
        return False

    themes, types, subtypes = getSets(entry)

    if themes & {'Graveyard', 'Counters', 'Horrors', 'Contagions'}:
        return True
    elif {'Anomalous', 'Creature'} <= types:
        if entry['Mana Value'] >= 4 or getPT(entry)[0] >= 4:
            return True
    elif subtypes & {'Contagions'}:
        return True

    return False

def isBrokenGod(entry: pd.Series):
    if entry['Color Identity'] not in IDENTITYMAP['Esper'] and entry['Color Identity'] != 'Colorless':
        return False

    themes, types, subtypes = getSets(entry)

    if themes & {'Artifacts'}:
        return True
    elif 'Artifact' in types:
        return True

    return False

def isFoundation(entry: pd.Series):
    if entry['Color Identity'] not in IDENTITYMAP['Bant'] and entry['Color Identity'] != 'Colorless':
        return False

    themes, types, subtypes = getSets(entry)

    if 'Noncreatures' in themes or 'Spellslinger' in themes:
        return False

    if themes & {'Soldiers', 'Scientists', 'Blink', 'Landfall'}:
        return True
    elif 'Anomalous' in types and 'Instant' not in types and 'Sorcery' not in types:
        return True

    return False

def isWondertainment(entry: pd.Series):
    if entry['Color Identity'] not in IDENTITYMAP['Jeskai'] and entry['Color Identity'] != 'Colorless':
        return False

    themes, types, subtypes = getSets(entry)

    if themes & {'Chaos', 'Goad', 'Wondertainment'}:
        return True
    elif 'Anomalous' in types and entry['Mana Value'] >= 5 and 'Instant' not in types and 'Sorcery' not in types and 'Land' not in types and 'Fifthist' not in themes:
        return True

    return False

def isFifthist(entry: pd.Series):
    themes, types, subtypes = getSets(entry)
    pt = [0, 0]
    if 'Creature' in types:
        pt = getPT(entry)

    if 'Fifthist' in themes:
        return True
    # elif entry['Mana Value'] == 5 or pt[0] == 5 or pt[1] == 5:
    #     return True

    return False

def isWilsons(entry: pd.Series):
    if entry['Color Identity'] not in IDENTITYMAP['Naya'] and entry['Color Identity'] != 'Colorless':
        return False

    themes, types, subtypes = getSets(entry)

    if 'Noncreatures' in themes or 'Spellslinger' in themes:
        return False

    if themes & {'Wilsons'}:
        return True
    elif {'Anomalous', 'Creature'} <= types:
        return True
    elif 'Human' in subtypes and 'Scientist' not in subtypes and 'Soldier' not in subtypes:
        return True

    return False

def isCI(entry: pd.Series):
    if entry['Color Identity'] not in IDENTITYMAP['Grixis'] and entry['Color Identity'] != 'Colorless':
        return False

    themes, types, subtypes = getSets(entry)

    if themes & {'Chaos', 'Spellslinger'}:
        return True
    elif 'Anomalous' in types and ('Instant' in types or 'Sorcery' in types):
        return True
    elif ('Instant' in types or 'Sorcery' in types) and themes & {'Graveyard', 'Card-Draw', 'Control', 'Exile'}:
        return True

    return False

def isAwcy(entry: pd.Series):
    if entry['Color Identity'] not in IDENTITYMAP['Temur'] and entry['Color Identity'] != 'Colorless':
        return False

    themes, types, subtypes = getSets(entry)

    if themes & {'Anart', 'Noncreatures', 'Spellslinger', 'Artists'}:
        return True
    elif 'Anomalous' in types and 'Creature' not in types and 'Land' not in types:
        return True
    elif 'Artist' in subtypes:
        return True

    return False

def isMcd(entry: pd.Series):
    if entry['Color Identity'] not in IDENTITYMAP['Mardu'] and entry['Color Identity'] != 'Colorless':
        return False

    themes, types, subtypes = getSets(entry)

    if themes & {'Treasures', 'Chaos', 'Tokens'}:
        return True
    elif 'Anomalous' in types and types & {'Aggro', 'Combat', 'Burn'}:
        return True
    elif 'Merchant' in subtypes:
        return True

    return False

def isSerpents(entry: pd.Series):
    if entry['Color Identity'] not in IDENTITYMAP['Sultai'] and entry['Color Identity'] != 'Colorless':
        return False

    themes, types, subtypes = getSets(entry)

    if themes & {'Serpents', 'Graveyard'}:
        return True
    elif 'Rogue' in subtypes:
        return True

    return False

def isRamp(entry: pd.Series):
    themes, types, subtypes = getSets(entry)
    if 'Ramp' in themes:
        return True

    return False

def isControl(entry: pd.Series):
    themes, types, subtypes = getSets(entry)
    if 'Control' in themes:
        return True

    return False

def isCardDraw(entry: pd.Series):
    themes, types, subtypes = getSets(entry)
    if 'Card-Draw' in themes:
        return True

    return False

def isProtection(entry: pd.Series):
    themes, types, subtypes = getSets(entry)
    if 'Protection' in themes:
        return True

    return False


def getPT(entry):
    PT = str(entry['PT']).split('/')
    if PT[0] == '*':
        PT[0] = 100
    if PT[1] == '*':
        PT[1] = 100
    return int(PT[0]), int(PT[1])

def get(df, *args, num=False):
    if len(args) == 0:
        print("\tNo quantity specified")
        return

    for arg in (arg for arg in args if arg.lower() in GOI_FUNCS.keys()):
        df = df.loc[df.apply(GOI_FUNCS[arg.lower()], axis=1)]

    if not num:
        print(f"There are {len(df)} cards in:", *args, sep=' ')
        print(df.Name)
    else:
        print(f"There are {len(df)} cards in:", *args, sep=' ')

    return df

def correctThemes(df: pd.DataFrame):
    for idx, row in df.iterrows():
        themes, types, subtypes = getSets(row)

        #print(df.iloc[idx]['Name'],types)

        if any(t in themes for t in TO_GRAVEYARD):
            themes.add('Graveyard')

        if 'Creature' in types:
            for subtype in subtypes:
                if subtype in TRIBES:
                    themes.add(subtype)

        df.at[idx, 'Themes'] = list(themes)


GOI_FUNCS = {
    'sarkic': isSarkic,
    'brokengod': isBrokenGod,
    'foundation': isFoundation,
    'wondertainment': isWondertainment,
    'fifthist': isFifthist,
    'wilsons': isWilsons,
    'ci': isCI,
    'awcy': isAwcy,
    'mcd': isMcd,
    'serpents': isSerpents,
    'ramp': isRamp,
    'control': isControl,
    'protection': isProtection,
    'card-draw': isCardDraw
}

if __name__ == '__main__':
    cards = pd.read_csv('new_db.csv')
    cards = cards.fillna(value='')
    #print(get(cards, 'wondertainment'))
    #print(cards)
    correctThemes(cards)
    cards.to_csv('new_db.csv', index=False)
    for each in GOI_FUNCS.keys():
        args = [each]
        get(cards, each, num=True)