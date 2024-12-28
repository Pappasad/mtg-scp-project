import os
import subprocess
import sys

env = os.path.abspath('.venv/Scripts/python.exe')
app = os.path.abspath('code/app.py')

subprocess.Popen([env, app, 'manager'], close_fds=True, creationflags=subprocess.CREATE_NO_WINDOW)

sys.exit()

    