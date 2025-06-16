from diffusers import StableDiffusion3Pipeline
import torch
import os
from ui import Interface
from pycards import Cards
import shutil
import PySide6.QtWidgets as Widgets
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QStringListModel, QThread, Signal
import numpy as np
import pandas as pd
import json
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PySide6.QtGui import QPixmap, QImage
from PIL import Image
import sys
import io

MODEL = "stabilityai/stable-diffusion-3-medium-diffusers"
OUTPUT_DIR = 'Generated'
PRETRAINED_PATH = "mtg_model_weights.safetensors"


class ImageGenerator:

    def __init__(self, model=MODEL):
        self.pipe = StableDiffusion3Pipeline.from_pretrained(
            model,
            torch_dtype=torch.float16
        ).to("cuda")
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    @classmethod
    def fromPretrained(cls, path=PRETRAINED_PATH):
        ins = cls()
        ins.pipe.load_lora_weights(path)
        ins.pipe.fuse_lora()
        return ins

    def generate(self, prompt: str, neg_prompt: str="", steps: int=30, guidance: float=7.0, width: int=1280, height: int=720, retvrn=False):
        output_path = os.path.join(OUTPUT_DIR, prompt[:64]+'.png')

        print(f"Generating {prompt}...")
        result = self.pipe(
            prompt=prompt,
            negative_prompt=neg_prompt,
            num_inference_steps=steps,
            guidance_scale=guidance,
            width = width,
            height = height
        ).images[0]

        if retvrn:
            return result
        else:
            result.save(output_path)
            print(f"Saved image to {output_path}")

class ImageGenGUI(Interface):
    
    def __init__(self):
        super().__init__(save_logs=False)
        self.setWindowTitle("Image Generator")

        self.layout.removeWidget(self.input_box)
        self.input_box.setParent(None)
        self.input_box.deleteLater()

        self.text_output = Widgets.QTextEdit()
        self.text_output.setReadOnly(True)
        self.text_output.setFixedHeight(100)  # Limit the height for smaller output
        self.layout.addWidget(self.text_output)

        self.output_box = Widgets.QWidget()
        self.output_box.setStyleSheet("background-color: white")
        self.output_box.setSizePolicy(Widgets.QSizePolicy.Policy.Expanding, Widgets.QSizePolicy.Policy.Expanding)

        self.display_frame = Widgets.QGridLayout()
        self.display_frame.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)  # Align widgets to the top-left
        self.display_frame.setHorizontalSpacing(10)  # Spacing between images
        self.display_frame.setVerticalSpacing(10)  # Spacing between rows
        self.output_box.setLayout(self.display_frame)

        self.scroll_area = Widgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)  # Allow the scroll area to adjust to the widget size
        self.scroll_area.setWidget(self.output_box)  # Set the image display area as the scroll area's content

        self.layout.addWidget(self.scroll_area)

        self.current_image = None

        cur = os.getcwd()
        cc_master = 'cardconjurer-master'
        while not cc_master in os.listdir(cur):
            next = os.path.dirname(cur)
            if next == cur:
                print("Could not find cc master")
                sys.exit(1)
            cur = next
        self.local_art_dir = os.path.join(cur, cc_master, 'local_art')

        self.imageGen = ImageGenerator.fromPretrained()

        self.prompt = Widgets.QLineEdit()
        self.neg_prompt = Widgets.QLineEdit()
        self.steps = Widgets.QSpinBox()
        self.steps.setRange(1, 150)
        self.steps.setValue(30)
        self.guidance = Widgets.QDoubleSpinBox()
        self.guidance.setRange(1.0, 20.0)
        self.guidance.setSingleStep(0.1)
        self.guidance.setValue(7.5)
        self.isvert = Widgets.QCheckBox()
        self.isvert.setChecked(False)

        self.button_layout.addWidget(QLabel("Prompt"))
        self.button_layout.addWidget(self.prompt)
        self.button_layout.addWidget(QLabel("Neg Prompt"))
        self.button_layout.addWidget(self.neg_prompt)
        self.button_layout.addWidget(QLabel("Steps"))
        self.button_layout.addWidget(self.steps)
        self.button_layout.addWidget(QLabel("Guidance"))
        self.button_layout.addWidget(self.guidance)
        self.button_layout.addWidget(QLabel("Vertical"))
        self.button_layout.addWidget(self.isvert)

        self.addButton("Generate", self.generateImg)
        self.addButton("Save Img", self.saveImg)
        self.addButton("Move Images", self.moveImages)

    def print(self, msg: str):
        """
        Appends a message to the main output box.

        :param msg: The message to display.
        """
        self.text_output.append(msg)

    def displayImage(self, img):
        if img.mode != "RGB":
            img = img.convert("RGB")
        with io.BytesIO() as buf:
            img.save(buf, format="PNG")
            bytes = buf.getvalue()
        qimage = QImage.fromData(bytes)

        label = QLabel()
        pixmap = QPixmap.fromImage(qimage)
        label.setPixmap(pixmap)

        self.display_frame.addWidget(label)

    def clearLayout(self):
        while self.display_frame.count() > 0:
            child = self.display_frame.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.current_image = None

    def generateImg(self):
        self.clearLayout()
        prompt = self.prompt.text()
        neg_prompt = self.neg_prompt.text()
        steps = self.steps.value()
        guidance = self.guidance.value()

        if self.isvert.isChecked():
            width = 1088
            height = 1920
        else:
            width = 1920
            height = 1088

        img = self.imageGen.generate(
            prompt,
            neg_prompt,
            steps,
            guidance,
            width=width,
            height=height,
            retvrn=True
        )

        self.current_image = img
        self.displayImage(img)

    def saveImg(self):
        if not self.current_image:
            print("no image")
            return

        path, _ = Widgets.QFileDialog.getSaveFileName(parent=None, caption="Save Image", dir='Generated', filter="Images (*.png *.jpg *.jpeg)")
        if path:
            ext = path.split('.')[-1].upper()
            if ext not in ['PNG', 'JPG', 'JPEG']:
                ext = 'PNG'  # fallback
            self.current_image.save(path)
            print(f"Saved image to {path}")

    def moveImages(self):
        imgs, _ = Widgets.QFileDialog.getOpenFileNames(None, "Move Images", dir='Generated', filter="Images (*.png *.jpg *.jpeg)")
        if imgs:
            for img in imgs:
                new_path = os.path.join(self.local_art_dir, os.path.basename(img))
                shutil.move(img, new_path)

            print(f"Moved {len(imgs)} images.")



