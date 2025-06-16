import os, json, requests, sys, subprocess
from PIL import Image
from imageGen import MODEL

TRAIN_DATA = os.path.join('training', 'images')
#TRAIN_LABELS = os.path.join('training', 'labels')
BULK_PATH = os.path.join('training', 'scryfall.json')
MAX_IMAGES = 500
TRAIN_IMG_SIZE = (1024, 1024)
DEF_LABEL = "mtg-style sci-fi fantasy card art, detailed, dramatic lighting, digital painting"
MODEL_OUTPUT = os.path.join('training', 'lora-mtg-style')

def Preprocessing():
    if not os.path.exists(BULK_PATH):
        print("Error: Can't find bulk data.")
        sys.exit(2)

    if os.path.exists(TRAIN_DATA):
        print("Training Data already exists")
        sys.exit(2)

    os.makedirs(TRAIN_DATA)

    print("Loading cards...")
    with open(BULK_PATH, 'r', encoding='utf-8') as f:
        training_cards = json.load(f)
    print("Cards loaded.")

    print("Creating training data...")
    count = 0
    total = min(len(training_cards), MAX_IMAGES)
    for card in training_cards:
        print(f"\r\tProgress: {100*count/total:.0f}%", end="", flush=True)
        if 'art_crop' in card.get('image_uris', ''):
            cardname = card.get('name', '').replace("/", "_").replace(":", "_")
            url = card['image_uris']['art_crop']
            path = os.path.join(TRAIN_DATA, f"{cardname}_{count}.jpg")
            label_path = os.path.join(TRAIN_DATA, f"{cardname}_{count}.txt")
            type_line = card.get('type_line', '')
            oracle = card.get('oracle_text', '')

            prompt = f"mtg-style digital fantasy art of a {type_line.lower()}. {oracle}"

            try:
                img = requests.get(url)
                with open(path, 'wb') as f:
                    f.write(img.content)
                with open(label_path, 'w', encoding='utf-8') as f:
                    f.write(prompt)
                count += 1
            except:
                total -= 1
                continue

        if count >= MAX_IMAGES:
            break

    print()
    print(f"Created {count} training images and labels.")

    print("Resizing images...")
    def center_crop_resize(img: Image):
        width, height = img.size
        short = min(width, height)
        left = (width - short) // 2
        top = (height - short) // 2
        right = left + short
        bottom = top + short
        return img.crop((left, top, right, bottom)).resize(TRAIN_IMG_SIZE, Image.Resampling.BICUBIC)
    
    total = count
    count = 0
    for file in os.listdir(TRAIN_DATA):
        print(f"\r\tProgress: {100*count/total:.0f}%", end="", flush=True)
        if file.endswith('.jpg'):
            path = os.path.join(TRAIN_DATA, file)
            img = Image.open(path).convert("RGB")
            img = center_crop_resize(img)
            img.save(path, quality=95)
            count += 1

    print()
    print(f"Resized {count} images.")

def Train(base_model, batch_size=1, steps=2, lr=1e-4, max_train_steps=1500, checkpoints=500):
    cmd = [
        "accelerate", "launch", os.path.join('code', "train_dreambooth_lora_sd3.py"),
        "--pretrained_model_name_or_path", base_model,
        "--instance_data_dir", TRAIN_DATA,  # Contains both images and .txt files
        "--instance_prompt", "mtg-style fantasy art",
        "--output_dir", MODEL_OUTPUT,
        "--resolution", str(TRAIN_IMG_SIZE[0]),
        "--train_batch_size", str(batch_size),
        "--gradient_accumulation_steps", str(steps),
        "--learning_rate", str(lr),
        "--lr_scheduler", "constant",
        "--max_train_steps", str(max_train_steps),
        "--checkpointing_steps", str(checkpoints),
        "--mixed_precision", "fp16",
        "--train_text_encoder",
        "--caption_column", "text"
    ]

    subprocess.run(cmd)




if __name__ == '__main__':
    if not os.path.exists(TRAIN_DATA):
        Preprocessing()
    Train(MODEL)
    
