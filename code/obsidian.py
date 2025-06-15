import os
import sys
import frontmatter
import re
from tkinter import Tk, filedialog
from util import int2Rom

VAULT_DIR = 'Remote'
TRANSFORM_MKR = 'transform'

cur = os.getcwd()
while not VAULT_DIR in os.listdir(cur):
    next = os.path.dirname(cur)
    if next == cur:
        print("Could not find Obsidian vault")
        sys.exit(1)
    cur = next
VAULT_DIR = os.path.join(cur, VAULT_DIR, 'MTG Prj')

def getMdFiles(subdir='SCP'):
    subdir = os.path.join(VAULT_DIR, subdir)
    markdowns = []

    for root, dirs, files in os.walk(subdir):
        markdowns += [os.path.join(root, file) for file in files if file.endswith('.md')]
            
    return markdowns

def parseCards(md_path: str):
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    parsed = frontmatter.loads(content)
    body = parsed.content
    lines = body.splitlines()
   
    cards = []
    s = 0
    while s < len(lines):
        if not lines[s].strip():
            s += 1
            continue

        e = s
        while e < len(lines):
            if not lines[e].strip():
                break 
            e += 1

        card = lines[s:e]
        cards.append(card)
        s = e

    real_cards = []
    for card_lines in cards:
        try:
            card = {}
            name_cost_split_idx = card_lines[0].find('{')
            if name_cost_split_idx > 0:
                #Split title and mana cost
                card['Title'] = card_lines[0][:name_cost_split_idx].strip()
                card['Mana Cost'] = card_lines[0][name_cost_split_idx:].strip().upper()

                #Set color
                color = ''
                for c in card['Mana Cost']:
                    if str.isalpha(c) and c not in color and c.lower() in {'w', 'u', 'b', 'r', 'g'}:
                        color += c.upper()
                if color:
                    card['Color'] = ''.join(sorted(color))
                else:
                    card['Color'] = 'colorless'
            else: 
                #if card has no mana cost
                card['Title'] = card_lines[0].strip()
                card['Mana Cost'] = ''
                card['Color'] = 'colorless'
                color = ''

            if any(c['Title'] == card['Title'] for c in real_cards):
                continue

            if TRANSFORM_MKR in card_lines[1]:
                #if card is a transform
                transform = card_lines[1][card_lines[1].rfind(TRANSFORM_MKR) + len(TRANSFORM_MKR):].strip().lower()
                typeline_idx = 2
                if 'back' in transform:
                    #if its the back side
                    card['Mana Cost'] = ''
                    for c in transform[transform.find('{'):]:
                        if c == '}':
                            break
                        if str.isalpha(c) and c not in color and c.lower() in {'w', 'u', 'b', 'r', 'g'}:
                            color += c.upper()
                        if color:
                            card['Color'] = ''.join(sorted(color))
                    
                transform = re.sub(r'\{.*?\}', '', transform).strip().lower()

                transform = transform.split()
                card['Transform'] = transform[0]
                if 'front' in transform and len(transform) > 1:
                    card['Reverse PT'] = transform[1]

            else:
                typeline_idx = 1
 
            types = re.split(r'(\{.*?\})', card_lines[typeline_idx])
            if len(types) > 1:
                card['Type'] = types[0] + chr(8212) + types[-1]
            else:
                card['Type'] = types[0]
            if card.get('Transform', '') == 'back':
                card['Type'] = '{right88}' + card['Type']

            if '[' in card_lines[-1]:
                card['Power/Toughness'] = card_lines[-1].replace('[', '').replace(']', '')
                rules = '\n'.join(card_lines[1+typeline_idx:-1])
            else:
                rules = '\n'.join(card_lines[1+typeline_idx:])

            new_lines = []
            for line in rules.splitlines():
                if line[0] == '-':
                    new_lines.append(chr(8226) + line[1:])
                else:
                    new_lines.append(line)
            rules = '\n'.join(line for line in new_lines)


            ###SAGA detection  
            if 'saga' in card.get('Type', '').lower():
                chapters = {}
                chapter_pattern = re.compile(r'^(I{1,3}|IV|V|VI{0,3}|IX|X):\s*(.*)', re.IGNORECASE)
                chapter = None
                for line in rules.splitlines():
                    match = chapter_pattern.match(line.strip())
                    if match:
                        chapter = match.group(1).upper()
                        chapters[chapter] = match.group(2)
                    elif chapter:
                        chapters[chapter] += '\n' + line.strip()
                rules = rules[:rules.find('I') if rules.find('I') != -1 else 99999999]
                card['Chapters'] = chapters
            
            if rules and rules[-1] == '\n':
                rules = rules[:-1]
            card['Rules Text'] = rules
            real_cards.append(card)
        except Exception as e:
            print(f'ERROR ON {card_lines[0]}:', e)
            raise

    return real_cards

root = Tk()
root.withdraw()
def selectMd():
    return filedialog.askopenfilenames(title='Select Markdowns', initialdir=VAULT_DIR, filetypes=[("Markdown files", "*.md")])
        
def selectCCAndMd():
    cc = filedialog.askopenfilename(title='Select Existing Cards To Replace', initialdir='cc', filetypes=[("Cardconjurer file", "*.cardconjurer")])
    md = filedialog.askopenfilename(title="Select Replacement Cards", initialdir=VAULT_DIR, filetypes=[("Markdown file", "*.md")])
    return cc, md

if __name__ == '__main__':
    files = getMdFiles('Test')
    cards = parseCards(files[0])
    for card in cards:
        print(card)

    


