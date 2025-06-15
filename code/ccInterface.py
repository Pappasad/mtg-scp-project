import json
import os
import obsidian as ob
import copy
import sys
from pycards import Cards
from util import int2Rom

TEMPLATE_PATH = "template.cardconjurer"
OUTPUT_DIR = "custom_cc"
FRAME_BASE_PATH = "/img/frames/m15/ub"
FRAME_SCP_PATH = "/img/frames/dossier"
DEF_VER = 'ubRegular'
SCP_VER = 'dossier'
TR_FRONT_DIR = "/img/frames/m15/transform/ub"
TR_BACK_DIR = "/img/frames/m15/transform/ub/new"
TR_CROWN_DIR = "/img/frames/m15/transform/crowns/ub"
TRANSFORM_PIP_DIR = "img/frames/m15/ciPips"
SAGA_DIR = "/img/frames/saga/ub"
SAGA_CREATURE_DIR = "/img/frames/saga/creature/ub"



#globals
Template = {}
with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
    template_data = json.load(f)
for temp in template_data:
    if temp.get('key', '') == 'Dossier':
        Template[SCP_VER] = temp
    elif temp.get('key', '') == 'Legendary Creature':
        Template['Double Color'] = temp
    elif temp.get('key', '') == 'Title':
        Template[DEF_VER] = temp
    elif temp.get('key', '') == 'Front':
        Template['Front'] = temp
    elif temp.get('key', '') == 'Back':
        Template['Back'] = temp
    elif temp.get('key', '') == 'Saga':
        Template['Saga'] = temp
    elif temp.get('key', '') == 'Saga Creature':
        Template['Saga Creature'] = temp
    elif temp.get('key', '') == 'Saga Creature Front':
        Template['Saga Creature Front'] = temp
    elif temp.get('key', '') == 'Saga Creature Back':
        Template['Saga Creature Back'] = temp
    elif temp.get('key', '') == 'Vehicle':
        Template['Vehicle'] = temp

def fillCard(card: dict):
    isSCP = 'SCP' in card.get('Title', '')

    if 'saga' in card.get('Type' ,'').lower():
        if 'creature' in card.get('Type' ,'').lower():
            if card.get('Transform', '') == 'front':
                template = Template['Saga Creature Front']
            elif card.get('Transform', '') == 'back':
                template = Template['Saga Creature Back']
            else:
                template = Template['Saga Creature']
        else:
            template = Template['Saga']
    elif card.get('Transform', '') == 'front':
        template = Template['Front']
    elif card.get('Transform', '') == 'back':
        template = Template['Back']
    elif isSCP:
        template = Template[SCP_VER]
    elif 'vehicle' in card.get('Type', '').lower():
        template = Template['Vehicle']
    else:
        template = Template[DEF_VER]

    layout = copy.deepcopy(template)
    text = layout["data"]["text"]

    text["title"]["text"] = card.get("Title", "")
    text["mana"]["text"] = card.get("Mana Cost", "")
    text["type"]["text"] = card.get("Type", "")
    if card.get('Rules Text', ''):
        text["rules"]["text"] = card.get("Rules Text", "")

    layout['data']['frames'] = []

    if 'creature' in card.get('Type', '').lower() or 'vehicle' in card.get('Type', '').lower():
        text["pt"]["text"] = card.get("Power/Toughness", "")
        layout['data']['frames'].append(getPTFrame(card, isSCP))

    if 'saga' in card.get('Type', '').lower():
        chapters = card['Chapters']
        for i, chapter in enumerate(chapters.values()):
            if i > 4:
                break
            text[f'ability{i}']['text'] = chapter
        if card.get('Transform', '') == 'front':
            text['reminder']['text'] = "{i}As this Saga enters and after your draw step, add a lore counter.{/i}"
        else:
            last_chap = list(chapters.keys())[-1]
            text['reminder']['text'] = f"{{i}}As this Saga enters and after your draw step, add a lore counter. Sacrifice after {last_chap}.{{/i}}"
    elif card.get('Reverse PT', ''):
        text['reminder']['text'] = card.get('Reverse PT', '')

    if card.get('Transform', '') == 'back':
        #layout['data']['frames'].append(getTransformPip(card))
        pass

    if 'legendary' in card.get('Type', '').lower():
        if isSCP:
            layout['data']['frames'].extend(getLegendCrown(card, True))
        else:
            layout['data']['frames'].extend(getLegendCrown(card, False))

    if len(card.get('Color', '')) == 2:
        layout['data']['frames'].extend(getPinlineColor(card))

    frame = getCardFrame(card)
    layout['version'] = frame['version']
    layout['data']['frames'].extend(getFrameColor(card))

    return {"key": card.get("Title", "unnamed"), "data": layout["data"]}


