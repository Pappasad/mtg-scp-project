import os
import copy

CARD_DIRS = ['orgs and commanders', 'transforms', 'dim', 'scp']

def correctImgPaths(dirs=CARD_DIRS):
    for img_dir in dirs:
        if os.path.exists(img_dir):
            for img_file in (file for file in os.listdir(img_dir) if file.endswith('.png')):

                if '_' in img_file:
                    new_name = img_file.replace('_', '').strip()
                    new_path = os.path.join(img_dir, new_name)
                    old_path = os.path.join(img_dir, img_file)
                    print("Renamed", old_path)
                    os.rename(old_path, new_path)
                
                if '(' in img_file and 'unnamed' not in img_file:
                    findex = img_file.rfind('(')
                    new_file = img_file[:findex].strip() + '.png'
                    new_path = os.path.join(img_dir, new_file)
                    old_path = os.path.join(img_dir, img_file)
                    print("Renamed", old_path)
                    os.rename(old_path, new_path)
 


def findIncongruencies(titles, dirs=CARD_DIRS):
    titles = set(titles)
    names_from_folders = set()

    for img_dir in dirs:
        if os.path.exists(img_dir):
            for name in (file.replace('.png', '') for file in os.listdir(img_dir) if file.endswith('.png')):
                names_from_folders.add(name)

    not_in_folders = titles - names_from_folders
    not_in_database = names_from_folders - titles

    for name in not_in_database:
        print(f"[WARNING] Saved card {name} not in database")
    for name in not_in_folders:
        print(f"[WARNING] database entry {name} not in img folders")
                    








