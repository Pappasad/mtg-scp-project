import os

# Directories containing card images
CARD_DIR = 'cards'
CARD_DIRS = [CARD_DIR] + [os.path.join(CARD_DIR, dirname) for dirname in os.listdir(CARD_DIR) if os.path.isdir(os.path.join(CARD_DIR, dirname))]

def correctImgPaths(dirs=CARD_DIRS):
    print(CARD_DIRS)
    """
    Corrects the file paths of images in the specified directories by removing 
    underscores and trimming unnecessary text in parentheses.

    :param dirs: List of directories to process.
    """
    for img_dir in dirs:
        if os.path.exists(img_dir):
            for img_file in (file for file in os.listdir(img_dir) if file.endswith('.png')):

                # Remove underscores from file names
                if '_' in img_file:
                    new_name = img_file.replace('_', '').strip()
                    new_path = os.path.join(img_dir, new_name)
                    old_path = os.path.join(img_dir, img_file)
                    print("Renamed", old_path)
                    os.rename(old_path, new_path)

                # Remove text in parentheses from file names (excluding 'unnamed')
                if '(' in img_file and 'unnamed' not in img_file:
                    findex = img_file.rfind('(')
                    new_file = img_file[:findex].strip() + '.png'
                    new_path = os.path.join(img_dir, new_file)
                    old_path = os.path.join(img_dir, img_file)
                    print("Renamed", old_path)
                    os.rename(old_path, new_path)
 

def findIncongruencies(titles, dirs=CARD_DIRS, exclude={os.path.join(CARD_DIR, 'tokens')}):
    """
    Identifies inconsistencies between the titles in the database and the image files
    in the specified directories.

    :param titles: Set of titles from the database.
    :param dirs: List of directories to check for image files.
    """
    titles = set(titles)  # Ensure titles are a set for efficient operations
    names_from_folders = set()

    # Collect names of image files from directories
    for img_dir in dirs:
        if os.path.exists(img_dir) and img_dir not in exclude:
            for name in (file.replace('.png', '') for file in os.listdir(img_dir) if file.endswith('.png')):
                names_from_folders.add(name)

    # Calculate discrepancies
    not_in_folders = titles - names_from_folders
    not_in_database = names_from_folders - titles

    # Log discrepancies
    for name in not_in_database:
        print(f"[NOT IN DATABASE] Saved card {name} not in database")
    for name in not_in_folders:
        print(f"[NOT IN FOLDERS] Database entry {name} not in img folders")