#TODO
def getTransformPip(card: dict):
    pass
    # color = card.get('Color')

    # color_map = {
    #     "W": "w",
    #     "U": "u",
    #     "B": "b",
    #     "R": "r",
    #     "G": "g",
    #     "COLORLESS": "a"
    # }

    # color = color_map.get(color, 'm')

    # if len(color) == 1:




def getLegendCrown(card: dict, isSCP):
    color = card.get('Color')

    color_map = {
        "W": "w",
        "U": "u",
        "B": "b",
        "R": "r",
        "G": "g",
        'COLORLESS': 'a'
    }

    color_name_map = {
        'W': 'White',
        'U': 'Blue',
        'B': 'Black',
        'R': 'Red',
        'G': 'Green',
        'COLORLESS': 'Artifact'
    }

    color_ids = list(color)

    regular = False
    if card.get('Transform', ''):
        frame = TR_CROWN_DIR
        if card.get('Transform', '') == 'front':
            src = os.path.join(frame, 'regular')
        elif card.get('Transform', '') == 'back':
            src = os.path.join(frame, 'regular', 'new')
        else:
            print("bad things happen matey")
            sys.exit(1)
    elif isSCP:
        frame = FRAME_SCP_PATH
        src = os.path.join(frame, 'crown')
    else:
        frame = FRAME_BASE_PATH
        src = os.path.join(frame, 'crowns')
        regular = True

    if not isSCP:
        bounds = {"x":0.0274,"y":0.0191,"width":0.9454,"height":0.1667}
    else:
        bounds = {"x":0.016417910447761194,"y":0,"width":0.8905472636815921,"height":0.14889836531627576}

    crowns = []
    if len(color_ids) == 2:
        # Two-color crown with masks
        for i, c in enumerate(color_ids):
            suffix = color_map.get(c.upper())
            side = "Right Half" if i == 0 else "Left Half"
            mask_src = "/img/frames/maskRightHalf.png" if i == 0 else "/img/frames/maskLeftHalf.png"
            crowns.append({
                "name": f"{color_name_map.get(c)} Legend Crown",
                "src": os.path.join(src, suffix+'.png') if not regular else os.path.join(src, 'm15Crown'+suffix.upper()+'.png'),
                "masks": [{"src": mask_src, "name": side}] if i == 0 else [],
                "bounds": bounds
            })
    else:
        # Single-color crown or gold
        suffix = color_map.get(color.upper(), 'm')
        if suffix == 'a' and 'land' in card.get('Type', '').lower():
            suffix = 'l'
        crowns.append({
            "name": f"{color_name_map.get(color.upper(), 'Multicolored')} Legend Crown",
            "src": os.path.join(src, suffix+'.png') if not regular else os.path.join(src, 'm15Crown'+suffix.upper()+'.png'),
            "masks": [],
            "bounds": bounds
        })

    # Optional black bar overlay (always goes last)
    crowns.append({
        "name": "Legend Crown Border Cover",
        "src": "/img/black.png",
        "bounds": {
            "x": 0.0394,
            "y": 0.0277,
            "width": 0.9214,
            "height": 0.0177
        },
        "masks": []
    })

    return crowns


def getPTFrame(card: dict, isSCP):
        color = card.get('Color')

        if 'land' in card.get('Type', '').lower():
            color = 'l'
            color_name = 'Land'
        elif 'vehicle' in card.get('Type', '').lower():
            color = 'v'
            color_name = 'Vehicle'
        elif color == "W":
            color = 'w'
            color_name = 'White'
        elif color == "U":
            color = 'u'
            color_name = 'Blue'
        elif color == "B":
            color = 'b'
            color_name = 'Black'
        elif color == "R":
            color = 'r'
            color_name = 'Red'
        elif color == "G":
            color = 'g'
            color_name = 'Green'
        elif color == "colorless":
            color = 'a'
            color_name = 'Artifact'
        else:
            color = 'm'
            color_name = 'Multicolored'

        if card.get('Transform', '') == 'back':
            frame = TR_FRONT_DIR
            src = os.path.join(frame, 'pt'+color.upper()+'.png')
        elif isSCP:
            frame = FRAME_SCP_PATH
            src = os.path.join(frame, 'pt.png')
        else:
            frame = FRAME_BASE_PATH
            src = os.path.join(frame, 'pt', color+'.png')
        
        
        return {
            "name": f"{color_name} Power/Toughness",
            "src": src,
            "bounds": {
                "x": 0.7573,
                "y": 0.8848,
                "width": 0.188,
                "height": 0.0733
            },
            "masks": []
        }


