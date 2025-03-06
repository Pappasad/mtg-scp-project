import os
import sys
from pycards import Cards
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from threading import Thread
from typing import TypedDict
import numpy as np
import numpy.typing as npt
from ci import IDENTITY_MAP
import textwrap
import re
import easyocr
import cv2

CARD_DIM = (822, 1122)
DPI = 300
SAVE_DIR = 'showcase'
FRAME_DIR = 'frames'
CROWN_DIR = os.path.join(FRAME_DIR, 'crowns')
PIPS = set([file[:-4] for file in os.listdir(os.path.join(FRAME_DIR, 'pips'))])

CROWN_MASK = Image.open(os.path.join(CROWN_DIR, 'l.png')).convert('RGBA').getchannel('A')
PINLINE_MASK = Image.open(os.path.join(FRAME_DIR, 'pinline.png')).convert('RGBA').getchannel('A')
FRAME_MASK = Image.open(os.path.join(FRAME_DIR, 'frame.png')).convert('RGBA').getchannel('A')
FONT_MAP = {
    'Mana Cost': os.path.join('fonts', 'beleren-b.ttf'),
    'Title': os.path.join('fonts', 'beleren-b.ttf'),
    'Type': os.path.join('fonts', 'beleren-b.ttf'),
    'Rules Text': os.path.join('fonts', 'mplantin.ttf'),
    'Power/Toughness': os.path.join('fonts', 'beleren-b.ttf'),
    'Italic': os.path.join('fonts', 'mplantin-i.ttf')
}
POS_MAP = {
    'Mana Cost': [0, 0],
    'Title': [70, 70],
    'Type': [70, 650],
    'Rules Text': [70, 720],
    'Power/Toughness': [710, 1018]
}

MAX_WIDTH = CARD_DIM[0] - 40
MAX_LENGTH = 50
MIN_LENGTH = 20
SPACING = 5
MAX_FONT_SIZE = 43

READER = easyocr.Reader(['en'], detect_network='craft')


