import os
import sys
import frontmatter
import re

VAULT_DIR = 'Remote'

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
        empty = True
        while e < len(lines):
            if lines[e].strip():
                empty = True
            else:
                if empty:
                    break
                else:
                    empty = True
            
            e += 1
        card = [line for line in lines[s:e] if line]
        cards.append(card)
        s = e

    newcards = []
    for card in cards:
        try:
            newcard = {}
            splitdex = card[0].find('{')
            if splitdex > 0:
                newcard['Title'] = card[0][:splitdex].strip()
                newcard['Mana Cost'] = card[0][splitdex:].strip().upper()
                color = ''
                for c in newcard['Mana Cost']:
                    if str.isalpha(c) and c not in color and c.lower() in {'w', 'u', 'b', 'r', 'g'}:
                        color += c.upper()
                if color:
                    newcard['Color'] = ''.join(sorted(color))
                else:
                    newcard['Color'] = 'colorless'
            else:
                newcard['Title'] = card[0].strip()
                newcard['Mana Cost'] = ''
                newcard['Color'] = 'colorless'

            #print(card)
            types = re.split(r'(\{.*?\})', card[1])
            if len(types) > 1:
                newcard['Type'] = types[0] + chr(8212) + types[-1]
            else:
                newcard['Type'] = types[0]


            if '[' in card[-1]:
                newcard['Power/Toughness'] = card[-1].replace('[', '').replace(']', '')
                rules = '\n'.join(card[2:-1])
            else:
                rules = '\n'.join(card[2:])
            if '{flavor}' in rules:
                rules = rules[:rules.find('{flavor}')+1]
            rules = rules.replace('{-}', chr(8212))
            #print(rules, '\n')
            newcard['Rules Text'] = rules

            newcards.append(newcard)
        except:
            print(f'ERROR ON {card}')
            continue

    return newcards


        




    

if __name__ == '__main__':
    import showcase as sc
    #files = getMdFiles()
    file = os.path.join(VAULT_DIR, 'SCP', 'SCPs new.md')
    cards = parseCards(file)
    cards = [card for card in cards]# if card['Title'] == 'SCP-2815, Sarkic Village']
   # print(cards)
    sc.multipleShowcases(cards)
    # for file in files:
    #     try:
    #         cards = parseCards(file)
    #         sc.multipleShowcases(cards)
    #     except:
    #         print("Can't do", file)
    #         continue
        

    


