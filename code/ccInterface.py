import json
import os
import obsidian as ob
import copy
import sys

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

def fillCard(card: dict):
    isSCP = 'SCP' in card.get('Title', '')

    if card.get('Transform', '') == 'front':
        template = Template['Front']
    elif card.get('Transform', '') == 'back':
        template = Template['Back']
    elif isSCP:
        template = Template[SCP_VER]
    else:
        template = Template[DEF_VER]

    layout = copy.deepcopy(template)
    text = layout["data"]["text"]

    text["title"]["text"] = card.get("Title", "")
    text["mana"]["text"] = card.get("Mana Cost", "")
    text["type"]["text"] = card.get("Type", "")
    text["rules"]["text"] = card.get("Rules Text", "")
    text["pt"]["text"] = card.get("Power/Toughness", "") if "Power/Toughness" in card else ""

    layout['data']['frames'] = []

    if 'creature' in card.get('Type', '').lower() or 'vehicle' in card.get('Type', '').lower():
        if isSCP:
            layout['data']['frames'].append(getPTFrame(card, True))
        else:
            layout['data']['frames'].append(getPTFrame(card, False))

    if card.get('Reverse PT', ''):
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
    layout['data']['frames'] += getFrameColor(card)

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
            src = os.path.join(frame, 'pt', color+'.png')
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


    if card.get('Transform', ''):
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
        src = f"{frame}/{color}.png"
    else:
        frame = os.path.join(FRAME_BASE_PATH, 'regular')
        src = f"{frame}/{color}.png"

    return [{"name": color_name + 'Frame', "src": src, "masks": []}]

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

    frames = []
    if len(color) == 2 and all(c in color_map for c in color):
        left_color = color_map[color[0]]
        right_color = color_map[color[1]]

        if card.get('Transform', ''):
            left_color = left_color.upper()
            right_color = right_color.upper()

        left = {
            "name": f"{color[1]} Pinline",
            "src": f"{frame}/{card.get('Transform', '')+right_color}.png",
            "masks": [{"src": "/img/frames/m15/regular/m15MaskPinline.png", "name": "Pinline"}]
        }
        right = {
            "name": f"{color[0]} Pinline (Right)",
            "src": f"{frame}/{card.get('Transform', '')+left_color}.png",
            "masks": [
                {"src": "/img/frames/m15/regular/m15MaskPinline.png", "name": "Pinline"},
                {"src": "/img/frames/maskRightHalf.png", "name": "Right Half"}
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



if __name__ == "__main__":
    chooseAndExport()
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

