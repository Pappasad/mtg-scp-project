from enum import Enum

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

class InvalidColor(Exception):
    def __init__(self, color: str):
        super().__init__(color)

class ColorIdentity:

    def __init__(self, inp: str):
        if inp in REVERSE_MAP:
            self.name = inp
            self.color = REVERSE_MAP[inp]
        elif inp.lower() in IDENTITY_MAP:
            self.color = inp.lower()
            self.name = IDENTITY_MAP[inp.lower()]
        else:
            raise InvalidColor(inp)
            
    @property
    def _set(self):
        return set(self.color)
    
    def __add__(self, other):
        if not isinstance(other, ColorIdentity):
            raise TypeError(other)
        
        new = self._set.union(other._set)
        new_color = ''.join(sorted(new))
        return ColorIdentity(new_color)
          
    def __contains__(self, item):
        if isinstance(item, ColorIdentity):
            return item._set.issubset(self._set)
        elif isinstance(item, str):
            return set(item).issubset(self._set)
        else:
            raise TypeError("Unsupported type for containment check")
    
    def __str__(self):
        return self.name

class CI(Enum):
    COLORLESS = ColorIdentity('')
    WHITE = ColorIdentity('w')
    BLUE = ColorIdentity('u')
    BLACK = ColorIdentity('b')
    RED = ColorIdentity('r')
    GREEN = ColorIdentity('g')
    GOLGARI = ColorIdentity('bg')
    RAKDOS = ColorIdentity('br')
    DIMIR = ColorIdentity('bu')
    ORZHOV = ColorIdentity('bw')
    GRUUL = ColorIdentity('gr')
    SIMIC = ColorIdentity('gu')
    SELESNYA = ColorIdentity('gw')
    IZZET = ColorIdentity('ru')
    BOROS = ColorIdentity('rw')
    AZORIUS = ColorIdentity('uw')
    JUND = ColorIdentity('bgr')
    SULTAI = ColorIdentity('bgu')
    ABZAN = ColorIdentity('bgw')
    GRIXIS = ColorIdentity('bru')
    MARDU = ColorIdentity('brw')
    ESPER = ColorIdentity('buw')
    TEMUR = ColorIdentity('gru')
    NAYA = ColorIdentity('grw')
    BANT = ColorIdentity('guw')
    JESKAI = ColorIdentity('ruw')
    NON_WHITE = ColorIdentity('bgru')
    NON_BLUE = ColorIdentity('bgrw')
    NON_GREEN = ColorIdentity('bruw')
    NON_RED = ColorIdentity('bguw')
    NON_BLACK = ColorIdentity('gruw')
    WUBRG = ColorIdentity('bgruw')

    def __contains__(self, item):
        """Allow direct containment check on CI.JESKAI instead of CI.JESKAI.value"""
        return item in self.value  # Redirect containment check to ColorIdentity instance