from PIL import Image
import json
import os

GRID_SIZE = (10, 7)
CARD_SIZE = (1636, 2468)  # Ultra-high resolution per card (4x original)

TTS_DIR = os.path.join('decks', 'tts')
os.makedirs(TTS_DIR, exist_ok=True)

def createCardSheet(paths, name):

    col, row = GRID_SIZE
    sheet_width = col * CARD_SIZE[0]
    sheet_height = row * CARD_SIZE[1]

    sheet = Image.new("RGB", (sheet_width, sheet_height))

    for idx, path in enumerate(paths):
        if idx >= col * row:
            break
            
        card = Image.open(path).resize(CARD_SIZE)
        dx = CARD_SIZE[0] * (idx % col)
        dy = CARD_SIZE[1] * (idx // col)
        sheet.paste(card, (dx, dy))

    output_path = os.path.join(TTS_DIR, name+'.png')
    sheet.save(output_path, quality=95)
    print(f"Card sheet saved at {output_path}")

def createJson(fg_url, bg_url, length, name):
    deck = {
        "ObjectStates": [
            {
                "Name": name,
                "DeckIDs": [i*100 for i in range(1, length+1)],
                "CustomDeck": {
                    "1":{
                        "FaceURL": fg_url,
                        "BackURL": bg_url,
                        "NumWidth": 10,
                        "NumHeight": 7,
                        "BackIsHidden": True
                    }
                }
            }
        ]
    }

    save_path = os.path.join(TTS_DIR, name+'.json')
    with open(save_path, 'w') as f:
        json.dump(deck, f, indent=4)
    print(f"Deck JSON saved at {save_path}")