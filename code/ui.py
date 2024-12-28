import PySide6.QtWidgets as Widgets
from PySide6.QtCore import Qt
import sys
from functools import partial
from datetime import datetime
import os

# Default geometry for the main application window
GEOMETRY = (100, 100, 800, 600)

# Directory to store logs
LOG_DIR = 'logs'

class Interface(Widgets.QMainWindow):
    """
    Represents a graphical user interface.

    This class handles creating the main application window, adding buttons, displaying output,
    and saving logs of user actions.
    """

    class PrintRedirector:
        """
        Redirects print statements to the interface's output box.

        This is useful for displaying logs or outputs from other functions directly
        in the GUI.
        """
        def __init__(self, parent):
            self.parent = parent

        def write(self, msg):
            """
            Redirects messages to the interface's print method if non-empty.

            :param msg: The message to write.
            """
            if msg.strip():
                self.parent.print(msg)

        def flush(self):
            """
            Flush method for compatibility, does nothing.
            """
            pass

    def __init__(self, save_logs=True, geometry=GEOMETRY):
        """
        Initializes the interface window with default or specified settings.

        :param save_logs: Boolean indicating whether to save logs upon closing.
        :param geometry: Tuple specifying the geometry of the window (x, y, width, height).
        """
        super().__init__()
        self.setWindowTitle("Local Card Manager")
        self.setGeometry(*geometry)

        # Central widget and layout for the application
        self.central_w = Widgets.QWidget()
        self.setCentralWidget(self.central_w)

        self.layout = Widgets.QVBoxLayout()
        self.central_w.setLayout(self.layout)

        # Layout for buttons
        self.button_layout = Widgets.QHBoxLayout()
        self.layout.addLayout(self.button_layout)

        # Text output box for displaying messages
        self.output_box = Widgets.QTextEdit()
        self.output_box.setReadOnly(True)
        self.output_box.setSizePolicy(Widgets.QSizePolicy.Policy.Expanding, Widgets.QSizePolicy.Policy.Expanding)
        self.layout.addWidget(self.output_box)

        # Option to save logs when closing
        self.save = save_logs

    def show(self):
        """
        Overrides the show method to redirect standard output to the interface.
        """
        sys.stdout = self.PrintRedirector(self)
        super().show()

    def addButton(self, text: str, foo, *b_args):
        """
        Adds a button to the interface with a specified action.

        :param text: Label for the button.
        :param foo: Function to execute when the button is clicked.
        :param b_args: Arguments to pass to the function.
        """
        button = Widgets.QPushButton(text)
        foo2 = partial(foo, *b_args)  # Partially apply the arguments to the function
        button.clicked.connect(foo2)
        self.button_layout.addWidget(button)
        self.__setattr__("BUTTON_" + text.replace(" ", "_"), button)

    def print(self, msg: str):
        """
        Appends a message to the output box.

        :param msg: The message to display.
        """
        self.output_box.append(msg)

    def closeEvent(self, event):
        """
        Handles the event when the application is closed.

        Saves logs to a file if logging is enabled.

        :param event: The close event.
        """
        if self.save:
            os.makedirs(LOG_DIR, exist_ok=True)
            file_name = datetime.now().strftime("%m-%d-%Y.txt")
            file_path = os.path.join(LOG_DIR, file_name)
            log = self.output_box.toPlainText()
            with open(file_path, 'a', encoding='utf-8') as file:
                file.write(log)
        super().closeEvent(event)

if __name__ == '__main__':
    # Example usage of the Interface class
    app = Widgets.QApplication(sys.argv)
    window = Interface(save_logs=True)

    def test_function(arg):
        print(f"Button pressed with argument: {arg}")

    window.addButton("Test Button", test_function, "Test Argument")
    window.show()
    sys.exit(app.exec())
