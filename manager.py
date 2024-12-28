import os
import subprocess
import sys

env = os.path.abspath('.venv/Scripts/python.exe')
app = os.path.abspath('code/app.py')

subprocess.Popen([env, app], close_fds=True)

sys.exit()

    