def getFrameColor(card: dict):
    color = card.get('Color')

    if 'land' in card.get('Type', '').lower():
        color = 'l'
        color_name = 'Land'
    elif color == "W":
        color = 'w'
        color_name = 'White'
    elif color == "U":
        color = 'u'
        color_name = 'Blue'
    elif color == "B":
        color = 'b'
        color_name = 'Black'
    elif color == "R":
        color = 'r'
        color_name = 'Red'
    elif color == "G":
        color = 'g'
        color_name = 'Green'
    elif color == "colorless":
        color = 'a'
        color_name = 'Artifact'
    else:
        color = 'm'
        color_name = 'Multicolored'

    frames = []
    if 'saga' in card.get('Type', '').lower():
        color_name += ' Saga '
        if 'creature' in card.get('Type', '').lower():
            color_name += ' Creature '
            if card.get('Transform', ''):
                frame = os.path.join(SAGA_CREATURE_DIR, f'transform-{card["Transform"]}')
                color_name += card['Transform']
            else:
                frame = SAGA_CREATURE_DIR
            
            src = f"{frame}/{color}.png"
        else:
            frame = SAGA_DIR
            if 'land' in card.get('Type', ''):
                src = f"{frame}/{color}.png"
            else:
                src = f"{frame}/sagaFrame{color.upper()}.png"
    elif card.get('Transform', ''):
        if card.get('Transform', '') == 'front':
            frame = TR_FRONT_DIR
            color_name += ' Front '
        elif card.get('Transform', '') == 'back':
            frame = TR_BACK_DIR
            color_name += ' Back '
        else:
            print("bad things happen matey MAIN")
            sys.exit(1)

        src = os.path.join(frame, card.get('Transform')+color.upper()+'.png')
    elif 'SCP' in card.get('Title', ''):
        frame = FRAME_SCP_PATH
        if color == 'l' or color == 'v':
            color = 'a'
        src = f"{frame}/{color}.png"
    else:
        frame = os.path.join(FRAME_BASE_PATH, 'regular')
        src = f"{frame}/{color}.png"
        if 'artifact' in card.get('Type', '').lower():
            mask_path = "/img/frames/m15/regular/m15MaskFrame.png"
            if 'vehicle' in card.get('Type', '').lower():
                mask = 'v'
                name = 'Vehicle'
            else:
                mask = 'a'
                name = 'Artifact'
            frames.append({"name": name + 'Mask', "src": os.path.join(frame, mask+'.png'), "masks": [{"src": mask_path, "name": "Frame"}]})

    frames.append({"name": color_name + 'Frame', "src": src, "masks": []})
    return frames

    # if color == "W":
    #     return [{"name": "White Frame", "src": f"{frame}/w.png", "masks": []}]
    # elif color == "U":
    #     return [{"name": "Blue Frame", "src": f"{frame}/u.png", "masks": []}]
    # elif color == "B":
    #     return [{"name": "Black Frame", "src": f"{frame}/b.png", "masks": []}]
    # elif color == "R":
    #     return [{"name": "Red Frame", "src": f"{frame}/r.png", "masks": []}]
    # elif color == "G":
    #     return [{"name": "Green Frame", "src": f"{frame}/g.png", "masks": []}]
    # elif color == "colorless":
    #     return [{"name": "Artifact Frame", "src": f"{frame}/a.png", "masks": []}]
    # else:
    #     return [{"name": "Multicolored Frame", "src": f"{frame}/m.png", "masks": []}]
    