def createShowcaseImg(card: dict):
    os.makedirs(SAVE_DIR, exist_ok=True)
    if not card.get('Type'):
        print("Card has no type")
        return
    elif not card.get('Color'):
        print(f'Card: {card["Title"]} has no color at all')
        return

    color: str = card['Color'].replace('{', '').replace('}', '').lower()
    pinline = ''
    if 'Land' in card['Type']:
        base = 'l.png'
    elif color.lower() == 'colorless':
        base = 'a.png'
    elif len(color) > 1:
        base = 'm.png'
        if len(color) == 2:
            pinline = color
    elif len(color) == 1:
        base = color + '.png'
    else:
        base = 'a.png'

    img = Image.open(os.path.join(FRAME_DIR, base)).convert('RGBA')

    if pinline:
        Xs = np.linspace(0, img.width, len(pinline) + 1, dtype=int)
        for i, p in enumerate(pinline):
            temp = Image.open(os.path.join(FRAME_DIR, p + '.png')).convert('RGB')

            mask = np.array(PINLINE_MASK, dtype=bool) #| np.array(FRAME_MASK, dtype=bool)
            mask[:, :Xs[i]] = False
            mask[:, Xs[i+1]:] = False
            mask = (mask * 255).astype(np.uint8)
            mask = Image.fromarray(mask, 'L')
            # Paste using the resized mask
            img.paste(temp, mask=mask)

    pt = None
    if 'Creature' in card.get('Type') or 'Vehicle' in card.get('Type'):
        pt = base[0] + 'pt.png'
        temp = Image.open(os.path.join(FRAME_DIR, pt)).convert('RGBA')
        mask = np.array(temp.getchannel('A'))
        mask = (mask == 255) * 255
        mask = Image.fromarray(mask.astype(np.uint8), 'L')
        pt_box = (1600, 2500)
        img.paste(temp, mask=mask, box=pt_box)

    if 'Legendary' in card.get('Type'):
        if pinline:
            temp = Image.new('RGBA', CROWN_MASK.size, (0, 0, 0, 0))
            Xs = np.linspace(0, temp.width, len(pinline) + 1, dtype=int)
            for i, p in enumerate(pinline):
                tempP = Image.open(os.path.join(CROWN_DIR, p + '.png')).convert('RGBA')

                mask = np.array(CROWN_MASK, dtype=bool) #| np.array(FRAME_MASK, dtype=bool)
                mask[:, :Xs[i]] = False
                mask[:, Xs[i+1]:] = False
                mask = (mask * 255).astype(np.uint8)
                mask = Image.fromarray(mask, 'L')
                # Paste using the resized mask
                temp.paste(tempP, mask=mask)
        else:
            crown = base[0] + '.png'
            temp = Image.open(os.path.join(CROWN_DIR, crown)).convert('RGBA')

        border = Image.new('RGB', (img.width, 140), (0, 0, 0))
        img.paste(border)
        bbox = (55, 55)
        img.paste(temp, box=bbox, mask=temp)

    img = img.resize(CARD_DIM)
    draw = ImageDraw.Draw(img)
    px_s = MAX_WIDTH
    for metric, pos in POS_MAP.items():
        if metric in card:
            text = card[metric]
            # print(metric)
            if not text:
                continue
            
            if metric == 'Rules Text':
                if '{flavor}' in text:
                    text = text[:text.find('{flavor}')]
                text = text.replace('~', card['Title'])
                #print(text)
                lines = text.split('\n')
                italics = re.split(r"(\{i\}.*?\{/i\})", text)
                new_lines = ''
                width = MIN_LENGTH
                max_length = MAX_LENGTH//4 * len(lines) if len([line for line in lines if len(line) > width]) > 3 else MAX_LENGTH
                for line in lines:
                    if len(line) <= width:
                        new_lines += line + '\n\n'
                    else:
                        while len(line) > width:
                            width += 1
                            if width >= max_length:        
                                break
                        new_lines += '\n'.join(textwrap.wrap(line, width=width)) + '\n\n'
                text = new_lines

                lower = img.height - 120
                if pt:
                    lower -= (img.height - pt_box[1])
                bbox = pos + [MAX_WIDTH, lower]

                font = getDynamicFont(text, bbox, FONT_MAP[metric])
                temp = img.copy()
                tempdraw = ImageDraw.Draw(temp)
                tempdraw.text(pos, text, font=font, fill='black', spacing=SPACING)
                specials = re.findall(r"(\{.*?\})", text)
                syms = findSymbols(specials, temp, font)
                for s in specials: 
                    if s.replace('{','').replace('}','') in PIPS:
                        text = text.replace(s, '   ')
                    else:
                        text = text.replace(s, '')
                draw.text(pos, text, font=font, fill='black', spacing=SPACING)
                for coords, pip in syms.items():
                    # print(pip)
                    pip_img = getSpecialChar(pip, font, rules=True)
                    img.paste(pip_img, box=coords, mask=pip_img)
                continue
            elif metric == 'Mana Cost':
                x = img.width - 25*len(text) - 25
                pos = [x, 70]
                bbox = pos + [MAX_WIDTH + 10, 120]
                font = getDynamicFont(text, bbox, FONT_MAP[metric])
                pips = re.findall(r"\{(.*?)\}", text)
                for i, pip in enumerate(pips):
                   # print(pip)
                    pip_img = getSpecialChar(pip, font)
                    mask = np.array(pip_img.getchannel('A'))
                    mask = (mask >= 5) * 255
                    mask = Image.fromarray(mask.astype(np.uint8), 'L')
                    px = img.width - 60 - pip_img.width*(len(pips) - i)
                    py = 60
                    #pip_img = add_bevel(pip_img)
                    img.paste(pip_img, box=(px, py), mask=pip_img)
                px_s = img.width - 60 - pip_img.width*len(pips)
                continue
            elif metric == 'Title':
                bbox = pos + [px_s, 110]
            elif metric == 'Type':
                bbox = pos + [MAX_WIDTH, img.height//2 + 120]
            elif metric == 'Power/Toughness':
                bbox = pos + [img.width - 30, img.height - 50]
            
            font = getDynamicFont(text, bbox, FONT_MAP[metric])
            draw.text(pos, text, font=font, fill='black', spacing=SPACING)



    img.save(os.path.join(SAVE_DIR, card['Title']+'.png'), format='png')

def getDynamicFont(text: str, bbox, style) -> ImageFont.truetype:
    left, upper, right, lower = bbox
    max_width = right - left
    max_height = lower- upper
    #print(bbox)

    size = MAX_FONT_SIZE
    font = ImageFont.truetype(style, size)
    bbox = ImageDraw.Draw(Image.new('RGB', (1, 1))).textbbox((0, 0), text, font=font)
    left, upper, right, lower = bbox
    width = right - left
    height = lower - upper
    
    while width > max_width or height > max_height:
        size -= 1
        #print(width, height, ">", max_width, max_height)

        font = ImageFont.truetype(style, size)
        bbox = ImageDraw.Draw(Image.new('RGB', (1, 1))).textbbox((0, 0), text, font=font)
        left, upper, right, lower = bbox
        width = right - left
        height = lower - upper

    return font


def getSpecialChar(char, font, rules=False) -> Image.Image:
    png = os.path.join(FRAME_DIR, 'pips', char+'.png')
    img = Image.open(png).convert('RGBA')

    bbox = font.getbbox('O')
    width, height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    if rules:
        img = img.resize((int(width), int(height*1.1)), Image.Resampling.LANCZOS)
    else:
        img = img.resize((int(width*1.3), int(height*1.3)), Image.Resampling.LANCZOS)

    return img

def findSymbols(symbols, img, font):
    img = np.array(img)
    results = READER.readtext(img)
    coords = {}

    for (bbox, text, prob) in results:
        bbox = np.array(bbox, dtype=int)
        # Extract full bounding box
        (top_left, top_right, bottom_right, bottom_left) = bbox
        x1, y1 = top_left
        # bbox2 = font.getbbox('O')
        # char_width = bbox2[2] - bbox2[0]
        # char_width = (top_right[0] - x1) / len(text)
        
        # # Approximate character width
        # text_length = len(text)
        # char_width = (x2 - x1) / text_length  # Approximate width of each character
        brackets = re.findall(r"(\{.*?\})", text)
        syms = []
        for b in range(len(brackets)):
            newb = brackets[b].replace(' ', '')
            if newb in symbols:
                syms.append(newb)
            #text = text.replace(brackets[b], newb)

        # syms = [sym for sym in symbols if sym in text]
        # print(syms)
        if '{i}' in text or '{/i}' in text:
            text = text.replace('{i}','').replace('{/i}','')
        for symbol in syms:
            if symbol.replace('{','').replace('}','') in PIPS:
                sx = x1
                for char in text[:text.find(symbol)]:
                    box = font.getbbox(char)
                    sx += box[2] - box[0]
                if sx != x1:
                    sx += 5

                sym_bbox = (int(sx), int(y1))
                coords[sym_bbox] = symbol.replace('{','').replace('}','')
                text = text.replace(symbol, '  ', 1)
                print(f"Detected: '{symbol}' at {sym_bbox}")
                #print('\t', text)

    # sys.exit()
    return coords
    

def multipleShowcases(cards):
    for card in cards:
        print(card['Title'])
        try:
            createShowcaseImg(card)
        except:
            print("BAD")
            raise
        #sys.exit()





if __name__ == '__main__':
    c = Cards('cc/Leaders.cardconjurer')
    multipleShowcases(c)



