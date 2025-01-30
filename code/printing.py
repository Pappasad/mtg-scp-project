import os
from PIL import Image
from fpdf import FPDF

# Define card size in inches and convert to points (1 inch = 72 points)
CARD_WIDTH_INCHES = 2.46
CARD_HEIGHT_INCHES = 3.46
DPI = 300  # High-resolution printing

CARD_WIDTH_PX = int(CARD_WIDTH_INCHES * DPI)  # Card width in pixels
CARD_HEIGHT_PX = int(CARD_HEIGHT_INCHES * DPI)  # Card height in pixels

# Define PDF page size in points (1 inch = 72 points)
PG_WIDTH = 8.5 * 72  # Letter size width
PG_HEIGHT = 11 * 72  # Letter size height

ROW_CARDS = 3  # Number of cards per row
COL_CARDS = 3  # Number of cards per column

# Calculate margins for centering the cards on the page
MARGIN_X = (PG_WIDTH - (CARD_WIDTH_INCHES * ROW_CARDS * 72)) / 2
MARGIN_Y = (PG_HEIGHT - (CARD_HEIGHT_INCHES * COL_CARDS * 72)) / 2

TEMPDIR = 'temp'

def getDeckImages(name):
    deckpath = os.path.join('decks', name)
    if not os.path.exists(deckpath):
        print(f"Error: Deck '{name}' not found.")
        return []
    
    img_files = [os.path.join(deckpath, img) for img in os.listdir(deckpath) if img.endswith(('.png', '.jpg'))]
    return img_files

def getRealImages(name):
    real_card_file = os.path.join("decks", f"_REAL_CARDS_{name}.txt")
    if not os.path.exists(real_card_file):
        print(f"Warning: No real card file found for {name}.")
        return []

    real_cards = []
    with open(real_card_file, "r") as file:
        for line in file.readlines():
            line = line.strip()
            if "x " in line:
                count, card_name = line.split("x ", 1)
                card_name = os.path.join('Real_Cards', card_name+'.png')
                real_cards.extend([card_name] * int(count))  # Add multiple copies
            else:
                real_cards.append(line)

    return real_cards

def getImg(path):
    """ Loads and resizes an image to the correct card size. """
    image = Image.open(path)
    image = image.resize((CARD_WIDTH_PX, CARD_HEIGHT_PX), Image.Resampling.LANCZOS)
    return image

def createPDF(name):
    pdf = FPDF(unit='pt', format=[PG_WIDTH, PG_HEIGHT])
    output_path = os.path.join('decks', name+'.pdf')

    custom_images = getDeckImages(name)
    real_images = getRealImages(name)

    all_cards = custom_images + real_images

    for i in range(0, len(all_cards), ROW_CARDS * COL_CARDS):
        pdf.add_page()

        x_off = MARGIN_X
        y_off = MARGIN_Y

        for j in range(ROW_CARDS * COL_CARDS):
            if i + j >= len(all_cards):
                break

            card_path = all_cards[i + j]

            try:
                img = getImg(card_path)
                rz_path = os.path.join(TEMPDIR, f"temp_{i+j}.png")
                img.save(rz_path, 'PNG')

                # Insert image at correct size (in points)
                pdf.image(rz_path, x=x_off, y=y_off, w=CARD_WIDTH_INCHES * 72, h=CARD_HEIGHT_INCHES * 72)
                print(f"Added {card_path}")

            except Exception as e:
                print(f"Error processing {card_path}: {e}")

            # Move to the next column
            x_off += CARD_WIDTH_INCHES * 72

            # Move to the next row if at the end of the current row
            if (j + 1) % ROW_CARDS == 0:
                x_off = MARGIN_X
                y_off += CARD_HEIGHT_INCHES * 72

    pdf.output(output_path)

    for file in os.listdir(TEMPDIR):
        os.remove(os.path.join(TEMPDIR, file))
    print(f"PDF saved to {output_path}")



if __name__ == '__main__':
    createPDF('Spiders')
