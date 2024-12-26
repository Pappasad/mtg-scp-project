import PySide6.QtWidgets as Widgets
from PySide6.QtCore import Qt
from database import CardDatabase
import sys
from functools import partial
from datetime import datetime
import os

GEOMETRY = (100, 100, 800, 600)
#BUTTON_SIZE = (150, 5)

LOG_DIR = 'logs'

class Interface(Widgets.QMainWindow):

    class PrintRedirector:
        def __init__(self, parent):
            self.parent = parent

        def write(self, msg):
            if msg.strip():
                self.parent.print(msg)

        def flush(self):
            pass

    def __init__(self, save_logs=True, geometry=GEOMETRY):
        super().__init__()
        self.setWindowTitle("Local Card Manager")
        self.setGeometry(*geometry)

        self.central_w = Widgets.QWidget()
        self.setCentralWidget(self.central_w)

        self.layout = Widgets.QVBoxLayout()
        self.central_w.setLayout(self.layout)

        self.button_layout = Widgets.QHBoxLayout()
        self.layout.addLayout(self.button_layout)

        self.output_box = Widgets.QTextEdit()
        self.output_box.setReadOnly(True)
        self.output_box.setSizePolicy(Widgets.QSizePolicy.Policy.Expanding, Widgets.QSizePolicy.Policy.Expanding)
        self.layout.addWidget(self.output_box)

        self.save = save_logs

    def show(self):
        sys.stdout = self.PrintRedirector(self)
        super().show()

    def addButton(self, text: str, foo, *b_args):
        button = Widgets.QPushButton(text)
        foo2 = partial(foo, *b_args)
        button.clicked.connect(foo2)
        self.button_layout.addWidget(button)
        self.__setattr__("BUTTON_"+text, button)

    def print(self, msg: str):
        self.output_box.append(msg)

    def closeEvent(self, event):
        if self.save:
            os.makedirs(LOG_DIR, exist_ok=True)
            file_name = datetime.now().strftime("%m-%d-%Y.txt")
            file_path = os.path.join(LOG_DIR, file_name)
            log = self.output_box.toPlainText()
            with open(file_path, 'a', encoding='utf-8') as file:
                file.write(log)
        super().closeEvent(event)








        
if __name__ == '__main__':
    app = Widgets.QApplication(sys.argv)
    window = Interface(None)

    test = lambda arg: print(arg)

    window.addButton("TEST", test, sys.argv[1])
    print(window.BUTTON_TEST)
    window.show()
    sys.exit(app.exec())