def getPinlineColor(card: dict):
    color = ''.join(sorted(card.get('Color', '')))
    mask_path = "/img/frames/m15/regular/m15MaskPinline.png"
    mask_path_r = "/img/frames/maskRightHalf.png"

    if card.get('Transform', ''):
        if card.get('Transform', '') == 'front':
            frame = TR_FRONT_DIR
        elif card.get('Transform', '') == 'back':
            frame = TR_BACK_DIR
        else:
            print("bad things happen matey pinline")
            sys.exit(1)
    elif 'SCP' in card.get('Title', ''):
        frame = FRAME_SCP_PATH
    else:
        frame = os.path.join(FRAME_BASE_PATH, 'regular')

    color_map = {
        "W": "w",
        "U": "u",
        "B": "b",
        "R": "r",
        "G": "g"
    }

    if 'saga' in card.get('Type', '').lower():
        if 'creature' in card.get('Type', '').lower():
            frame = SAGA_CREATURE_DIR
            if card.get('Transform', ''):
                frame = os.path.join(frame, f'transform-{card["Transform"].lower()}')
                mask_path = f"/img/frames/saga/creature/transform-{card['Transform'].lower()}/masks/pinline.png"
            else:
                mask_path = "/img/frames/saga/creature/masks/sagaMaskPinline.png"
        else:
            frame = SAGA_DIR
            mask_path = "/img/frames/saga/sagaMaskPineline.png"

    frames = []
    if len(color) == 2 and all(c in color_map for c in color):
        left_color = color_map[color[0]]
        right_color = color_map[color[1]]

        if 'saga' in card.get('Type', '').lower():
            if 'creature' not in card.get('Type', '').lower() and 'land' not in card.get('Type', '').lower():
                left_color = 'sagaFrame'+left_color.upper()
                right_color = 'sagaFrame'+right_color.upper()
        elif card.get('Transform', ''):
            left_color = card.get('Transform', '')+left_color.upper()
            right_color = card.get('Transform', '')+right_color.upper()

        left = {
            "name": f"{color[1]} Pinline",
            "src": f"{frame}/{right_color}.png",
            "masks": [{"src": mask_path, "name": "Pinline"}]
        }
        right = {
            "name": f"{color[0]} Pinline (Right)",
            "src": f"{frame}/{left_color}.png",
            "masks": [
                {"src": mask_path, "name": "Pinline"},
                {"src": mask_path_r, "name": "Right Half"}
            ]
        }

        frames.extend([right, left])
    return frames


def getCardFrame(card: dict):
    type_line = card.get("Type", "").lower()

    # Default frame for most cards
    frame = {
        "version": DEF_VER
    }

    if "planeswalker" in type_line:
        frame["version"] = "planeswalker"
    elif "saga" in type_line:
        frame["version"] = "saga"
    elif card.get('Transform', ''):
        frame['version'] = 'transform ' + card.get('Transform')
    elif "land" in type_line and "creature" not in type_line:
        frame["version"] = "m15Land"
    elif 'SCP' in card.get("Title", ""):
        frame['version'] = SCP_VER

    return frame

def exportNewCC(md_file, outdir=OUTPUT_DIR):
    os.makedirs(outdir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(md_file))[0]
    output_path = os.path.join(outdir, f"{base_name}.cardconjurer")
    cards = ob.parseCards(md_file)
    cc = []
    for card in cards:
        cc.append(fillCard(card))
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(cc, f, indent=2)

    print(f"✅ Saved {len(cc)} cards to: {output_path}")


def chooseAndExport():
    files = ob.selectMd()
    for file in files:
        exportNewCC(file)

def changeCards():
    existing, new = ob.selectCCAndMd()
    if not new or not existing:
        print("not selected")
        return
    with open(existing, 'r', encoding='utf-8') as f:
        cards = json.load(f)
    new_cards = {card['Title']: card for card in ob.parseCards(new)}

    fixed = 0
    for card in cards:
        title = card['key']
        if title in new_cards:
            # print("Before: ", card['data']['text'])
            fixed += 1
            for k, v in new_cards[title].items():
                if k == 'Rules Text':
                    k = 'rules'
                if k.lower() in card['data']['text']:
                    card['data']['text'][k.lower()]['text'] = v
            #print("After: ", card['data']['text'])

    with open(existing, "w", encoding="utf-8") as f:
        json.dump(cards, f, indent=2)

    if fixed:
        print(f"Fixed {fixed} cards in {os.path.basename(existing)} using {os.path.basename(new)}")




    



if __name__ == "__main__":
    chooseAndExport()
    #changeCards()
    # files = ob.getMdFiles("Test")
    # for file in files:
    #     all_cards = []
    #     cards = ob.parseCards(file)
    #     for card in cards:
    #         card_json = fillCard(card)
    #         all_cards.append(card_json)

    #     # Name the output file based on the source .md file
    #     base_name = os.path.splitext(os.path.basename(file))[0]
    #     output_path = os.path.join(OUTPUT_DIR, f"{base_name}.cardconjurer")

    #     os.makedirs(OUTPUT_DIR, exist_ok=True)
    #     with open(output_path, "w", encoding="utf-8") as f:
    #         json.dump(all_cards, f, indent=2)

    #     print(f"✅ Saved {len(all_cards)} cards to: {output_path}")

